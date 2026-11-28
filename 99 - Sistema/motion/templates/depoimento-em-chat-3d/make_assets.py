#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição 3D (three.js r186 + GSAP no HyperFrames).
- live/NNNN.jpg: quadros da live do Instagram (432x768 original → 360x640) indexados pelo QUADRO DE SAÍDA, só nos trechos do
  Instagram do EDL (a tela do celular desenha a live; nos trechos do áudio do Convidado a tela mostra a conversa).
- seq/long: vídeo longo LONGO_1 (editado pelo Cortez) 768x432; seq/s1..s10: vídeos curtos editados pelo Cortez (EXEMPLO_2, EXEMPLO_3, EXEMPLO_4) 270x480;
  seq/st1..st4: estilos diferentes, todos editados pelo Cortez (EXEMPLO_3 roxo, EXEMPLO_4 laranja, EXEMPLO_5 azul-claro, EXEMPLO_6 dourado) 270x480.
  Só entregas do próprio usuário; nada de terceiros nem logotipos.
- wave.json: envelope da voz final (60 por segundo) e forma de onda estática de cada áudio do Convidado (para a bolha de áudio).
- fontes da ID01 (Inter + IBM Plex Mono), three.js r186 + addons, GSAP.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
V = WS / '<PREENCHER: fonte ou prova própria>'
IG = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_6 = V / 'EXEMPLO_7 - Cortes das lives do Cortez/EXEMPLO_6 V1 - Corte 2 Nao e possivel que exista (previa).mp4'
YT = V / '<PREENCHER: fonte ou prova própria>'
# Reel real do Convidado (@perfil-do-convidado, 27/11/2026, baixado via ScrapeCreators a pedido do usuário; mudo; NÃO rotulado como editado pelo Cortez)
REEL = J.parent / '<PREENCHER: fonte ou prova própria>'
S = '270:480'
SEQ = {
    'long': ([(YT, 268.5, 1.6), (YT, 66.0, 1.6)], '768:432'),
    's1': ([(EXEMPLO_2, 46.0, 2.0)], S), 's2': ([(EXEMPLO_2, 40.5, 2.0)], S), 's3': ([(EXEMPLO_4, 54.55, 2.0)], S), 's4': ([(EXEMPLO_2, 57.0, 2.0)], S),
    's5': ([(EXEMPLO_4, 28.5, 2.0)], S), 's6': ([(EXEMPLO_3, 24.5, 2.0)], S), 's7': ([(EXEMPLO_2, 7.0, 2.0)], S), 's8': ([(EXEMPLO_4, 10.0, 2.0)], S),
    's9': ([(EXEMPLO_3, 41.0, 2.0)], S), 's10': ([(EXEMPLO_4, 31.5, 2.0)], S),
    'reel': ([(REEL, 0.0, 4.4)], '360:640'),
    'st1': ([(EXEMPLO_3, 9.0, 2.0)], S), 'st2': ([(EXEMPLO_4, 21.0, 2.0)], S), 'st3': ([(EXEMPLO_5, 4.0, 2.0)], S), 'st4': ([(EXEMPLO_6, 17.6, 2.0)], S),
}
rep = {}
for name, (parts, size) in SEQ.items():
    d = A / 'seq' / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    k = 0
    for src, ss, dur in parts:
        tmp = J / 'tmp' / f'seq-{name}'
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur), '-vf', f'fps=30,scale={size}:flags=lanczos',
                        '-q:v', '4', str(tmp / '%04d.jpg')], check=True)
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    rep[name] = {'frames': k, 'parts': [(p[0].name, p[1], p[2]) for p in parts]}

# quadros da live por quadro de saída
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
d = A / 'live'
shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
live = []
for s in edl['segments']:
    if s['src'] != 'ig':
        continue
    f0 = round(s['start'] * FPS)
    tmp = J / 'tmp/live-seg'
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['in']:.4f}", '-i', str(IG), '-frames:v', str(s['frames']), '-an',
                    '-vf', 'fps=30,scale=360:640:flags=lanczos,hqdn3d=1.2:1.2:2:2,unsharp=5:5:0.4:5:5:0', '-q:v', '3', str(tmp / '%04d.jpg')], check=True)
    fs = sorted(tmp.glob('*.jpg'))
    if len(fs) != s['frames']:
        raise SystemExit(f"{s['take']}: {len(fs)} quadros != {s['frames']}")
    for i, f in enumerate(fs):
        f.rename(d / f'{f0 + i:04d}.jpg'); live.append(f0 + i)
    shutil.rmtree(tmp)
rep['live'] = {'frames': len(live)}

# envelope da voz final
sr, x = wavfile.read(J / 'renders/voice.wav')
x = (x.mean(1) if x.ndim > 1 else x).astype(np.float32) / 32768
H = sr // 60
n = len(x) // H
env = 20 * np.log10(np.sqrt((x[:n * H].reshape(n, H) ** 2).mean(1)) + 1e-9)
envn = np.clip((env + 50) / 38, 0, 1)
notes = {}
for s in edl['takes']:
    if s['src'] != 'yt':
        continue
    ss = [g for g in edl['segments'] if g['take'] == s['id']]
    a, b = ss[0]['start'], ss[-1]['start'] + ss[-1]['frames'] / FPS
    seg = envn[int(a * 60):int(b * 60)]
    raw = np.array([float(np.mean(c)) if len(c) else 0.0 for c in np.array_split(env[int(a * 60):int(b * 60)], 34)])
    lo, hi = np.percentile(raw, 5), np.max(raw)
    bars = list(np.clip((raw - lo) / max(1e-6, hi - lo), 0, 1) ** 1.3)
    notes[s['id']] = {'start': round(a, 3), 'end': round(b, 3), 'bars': [round(v, 3) for v in bars]}
(A / 'wave.json').write_text(json.dumps({'rate': 60, 'env': [round(float(v), 3) for v in envn], 'notes': notes, 'live': live}))

F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-600-latin-ext.woff2', 'inter-700-latin.woff2',
          'inter-700-latin-ext.woff2', 'inter-800-latin.woff2', 'inter-800-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
G = J.parent / '<PREENCHER: fonte ou prova própria>'
for f in ['gsap.min.js', 'grain.png']:
    shutil.copyfile(C2 / f, A / f)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v['frames'] for k, v in rep.items()}))
