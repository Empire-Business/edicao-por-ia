#!/usr/bin/env python3
"""EXEMPLO_1 — materiais estáticos da composição: fontes da ID06 (Inter + IBM Plex Mono, arquivos locais OFL), three.js r186 (ESM)
com os addons usados (pós-processamento, shaders, ambiente, RoundedBoxGeometry), GSAP e textura de grão.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import shutil
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-500-latin.woff2', 'inter-600-latin.woff2', 'inter-600-latin-ext.woff2',
          'inter-700-latin.woff2', 'inter-700-latin-ext.woff2', 'inter-800-latin.woff2', 'inter-800-latin-ext.woff2', 'inter-OFL.txt',
          'ibm-plex-mono-400-latin.woff2', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons/geometries').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'math']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'examples/jsm/geometries/RoundedBoxGeometry.js', dst / 'addons/geometries/RoundedBoxGeometry.js')
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'grain.png')
print('ok')
