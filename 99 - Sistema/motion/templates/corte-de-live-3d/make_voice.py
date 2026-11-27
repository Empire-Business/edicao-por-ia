#!/usr/bin/env python3
# Modelo F22 Corte de Live 3D — derivado da edição de exemplo E119 (prévia aprovada pelo autor em 27/11/2026).
# Copie para jobs/<trabalho>/src e preencha: fonte, falas (TAKES), cenas/legendas, provas próprias e trilha. Ver README.md desta pasta.
"""Voz. Fonte (exemplo E119): janela 240–530 s do áudio original da live isolada no ElevenLabs Audio Isolation
(audio/ig-355-420-el.wav; defasagem medida 0,3 ms).
Cadeia: corte pelo EDL com fades 10/12 ms → ganho por fala (anfitrião e convidado no mesmo nível, alvo −17 LUFS por trecho) →
HPF 85 Hz → EQ de clareza (−2,5 dB em 280 Hz, +2,5 dB em 3,2 kHz, +1,5 dB acima de 7 kHz) → compressor suave 2,5:1 →
ganho fixo para −16 LUFS → limitador (≤ −1,5 dBTP). Saídas: renders/voice.wav, analysis/voice_levels.json, analysis/splice_check.json."""
import json, subprocess
import numpy as np
from pathlib import Path
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
ISO = J / 'audio/<janela>-el.wav'   # janela do áudio original isolada (local ou ElevenLabs com autorização)
OFF = 240.0
SR = 48000
edl = json.loads((J / 'edit/edl.json').read_text())
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


segs = edl['segments']
if segs[0]['in'] < OFF or max(s['in'] + s['frames'] / edl['fps'] for s in segs) > OFF + 290:
    raise SystemExit('EDL fora da janela isolada no ElevenLabs')
# ganho por fala: mede cada take inteiro na voz isolada
take_gain = {}
for tid in dict.fromkeys(s['take'] for s in segs):
    ss = [s for s in segs if s['take'] == tid]
    a, b = ss[0]['in'] - OFF, ss[-1]['in'] + ss[-1]['frames'] / edl['fps'] - OFF
    I, _ = lufs(ISO, a, b - a)
    take_gain[tid] = round(TARGET_TAKE - I, 2)

f = []
for i, s in enumerate(segs):
    d = s['frames'] / edl['fps']
    a = s['in'] - OFF
    f.append(f"[0:a]atrim={a:.4f}:{a + d:.4f},asetpts=PTS-STARTPTS,volume={take_gain[s['take']]}dB,afade=t=in:d=0.010,afade=t=out:st={max(0, d - 0.012):.4f}:d=0.012[a{i}]")
CHAIN = ('highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,highshelf=f=7000:g=1.5,'
         'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=140:makeup=2')
f.append(''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1,{CHAIN}[o]')
raw = TMP / 'voice-raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ISO), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', str(raw)], check=True)
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

sr, x = wavfile.read(ISO)
x = x.astype(np.float32) / 32768
x = x.mean(1) if x.ndim > 1 else x


def dbfs(a, b):
    seg = x[max(0, int((a - OFF) * sr)):int((b - OFF) * sr)]
    return round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)


checks = [{'take': s['take'], 'piece': s['piece'], 'in_db': dbfs(s['in'], s['in'] + 0.03),
           'out_db': dbfs(s['in'] + s['frames'] / edl['fps'] - 0.03, s['in'] + s['frames'] / edl['fps'])} for s in segs]
(J / 'analysis/splice_check.json').write_text(json.dumps({'source': 'audio/<janela>-el.wav', 'all': checks}, ensure_ascii=False, indent=1))
rep = {'source': 'audio/<janela>-el.wav — ElevenLabs Audio Isolation da janela 240–530 s do áudio original (serviço pago: só com autorização do usuário)',
       'per_take_gain_db': take_gain, 'before': {'lufs': I0, 'peak_dbtp': P0}, 'fixed_gain_db': round(g, 2), 'final_lufs': I2, 'final_true_peak_dbtp': P2,
       'duration': edl['duration'], 'chain': 'corte EDL + fades → ganho por fala → ' + CHAIN + ' → ganho fixo → alimiter'}
(J / 'analysis/voice_levels.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
