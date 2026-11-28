#!/usr/bin/env python3
"""EXEMPLO_1 — materiais fixos da composição: fontes da ID05 Roxo (Manrope e JetBrains Mono — SIL OFL, cópias locais em assets/fonts/portable),
three.js r186 (ESM) + addons usados, GSAP. Run: ../../../.venv/bin/python src/make_assets.py"""
import shutil
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
F = SYS / 'assets/fonts/portable'
for f in ['manrope-variable.ttf', 'manrope-OFL.txt', 'jetbrains-mono-variable.ttf', 'jetbrains-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries', 'math']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
print(sorted(p.name for p in A.iterdir()))
