#!/usr/bin/env python3
"""EXEMPLO_1 — rostos da live do Instagram (tela dividida: Apresentador em cima, Convidado embaixo), seguindo a EDL atual quadro a quadro.
Gera comp/assets/convidado.mp4 e comp/assets/apresentador.mp4: o mesmo trecho da EDL recortado em cada metade (os dois aparecem o tempo todo na
live; a composição mostra só quem fala). Ampliação lanczos, redução de blocos e nitidez suave (live em 432×768).
Run: ../../../.venv/bin/python src/make_media.py
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
IG = WS / '<PREENCHER: fonte ou prova própria>'
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
POST = 'scale=560:560:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.6:5:5:0,eq=saturation=1.04,fps=30,setsar=1,format=yuv420p'
CROPS = {'convidado': 'crop=370:370:31:394', 'apresentador': 'crop=340:340:76:12'}


def run(a):
    subprocess.run(a, check=True)


def frames(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip())


rep = {}
for who, crop in CROPS.items():
    lst = []
    for i, s in enumerate(edl['segments']):
        p = TMP / f'{who}{i:02d}.mp4'
        run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f"{s['in']:.4f}", '-i', str(IG), '-t', f"{s['frames'] / FPS + 0.2:.4f}", '-an',
             '-vf', f'{crop},{POST}', '-frames:v', str(s['frames']), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
        if frames(p) != s['frames']:
            raise SystemExit(f'{who} seg {i}: {frames(p)} != {s["frames"]}')
        lst.append(f"file '{p}'")
    (TMP / f'{who}.txt').write_text('\n'.join(lst) + '\n')
    out = A / f'{who}.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / f'{who}.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=6',
         '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(out)])
    rep[who] = {'frames': frames(out), 'crop': crop}
(J / 'analysis/media.json').write_text(json.dumps({'faces': rep, 'source': 'live do Instagram (432×768, tela dividida)'}, ensure_ascii=False, indent=1))
print(json.dumps(rep))
