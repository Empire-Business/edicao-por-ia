#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Um vídeo longo vira cortes" (F10 · ID03 Azul · voz de IA do Cortez).
Prova = só entregas do próprio usuário feitas pelo Cortez, rotuladas "exemplo", e o Reel real do Convidado (@perfil-do-convidado, baixado
pelo ScrapeCreators a pedido do usuário; rótulo sem "editado pelo Cortez"). Sem logotipos nem material de terceiros.
- seq/long  = vídeo longo LONGO_1 V6 (16:9) 66,0–69,0 s, 960x540 · "Me dá um vídeo longo"
- seq/s1..s9 = cortes curtos 9:16 editados pelo Cortez (EXEMPLO_2, EXEMPLO_3, EXEMPLO_4, EXEMPLO_5, EXEMPLO_6, EXEMPLO_7, EXEMPLO_8, EXEMPLO_9), 2,5 s cada, 270x480 · os 10 cortes
- seq/j, seq/jh = Reel do Convidado (reel-do-convidado, postado em 27/11) 0,6–3,1 s, 270x480 e 540x960 · "um cliente… dez cortes"
- seq/hb, hl, hc = cartão herói: imagem de câmera do EXEMPLO_4 sem legenda (base-v2) → EXEMPLO_4 com legenda → cena do escritório · "legenda, cena e música"
- analysis/longo_envelope.json = energia real do áudio do LONGO_1 em blocos de 2 s (relevo da cordilheira)
- analysis/e117_env.json = envelope do áudio do EXEMPLO_4 12,3–18,5 s (faixa "música" do cartão herói)
Fontes Inter + IBM Plex Mono (ID03), three.js r186 + addons, GSAP e grão copiados de jobs/cortez-live-c2/comp/assets.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
YT = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
CL = V / 'EXEMPLO_10 - Cortes das lives do Cortez'
EXEMPLO_5 = CL / 'EXEMPLO_5 V1 - Corte 2 Nao e possivel que exista (previa).mp4'
EXEMPLO_6 = CL / 'EXEMPLO_6 V1 - Corte 4 Tem formato pra tudo (previa).mp4'
EXEMPLO_7 = CL / 'EXEMPLO_7 V2 - Corte 8 Cara de IA (previa).mp4'
EXEMPLO_9 = V / 'Criativos Cortez - Voz de IA/EXEMPLO_9 V1 - IA 3 Confissao (previa).mp4'
EXEMPLO_8 = V / 'Criativos Cortez - Voz de IA/EXEMPLO_8 V1 - IA 1 Ninguem editou este video (previa).mp4'
CONVIDADO = J.parent / '<PREENCHER: fonte ou prova própria>'
BASE = J.parent / '<PREENCHER: fonte ou prova própria>'      # imagem de câmera do EXEMPLO_4, mesma linha do tempo, sem legenda


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
    return {'src': Path(src).name, 'ss': ss, 'dur': dur, 'frames': len(fs)}


SHORTS = [('s1', EXEMPLO_2, 46.0), ('s2', EXEMPLO_3, 3.6), ('s3', EXEMPLO_4, 54.55), ('s4', EXEMPLO_5, 15.0), ('s5', EXEMPLO_6, 1.0), ('s6', EXEMPLO_7, 6.5),
          ('s7', EXEMPLO_3, 24.5), ('s8', EXEMPLO_8, 3.0), ('s9', EXEMPLO_9, 9.5)]
rep = {'long': seq('long', YT, 66.0, 3.0, '960:540')}
for n, src, ss in SHORTS:
    rep[n] = seq(n, src, ss, 2.5, '270:480')
rep['j'] = seq('j', CONVIDADO, 0.6, 2.5, '270:480')
rep['jh'] = seq('jh', CONVIDADO, 0.6, 3.0, '540:960')
rep['hb'] = seq('hb', BASE, 12.30, 3.0, '540:960')
rep['hl'] = seq('hl', EXEMPLO_4, 12.30, 3.0, '540:960')
rep['hc'] = seq('hc', EXEMPLO_4, 15.45, 3.0, '540:960')


def env(src, ss, dur, rate):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ss:.3f}', '-t', f'{dur:.3f}', '-i', str(src), '-f', 's16le', '-ac', '1', '-ar', '8000', '-'],
                       capture_output=True).stdout
    x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
    h = int(8000 / rate); n = len(x) // h
    return 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)


ydb = env(YT, 0, 780, 0.5)                                   # blocos de 2 s
yv = np.clip((ydb + 50) / 38, 0, 1)
ys = np.convolve(yv, np.ones(5) / 5, mode='same')            # relevo suavizado (o que a câmera vê)
# 10 "melhores trechos" para a ilustração: máximos locais do relevo suavizado, separados por ≥ 50 s, fora das pontas
order = np.argsort(-ys)
picks = []
for i in order:
    if 8 <= i <= len(ys) - 8 and all(abs(i - p) >= 25 for p in picks):
        picks.append(int(i))
    if len(picks) == 10:
        break
picks.sort()
(J / 'analysis').mkdir(exist_ok=True)
(J / '<PREENCHER: fonte ou prova própria>').write_text(json.dumps({'bin_s': 2.0, 'dur_s': 779.13, 'raw': [round(float(v), 3) for v in yv],
    'smooth': [round(float(v), 3) for v in ys], 'peaks': picks, 'note': '<PREENCHER: fonte ou prova própria>'}, indent=0))
edb = env(EXEMPLO_4, 12.3, 6.2, 25)
(J / 'analysis/e117_env.json').write_text(json.dumps([round(float(v), 3) for v in np.clip((edb + 52) / 40, 0, 1)]))
rep['<PREENCHER: fonte ou prova própria>'] = [p * 2 for p in picks]

F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-600-latin-ext.woff2', 'inter-800-latin.woff2',
          'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    if (F / f).exists():
        shutil.copyfile(F / f, A / f)
for f in ['gsap.min.js', 'grain.png']:
    shutil.copyfile(C2 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v.get('frames') if isinstance(v, dict) else v) for k, v in rep.items()}, ensure_ascii=False))
