#!/usr/bin/env python3
"""EXEMPLO_1 — materiais fixos da composição: fontes da ID07 Laranja (Inter 400–800 e IBM Plex Mono 400/500 — SIL OFL, cópias locais da ID,
as mesmas do EXEMPLO_2), three.js r186 (ESM) + addons usados, GSAP e textura de grão.
Run: ../../../.venv/bin/python src/make_assets.py"""
import shutil
from pathlib import Path

J = Path(__file__).resolve().parents[1]
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
F = J.parent / '<PREENCHER: fonte ou prova própria>'
for f in F.iterdir():
    if f.name.startswith(('inter-', 'ibm-plex-mono-')):
        shutil.copyfile(f, A / f.name)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries', 'math']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'grain.png')
print(sorted(p.name for p in A.iterdir()))
