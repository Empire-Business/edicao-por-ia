#!/usr/bin/env python3
# Modelo F22 Corte de Live 3D — derivado da edição de exemplo E119 (prévia aprovada pelo autor em 27/11/2026).
# Copie para jobs/<trabalho>/src e preencha: fonte, falas (TAKES), cenas/legendas, provas próprias e trilha. Ver README.md desta pasta.
"""Materiais da composição 3D (exemplo E119).
- Prova (só entregas do próprio usuário editadas pelo Cortez, sem logotipos): sequências de quadros para texturas three.js
  (determinísticas, um quadro por frame): `long` = vídeo longo próprio (16:9) e `s1..s6` = vídeos curtos 9:16.
- Fontes da ID escolhida (no exemplo, ID04: Libre Baskerville, Inter, IBM Plex Mono) e uma fonte "typeface" (JSON) da Libre Baskerville gerada com fontTools
  para o texto 3D extrudado (TextGeometry), com só os caracteres usados.
- three.js r186 (ESM) + addons usados, GSAP.
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
V = WS / '02 - Ver vídeos'
PROOF1 = V / '<entrega-propria-1>.mp4'   # 9:16 editado pelo Cortez, sem logotipos de terceiros
PROOF2 = V / '<entrega-propria-2>.mp4'
PROOF3 = V / '<entrega-propria-3>.mp4'
LONG = V / '<video-longo-proprio>.mp4'   # 16:9
SEQ = {
    'long': ([(LONG, 66.0, 1.6), (LONG, 268.5, 1.6), (LONG, 365.0, 1.6), (LONG, 560.0, 1.6)], '960:540'),
    's1': ([(PROOF1, 46.0, 3.0)], '432:768'), 's2': ([(PROOF2, 3.6, 3.0)], '432:768'), 's3': ([(PROOF3, 54.55, 3.0)], '432:768'),
    's4': ([(PROOF1, 57.0, 3.0)], '432:768'), 's5': ([(PROOF3, 28.5, 3.0)], '432:768'), 's6': ([(PROOF2, 24.5, 3.0)], '432:768'),
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

F = SYS / 'assets/fonts/portable'
for f in ['libre-baskerville-variable.ttf', 'libre-baskerville-OFL.txt', 'inter-400-latin.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2',
          'inter-400-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)


class TypefacePen(BasePen):
    """Contornos TrueType → comandos do formato typeface.js usado pelo FontLoader do three.js (q = fim, controle)."""
    def __init__(self, gs):
        super().__init__(gs); self.o = []
    def _moveTo(self, p): self.o += ['m', round(p[0]), round(p[1])]
    def _lineTo(self, p): self.o += ['l', round(p[0]), round(p[1])]
    def _qCurveToOne(self, c, p): self.o += ['q', round(p[0]), round(p[1]), round(c[0]), round(c[1])]
    def _curveToOne(self, c1, c2, p): self.o += ['b', round(p[0]), round(p[1]), round(c1[0]), round(c1[1]), round(c2[0]), round(c2[1])]
    def _closePath(self): pass


def typeface(ttf, wght, chars, out):
    font = TTFont(ttf)
    if 'fvar' in font:
        font = instancer.instantiateVariableFont(font, {'wght': wght})
    gs = font.getGlyphSet(); cmap = font.getBestCmap(); hmtx = font['hmtx']; head = font['head']
    glyphs = {}
    for ch in sorted(set(chars)):
        gn = cmap.get(ord(ch))
        if gn is None:
            continue
        pen = TypefacePen(gs); gs[gn].draw(pen)
        xs = pen.o
        glyphs[ch] = {'ha': hmtx[gn][0], 'x_min': head.xMin, 'x_max': head.xMax, 'o': ' '.join(str(v) for v in xs)}
    data = {'glyphs': glyphs, 'familyName': 'Libre Baskerville', 'ascender': font['hhea'].ascent, 'descender': font['hhea'].descent,
            'underlinePosition': font['post'].underlinePosition, 'underlineThickness': font['post'].underlineThickness,
            'boundingBox': {'xMin': head.xMin, 'yMin': head.yMin, 'xMax': head.xMax, 'yMax': head.yMax}, 'resolution': head.unitsPerEm,
            'original_font_information': {'license': 'SIL OFL 1.1 (libre-baskerville-OFL.txt)'}, 'cssFontWeight': 'bold' if wght >= 600 else 'normal', 'cssFontStyle': 'normal'}
    out.write_text(json.dumps(data, ensure_ascii=False))
    return len(glyphs)


CH = 'Incrível.IncrívelVídeosLongoCortesCortez1→ ,!?abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZáéíóúãõç'
rep['typeface'] = typeface(F / 'libre-baskerville-variable.ttf', 700, CH, A / 'libre-baskerville-bold.typeface.json')

T3 = J / 'vendor/three186/package'   # npm pack three@0.186.1 && tar xzf three-0.186.1.tgz -C vendor/three186
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons/loaders').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'examples/jsm/loaders/FontLoader.js', dst / 'addons/loaders/FontLoader.js')
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J / 'vendor/gsap.min.js', A / 'gsap.min.js')   # GSAP 3: mesma cópia local usada nas composições HyperFrames
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) else v) for k, v in rep.items()}))
