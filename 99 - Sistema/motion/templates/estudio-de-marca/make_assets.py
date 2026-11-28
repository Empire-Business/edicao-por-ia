#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Com a sua cara" (F10 · ID05 Roxo · voz de IA do Cortez).
Prova = só entregas do próprio usuário feitas pelo Cortez, em identidades visuais diferentes (sem logotipos nem terceiros):
- seq/base = imagem de câmera do EXEMPLO_2 (jobs/video-18157f4a38d1/renders/base-v2.mp4, sem legenda nem gráfico) 12,30–15,30 s:
  o MESMO vídeo que troca de identidade na cena "todo vídeo… sai com a sua cara" (ilustração rotulada).
- seq/p0..p4 = trechos reais de 3 s de entregas em IDs diferentes: EXEMPLO_2 V2 (ID07), EXEMPLO_3 V1 (ID04), EXEMPLO_4 V2 (ID08),
  EXEMPLO_5 V1 (ID05), EXEMPLO_6 V2 (IDP02) — parede final "do seu jeito".
- Fontes reais das IDs (Manrope ID05, Libre Baskerville ID04, Instrument Serif IDP02, JetBrains Mono, Inter) e fontes "typeface"
  (JSON gerado com fontTools) para as letras 3D dos tipos de metal.
- three.js r186 + addons, GSAP e grão copiados de jobs/cortez-live-c2/comp/assets.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.basePen import BasePen

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
BASE = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_6 = J.parent / '<PREENCHER: fonte ou prova própria>'


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, src, ss, dur, size):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    n = int(round(dur * 30))
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', src, '-vf', f'fps=30,scale={size}:flags=lanczos', '-frames:v', n, '-q:v', 3, d / '%04d.jpg'])
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    return {'src': str(src.relative_to(WS)), 'ss': ss, 'dur': dur, 'frames': len(fs)}


PROOF = [('p0', EXEMPLO_2, 4.60, 'ID07 · Laranja'), ('p1', EXEMPLO_3, 17.20, 'ID04 · Dourado'), ('p2', EXEMPLO_4, 9.50, 'ID08 · Azul e Papel'),
         ('p3', EXEMPLO_5, 9.80, 'ID05 · Roxo'), ('p4', EXEMPLO_6, 18.00, 'IDP02 · Black Alto Valor')]
rep = {'base': seq('base', BASE, 12.30, 3.0, '720:1280')}
for name, src, ss, label in PROOF:
    rep[name] = seq(name, src, ss, 3.0, '432:768'); rep[name]['label'] = label


class TypefacePen(BasePen):
    """Contornos → comandos typeface.js do FontLoader do three.js (q = fim, controle)."""
    def __init__(self, gs):
        super().__init__(gs); self.o = []
    def _moveTo(self, p): self.o += ['m', round(p[0]), round(p[1])]
    def _lineTo(self, p): self.o += ['l', round(p[0]), round(p[1])]
    def _qCurveToOne(self, c, p): self.o += ['q', round(p[0]), round(p[1]), round(c[0]), round(c[1])]
    def _curveToOne(self, c1, c2, p): self.o += ['b', round(p[0]), round(p[1]), round(c1[0]), round(c1[1]), round(c2[0]), round(c2[1])]
    def _closePath(self): pass


def typeface(ttf, wght, chars, out, family):
    font = TTFont(ttf)
    if 'fvar' in font and wght:
        font = instancer.instantiateVariableFont(font, {'wght': wght})
    gs = font.getGlyphSet(); cmap = font.getBestCmap(); hmtx = font['hmtx']; head = font['head']
    glyphs = {}
    for ch in sorted(set(chars)):
        gn = cmap.get(ord(ch))
        if gn is None:
            continue
        pen = TypefacePen(gs); gs[gn].draw(pen)
        glyphs[ch] = {'ha': hmtx[gn][0], 'x_min': head.xMin, 'x_max': head.xMax, 'o': ' '.join(str(v) for v in pen.o)}
    data = {'glyphs': glyphs, 'familyName': family, 'ascender': font['hhea'].ascent, 'descender': font['hhea'].descent,
            'underlinePosition': font['post'].underlinePosition, 'underlineThickness': font['post'].underlineThickness,
            'boundingBox': {'xMin': head.xMin, 'yMin': head.yMin, 'xMax': head.xMax, 'yMax': head.yMax}, 'resolution': head.unitsPerEm,
            'original_font_information': {'license': 'SIL OFL 1.1'}, 'cssFontWeight': 'bold' if (wght or 400) >= 600 else 'normal', 'cssFontStyle': 'normal'}
    out.write_text(json.dumps(data, ensure_ascii=False))
    return len(glyphs)


F = SYS / 'assets/fonts/portable'
IF = SYS / 'context/visual-identities/IDP02/fonts'
CH = 'AaÁáBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZzçãõéêíóú.,!?·0123456789 '
tf = {'manrope': typeface(F / 'manrope-variable.ttf', 800, CH, A / 'manrope-800.typeface.json', 'Manrope'),
      'baskerville': typeface(F / 'libre-baskerville-variable.ttf', 700, CH, A / 'baskerville-700.typeface.json', 'Libre Baskerville'),
      'instrument': typeface(IF / 'InstrumentSerif-Regular.ttf', None, CH, A / 'instrument-400.typeface.json', 'Instrument Serif'),
      'jetbrains': typeface(F / 'jetbrains-mono-variable.ttf', 700, CH, A / 'jetbrains-700.typeface.json', 'JetBrains Mono')}
rep['typeface'] = tf

for f in ['manrope-variable.ttf', 'manrope-OFL.txt', 'libre-baskerville-variable.ttf', 'libre-baskerville-OFL.txt', 'jetbrains-mono-variable.ttf', 'jetbrains-mono-OFL.txt',
          'inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2', 'inter-OFL.txt']:
    shutil.copyfile(F / f, A / f)
for f in ['InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf', 'InstrumentSerif-OFL.txt']:
    shutil.copyfile(IF / f, A / f)
for f in ['gsap.min.js', 'grain.png']:
    shutil.copyfile(C2 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
# FontLoader + TextGeometry (não vieram na cópia do c2? garante)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package/examples/jsm'
(A / 'three/addons/loaders').mkdir(parents=True, exist_ok=True)
shutil.copyfile(T3 / 'loaders/FontLoader.js', A / 'three/addons/loaders/FontLoader.js')
for d in ['geometries', 'environments', 'postprocessing', 'shaders']:
    if not (A / 'three/addons' / d).exists():
        shutil.copytree(T3 / d, A / 'three/addons' / d)
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v.get('frames') if isinstance(v, dict) and 'frames' in v else v) for k, v in rep.items()}, ensure_ascii=False))
