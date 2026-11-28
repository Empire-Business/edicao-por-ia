#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Ninguém editou este vídeo" (F10 · IDP01 · voz de IA do Cortez).
Prova = só entregas do próprio usuário feitas pelo Cortez (EXEMPLO_2 V2 OFERTA) e a gravação bruta dessa mesma entrega
(HDR do iPhone → BT.709 pelo VideoToolbox + a curva da V2 do EXEMPLO_2, como no EXEMPLO_3). Sem logotipos nem material de terceiros.
- seq/sa  = imagem de câmera do EXEMPLO_2 (renders/base-v2.mp4) 12,30–15,30 s, plano fechado · camada CENAS antes do corte
- seq/sb  = a mesma imagem 15,45–18,45 s, plano aberto          · depois do corte ("cada corte"); sem legenda queimada
- seq/raw = gravação bruta 0,98–3,98 s                   · "você grava"
- seq/fin + fin.mp4 (1080x1920, quadros-chave densos) = EXEMPLO_2 0,00–4,50 s + 31,40–35,00 s · "eu te devolvo pronto" e CTA
Fontes Inter (IDP01), three.js r186 + addons, GSAP e grão copiados de jobs/cortez-live-c2/comp/assets.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'
RAW = WS / '<PREENCHER: fonte ou prova própria>'
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, parts, size='540:960', hdr=False):
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


FIN = [(EXEMPLO_2, 0.0, 4.5), (EXEMPLO_2, 31.4, 3.6)]
BASE = J.parent / '<PREENCHER: fonte ou prova própria>'      # imagem de câmera do EXEMPLO_2 (sem legenda nem gráfico), mesma linha do tempo
rep = {'sa': seq('sa', [(BASE, 12.30, 3.0)], size='540:960,crop=460:818:40:52,scale=540:960'), 'sb': seq('sb', [(BASE, 15.45, 3.0)]), 'raw': seq('raw', [(RAW, 0.98, 3.0)], hdr=True),
       'fin': seq('fin', FIN)}
# vídeo final em resolução cheia para o trecho em tela cheia (HTML <video>, mesmos quadros do seq/fin)
lst = J / 'tmp/fin.txt'
parts = []
for i, (src, ss, dur) in enumerate(FIN):
    o = J / f'tmp/fin{i}.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', src, '-t', f'{dur:.3f}', '-an', '-vf', 'fps=30,scale=1080:1920:flags=lanczos,format=yuv420p',
         '-c:v', 'libx264', '-crf', 14, '-preset', 'medium', '-g', 15, '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', o])
    parts.append(f"file '{o}'")
lst.write_text('\n'.join(parts) + '\n')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', 0, '-i', lst, '-c:v', 'libx264', '-crf', 14, '-preset', 'medium', '-g', 15,
     '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', A / 'fin.mp4'])
rep['fin_mp4'] = {'parts': [(p[0].name, p[1], p[2]) for p in FIN]}

for f in ['gsap.min.js', 'grain.png', 'inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2', 'inter-OFL.txt']:
    shutil.copyfile(C2 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v.get('frames') for k, v in rep.items()}))
