#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Me fala que eu ajusto" (F10 · ID01 Verde · voz de IA do Cortez).
Prova = uma só entrega real do usuário feita pelo Cortez (EXEMPLO_2 V2, Oferta), sem logotipos nem material de terceiros:
- seq/v1  = EXEMPLO_2 V2 13,60–15,30 s (apresentador falando) · versão 1 da tela, a "cena" que o pedido de exemplo troca
- seq/cc  = EXEMPLO_2 V2 17,30–17,95 s (cena do call center vazio da mesma entrega, câmera parada, legenda queimada "a agenda esvazia")
- seq/fin = EXEMPLO_2 V2 31,50–39,40 s (apresentador falando, trecho contínuo) · o vídeo depois dos ajustes, no "eu ajusto o vídeo"
Fontes Inter e IBM Plex Mono (ID01), three.js r186 + addons, GSAP e grão copiados de jobs/cortez-ia-d5/comp/assets.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
D5 = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, src, ss, dur, size='608:1080'):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    n = int(round(dur * 30))
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', src, '-vf', f'fps=30,scale={size}:flags=lanczos', '-frames:v', n, '-q:v', 2, d / '%04d.jpg'])
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    return {'frames': len(fs), 'src': src.name, 'ss': ss, 'dur': dur}


rep = {'v1': seq('v1', EXEMPLO_2, 13.60, 1.70), 'cc': seq('cc', EXEMPLO_2, 17.30, 0.65), 'fin': seq('fin', EXEMPLO_2, 31.50, 7.9)}
for f in ['gsap.min.js', 'grain.png', 'inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2',
          'inter-700-latin-ext.woff2', 'inter-800-latin.woff2', 'inter-800-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(D5 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(D5 / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep))
