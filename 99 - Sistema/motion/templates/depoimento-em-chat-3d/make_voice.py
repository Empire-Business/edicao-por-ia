#!/usr/bin/env python3
"""EXEMPLO_1 — voz. Fontes isoladas no ElevenLabs Audio Isolation (lote pago autorizado pelo usuário: "se precisar use eleven labs";
sincronia conferida em 0 ms): live do Instagram = material-compartilhado/audio/ig-240-530-el.wav (janela 240–530 s);
áudio do Convidado tocado na live do YouTube = material-compartilhado/audio/yt-1682-1762-el.wav (janela 1682–1762 s).
Cadeia: corte pelo EDL com fades 10/12 ms → ganho por trecho (alvo −17 LUFS) → no áudio de WhatsApp, leve corpo (+2 dB em 200 Hz) e
menos chiado (−2 dB acima de 7 kHz) → HPF 85 Hz → EQ de clareza (−2,5 dB em 280 Hz, +2,5 dB em 3,2 kHz, +1,5 dB acima de 7 kHz) →
compressor 2,5:1 → ganho fixo para −16 LUFS → limitador (≤ −1,5 dBTP). Saídas: renders/voice.wav, analysis/voice_levels.json,
analysis/splice_check.json."""
import json, subprocess
import numpy as np
from pathlib import Path
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
A = J.parent / 'material-compartilhado/audio'
ISO = {'ig': (A / 'ig-240-530-el.wav', 240.0, 290.0), 'yt': (A / 'yt-1682-1762-el.wav', 1682.0, 80.0)}
IDX = {'ig': 0, 'yt': 1}
SR = 48000
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
OUT = J / 'renders/voice.wav'
OUT.parent.mkdir(exist_ok=True)
TMP = J / 'tmp'
TMP.mkdir(exist_ok=True)
TARGET_TAKE = -17.0
import os
PRES = float(os.environ.get('VN_PRESENCE_DB', '2'))   # presença no áudio de WhatsApp (dB em 3 kHz)


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    o = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in o if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1]))


segs = edl['segments']
for s in segs:
    f, off, dur = ISO[s['src']]
    if s['in'] < off or s['in'] + s['frames'] / FPS > off + dur:
        raise SystemExit(f"{s['take']}: fora da janela isolada")
take_gain = {}
for tid in dict.fromkeys(s['take'] for s in segs):
    ss = [s for s in segs if s['take'] == tid]
    f, off, _ = ISO[ss[0]['src']]
    a, b = ss[0]['in'] - off, ss[-1]['in'] + ss[-1]['frames'] / FPS - off
    I, _ = lufs(f, a, b - a)
    take_gain[tid] = round(TARGET_TAKE - I, 2)

f = []
for i, s in enumerate(segs):
    d = s['frames'] / FPS
    a = s['in'] - ISO[s['src']][1]
    # V2b (nota do diretor): no áudio de WhatsApp, +2 dB de presença em 3 kHz para a fala lo-fi atravessar a trilha
    pre = f',equalizer=f=200:t=q:w=1.2:g=2,equalizer=f=3000:t=q:w=0.9:g={PRES},highshelf=f=7000:g=-2' if s['src'] == 'yt' else ''
    f.append(f"[{IDX[s['src']]}:a]atrim={a:.4f}:{a + d:.4f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,volume={take_gain[s['take']]}dB{pre},"
             f"afade=t=in:d=0.010,afade=t=out:st={max(0, d - 0.012):.4f}:d=0.012[a{i}]")
CHAIN = ('highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,highshelf=f=7000:g=1.5,'
         'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=140:makeup=2')
f.append(''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1,{CHAIN}[o]')
raw = TMP / 'voice-raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ISO['ig'][0]), '-i', str(ISO['yt'][0]), '-filter_complex', ';'.join(f), '-map', '[o]',
                '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', str(raw)], check=True)
I0, P0 = lufs(raw)
g = -16.0 - I0


def master(gain):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', f'volume={gain:.2f}dB,alimiter=limit=0.79:attack=3:release=60:level=disabled',
                    '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', str(OUT)], check=True)
    return lufs(OUT)


I2, P2 = master(g)
for _ in range(3):
    if abs(I2 + 16.0) <= 0.3 and P2 <= -1.5:
        break
    g += -16.0 - I2
    I2, P2 = master(g)

checks = []
for k, (path, off, _) in ISO.items():
    sr, x = wavfile.read(path)
    x = x.astype(np.float32) / 32768
    x = x.mean(1) if x.ndim > 1 else x
    for s in segs:
        if s['src'] != k:
            continue
        def dbfs(a, b):
            seg = x[max(0, int((a - off) * sr)):int((b - off) * sr)]
            return round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)
        e = s['in'] + s['frames'] / FPS
        checks.append({'take': s['take'], 'piece': s['piece'], 'in_db': dbfs(s['in'], s['in'] + 0.03), 'out_db': dbfs(e - 0.03, e)})
(J / 'analysis/splice_check.json').write_text(json.dumps({'sources': {k: str(v[0].name) for k, v in ISO.items()}, 'all': checks}, ensure_ascii=False, indent=1))
rep = {'sources': {k: f'material-compartilhado/audio/{v[0].name} (ElevenLabs Audio Isolation, janela {v[1]:.0f}–{v[1] + v[2]:.0f} s)' for k, v in ISO.items()},
       'per_take_gain_db': take_gain, 'before': {'lufs': I0, 'peak_dbtp': P0}, 'fixed_gain_db': round(g, 2), 'final_lufs': I2, 'final_true_peak_dbtp': P2,
       'duration': edl['duration'], 'chain': 'corte EDL + fades → ganho por trecho → (WhatsApp: +2 dB 200 Hz, −2 dB >7 kHz) → ' + CHAIN + ' → ganho fixo → alimiter'}
(J / 'analysis/voice_levels.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: rep[k] for k in ('per_take_gain_db', 'final_lufs', 'final_true_peak_dbtp', 'duration')}, ensure_ascii=False))
print([c for c in checks if c['in_db'] > -30 or c['out_db'] > -30])
