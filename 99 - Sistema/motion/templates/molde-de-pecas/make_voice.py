#!/usr/bin/env python3
"""EXEMPLO_1 — voz final a partir da narração ElevenLabs já gerada (voz plASsyS7JE6GCAvx9uIc, texto d11.txt; nenhuma palavra alterada).
Só INSERE respiros entre as frases (nunca remove áudio): divide no ponto de menor energia do intervalo entre a última palavra de uma
frase e a primeira da próxima (alinhamento ElevenLabs), com microfades de 6 ms, e acrescenta silêncio. Nada é cortado, então nenhuma
palavra perde começo/fim. Normaliza para −16 LUFS (limitador −1,5 dBTP).
Saídas: renders/voice.wav, analysis/transcript_final_voice.json (tempos das palavras na voz final), edit/edl.json, analysis/voice_levels.json.
Run: ../../../.venv/bin/python src/make_voice.py
"""
import json, subprocess
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado/audio/tts'
SRC = SH / 'd11-v1.wav'
WJ = json.loads((SH / 'd11-v1.words.json').read_text())['words']
SR = 48000
LEAD, TAIL = 0.10, 0.32
# respiro extra depois de cada frase (índice da última palavra da frase → segundos)
PAUSE_AFTER = {'ouvindo?': 0.15, 'gerei.': 0.30, 'vídeo?': 0.12, 'faço.': 0.30, 'animação.': 0.35, 'fim.': 0.30, 'grava.': 0.28}


def load(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.float32).copy()


x = load(SRC)
env = np.sqrt(np.convolve(x ** 2, np.ones(240) / 240, mode='same'))      # 5 ms
cuts = []   # (ponto de divisão na fonte, pausa inserida, palavra)
for k, w in enumerate(WJ[:-1]):
    if w['word'] in PAUSE_AFTER:
        a, b = int(w['end'] * SR), int((WJ[k + 1]['start'] - 0.012) * SR)   # margem antes do ataque da palavra seguinte
        lo, hi = min(a, b), max(a, b)
        i = lo + int(np.argmin(env[lo:hi + 1])) if hi > lo else lo
        cuts.append((i, PAUSE_AFTER[w['word']], w['word']))
pieces, last, shift, shifts = [np.zeros(int(LEAD * SR), np.float32)], 0, LEAD, []
F = int(0.006 * SR)
for i, p, wd in cuts:
    seg = x[last:i].copy()
    if last > 0: seg[:F] *= np.linspace(0, 1, F)
    seg[-F:] *= np.linspace(1, 0, F)
    pieces += [seg, np.zeros(int(p * SR), np.float32)]
    shifts.append((last / SR, i / SR, shift)); shift += p; last = i
seg = x[last:].copy(); seg[:F] *= np.linspace(0, 1, F); pieces.append(seg); shifts.append((last / SR, len(x) / SR, shift))
pieces.append(np.zeros(int(TAIL * SR), np.float32))
y = np.concatenate(pieces)
raw = J / 'tmp/voice-raw.wav'; raw.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-c:a', 'pcm_s16le', str(raw)], input=y.tobytes(), check=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])


I0, _ = lufs(raw)
out = J / 'renders/voice.wav'; out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', f'highpass=f=70,volume={-16.0 - I0:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled',
                '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', str(out)], check=True)
I1, P1 = lufs(out)


def tmap(t, end=False):
    for a, b, s in shifts:
        if (a < t <= b + 1e-6) if end else (a - 1e-6 <= t < b):
            return t + s
    return t + shifts[-1][2]


words = [{'word': w['word'], 'start': round(tmap(w['start']), 3), 'end': round(tmap(w['end'], True), 3)} for w in WJ]
segs, cur = [], []
for w in words:
    cur.append(w)
    if w['word'][-1] in '.?!':
        segs.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'text': ' '.join(z['word'] for z in cur), 'words': cur}); cur = []
if cur: segs.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'text': ' '.join(z['word'] for z in cur), 'words': cur})
SPEECH = round(len(y) / SR, 3)
(J / 'analysis').mkdir(exist_ok=True); (J / 'edit').mkdir(exist_ok=True)
(J / 'analysis/transcript_final_voice.json').write_text(json.dumps({'source': 'alinhamento ElevenLabs deslocado pelos respiros inseridos', 'segments': segs}, ensure_ascii=False, indent=1))
(J / 'edit/edl.json').write_text(json.dumps({'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'format_code': 'F10', 'visual_identity': 'IDP01',
    'duration': SPEECH, 'fps': 30, 'source': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d11-v1.wav',
    'policy': 'narração IA inteira, sem remoção; só respiros inseridos entre frases no mínimo de energia do intervalo',
    'lead_s': LEAD, 'tail_s': TAIL, 'pieces': [{'src_in': round(a, 4), 'src_out': round(b, 4), 'out_start': round(a + s, 4)} for a, b, s in shifts],
    'inserted_pauses': [{'after': wd, 'src_t': round(i / SR, 4), 'seconds': p} for i, p, wd in cuts]}, ensure_ascii=False, indent=1))
(J / 'analysis/voice_levels.json').write_text(json.dumps({'raw_lufs': I0, 'final_lufs': I1, 'final_tp': P1, 'duration': SPEECH}, indent=1))
print(json.dumps({'speech': SPEECH, 'lufs': I1, 'tp': P1, 'cuts': [(round(i / SR, 3), wd) for i, p, wd in cuts]}, ensure_ascii=False))
