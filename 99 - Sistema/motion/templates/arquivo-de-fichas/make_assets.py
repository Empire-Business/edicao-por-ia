#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "22 jeitos de editar" (F10 · ID08 Azul e Papel · voz de IA do Cortez).
Cada formato citado na narração aparece com um exemplo REAL do próprio usuário ou um exemplo original do Cortez (sem terceiros):
- talk  = EXEMPLO_2 V2 (OFERTA, entrega do usuário editada pelo Cortez) 2,20–5,20 s · apresentador falando (mecanismo talking head)
- f13   = exemplo original do Cortez do F13 Dados Dark (examples/reference-library/F13/cortez-2026-10) 1,00–4,00 s · vídeo sem aparecer
- live  = EXEMPLO_3 V1 (corte 2 da live, aprovado; exemplo oficial do F22) 0,10–3,10 s · corte de live
- doc   = exemplo original do Cortez do F12 Documentário (examples/reference-library/F12/cortez-2026-10) 4,00–7,00 s
- motion= EXEMPLO_4 V2 9x16 (Motion institucional do próprio usuário, Motions institucionais/07) 1,00–4,00 s
- hero  = EXEMPLO_3 V1 12,50–17,30 s · "você escolhe o formato, as cores… e eu edito no estilo que você quiser" (EXEMPLO_3 é ID04 Dourado)
F05 Notícia Comentada não tem entrega própria: aparece só como cartão desenhado do catálogo (nenhum vídeo de terceiros).
Fontes Inter + IBM Plex Mono (ID08), Libre Baskerville (só para a amostra da ID04), three.js r186 + addons, GSAP e grão.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / 'EXEMPLO_5 - Cortes das lives do Cortez/EXEMPLO_3 V1 - Corte 2 Nao e possivel que exista (previa).mp4'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
F12 = SYS / 'examples/reference-library/F12/cortez-2026-10/exemplo.mp4'
F13 = SYS / 'examples/reference-library/F13/cortez-2026-10/exemplo.mp4'


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, src, ss, dur, size='432:768'):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    n = int(round(dur * 30))
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', src, '-vf', f'fps=30,scale={size}:flags=lanczos', '-frames:v', n, '-q:v', 3, d / '%04d.jpg'])
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    return {'source': str(src.relative_to(WS)), 'ss': ss, 'dur': dur, 'frames': len(fs)}


rep = {'talk': seq('talk', EXEMPLO_2, 2.20, 3.0), 'f13': seq('f13', F13, 1.00, 3.0), 'live': seq('live', EXEMPLO_3, 0.10, 3.0),
       'doc': seq('doc', F12, 4.00, 3.0), 'motion': seq('motion', EXEMPLO_4, 1.00, 3.0), 'hero': seq('hero', EXEMPLO_3, 12.50, 4.8)}

F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2', 'inter-800-latin.woff2',
          'inter-600-latin-ext.woff2', 'inter-800-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-400-latin.woff2', 'ibm-plex-mono-500-latin.woff2',
          'ibm-plex-mono-OFL.txt', 'libre-baskerville-variable.ttf', 'libre-baskerville-OFL.txt', 'manrope-variable.ttf', 'manrope-OFL.txt']:
    shutil.copyfile(F / f, A / f)
for f in ['gsap.min.js', 'grain.png']:
    shutil.copyfile(C2 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v['frames'] for k, v in rep.items()}))
