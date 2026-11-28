#!/usr/bin/env python3
"""EXEMPLO_1 — rostos da live para as miniaturas redondas (quem está falando).
A live do Instagram tem 432x768 (Apresentador em cima, Convidado embaixo). Para cada segmento do EDL, recorta um quadrado de 300 px
centrado no rosto de cada um, amplia para 360 px (lanczos + redução leve de blocos + nitidez suave) e junta tudo no relógio
do vídeo final (mesmo número de quadros do EDL). +1 s congelado no fim para a saída da miniatura no início do CTA.
Saídas: comp/assets/apresentador.mp4 e comp/assets/convidado.mp4. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
SRC = WS / '<PREENCHER: fonte ou prova própria>'
A = J / 'comp/assets'
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
CROPS = {'apresentador': 'crop=300:300:72:70', 'convidado': 'crop=300:300:120:395'}
LOOK = 'scale=360:360:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.5:5:5:0,fps=30,setsar=1,format=yuv420p'


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
                            '-vf', f'{crop},{LOOK}', '-frames:v', str(n), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15',
                            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', str(p)], check=True)
            if frames(p) != n:
                raise SystemExit(f'{name} seg {i}: quadros {frames(p)} != {n}')
            spec.write_text(key)
        lst.append(f"file '{p}'")
    (TMP / f'{name}.txt').write_text('\n'.join(lst) + '\n')
    out = A / f'{name}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / f'{name}.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
                    '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(out)], check=True)
    print(name, frames(out), round(edl['duration'] * FPS) + 30)
