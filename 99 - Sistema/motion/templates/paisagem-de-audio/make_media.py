#!/usr/bin/env python3
"""EXEMPLO_1 — mídia das pessoas.
1) Apresentador: webcam da live do YouTube (canto inferior direito da tela compartilhada; recorte quadrado no rosto, nunca a barra lateral
   nem o aviso de limite), exatamente os quadros dos trechos do EDL em que ele fala: apresentador_intro.mp4 (apresentação) e
   apresentador_after.mp4 (quem é o Convidado). Quadros-chave densos (-g 15) e 1 s extra no fim (tpad) para não ficar preto.
2) Convidado: quadro parado dele sorrindo na live do Instagram (IG 250,25 s, quadro de baixo), para o cartão do "áudio real" —
   o áudio de WhatsApp não tem imagem; a foto não finge sincronia de boca.
Saídas em comp/assets/. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
YT = WS / '<PREENCHER: fonte ou prova própria>'
IG = WS / '<PREENCHER: fonte ou prova própria>'
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
PIP = 'crop=232:232:1599:773,scale=320:320:flags=lanczos,hqdn3d=1.2:1.2:3:3,unsharp=5:5:0.5:5:5:0,eq=saturation=1.05,fps=30,setsar=1,format=yuv420p'
CONVIDADO = 'crop=370:370:31:394,scale=512:512:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.6:5:5:0,eq=saturation=1.04'


def run(a):
    subprocess.run(a, check=True, stdin=subprocess.DEVNULL)


def frames(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip())


rep = {}
for name, takes in (('apresentador_intro', {'t01'}), ('apresentador_after', {'t06'})):
    lst = []
    for i, s in enumerate(edl['segments']):
        if s['take'] not in takes:
            continue
        p = TMP / f'{name}{i:02d}.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['in']:.4f}", '-i', str(YT), '-t', f"{s['frames'] / FPS + 0.2:.4f}", '-an', '-vf', PIP,
             '-frames:v', str(s['frames']), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
        if frames(p) != s['frames']:
            raise SystemExit(f'{name} seg {i}: quadros {frames(p)} != {s["frames"]}')
        lst.append(f"file '{p}'")
    (TMP / f'{name}.txt').write_text('\n'.join(lst) + '\n')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / f'{name}.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
         '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(A / f'{name}.mp4')])
    rep[name] = frames(A / f'{name}.mp4')
run(['ffmpeg', '-v', 'error', '-y', '-ss', '250.25', '-i', str(IG), '-frames:v', '1', '-vf', CONVIDADO, '-q:v', '2', str(A / 'convidado_still.jpg')])
rep['convidado_still'] = 'live do Instagram @250,25 s (quadro de baixo, sorrindo)'
(J / 'analysis/people_media.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
