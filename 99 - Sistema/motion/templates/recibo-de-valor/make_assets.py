#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição (comp/assets/).
- Fontes da ID04 Dourado (Libre Baskerville, Inter, IBM Plex Mono — licenças OFL junto), three.js r186 (ESM + addons) e GSAP do lote.
- Pessoas (live do Instagram, 432x768: Apresentador no quadro de cima, Convidado no de baixo): recorte quadrado no rosto de cada um, seguindo
  exatamente os trechos do EDL (mesmo número de quadros), em vídeos HTML para os círculos/cartão: convidado.mp4 e apresentador.mp4.
- Prova — só entregas do próprio usuário editadas pelo Cortez (02 - Ver vídeos), trechos já conferidos sem logotipos nem terceiros
  nos cortes EXEMPLO_2/EXEMPLO_3: EXEMPLO_4 V2 @13,0 s (apresentador), EXEMPLO_5 V3 @46,0 s, EXEMPLO_6 V1 @3,6 s (9:16) e o vídeo longo LONGO_1 @66,0 s (16:9).
  Sequências JPG por quadro (textura 3D determinística).
Run: ../../../.venv/bin/python src/make_assets.py"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
IG = WS / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_6 = V / '<PREENCHER: fonte ou prova própria>'
LONGO_1 = V / '<PREENCHER: fonte ou prova própria>'
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']


def run(a):
    subprocess.run(a, check=True)


def nframes(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip())


# fontes, three.js, gsap, grão
F = SYS / 'assets/fonts/portable'
for f in ['libre-baskerville-variable.ttf', 'libre-baskerville-OFL.txt', 'inter-400-latin.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2',
          'inter-400-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
for f in ['ibm-plex-mono-400-latin.woff2', 'inter-600-latin-ext.woff2', 'inter-800-latin-ext.woff2']:
    if (F / f).exists():
        shutil.copyfile(F / f, A / f)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
for f in ['gsap.min.js', 'grain.png']:
    shutil.copyfile(C2 / f, A / f)

# pessoas: recortes quadrados seguindo o EDL
CROP = {'convidado': 'crop=370:370:31:394', 'apresentador': 'crop=370:370:31:4'}
rep = {}
for who, cr in CROP.items():
    lst = []
    for i, s in enumerate(edl['segments']):
        p = TMP / f'{who}{i:02d}.mp4'
        run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f"{s['in']:.4f}", '-i', str(IG), '-t', f"{s['frames'] / FPS + 0.3:.4f}", '-an',
             '-vf', f'fps=30,{cr},scale=512:512:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.6:5:5:0,eq=saturation=1.04,setsar=1,format=yuv420p',
             '-frames:v', str(s['frames']), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
        if nframes(p) != s['frames']:
            raise SystemExit(f'{who} seg {i}: quadros {nframes(p)} != {s["frames"]}')
        lst.append(f"file '{p}'")
    (TMP / f'{who}.txt').write_text('\n'.join(lst) + '\n')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / f'{who}.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
         '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(A / f'{who}.mp4')])
    rep[who] = nframes(A / f'{who}.mp4')


def seq(name, src, ss, n, vf):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', str(src), '-frames:v', str(n), '-vf', f'fps=30,{vf}', '-q:v', '3', '-start_number', '0', str(d / '%04d.jpg')])
    return len(list(d.glob('*.jpg')))


rep['pA'] = seq('pA', EXEMPLO_4, 13.0, 105, 'scale=432:768:flags=lanczos')
rep['pB'] = seq('pB', EXEMPLO_5, 46.0, 90, 'scale=432:768:flags=lanczos')
rep['pC'] = seq('pC', EXEMPLO_6, 3.6, 90, 'scale=432:768:flags=lanczos')
rep['pL'] = seq('pL', LONGO_1, 66.0, 60, 'scale=768:432:flags=lanczos')
rep['sources'] = {'convidado/apresentador': 'live do Instagram, trechos do EDL (Convidado: quadro de baixo; Apresentador: quadro de cima)',
                  'pA': 'EXEMPLO_4 V2 @13,0 s', 'pB': 'EXEMPLO_5 V3 @46,0 s', 'pC': 'EXEMPLO_6 V1 @3,6 s', 'pL': '<PREENCHER: fonte ou prova própria>'}
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
