#!/usr/bin/env python3
"""EXEMPLO_1 — mídia da composição.
1) Masters dos dois quadros da live (Apresentador em cima, Convidado embaixo), cada segmento do EDL com o número exato de quadros,
   recortados do 432x768 original e ampliados com lanczos + redução leve de blocos + nitidez suave (a live é de baixa
   resolução; por isso a composição usa cartões, nunca tela cheia).
2) Vitrine "editado pelo Cortez": quadros e trechos curtos de entregas do próprio usuário feitas pelo Cortez
   (02 - Ver vídeos). Só material próprio; nada de terceiros nem marcas alheias.
Saídas em comp/assets/. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
SRC = WS / '<PREENCHER: fonte ou prova própria>'
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
CROPS = {'apresentador': 'crop=420:370:6:4', 'convidado': 'crop=420:370:6:394'}
LOOK = 'scale=900:794:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.55:5:5:0,fps=30,setsar=1,format=yuv420p'


def frames(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip())


for name, crop in CROPS.items():
    lst = []
    for i, s in enumerate(edl['segments']):
        n = s['frames']
        p = TMP / f'{name}{i:02d}.mp4'
        spec = TMP / f'{name}{i:02d}.spec'
        key = json.dumps([s['in'], n, crop, LOOK])
        if not (p.exists() and spec.exists() and spec.read_text() == key):
            subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f"{s['in']:.4f}", '-i', str(SRC), '-t', f'{n / FPS + 0.2:.4f}', '-an',
                            '-vf', f'{crop},{LOOK}', '-frames:v', str(n), '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-g', '15',
                            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', str(p)], check=True)
            if frames(p) != n:
                raise SystemExit(f'{name} seg {i}: quadros {frames(p)} != {n}')
            spec.write_text(key)
        lst.append(f"file '{p}'")
    (TMP / f'{name}.txt').write_text('\n'.join(lst) + '\n')
    out = A / f'{name}.mp4'
    # +1 s congelando o último quadro: o cartão ainda está na tela enquanto sai, no início do CTA
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / f'{name}.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
                    '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(out)], check=True)
    print(name, frames(out), round(edl['duration'] * FPS) + 30)

# vitrine: (arquivo, segundo, nome) — quadros escolhidos na folha de contato das entregas
V = WS / '<PREENCHER: fonte ou prova própria>'
SHOW = [
    ('<PREENCHER: fonte ou prova própria>', [7.0, 14.0, 40.5, 47.0, 60.0, 67.0]),
    ('<PREENCHER: fonte ou prova própria>', [3.0, 9.0, 27.0, 41.0, 62.0, 70.0]),
    ('<PREENCHER: fonte ou prova própria>', [10.0, 21.0, 26.5, 31.5, 47.5, 58.0]),
    ('<PREENCHER: fonte ou prova própria>', [65.0, 195.0, 260.0, 325.0, 390.0, 520.0, 585.0, 650.0]),
]
k = 0
for f, ts in SHOW:
    for t in ts:
        k += 1
        o = TMP / f'show{k:02d}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(V / f), '-frames:v', '1', '-vf', 'scale=540:-2', '-q:v', '3', str(o)], check=True)
print('stills', k)
