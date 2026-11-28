#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição (tudo copiado para dentro do trabalho).
- Convidado (cliente): recorte quadrado do quadro de baixo da live do Instagram (432x768; Convidado = metade de baixo), centrado no rosto,
  ampliado (lanczos + redução de blocos + nitidez suave) — sequências JPG por quadro para a textura da janela da íris, uma por trecho da EDL,
  com o último quadro repetido (a janela continua viva até o CTA).
- Prova ("dizendo que sou bom"): 6 entregas do próprio usuário feitas pelo Cortez, conferidas quadro a quadro, sem logotipos de terceiros:
  EXEMPLO_2 (Oferta), EXEMPLO_3 e EXEMPLO_4 (criativos), EXEMPLO_5 (motion institucional) e EXEMPLO_6 (tutorial). Sequências curtas 270x480.
- Fontes da ID04 (Libre Baskerville, Inter, IBM Plex Mono), three.js r186 (ESM) + addons, GSAP, grão.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'; A.mkdir(parents=True, exist_ok=True)
EDL = json.loads((J / 'edit/edl.json').read_text())
IG = WS / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
FPS = 30


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, a)], check=True)


rep = {}
# 1) Convidado — um diretório por trecho (j1, j2); índice do quadro = floor((t − início do trecho) × 30)
JCROP = 'crop=344:344:68:388'
LOOK = f'{JCROP},scale=768:768:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.6:5:5:0,fps=30'
for take in ('j1', 'j2'):
    segs = [s for s in EDL['segments'] if s['take'] == take]
    d = A / 'seq' / take
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    k = 0
    for s in segs:
        n = int(round((s['out'] - s['in']) * FPS))
        tmp = J / 'tmp/jseq'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        ff('-ss', f"{s['in']:.4f}", '-i', IG, '-t', f'{n / FPS + 0.2:.4f}', '-an', '-vf', LOOK, '-frames:v', n, '-q:v', 3, '-start_number', 0, tmp / '%04d.jpg')
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
    rep[take] = {'frames': k, 'crop': JCROP}

# 1b) Convidado ouvindo (sem áudio dele): antes da fala, rindo da piada do Apresentador (IG 505,0–506,8) enquanto a íris abre; depois da fala, ouvindo
# a pergunta seguinte do Apresentador (IG 529,6–541,9) enquanto a IA fecha e no CTA. Imagem real da mesma live; nenhuma fala é atribuída a esses quadros.
for take, ss, dur in (('jpre', 505.0, 1.8), ('jpost', 529.6, 12.3)):
    d = A / 'seq' / take
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    n = int(round(dur * FPS))
    ff('-ss', ss, '-i', IG, '-t', f'{dur + 0.2:.3f}', '-an', '-vf', LOOK, '-frames:v', n, '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
    rep[take] = {'frames': len(list(d.glob('*.jpg'))), 'ig_s': [ss, ss + dur], 'note': 'Convidado ouvindo, sem a voz dele'}

# 1c) V2 (pedido do usuário via coordenador): Reel REAL do Convidado (@perfil-do-convidado, reel-do-convidado, postado em 27/11/2026, baixado via
# ScrapeCreators para jobs/material-compartilhado/convidado-ig/) — mostrado sem áudio dentro da íris quando ele diz "já tem um vídeo lá…" e quando a IA diz
# "em dois dias, ele já tinha vídeo postado". Rótulo "Reel do Convidado · @perfil-do-convidado" (SEM "editado pelo Cortez": não confirmado).
REEL = J.parent / '<PREENCHER: fonte ou prova própria>'
for take, ss, dur in (('rA', 1.3, 3.4), ('rB', 30.6, 2.6)):
    d = A / 'seq' / take
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    ff('-ss', ss, '-i', REEL, '-t', dur, '-an', '-vf', 'fps=30,scale=405:720:flags=lanczos', '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
    rep[take] = {'src': '<PREENCHER: fonte ou prova própria>', 'ss': ss, 'dur': dur, 'frames': len(list(d.glob('*.jpg'))),
                 'label': 'Reel do Convidado · @perfil-do-convidado (sem áudio; não rotulado como editado pelo Cortez)'}

# 2) prova: entregas do usuário (270x480, 2,6 s)
CARDS = [('c0', V / '<PREENCHER: fonte ou prova própria>', 12.1),
         ('c1', V / '<PREENCHER: fonte ou prova própria>', 0.3),
         ('c2', V / '<PREENCHER: fonte ou prova própria>', 5.0),
         ('c3', V / '<PREENCHER: fonte ou prova própria>', 46.0),
         ('c4', V / '<PREENCHER: fonte ou prova própria>', 3.0),
         ('c5', V / '<PREENCHER: fonte ou prova própria>', 17.3)]
for name, src, ss in CARDS:
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    ff('-ss', ss, '-i', src, '-t', 2.6, '-an', '-vf', 'fps=30,scale=270:480:flags=lanczos', '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
    rep[name] = {'src': str(src.relative_to(WS)), 'ss': ss, 'frames': len(list(d.glob('*.jpg')))}

# 3) fontes, three.js, gsap, grão
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
for f in ['libre-baskerville-variable.ttf', 'libre-baskerville-OFL.txt', 'inter-400-latin.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2',
          'inter-400-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt', 'gsap.min.js']:
    shutil.copyfile(C2 / f, A / f)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'; shutil.rmtree(dst, ignore_errors=True); dst.mkdir()
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
rng = np.random.default_rng(135)
g = rng.normal(128, 38, (256, 256)).clip(0, 255).astype(np.uint8)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', '256x256', '-i', '-', str(A / 'grain.png')], input=g.tobytes(), check=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v['frames'] for k, v in rep.items()}))
