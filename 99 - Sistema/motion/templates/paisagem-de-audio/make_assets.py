#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição 3D.
- Prova (só entregas do próprio usuário feitas pelo Cortez, conferidas quadro a quadro, sem logotipos de terceiros), em sequências JPG
  por quadro (texturas determinísticas):
  `id1..id4` = quatro entregas em identidades visuais diferentes (EXEMPLO_2 Dourado, EXEMPLO_3 Roxo, EXEMPLO_4 Verde, EXEMPLO_5 Azul Claro) — "estilo e cor";
  `long`     = vídeo longo do usuário editado pelo Cortez (LONGO_1, 16:9) — "um vídeo longo";
  `k01..k10` = dez vídeos curtos editados pelo Cortez — "uns 10 cortes" (exemplos; NÃO são os vídeos do Convidado).
- Fontes da ID03 (Inter + IBM Plex Mono) e fonte "typeface" (JSON) da Inter ExtraBold para o texto 3D (TextGeometry), gerada com fontTools
  a partir da InterVariable.ttf que já está na pasta da fábrica (.factory/cortez-voz-upstream), só com os caracteres usados.
- three.js r186 (ESM) + addons usados (pós-processamento, ambiente, Reflector, FontLoader/TextGeometry), GSAP, grão.
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
L = V / 'EXEMPLO_6 - Cortes das lives do Cortez'
N = V / '2026-11-07_criativos-namoral'
EXEMPLO_7 = V / '<PREENCHER: fonte ou prova própria>'
LONGO_1 = V / '<PREENCHER: fonte ou prova própria>'
P9 = 'scale=432:768:flags=lanczos'
P9s = 'scale=270:480:flags=lanczos'
SEQ = {
    'id1': [(L / 'EXEMPLO_2 V1 - Corte 2 Nao e possivel que exista (previa).mp4', 15.5, 3.0, P9)],
    'id2': [(L / 'EXEMPLO_3 V1 - Corte 4 Tem formato pra tudo (previa).mp4', 2.0, 3.0, P9)],
    'id3': [(L / 'EXEMPLO_4 V1 - Corte 3 Isso daqui e sinistro (previa).mp4', 17.0, 3.0, P9)],
    'id4': [(L / 'EXEMPLO_5 V2 - Corte 7 Nao precisa ser tecnico (previa).mp4', 6.0, 3.0, P9)],
    'long': [(LONGO_1, 66.0, 1.6, 'scale=960:540:flags=lanczos'), (LONGO_1, 268.5, 1.6, 'scale=960:540:flags=lanczos'),
             (LONGO_1, 365.0, 1.6, 'scale=960:540:flags=lanczos')],
    'k01': [(N / '<PREENCHER: fonte ou prova própria>', 46.0, 2.0, P9s)],
    'k02': [(N / '<PREENCHER: fonte ou prova própria>', 3.6, 2.0, P9s)],
    'k03': [(EXEMPLO_7, 54.55, 2.0, P9s)],
    'k04': [(N / '<PREENCHER: fonte ou prova própria>', 20.0, 2.0, P9s)],
    'k05': [(L / 'EXEMPLO_6 V2 - Corte 1 Editor caro (prévia para aprovação).mp4', 20.0, 2.0, P9s)],
    'k06': [(L / 'EXEMPLO_8 V2 - Corte 5 Antes e depois (previa).mp4', 10.0, 2.0, P9s)],
    'k07': [(L / 'EXEMPLO_9 V2 - Corte 6 5 minutos do seu dia (previa).mp4', 3.0, 2.0, P9s)],
    'k08': [(L / 'EXEMPLO_10 V2 - Corte 8 Cara de IA (previa).mp4', 12.0, 2.0, P9s)],
    'k09': [(EXEMPLO_7, 17.0, 2.0, P9s)],
    'k10': [(N / '<PREENCHER: fonte ou prova própria>', 57.0, 2.0, P9s)],
    # Reel real do Convidado (@perfil-do-convidado, postado em 27/11; baixado pelo coordenador em material-compartilhado/convidado-ig) — só os trechos com o
    # rosto dele (abertura "Fui chamado de burro" e 22,5–27 s), sem B-roll de terceiros; mudo. Rótulo: "Reel do Convidado · @perfil-do-convidado"
    # (sem "editado pelo Cortez" até o usuário confirmar).
    'jr': [(J.parent / '<PREENCHER: fonte ou prova própria>', 0.0, 5.0, P9), (J.parent / '<PREENCHER: fonte ou prova própria>', 22.5, 4.5, P9)],
}
ONLY = set(__import__('os').environ.get('ONLY', '').split(',')) - {''}
rep = {}
for name, parts in SEQ.items():
    if ONLY and name not in ONLY:
        continue
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    k = 0
    for src, ss, dur, vf in parts:
        tmp = J / 'tmp' / f'seq-{name}'
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur), '-vf', f'fps=30,{vf}', '-q:v', '3',
                        str(tmp / '%04d.jpg')], check=True, stdin=subprocess.DEVNULL)
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    rep[name] = {'frames': k, 'parts': [(str(p[0].relative_to(WS)), p[1], p[2]) for p in parts]}

if ONLY:
    print(json.dumps({k: v['frames'] for k, v in rep.items()})); raise SystemExit(0)
F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-600-latin-ext.woff2', 'inter-800-latin.woff2',
          'inter-800-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)


class TypefacePen(BasePen):
    """Contornos → comandos typeface.js do FontLoader do three.js (q = fim, controle; b = fim, c1, c2)."""
    def __init__(self, gs):
        super().__init__(gs); self.o = []
    def _moveTo(self, p): self.o += ['m', round(p[0]), round(p[1])]
    def _lineTo(self, p): self.o += ['l', round(p[0]), round(p[1])]
    def _qCurveToOne(self, c, p): self.o += ['q', round(p[0]), round(p[1]), round(c[0]), round(c[1])]
    def _curveToOne(self, c1, c2, p): self.o += ['b', round(p[0]), round(p[1]), round(c1[0]), round(c1[1]), round(c2[0]), round(c2[1])]
    def _closePath(self): pass


def typeface(ttf, wght, chars, out, family):
    font = instancer.instantiateVariableFont(TTFont(ttf), {'wght': wght, 'opsz': 32} if 'opsz' in [a.axisTag for a in TTFont(ttf)['fvar'].axes] else {'wght': wght})
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
            'original_font_information': {'license': 'SIL OFL 1.1 (inter-OFL.txt)'}, 'cssFontWeight': 'bold', 'cssFontStyle': 'normal'}
    out.write_text(json.dumps(data, ensure_ascii=False))
    return len(glyphs)


INTER = WS / '99 - Sistema/.factory/cortez-voz-upstream/mobile/ios/VoiceStudio/Resources/Fonts/InterVariable.ttf'
CH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÃÕÇÂÊ0123456789!?.,·' + ' '
rep['typeface'] = typeface(INTER, 800, CH, A / 'inter-800.typeface.json', 'Inter')

T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons/loaders').mkdir(parents=True); (dst / 'addons/objects').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'examples/jsm/loaders/FontLoader.js', dst / 'addons/loaders/FontLoader.js')
shutil.copyfile(T3 / 'examples/jsm/objects/Reflector.js', dst / 'addons/objects/Reflector.js')
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
shutil.copyfile(C2 / 'gsap.min.js', A / 'gsap.min.js')
shutil.copyfile(C2 / 'grain.png', A / 'grain.png')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) else v) for k, v in rep.items()}))
