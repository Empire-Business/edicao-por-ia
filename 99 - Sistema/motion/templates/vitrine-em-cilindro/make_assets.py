#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição 3D "Tem formato pra tudo".
- Prova = só entregas do próprio usuário editadas pelo Cortez (02 - Ver vídeos), sem logotipos/terceiros, conferidas por quadros
  (tmp/inv/*.jpg). Cada tela do anel de formatos é uma sequência de quadros JPG (textura determinística, um quadro por frame):
  heróis (os formatos que o Convidado cita) em 486x864 e ~3,3 s; demais telas em 324x576 e 2,5 s, em laço.
- Recortes 9:16 de trechos 16:9 (LONGO_1) só em cenas ilustradas sem rosto (o mecanismo "sem aparecer").
- Fontes da ID05 (Manrope, JetBrains Mono) + Libre Baskerville (só como uma das "letras" da máquina de tipos) e fontes
  "typeface" (JSON) geradas com fontTools para o texto 3D extrudado (TextGeometry).
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
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / '<PREENCHER: fonte ou prova própria>'
F16 = V / '2026-10-08_tutorial-edicao/exemplo_9x16_F16_ID07_V3.mp4'
YT = V / '<PREENCHER: fonte ou prova própria>'
E59 = V / 'E59 - Tutorial de PR do Cortez/E59_tutorial-contribuir-com-cortez_9x16_F07_ID05_PREVIEW_V1.mp4'
EXEMPLO_6 = V / '<PREENCHER: fonte ou prova própria>'
HERO, EXTRA = '486:864', '324:576'
# nome: (arquivo, início, duração, tamanho, recorte opcional, rótulo honesto)
SEQ = {
    'h_sem': (YT, 149.6, 3.34, HERO, 'crop=608:1080:40:0', '<PREENCHER: fonte ou prova própria>'),
    'h_apa': (F16, 6.0, 3.34, HERO, None, 'Aparecendo · exemplo F16 (talking head)'),
    'h_cen': (EXEMPLO_2, 6.0, 3.34, HERO, None, 'Aparecendo com cenas · EXEMPLO_2 (pessoa + tela)'),
    'h_des': (EXEMPLO_2, 2.6, 3.34, HERO, None, 'Fundo desfocado · EXEMPLO_2 (abertura com o fundo desfocado)'),
    'h_ed': (EXEMPLO_5, 12.25, 3.0, HERO, None, 'Bem editado · EXEMPLO_5 (destaque na legenda)'),
    'x_mes': (EXEMPLO_5, 9.6, 2.5, EXTRA, None, 'EXEMPLO_5 cartão mês cheio/mês vazio'),
    'x_net': (EXEMPLO_4, 9.0, 2.5, EXTRA, None, 'EXEMPLO_4 rede de ferramentas + apresentador'),
    'x_jor': (EXEMPLO_4, 61.0, 2.5, EXTRA, None, 'EXEMPLO_4 interface jornada + apresentador'),
    'x_pro': (EXEMPLO_3, 10.4, 1.65, EXTRA, None, 'EXEMPLO_3 cartão de texto'),
    'x_eta': (F16, 20.6, 2.0, EXTRA, None, 'F16 cartão etapas invisíveis'),
    'x_loj': (YT, 218.0, 2.5, EXTRA, 'crop=608:1080:0:0', '<PREENCHER: fonte ou prova própria>'),
    'x_th': (EXEMPLO_2, 66.5, 2.5, EXTRA, None, 'EXEMPLO_2 apresentador'),
    'x_ia': (EXEMPLO_4, 19.0, 2.0, EXTRA, None, 'EXEMPLO_4 cartão IA + apresentador'),
    'x_ant': (F16, 14.0, 2.0, EXTRA, None, 'F16 destaque na legenda'),
    'x_pr': (E59, 20.0, 2.5, EXTRA, None, 'E59 tutorial do Cortez'),
    'x_ui': (EXEMPLO_6, 15.0, 2.5, EXTRA, None, 'EXEMPLO_6 tutorial de interface'),
}
rep = {}
for name, (src, ss, dur, size, crop, label) in SEQ.items():
    d = A / 'seq' / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    vf = (crop + ',' if crop else '') + f'fps=30,scale={size}:flags=lanczos'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur), '-vf', vf, '-q:v', '3', str(d / '%04d.jpg')], check=True)
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    rep[name] = {'frames': len(fs), 'source': str(src.relative_to(WS)), 'start': ss, 'dur': dur, 'crop': crop, 'label': label}

F = SYS / 'assets/fonts/portable'
for f in ['manrope-variable.ttf', 'manrope-OFL.txt', 'jetbrains-mono-variable.ttf', 'jetbrains-mono-OFL.txt',
          'libre-baskerville-variable.ttf', 'libre-baskerville-OFL.txt']:
    shutil.copyfile(F / f, A / f)


class TypefacePen(BasePen):
    """Contornos → comandos do formato typeface.js usado pelo FontLoader do three.js (q = fim, controle)."""
    def __init__(self, gs):
        super().__init__(gs); self.o = []
    def _moveTo(self, p): self.o += ['m', round(p[0]), round(p[1])]
    def _lineTo(self, p): self.o += ['l', round(p[0]), round(p[1])]
    def _qCurveToOne(self, c, p): self.o += ['q', round(p[0]), round(p[1]), round(c[0]), round(c[1])]
    def _curveToOne(self, c1, c2, p): self.o += ['b', round(p[0]), round(p[1]), round(c1[0]), round(c1[1]), round(c2[0]), round(c2[1])]
    def _closePath(self): pass


def typeface(ttf, wght, chars, out, family):
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
        glyphs[ch] = {'ha': hmtx[gn][0], 'x_min': head.xMin, 'x_max': head.xMax, 'o': ' '.join(str(v) for v in pen.o)}
    data = {'glyphs': glyphs, 'familyName': family, 'ascender': font['hhea'].ascent, 'descender': font['hhea'].descent,
            'underlinePosition': font['post'].underlinePosition, 'underlineThickness': font['post'].underlineThickness,
            'boundingBox': {'xMin': head.xMin, 'yMin': head.yMin, 'xMax': head.xMax, 'yMax': head.yMax}, 'resolution': head.unitsPerEm,
            'original_font_information': {'license': 'SIL OFL 1.1'}, 'cssFontWeight': 'bold' if wght >= 600 else 'normal', 'cssFontStyle': 'normal'}
    out.write_text(json.dumps(data, ensure_ascii=False))
    return len(glyphs)


CH = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZáéíóúãõçâêô0123456789 .,!?'
rep['typeface'] = {
    'manrope': typeface(F / 'manrope-variable.ttf', 800, CH, A / 'tf-manrope.json', 'Manrope'),
    'baskerville': typeface(F / 'libre-baskerville-variable.ttf', 700, CH, A / 'tf-baskerville.json', 'Libre Baskerville'),
    'mono': typeface(F / 'jetbrains-mono-variable.ttf', 700, CH, A / 'tf-mono.json', 'JetBrains Mono'),
    'manrope_light': typeface(F / 'manrope-variable.ttf', 300, CH, A / 'tf-manrope-light.json', 'Manrope'),
}

T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons/loaders').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'examples/jsm/loaders/FontLoader.js', dst / 'addons/loaders/FontLoader.js')
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'grain.png')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) and 'frames' in v else v) for k, v in rep.items()}))
