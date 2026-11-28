#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Até a voz fui eu" (F10 · IDP01 · voz de IA do Cortez).
Prova = só entregas do próprio usuário feitas pelo Cortez, sem logotipos nem material de terceiros:
- img/capa.jpg   = capa 9:16 do mini curso "Edição de vídeos com IA" feita pelo Cortez (jobs/cami-curso-acesso/cover/capa-v1.png), recorte 390:640
- img/thumb.jpg  = a mesma capa na versão 16:9 (thumbnail) feita pelo Cortez (jobs/cami-curso-acesso/cover/capa-16x9-v1.png)
- seq/cena       = cena pesquisada pelo Cortez dentro do EXEMPLO_2 V2 (escritório vazio, 16,95–18,75 s), recorte 390:271
- seq/fin        = EXEMPLO_2 V2 31,60–37,40 s (o vídeo pronto: apresentador + legenda) · revelado quando as peças viram
- seq/f13        = exemplo original do F13 Dados Dark feito pelo Cortez (narração de IA, sem gravação; examples/reference-library/F13/cortez-2026-10) 0–7 s
Fontes Inter (IDP01), three.js r186 + addons, GSAP e grão copiados de trabalhos anteriores.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'
F13 = SYS / 'examples/reference-library/F13/cortez-2026-10/exemplo.mp4'
CAPA = J.parent / 'cami-curso-acesso/cover/capa-v1.png'
THUMB = J.parent / 'cami-curso-acesso/cover/capa-16x9-v1.png'


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, src, ss, dur, vf):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', src, '-vf', f'fps=30,{vf}', '-frames:v', int(round(dur * 30)), '-q:v', 3, d / '%04d.jpg'])
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    return {'src': src.name, 'ss': ss, 'dur': dur, 'frames': len(fs)}


rep = {'cena': seq('cena', EXEMPLO_2, 16.95, 1.8, 'crop=1080:750:0:585,scale=780:542:flags=lanczos'),
       'fin': seq('fin', EXEMPLO_2, 31.60, 5.8, 'scale=720:1280:flags=lanczos'),
       'f13': seq('f13', F13, 0.0, 7.0, 'scale=720:1280:flags=lanczos')}
(A / 'img').mkdir(exist_ok=True)
run(['ffmpeg', '-v', 'error', '-y', '-i', CAPA, '-vf', 'crop=iw:iw*640/390:0:0,scale=780:1280:flags=lanczos', '-q:v', 2, A / 'img/capa.jpg'])
run(['ffmpeg', '-v', 'error', '-y', '-i', THUMB, '-vf', 'scale=780:438:flags=lanczos', '-q:v', 2, A / 'img/thumb.jpg'])
rep['capa'] = CAPA.name; rep['thumb'] = THUMB.name

D1 = J.parent / '<PREENCHER: fonte ou prova própria>'
D3 = J.parent / '<PREENCHER: fonte ou prova própria>'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2', 'inter-OFL.txt', 'gsap.min.js', 'grain.png']:
    shutil.copyfile(D1 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(D3 / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
