#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição 3D (F22 + ID06 Azul Claro).
Prova = só entregas do próprio usuário editadas pelo Cortez (02 - Ver vídeos), conferidas quadro a quadro, sem logotipos de terceiros:
- `jreel`/`jcut` (V2, pedido do usuário: "pegar vídeos com a cara dele mesmo quando ele fala que postou"): Reel REAL do Convidado
             (@perfil-do-convidado, reel-do-convidado, postado em 27/11/2026, baixado via ScrapeCreators em jobs/material-compartilhado/convidado-ig/),
             trechos com o rosto dele, sem o áudio do Reel. Rótulo "Reel do Convidado · @perfil-do-convidado" — SEM "editado pelo Cortez"
             (não confirmado). `jreel` = tela do teste 1 (o curto que ele postou); `jcut` = tela do centro nos 5 cortes;
- `long`   : LONGO_1 V6 (vídeo longo 16:9 do próprio usuário editado pelo Cortez), 4 trechos de 1,6 s sem nomes/logos de terceiros
             (evitados: o recorte de notícia e as telas com o nome de empresa citada no vídeo);
- `v1..v5` : recortes 9:16 de 5 trechos desse mesmo vídeo longo — ILUSTRAÇÃO de "1 vídeo longo → 5 cortes" (rotulada assim no vídeo),
             não são os cortes que o Convidado fez nem cortes entregues do LONGO_1. Recortes escolhidos sem texto/etiqueta cortados na borda.
Sequências JPG indexadas por quadro (texturas determinísticas). Fontes da ID06 (Inter + IBM Plex Mono), three.js r186 (ESM) + addons, GSAP.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
YT = V / '<PREENCHER: fonte ou prova própria>'
JR = J.parent / '<PREENCHER: fonte ou prova própria>'
VCROP = lambda x0: f'crop=608:1080:{x0}:0,scale=360:640:flags=lanczos'
SEQ = {
    'jreel': ([(JR, 0.2, 7.8)], 'scale=432:768:flags=lanczos'),
    'jcut': ([(JR, 30.0, 7.4)], 'scale=360:640:flags=lanczos'),
    'long': ([(YT, 66.0, 1.6), (YT, 160.0, 1.6), (YT, 365.0, 1.6), (YT, 705.0, 1.6)], 'scale=960:540:flags=lanczos'),
    'v1': ([(YT, 705.0, 2.4)], VCROP(656)),
    'v2': ([(YT, 160.0, 2.4)], VCROP(560)),
    'v3': ([(YT, 640.0, 2.4)], VCROP(560)),
    'v4': ([(YT, 66.0, 2.4)], VCROP(760)),
    'v5': ([(YT, 708.0, 2.4)], VCROP(656)),
}
rep = {}
for name, (parts, vf) in SEQ.items():
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    k = 0
    for src, ss, dur in parts:
        tmp = J / 'tmp' / f'seq-{name}'
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur), '-vf', f'fps=30,{vf}', '-q:v', '3', str(tmp / '%04d.jpg')], check=True)
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    rep[name] = {'frames': k, 'parts': [(str(p[0].relative_to(WS)), p[1], p[2]) for p in parts], 'filter': vf}
shutil.rmtree(A / 'seq' / 'short', ignore_errors=True)

F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-500-latin.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2',
          'inter-800-latin.woff2', 'inter-800-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)

T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); dst.mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v['frames'] for k, v in rep.items()}))
