#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Horas perdidas editando" (F10 · ID07 Laranja · voz de IA do Cortez).
Prova = só entregas do próprio usuário feitas pelo Cortez, sem logotipos nem material de terceiros:
- seq/raw = gravação bruta da Oferta 0,98–3,98 s (HDR do iPhone → BT.709 pelo VideoToolbox + curva da V2 do EXEMPLO_2) · monitor da
  edição manual ("ajustando legenda")
- seq/fin = EXEMPLO_2 V2 0,00–4,50 s + 6,45–8,45 s (reunião) + 15,45–16,95 s (escritório vazio) — a entrega editada pelo Cortez a partir
  dessa gravação, sem o gráfico branco do contador · o vídeo pronto que se monta no "Eu sou o Cortez"
- broll/*.jpg = cenas que o Cortez achou para o EXEMPLO_2 (agenda, reunião, escritório vazio, call center), recortadas sem a legenda queimada ·
  chip "cenas encontradas"
Fontes Inter e IBM Plex Mono (ID07), three.js r186 + addons, GSAP e grão copiados de jobs/cortez-ia-d5/comp/assets.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
SRCA = J.parent / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
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


rep = {'raw': seq('raw', [(RAW, 0.98, 3.0)], hdr=True), 'fin': seq('fin', [(EXEMPLO_2, 0.0, 4.5), (EXEMPLO_2, 6.45, 2.0), (EXEMPLO_2, 15.45, 1.5)])}
BR = {'agenda': (0.45, 'crop=1080:700:0:0'), 'reuniao': (6.6, 'crop=900:400:90:712'), 'escritorio': (15.6, 'crop=1080:700:0:0'),
      'callcenter': (17.6, 'crop=1080:1060:0:20')}
d = A / 'broll'; shutil.rmtree(d, ignore_errors=True); d.mkdir()
for n, (t, cr) in BR.items():
    run(['ffmpeg', '-v', 'error', '-y', '-ss', t, '-i', EXEMPLO_2, '-frames:v', 1, '-vf', f'{cr},scale=480:-2:flags=lanczos', '-q:v', 3, d / f'{n}.jpg'])
rep['broll'] = BR

for f in ['gsap.min.js', 'grain.png', 'inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2',
          'inter-700-latin-ext.woff2', 'inter-800-latin.woff2', 'inter-800-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(SRCA / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(SRCA / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v.get('frames') if isinstance(v, dict) and 'frames' in v else v) for k, v in rep.items()}, ensure_ascii=False))
