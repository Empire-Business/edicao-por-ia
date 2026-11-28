#!/usr/bin/env python3
"""EXEMPLO_1 — voz. Fontes: janelas das duas lives já isoladas no ElevenLabs Audio Isolation (material-compartilhado/audio/*-el.wav;
chamada única do lote autorizada pelo usuário: "se precisar use eleven labs"; sincronia conferida em 0 ms). Nenhuma chamada nova.
Cadeia (igual ao EXEMPLO_2): corte pelo EDL com fades 10/12 ms → ganho por fala (alvo −17 LUFS por trecho; YT e IG no mesmo nível) →
HPF 85 Hz → EQ de clareza (−2,5 dB em 280 Hz, +2,5 dB em 3,2 kHz, +1,5 dB acima de 7 kHz) → compressor suave 2,5:1 →
ganho fixo para −16 LUFS → limitador (≤ −1,5 dBTP). Saídas: renders/voice.wav, analysis/voice_levels.json, analysis/splice_check.json."""
import json, subprocess
import numpy as np
from pathlib import Path
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
A = J.parent / 'material-compartilhado/audio'
WIN = [('yt', 626, 672), ('yt', 1370, 1396), ('yt', 1682, 1762), ('yt', 1279, 1350), ('yt', 773, 806), ('yt', 163, 206),
       ('ig', 655, 712), ('ig', 757, 782), ('ig', 240, 530)]
SR = 48000
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
OUT = J / 'renders/voice.wav'
OUT.parent.mkdir(exist_ok=True)
TMP = J / 'tmp'
TMP.mkdir(exist_ok=True)
TARGET_TAKE = -17.0
# fim de fala colado na palavra seguinte da fonte (sem silêncio real): fade de saída mais longo nesses dois fechamentos
FADE_OUT = {'t05': 0.025}   # V2: fades de 20 ms em todas as emendas; 25 ms no fim colado ao conectivo excluído


def win(s):
    for src, a, b in WIN:
        if src == s['src'] and a <= s['in'] and s['in'] + s['frames'] / FPS <= b:
            return A / f'{src}-{a}-{b}-el.wav', float(a)
    raise SystemExit(f'segmento fora das janelas isoladas: {s}')


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    o = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in o if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1]))


segs = edl['segments']
files = []
for s in segs:
    p, off = win(s)
    if str(p) not in files:
        files.append(str(p))
take_gain = {}
for tid in dict.fromkeys(s['take'] for s in segs):
    ss = [s for s in segs if s['take'] == tid]
    p, off = win(ss[0])
    a, b = ss[0]['in'] - off, ss[-1]['in'] + ss[-1]['frames'] / FPS - off
    I, _ = lufs(p, a, b - a)
    take_gain[tid] = round(TARGET_TAKE - I, 2)

f = []
for i, s in enumerate(segs):
    p, off = win(s)
    k = files.index(str(p))
    d = s['frames'] / FPS
    a = s['in'] - off
    last = i + 1 == len(segs) or segs[i + 1]['take'] != s['take']
    fo = FADE_OUT.get(s['take'], 0.020) if last else 0.020
    f.append(f"[{k}:a]atrim={a:.4f}:{a + d:.4f},asetpts=PTS-STARTPTS,aformat=sample_rates={SR}:channel_layouts=mono,volume={take_gain[s['take']]}dB,"
             f"afade=t=in:d=0.020,afade=t=out:st={max(0, d - fo):.4f}:d={fo}[a{i}]")
CHAIN = ('highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,highshelf=f=7000:g=1.5,'
         'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=140:makeup=2')
f.append(''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1,{CHAIN}[o]')
raw = TMP / 'voice-raw.wav'
ins = [x for p in files for x in ('-i', p)]
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

cache = {}


def dbfs(s, a, b):
    p, off = win(s)
    if p not in cache:
        sr, x = wavfile.read(p); x = x.astype(np.float32) / 32768
        cache[p] = (sr, x.mean(1) if x.ndim > 1 else x)
    sr, x = cache[p]
    seg = x[max(0, int((a - off) * sr)):int((b - off) * sr)]
    return round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)


checks = [{'take': s['take'], 'piece': s['piece'], 'in_db': dbfs(s, s['in'], s['in'] + 0.03),
           'out_db': dbfs(s, s['in'] + s['frames'] / FPS - 0.03, s['in'] + s['frames'] / FPS)} for s in segs]
(J / 'analysis/splice_check.json').write_text(json.dumps({'sources': [Path(p).name for p in files], 'all': checks}, ensure_ascii=False, indent=1))
rep = {'sources': [f'material-compartilhado/audio/{Path(p).name}' for p in files],
       'note': 'ElevenLabs Audio Isolation (chamada única do lote, autorizada pelo usuário); nenhuma chamada nova neste trabalho',
       'per_take_gain_db': take_gain, 'before': {'lufs': I0, 'peak_dbtp': P0}, 'fixed_gain_db': round(g, 2), 'final_lufs': I2, 'final_true_peak_dbtp': P2,
       'duration': edl['duration'], 'chain': 'corte EDL + fades → ganho por fala → ' + CHAIN + ' → ganho fixo → alimiter'}
(J / 'analysis/voice_levels.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: rep[k] for k in ('per_take_gain_db', 'final_lufs', 'final_true_peak_dbtp', 'duration')}, ensure_ascii=False))
print(json.dumps(checks))
