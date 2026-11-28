#!/usr/bin/env python3
"""EXEMPLO_1 — materiais fixos da composição: fontes da IDP02 Black Alto Valor (Instrument Serif regular/itálico, Roboto Condensed,
Schibsted Grotesk — SIL OFL, cópias locais da ID), three.js r186 (ESM) + addons usados, GSAP e textura de grão.
Run: ../../../.venv/bin/python src/make_assets.py"""
import shutil
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
F = SYS / 'context/visual-identities/IDP02/fonts'
for f in F.iterdir():
    if f.suffix in ('.ttf', '.txt'):
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
