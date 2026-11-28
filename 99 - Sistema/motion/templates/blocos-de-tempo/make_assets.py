#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Dois dias ou trinta minutos" (F10 · ID01 Verde · voz de IA do Cortez).
Prova = só entregas do próprio usuário feitas pelo Cortez, sem logotipos nem material de terceiros:
- seq/raw = gravação bruta da Oferta 0,98–3,98 s (HDR do iPhone → BT.709 pelo VideoToolbox + curva da V2 do EXEMPLO_2) · "você grava"
- seq/fin = EXEMPLO_2 V2 0,00–4,00 s (entrega editada pelo Cortez a partir dessa gravação) · "o vídeo está pronto"
- seq/v2  = EXEMPLO_2 V2 15,45–18,75 s (outra cena da mesma entrega, antes do gráfico branco) · rotulada "exemplo de ajuste" no "eu ajusto"
- seq/l1..l4 = EXEMPLO_3, EXEMPLO_4, EXEMPLO_5 (corte 2) e EXEMPLO_6 (corte 4) · fileira de entregas no "o resto é comigo"
Fonte typeface (JSON) Inter 800 gerada com fontTools a partir da InterVariable (OFL) para o texto 3D extrudado (TextGeometry).
Fontes Inter e IBM Plex Mono (ID01), three.js r186 + addons, GSAP e grão copiados de jobs/cortez-live-c2/comp/assets.
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
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / 'EXEMPLO_7 - Cortes das lives do Cortez/EXEMPLO_5 V1 - Corte 2 Nao e possivel que exista (previa).mp4'
EXEMPLO_6 = V / 'EXEMPLO_7 - Cortes das lives do Cortez/EXEMPLO_6 V1 - Corte 4 Tem formato pra tudo (previa).mp4'
RAW = WS / '<PREENCHER: fonte ou prova própria>'
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, parts, size='720:1280', hdr=False):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    k = 0
    for src, ss, dur in parts:
        tmp = J / 'tmp' / f'seq-{name}'
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        n = int(round(dur * 30))
        if hdr:
            a = ['ffmpeg', '-v', 'error', '-y', '-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld', '-ss', f'{ss:.3f}', '-i', src,
                 '-vf', f'{HDR},fps=30,scale={size}:flags=lanczos,format=yuvj420p', '-frames:v', n, '-q:v', 3, tmp / '%04d.jpg']
        else:
            a = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', src, '-vf', f'fps=30,scale={size}:flags=lanczos', '-frames:v', n, '-q:v', 3, tmp / '%04d.jpg']
        run(a)
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    return {'frames': k, 'parts': [(Path(p[0]).name, p[1], p[2]) for p in parts]}


rep = {'raw': seq('raw', [(RAW, 0.98, 3.0)], hdr=True), 'fin': seq('fin', [(EXEMPLO_2, 0.0, 4.0)]), 'v2': seq('v2', [(EXEMPLO_2, 15.45, 3.3)]),
       'l1': seq('l1', [(EXEMPLO_3, 46.0, 2.5)], size='405:720'), 'l2': seq('l2', [(EXEMPLO_4, 3.6, 2.5)], size='405:720'),
       'l3': seq('l3', [(EXEMPLO_5, 15.2, 2.5)], size='405:720'), 'l4': seq('l4', [(EXEMPLO_6, 2.2, 2.5)], size='405:720')}


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
        font = instancer.instantiateVariableFont(font, {'wght': wght, **({'opsz': 32} if any(a.axisTag == 'opsz' for a in font['fvar'].axes) else {})})
    gs = font.getGlyphSet(); cmap = font.getBestCmap(); hmtx = font['hmtx']; head = font['head']
    glyphs = {}
    for ch in sorted(set(chars)):
        gn = cmap.get(ord(ch))
        if gn is None:
            continue
        pen = TypefacePen(gs); gs[gn].draw(pen)
        glyphs[ch] = {'ha': hmtx[gn][0], 'x_min': head.xMin, 'x_max': head.xMax, 'o': ' '.join(str(v) for v in pen.o)}
    data = {'glyphs': glyphs, 'familyName': 'Inter', 'ascender': font['hhea'].ascent, 'descender': font['hhea'].descent,
            'underlinePosition': font['post'].underlinePosition, 'underlineThickness': font['post'].underlineThickness,
            'boundingBox': {'xMin': head.xMin, 'yMin': head.yMin, 'xMax': head.xMax, 'yMax': head.yMax}, 'resolution': head.unitsPerEm,
            'original_font_information': {'license': 'SIL OFL 1.1 (inter-OFL.txt)'}, 'cssFontWeight': 'bold', 'cssFontStyle': 'normal'}
    out.write_text(json.dumps(data, ensure_ascii=False))
    return len(glyphs)


ITTF = SYS / '.factory/cortez-voz-upstream/mobile/ios/VoiceStudio/Resources/Fonts/InterVariable.ttf'
rep['typeface'] = typeface(ITTF, 800, 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÃÕÇ0123456789+-–., :h', A / 'inter-800.typeface.json')

for f in ['gsap.min.js', 'grain.png', 'inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2', 'inter-OFL.txt']:
    shutil.copyfile(C2 / f, A / f)
F = SYS / 'assets/fonts/portable'
for f in ['ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt', 'inter-700-latin.woff2', 'inter-700-latin-ext.woff2', 'inter-800-latin-ext.woff2']:
    shutil.copyfile(F / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v.get('frames') if isinstance(v, dict) else v) for k, v in rep.items()}))
