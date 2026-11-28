#!/usr/bin/env python3
"""EXEMPLO_1 — voz. Fontes: janelas do áudio original da live do YouTube isoladas no ElevenLabs Audio Isolation (feitas pelo coordenador
do lote 3, autorizadas pelo usuário; sincronia conferida 0 ms): yt-363-401-el.wav (363–401 s) e yt-442-497-el.wav (442–497 s).
Nenhuma chamada paga neste corte.
Cadeia: corte pelo EDL com fades 15/20 ms nas emendas → ganho por fala (−17 LUFS por trecho) →
HPF 85 Hz → EQ de clareza (−2,5 dB em 280 Hz, +2,5 dB em 3,2 kHz, +1,5 dB acima de 7 kHz) → compressor suave 2,5:1 →
ganho fixo para −16 LUFS → limitador (≤ −1,5 dBTP). Saídas: renders/voice.wav, analysis/voice_levels.json, analysis/splice_check.json."""
import json, subprocess
import numpy as np
from pathlib import Path
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
A = J.parent / 'material-compartilhado/audio'
ISO = [('yt', A / 'yt-363-401-el.wav', 363.0, 401.0), ('yt', A / 'yt-442-497-el.wav', 442.0, 497.0)]
SR = 48000
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
OUT = J / 'renders/voice.wav'
OUT.parent.mkdir(exist_ok=True)
TMP = J / 'tmp'
TMP.mkdir(exist_ok=True)
TARGET_TAKE = -17.0


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    o = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in o if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1]))


def iso_for(s):
    for k, (src, p, a, b) in enumerate(ISO):
        if src == s['src'] and a <= s['in'] and s['in'] + s['frames'] / FPS <= b:
            return k
    raise SystemExit(f"trecho fora das janelas isoladas: {s['take']} {s['in']}")


segs = edl['segments']
for s in segs:
    s['iso'] = iso_for(s)
take_gain = {}
for tid in dict.fromkeys(s['take'] for s in segs):
    ss = [s for s in segs if s['take'] == tid]
    src, p, off, _ = ISO[ss[0]['iso']]
    a, b = ss[0]['in'] - off, ss[-1]['in'] + ss[-1]['frames'] / FPS - off
    I, _ = lufs(p, a, b - a)
    take_gain[tid] = round(TARGET_TAKE - I, 2)

f = []
for i, s in enumerate(segs):
    d = s['frames'] / FPS
    off = ISO[s['iso']][2]
    a = s['in'] - off
    f.append(f"[{s['iso']}:a]atrim={a:.4f}:{a + d:.4f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,volume={take_gain[s['take']]}dB,"
             f"afade=t=in:d=0.015,afade=t=out:st={max(0, d - 0.020):.4f}:d=0.020[a{i}]")
CHAIN = ('highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,highshelf=f=7000:g=1.5,'
         'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=140:makeup=2')
f.append(''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1,{CHAIN}[o]')
raw = TMP / 'voice-raw.wav'
ins = [x for _, p, _, _ in ISO for x in ('-i', str(p))]
subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', str(raw)], check=True)
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

X = {}
for k, (src, p, off, _) in enumerate(ISO):
    sr, x = wavfile.read(p)
    x = x.astype(np.float32) / 32768
    X[k] = (sr, x.mean(1) if x.ndim > 1 else x, off)


def dbfs(k, a, b):
    sr, x, off = X[k]
    seg = x[max(0, int((a - off) * sr)):int((b - off) * sr)]
    return round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)


checks = [{'take': s['take'], 'piece': s['piece'], 'in_db': dbfs(s['iso'], s['in'], s['in'] + 0.03),
           'out_db': dbfs(s['iso'], s['in'] + s['frames'] / FPS - 0.03, s['in'] + s['frames'] / FPS)} for s in segs]
(J / 'analysis/splice_check.json').write_text(json.dumps({'sources': [str(p.name) for _, p, _, _ in ISO], 'all': checks}, ensure_ascii=False, indent=1))
rep = {'sources': [f'material-compartilhado/audio/{p.name} — ElevenLabs Audio Isolation ({src} {a:.0f}–{b:.0f} s)' for src, p, a, b in ISO],
       'per_take_gain_db': take_gain, 'before': {'lufs': I0, 'peak_dbtp': P0}, 'fixed_gain_db': round(g, 2), 'final_lufs': I2, 'final_true_peak_dbtp': P2,
       'duration': edl['duration'], 'chain': 'corte EDL + fades → ganho por fala → ' + CHAIN + ' → ganho fixo → alimiter'}
(J / 'analysis/voice_levels.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
print([c for c in checks if c['in_db'] > -40 or c['out_db'] > -40])
