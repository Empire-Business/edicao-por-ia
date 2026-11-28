#!/usr/bin/env python3
"""EXEMPLO_1 — mídia da composição.
1) PiP do Apresentador: webcam da live do YouTube (canto inferior direito da tela compartilhada; recorte quadrado 232 px no rosto,
   nunca a barra lateral nem o aviso de limite), cada trecho do EDL com o número exato de quadros, só nas falas dele.
2) Convidado (live do Instagram, quadro de baixo): sequência JPG do trecho em que ele fala (textura 3D determinística) e um
   quadro parado dele sorrindo (IG 503,5 s, reação natural na live) para o cartão enquanto o Apresentador fala dele.
3) Prova — só entregas do próprio usuário editadas pelo Cortez (02 - Ver vídeos), sem logotipos:
   `raw`  = gravação sem edição do apresentador do EXEMPLO_2 (base de câmera convertida de HLG para BT.709 no próprio job do EXEMPLO_2,
            jobs/video-18157f4a38d1/renders/base-v2.mp4: só imagem de câmera, sem legenda nem gráfico) — rótulo "bruto";
   `hero` = o mesmo apresentador já editado pelo Cortez (EXEMPLO_2 V2), para o antes → depois;
   `c1..c3` = vídeos curtos editados pelo Cortez para o cartão final (EXEMPLO_2 V2, EXEMPLO_3, EXEMPLO_4).
Saídas em comp/assets/. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
YT = WS / '<PREENCHER: fonte ou prova própria>'
IG = WS / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
BASE = J.parent / '<PREENCHER: fonte ou prova própria>'
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']


def run(a):
    subprocess.run(a, check=True)


def frames(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip())


# 1) PiP do Apresentador (só trechos do YouTube; o Convidado fala no fim, quando o PiP já saiu)
PIP = 'crop=232:232:1599:773,scale=320:320:flags=lanczos,hqdn3d=1.2:1.2:3:3,unsharp=5:5:0.5:5:5:0,eq=saturation=1.05,fps=30,setsar=1,format=yuv420p'
lst = []
for i, s in enumerate(edl['segments']):
    if s['src'] != 'yt':
        continue
    p = TMP / f'pip{i:02d}.mp4'
    run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f"{s['in']:.4f}", '-i', str(YT), '-t', f"{s['frames'] / FPS + 0.2:.4f}", '-an', '-vf', PIP,
         '-frames:v', str(s['frames']), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
    if frames(p) != s['frames']:
        raise SystemExit(f'pip seg {i}: quadros {frames(p)} != {s["frames"]}')
    lst.append(f"file '{p}'")
(TMP / 'pip.txt').write_text('\n'.join(lst) + '\n')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / 'pip.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
     '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(A / 'apresentador_pip.mp4')])
pip_frames = frames(A / 'apresentador_pip.mp4')


def seq(name, parts, vf):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    k = 0
    for src, ss, n in parts:
        tmp = TMP / f'seq-{name}'
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.4f}', '-i', str(src), '-frames:v', str(n), '-vf', f'fps=30,{vf}', '-q:v', '3', str(tmp / '%04d.jpg')])
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    return k


CONVIDADO = 'crop=370:370:31:394,scale=512:512:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.6:5:5:0,eq=saturation=1.04'
rep = {'apresentador_pip_frames': pip_frames}
rep['convidado_live'] = seq('convidado_live', [(IG, s['in'], s['frames']) for s in edl['segments'] if s['src'] == 'ig'], CONVIDADO)
run(['ffmpeg', '-v', 'error', '-y', '-ss', '503.5', '-i', str(IG), '-frames:v', '1', '-vf', CONVIDADO, '-q:v', '2', str(A / 'convidado_still.jpg')])
rep['raw'] = seq('raw', [(BASE, 13.0, 90)], 'scale=360:640:flags=lanczos,eq=saturation=0.78:contrast=0.94:brightness=0.01')
rep['hero'] = seq('hero', [(EXEMPLO_2, 13.0, 105)], 'scale=540:960:flags=lanczos')
rep['c1'] = seq('c1', [(EXEMPLO_2, 29.2, 90)], 'scale=360:640:flags=lanczos')
rep['c2'] = seq('c2', [(EXEMPLO_3, 46.0, 90)], 'scale=360:640:flags=lanczos')
rep['c3'] = seq('c3', [(EXEMPLO_4, 3.6, 90)], 'scale=360:640:flags=lanczos')
rep['sources'] = {'apresentador_pip': 'live YouTube (webcam) — trechos do EDL', 'convidado': 'live Instagram (quadro de baixo)', 'raw': str(BASE.relative_to(WS)) + ' @13,0 s',
                  'hero': str(EXEMPLO_2.relative_to(WS)) + ' @13,0 s (mesmo instante do bruto: antes → depois)', 'c1': 'EXEMPLO_2 V2 @29,2 s', 'c2': 'EXEMPLO_3 V3 @46,0 s', 'c3': 'EXEMPLO_4 V1 @3,6 s'}
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
