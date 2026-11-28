#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Errou? Relaxa" (vidros das tomadas).
Prova: só material do próprio usuário —
  * gravação bruta real do apresentador (01 - Enviar vídeos/OFERTA/<gravacao-bruta>.mp4; HLG do iPhone → BT.709 pelo
    VideoToolbox + a mesma curva da V2 do EXEMPLO_2, como no EXEMPLO_3):
      p2 = tomada que trava  ("Tem consultor com 15 anos de mercado, que…"  18,50–20,62 s)
      p3 = gagueira          ("É assim. … É assim que…"                      1,00–2,95 s)
      p1 = tomada repetida   ("Tem consultor com mais de 15 anos…"          7,70–10,05 s)
      p4 = a 3ª tomada da frase repetida ("Tem consultor com 15 anos de mercado, que resolve…" 21,10–24,85 s)
      p5 = a melhor tomada da frase da gagueira ("É assim que eu encheria a minha agenda se eu fosse consultor…" 2,90–6,95 s)
  * a entrega EXEMPLO_2 V2 (feita pelo Cortez a partir dessa gravação): a mesma frase limpa, com o apresentador na câmera, 0,00–4,60 s.
Fontes da IDP02 (Instrument Serif, Roboto Condensed, Schibsted Grotesk), three.js r186, GSAP, grão.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'; A.mkdir(parents=True, exist_ok=True)
RAW = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'
C12 = J.parent / '<PREENCHER: fonte ou prova própria>'
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"      # = visual/grade-v2.txt do EXEMPLO_2
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE
SIZE = '720:1280'


def seq(name, src, ss, dur, hdr):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    n = int(round(dur * 30))
    if hdr:
        a = ['ffmpeg', '-v', 'error', '-y', '-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld', '-ss', f'{ss:.4f}', '-i', str(src),
             '-vf', f'{HDR},scale={SIZE}:flags=lanczos,format=yuvj420p', '-frames:v', str(n), '-q:v', '3', str(d / '%04d.jpg')]
    else:
        a = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.4f}', '-i', str(src), '-vf', f'fps=30,scale={SIZE}:flags=lanczos', '-frames:v', str(n),
             '-q:v', '3', str(d / '%04d.jpg')]
    subprocess.run(a, check=True)
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    return len(fs)


SEQ = {'p2': (RAW, 18.50, 2.12, True), 'p3': (RAW, 1.00, 1.95, True), 'p1': (RAW, 7.70, 2.35, True), 'p4': (RAW, 21.10, 3.75, True),
       'p5': (RAW, 2.90, 4.05, True), 'e117': (EXEMPLO_2, 0.00, 4.60, False)}
rep = {k: seq(k, *v) for k, v in SEQ.items()}
for f in ['InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf', 'InstrumentSerif-OFL.txt', 'RobotoCondensed-wght.ttf', 'RobotoCondensed-OFL.txt',
          'SchibstedGrotesk-wght.ttf', 'SchibstedGrotesk-OFL.txt', 'gsap.min.js', 'grain.png']:
    shutil.copyfile(C12 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True); shutil.copytree(C12 / 'three', A / 'three')
(J / 'analysis/proof_assets.json').write_text(json.dumps({'frames': rep, 'sources': {k: [str(v[0].relative_to(WS)), v[1], v[2]] for k, v in SEQ.items()}},
                                                         ensure_ascii=False, indent=1))
print(json.dumps(rep))
