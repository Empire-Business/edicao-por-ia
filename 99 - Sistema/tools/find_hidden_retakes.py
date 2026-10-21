#!/usr/bin/env python3
"""Find recording errors that a whole-file transcript hides: false starts, restarts and leftover tails.

Why (author, 20/10/2026): "eu cometi alguns erros de gravação que você não cortou" and "no vídeo do Felca eu cometi um
erro perto de 1:17 e você não tirou". Whisper often swallows an aborted attempt into ONE long word ("pessoas" lasting
2 s) or skips it entirely, so a clean-looking transcript is not proof of a clean take. Run this on the source voice
before choosing takes AND on the final cut voice before delivery.

Checks (local, no network):
- long words: a single word lasting more than --long-word seconds;
- voiced gaps: speech energy between two words that the transcript did not write down;
- repeats: the same 2–4 word sequence said again within --repeat-window seconds (restart of a phrase);
- adjacent duplicate words ("o o", "nossa nossa").
With --retranscribe each suspicious window is cut, raised by --gain dB and transcribed alone with tools/transcribe.py,
which usually reveals the hidden attempt ("O fato é que a IA… / O fato é…").
The report lists candidates only; choosing the take stays an editorial decision (method/SPEECH_ERROR_POLICY.md).

Usage:
  python3 tools/find_hidden_retakes.py --audio <voz.wav> --transcript <transcript.json> --out <report.json> [--retranscribe]
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, tempfile, unicodedata
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def norm(w: str) -> str:
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def words_of(transcript: dict) -> list[dict]:
    out = []
    for s in transcript.get('segments', []):
        for w in s.get('words', []) or []:
            t = str(w.get('word', '')).strip()
            if t:
                out.append({'w': t, 'n': norm(t), 's': float(w['start']), 'e': float(w['end'])})
    return sorted(out, key=lambda x: x['s'])


def envelope(audio: Path, sr: int = 16000, hop: float = 0.01) -> np.ndarray:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    h = int(sr * hop); m = len(x) // h
    return 20 * np.log10(np.sqrt((x[:m * h].reshape(m, h) ** 2).mean(1)) + 1e-9)


def voiced(env: np.ndarray, a: float, b: float, threshold: float, min_len: float = 0.08, join: float = 0.15,
           hop: float = 0.01) -> list[list[float]]:
    """Speech islands (energy above threshold) inside [a, b], close islands merged."""
    out, on = [], None
    lo, hi = max(0, int(round(a / hop))), min(len(env), int(round(b / hop)))
    for i in range(lo, hi):
        v = env[i] > threshold
        if v and on is None:
            on = i
        if (not v or i == hi - 1) and on is not None:
            end = i if not v else i + 1
            if out and on * hop - out[-1][1] < join:
                out[-1][1] = end * hop
            else:
                out.append([on * hop, end * hop])
            on = None
    return [[round(s, 2), round(e, 2)] for s, e in out if e - s >= min_len]


def find(words: list[dict], env: np.ndarray | None, long_word: float = 0.8, gap: float = 0.5, threshold: float = -45.0,
         repeat_window: float = 6.0) -> list[dict]:
    cands = []
    for w in words:
        d = w['e'] - w['s']
        if d > long_word:
            item = {'type': 'long_word', 'start': round(w['s'], 2), 'end': round(w['e'], 2), 'word': w['w'], 'seconds': round(d, 2)}
            if env is not None:
                item['voiced'] = voiced(env, w['s'], w['e'], threshold)
            cands.append(item)
    for a, b in zip(words, words[1:]):
        if b['s'] - a['e'] > gap and env is not None:
            v = voiced(env, a['e'] + 0.05, b['s'] - 0.05, threshold)
            if v:
                cands.append({'type': 'voiced_gap', 'start': round(a['e'], 2), 'end': round(b['s'], 2),
                              'after': a['w'], 'before': b['w'], 'voiced': v})
        if a['n'] and a['n'] == b['n'] and len(a['n']) > 1:
            cands.append({'type': 'adjacent_duplicate', 'start': round(a['s'], 2), 'end': round(b['e'], 2), 'word': b['w']})
    seen = set()
    for n in (4, 3, 2):
        for i in range(len(words) - n + 1):
            gram = tuple(x['n'] for x in words[i:i + n])
            if not all(gram) or sum(len(g) for g in gram) < 8 or (i, i) in seen:
                continue
            for j in range(i + n, len(words) - n + 1):
                if words[j]['s'] - words[i]['s'] > repeat_window:
                    break
                if tuple(x['n'] for x in words[j:j + n]) == gram:
                    seen.update((i + k, i + k) for k in range(n))
                    cands.append({'type': 'repeat', 'start': round(words[i]['s'], 2), 'end': round(words[j + n - 1]['e'], 2),
                                  'phrase': ' '.join(x['w'] for x in words[i:i + n]),
                                  'first_at': round(words[i]['s'], 2), 'again_at': round(words[j]['s'], 2)})
                    break
    return sorted(cands, key=lambda c: c['start'])


def retranscribe(audio: Path, cands: list[dict], gain: float, language: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        for k, c in enumerate(cands):
            a, b = max(0.0, c['start'] - 0.3), c['end'] + 0.3
            wav, js = Path(tmp) / f'w{k}.wav', Path(tmp) / f'w{k}.json'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.2f}', '-to', f'{b:.2f}', '-i', str(audio),
                            '-ac', '1', '-ar', '16000', '-af', f'volume={gain}dB', str(wav)], check=True)
            r = subprocess.run([sys.executable, str(HERE / 'transcribe.py'), str(wav), '--output', str(js), '--language', language],
                               capture_output=True, text=True)
            if r.returncode or not js.exists():
                c['window_text'] = None
                c['window_error'] = (r.stderr or '')[-200:]
                continue
            d = json.loads(js.read_text())
            c['window_text'] = ' | '.join(' '.join(f"{w['word'].strip()}@{w['start'] + a:.2f}" for w in s.get('words', []))
                                          for s in d.get('segments', []))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--audio', required=True, help='voz (de preferência isolada) na mesma escala de tempo da transcrição')
    ap.add_argument('--transcript', required=True, help='JSON com segments[].words[] (start/end/word)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--long-word', type=float, default=0.8)
    ap.add_argument('--gap', type=float, default=0.5)
    ap.add_argument('--threshold', type=float, default=-45.0, help='dBFS considerado voz')
    ap.add_argument('--repeat-window', type=float, default=6.0)
    ap.add_argument('--retranscribe', action='store_true')
    ap.add_argument('--gain', type=float, default=8.0)
    ap.add_argument('--language', default='pt')
    a = ap.parse_args(argv)
    words = words_of(json.loads(Path(a.transcript).read_text()))
    env = envelope(Path(a.audio))
    cands = find(words, env, a.long_word, a.gap, a.threshold, a.repeat_window)
    if a.retranscribe and cands:
        retranscribe(Path(a.audio), cands, a.gain, a.language)
    rep = {'audio': a.audio, 'transcript': a.transcript, 'words': len(words), 'candidates': cands,
           'settings': {'long_word': a.long_word, 'gap': a.gap, 'threshold_dbfs': a.threshold, 'repeat_window': a.repeat_window},
           'note': 'Candidates only. Open each window (and its retranscription) before cutting; keep the last complete take.'}
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({'candidates': len(cands), 'by_type': {t: sum(c['type'] == t for c in cands) for t in sorted({c['type'] for c in cands})},
                      'out': a.out}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
