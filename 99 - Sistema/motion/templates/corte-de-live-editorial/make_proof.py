#!/usr/bin/env python3
"""EXEMPLO_1 V3 — prova visual: trechos reais de vídeos que o Cortez já editou para o usuário (02 - Ver vídeos), só a parte de
motion design (sem logotipo, sem promessa de outro produto, sem a legenda queimada que brigaria com a nossa).
1) seqA/seqB: quadros JPG 30 fps para a tela do celular 3D (three.js troca a textura por quadro → vídeo de verdade, determinístico).
2) fsA/fsB: recortes grandes das animações para o trecho "a animação estilo After Effects".
3) convidado_cine.mp4 / convidado_pip.mp4: cópias do master do Convidado para o modo cinema e a miniatura (mesmo relógio).
Run: ../../../.venv/bin/python src/make_proof.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
V = WS / '<PREENCHER: fonte ou prova própria>'
A = J / 'comp/assets'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
SEQ = {
    'seqA': [(EXEMPLO_2, 2.0, 1.1), (EXEMPLO_2, 16.5, 1.1), (EXEMPLO_4, 20.0, 1.1), (EXEMPLO_2, 46.0, 1.1), (EXEMPLO_3, 26.0, 1.1), (EXEMPLO_4, 29.0, 1.1)],
    'seqB': [(EXEMPLO_2, 59.0, 1.2), (EXEMPLO_4, 41.0, 1.2), (EXEMPLO_3, 2.5, 1.2), (EXEMPLO_2, 69.5, 1.2)],
}
FS = {  # (fonte, início, duração, recorte)
    'fsA': (EXEMPLO_3, 3.6, 2.6, 'crop=1080:690:0:0'),
    'fsB': (EXEMPLO_4, 54.55, 4.0, 'crop=1080:880:0:520'),
}
rep = {}
for name, parts in SEQ.items():
    d = A / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    k = 0
    for src, ss, dur in parts:
        tmp = J / 'tmp' / f'{name}-part'
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur), '-vf', 'fps=30,scale=540:960:flags=lanczos',
                        '-q:v', '3', str(tmp / '%04d.jpg')], check=True)
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    rep[name] = {'frames': k, 'parts': [(p[0].name, p[1], p[2]) for p in parts]}
for name, (src, ss, dur, crop) in FS.items():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur), '-an', '-vf', f'{crop},fps=30,format=yuv420p',
                    '-c:v', 'libx264', '-crf', '14', '-g', '15', '-keyint_min', '15', '-movflags', '+faststart', str(A / f'{name}.mp4')], check=True)
    rep[name] = {'source': src.name, 'start': ss, 'dur': dur, 'crop': crop}
for n in ('convidado_cine', 'convidado_pip'):
    shutil.copyfile(A / 'convidado.mp4', A / f'{n}.mp4')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v.get('frames', v.get('dur')) for k, v in rep.items()}))
