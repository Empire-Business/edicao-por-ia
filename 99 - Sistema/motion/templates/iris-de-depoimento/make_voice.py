#!/usr/bin/env python3
"""EXEMPLO_1 — voz final: narração de IA (ElevenLabs já gerada, voz plASsyS7JE6GCAvx9uIc; nenhuma palavra alterada) + falas reais do Convidado
(janela da live do Instagram já isolada no ElevenLabs, ig-240-530-el.wav, sincronia 0 ms; nenhuma chamada paga nova).
- IA: só passa-alta 70 Hz (a voz sintética já é limpa).
- Convidado: cadeia dos cortes de live (HPF 85 Hz, −2,5 dB em 280 Hz, +2,5 dB em 3,2 kHz, +1,5 dB acima de 7 kHz, compressor 2,5:1);
  fades de 15/20 ms nas bordas.
- Cada bloco é igualado a −16 LUFS (IA e Convidado com o mesmo volume percebido nas trocas); respiros = silêncio inserido (edit/edl.json).
- Final −16 LUFS, limitador ≤ −1,5 dBTP.
Tempos da legenda L03 do Convidado: texto CONFERIDO alinhado às palavras da transcrição da live (tempos da fonte levados pela EDL); a voz final é transcrita só para conferência;
as palavras da IA vêm do alinhamento ElevenLabs. Saídas: renders/voice.wav, analysis/transcript_final_voice.json, analysis/voice_levels.json.
Run: ../../../.venv/bin/python src/make_voice.py
"""
import difflib, json, re, subprocess, unicodedata
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
SH = J.parent / 'material-compartilhado'
EDL = json.loads((J / 'edit/edl.json').read_text())
SR = 48000
TMP = J / 'tmp/voice'; TMP.mkdir(parents=True, exist_ok=True)
JCHAIN = ('highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,highshelf=f=7000:g=1.5,'
          'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=140:makeup=2')


def load(p, ss=None, t=None, af=None):
    a = ['ffmpeg', '-v', 'error'] + (['-ss', f'{ss:.4f}', '-t', f'{t:.4f}'] if ss is not None else []) + ['-i', str(p)]
    if af: a += ['-af', af]
    r = subprocess.run(a + ['-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.float32).copy()


def save(x, p):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-c:a', 'pcm_s24le', str(p)], input=x.astype(np.float32).tobytes(), check=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])


blocks, order = {}, []
for s in EDL['segments']:
    if s['take'] not in blocks:
        blocks[s['take']] = []; order.append(s['take'])
    blocks[s['take']].append(s)
ISO = SH / 'audio/ig-240-530-el.wav'
proc, levels = {}, {}
for b in order:
    segs = blocks[b]
    if segs[0]['src'] == 'tts':
        x = load(SH / f'audio/tts/{b}-v1.wav', af='highpass=f=70')
    else:
        parts = []
        for s in segs:
            d = s['out'] - s['in']
            y = load(ISO, s['in'] - 240.0, d)
            fi, fo = int(0.015 * SR), int(0.020 * SR)
            y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
            parts.append(y)
        raw = TMP / f'{b}-raw.wav'; save(np.concatenate(parts), raw)
        x = load(raw, af=JCHAIN)
    p = TMP / f'{b}-pre.wav'; save(x, p)
    I, _ = lufs(p)
    x = x * 10 ** ((-16.0 - I) / 20)
    proc[b] = x; levels[b] = {'measured_lufs': I, 'gain_db': round(-16.0 - I, 2), 'seconds': round(len(x) / SR, 3)}

# monta na linha do tempo da EDL (início de cada bloco = start do 1º pedaço)
total = int(round(EDL['duration'] * SR)) + SR
y = np.zeros(total, np.float32)
for b in order:
    i0 = int(round(blocks[b][0]['start'] * SR)); x = proc[b]
    y[i0:i0 + len(x)] += x
y = y[:int(round(EDL['duration'] * SR))]
pre = TMP / 'voice-pre.wav'; save(y, pre)
I0, _ = lufs(pre)
OUT = J / 'renders/voice.wav'; OUT.parent.mkdir(exist_ok=True)


def master(g):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled',
                    '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', str(OUT)], check=True)
    return lufs(OUT)


g = -16.0 - I0; I1, P1 = master(g)
for _ in range(3):
    if abs(I1 + 16.0) <= 0.3 and P1 <= -1.4: break
    g += -16.0 - I1; I1, P1 = master(g)

# ---------- palavras para a legenda ----------
EW = json.loads((J / 'analysis/edl_words.json').read_text())


def norm(w):
    w = unicodedata.normalize('NFD', w.lower().replace('%', ' por cento'))
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


tj = TMP / 'final-voice.json'
subprocess.run([str(SH / 'bin/withlock.py'), 'whisper', '--', str(SYS.parent / '.venv/bin/python'), str(SYS / 'tools/transcribe.py'), '--language', 'pt',
                '--output', str(tj), str(OUT)], check=True, capture_output=True, cwd=SYS)
IGW = [w for s in json.loads((SH / 'analysis/ig.transcript.json').read_text())['segments'] for w in s['words']]
words = []
for b in order:
    segs = blocks[b]
    if segs[0]['src'] == 'tts':
        words += [{'word': w['word'], 'start': w['start'], 'end': w['end'], 'speaker': 'ia', 'block': b} for w in EW if w['block'] == b]
        continue
    t0 = segs[0]['start']; t1 = segs[-1]['start'] + (segs[-1]['out'] - segs[-1]['in'])
    # tempos: palavras da transcrição da live (fonte) levadas para a linha do tempo pela EDL; a transcrição da voz final só confere o texto
    def to_out(ts):
        for sg in segs:
            if sg['in'] - 0.05 <= ts <= sg['out'] + 0.05:
                return sg['start'] + max(0.0, ts - sg['in'])
        return None
    src = [w for w in IGW if segs[0]['in'] - 0.1 <= w['start'] < segs[-1]['out']]
    hw = [{'word': w['word'], 'start': to_out(w['start']), 'end': to_out(min(w['end'], segs[-1]['out']))} for w in src]
    hw = [w for w in hw if w['start'] is not None and w['end'] is not None]
    ver = EDL['verified_text'][b].split()
    A = [norm(w) for w in ver]; B = [norm(w['word']) for w in hw]
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    tim = [None] * len(ver)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal' or (tag == 'replace' and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1): tim[i1 + k] = (hw[j1 + k]['start'], hw[j1 + k]['end'])
        elif tag == 'replace' and j2 > j1:
            a, z = hw[j1]['start'], hw[j2 - 1]['end']
            for k in range(i2 - i1): tim[i1 + k] = (a + (z - a) * k / (i2 - i1), a + (z - a) * (k + 1) / (i2 - i1))
    for k in range(len(ver)):
        if tim[k] is None:
            p = max([i for i in range(k) if tim[i]] or [-1]); q = min([i for i in range(k + 1, len(ver)) if tim[i]] or [len(ver)])
            a = tim[p][1] if p >= 0 else t0 + 0.05; z = tim[q][0] if q < len(ver) else t1 - 0.05
            n = q - p - 1; tim[k] = (a + (z - a) * (k - p - 1) / n, a + (z - a) * (k - p) / n)
    words += [{'word': w, 'start': round(max(t0, a), 3), 'end': round(min(t1, z), 3), 'speaker': 'convidado', 'block': b} for w, (a, z) in zip(ver, tim)]
segs_out, cur = [], []
for w in words:
    cur.append(w)
    if w['word'][-1] in '.?!:' or w is words[-1] or words[words.index(w) + 1]['block'] != w['block']:
        segs_out.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'speaker': cur[0]['speaker'], 'block': cur[0]['block'],
                         'text': ' '.join(z['word'] for z in cur), 'words': cur}); cur = []
(J / 'analysis/transcript_final_voice.json').write_text(json.dumps({'source': 'IA: alinhamento ElevenLabs; Convidado: texto conferido alinhado à transcrição da voz final',
    'heard_whisper': ' '.join(s['text'].strip() for s in json.loads(tj.read_text())['segments']), 'segments': segs_out}, ensure_ascii=False, indent=1))
(J / 'analysis/voice_levels.json').write_text(json.dumps({'blocks': levels, 'final_lufs': I1, 'final_tp': P1, 'duration': EDL['duration']}, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'blocks': levels}, ensure_ascii=False))
print(json.loads((J / 'analysis/transcript_final_voice.json').read_text())['heard_whisper'])
