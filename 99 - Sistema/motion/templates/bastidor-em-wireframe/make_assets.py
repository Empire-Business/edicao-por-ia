#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição (todos copiados para dentro do trabalho; nada referenciado fora da fábrica).
Prova = só entregas do próprio usuário feitas pelo Cortez (EXEMPLO_2 Oferta, EXEMPLO_3/EXEMPLO_4 criativos), conferidas quadro a quadro, sem logotipos:
- cenas candidatas ("escolhi as cenas"): recortes 16:9 de cenas que o Cortez pesquisou/usou nessas entregas;
- sequências JPG por quadro (texturas determinísticas do three.js): scrA (call center, EXEMPLO_2), scrB (apresentador com legenda, EXEMPLO_2),
  scrC (animação de chips, EXEMPLO_4) e o vídeo do herói em tela cheia (EXEMPLO_4, HTML <video>, quadros-chave densos).
- fontes ID05 (Manrope, JetBrains Mono), three.js r186 (ESM) + addons, GSAP, textura de grão.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, a)], check=True)


rep = {}
# 1) cenas candidatas 16:9 (640x360)
SC = [('agenda', EXEMPLO_2, 0.4, 'crop=1080:608:0:0'), ('reuniao', EXEMPLO_2, 7.0, 'crop=800:450:140:690'), ('escritorio', EXEMPLO_2, 15.8, 'crop=1080:608:0:150'),
      ('callcenter', EXEMPLO_2, 17.6, 'crop=1080:608:0:330'), ('relogio', EXEMPLO_2, 23.6, 'crop=800:450:140:690'), ('crm', EXEMPLO_3, 47.0, 'crop=1080:608:0:70')]
(A / 'scenes').mkdir(exist_ok=True)
for name, src, t, crop in SC:
    ff('-ss', t, '-i', src, '-frames:v', 1, '-vf', f'{crop},scale=640:360:flags=lanczos', '-q:v', 3, A / f'scenes/{name}.jpg')
rep['scenes'] = [(n, s.name, t) for n, s, t, _ in SC]

# 2) sequências por quadro para a tela 3D (540x960)
SEQ = {'scrA': (EXEMPLO_2, 17.3, 1.4), 'scrB': (EXEMPLO_2, 12.1, 2.7), 'scrC': (EXEMPLO_4, 0.3, 5.6)}
for name, (src, ss, dur) in SEQ.items():
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    ff('-ss', ss, '-i', src, '-t', dur, '-vf', 'fps=30,scale=540:960:flags=lanczos', '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
    rep[name] = {'src': src.name, 'ss': ss, 'dur': dur, 'frames': len(list(d.glob('*.jpg')))}

# 3) herói em tela cheia (mesma linha do tempo de scrC: começa em EXEMPLO_4 0,3 s)
ff('-ss', 0.3, '-i', EXEMPLO_4, '-t', 6.4, '-an', '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-crf', 14, '-preset', 'medium', '-g', 15,
   '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', A / 'hero.mp4')
rep['hero'] = {'src': EXEMPLO_4.name, 'ss': 0.3, 'dur': 6.4}

# 4) fontes, three.js, gsap, grão
F = SYS / 'assets/fonts/portable'
for f in ['manrope-variable.ttf', 'manrope-OFL.txt', 'jetbrains-mono-variable.ttf', 'jetbrains-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); dst.mkdir()
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
(dst / 'addons/objects').mkdir(parents=True, exist_ok=True); shutil.copyfile(T3 / 'examples/jsm/objects/Reflector.js', dst / 'addons/objects/Reflector.js')
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
rng = np.random.default_rng(129)
g = (rng.normal(128, 38, (256, 256))).clip(0, 255).astype(np.uint8)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', '256x256', '-i', '-', str(A / 'grain.png')], input=g.tobytes(), check=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) and 'frames' in v else '') for k, v in rep.items()}, ensure_ascii=False))
