#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição "Faz um teste comigo" (F10 · ID08 Azul e Papel · voz de IA do Cortez).
Prova = só material do próprio usuário, sem logotipos nem terceiros:
- seq/raw  = gravação bruta da Oferta 0,98–3,98 s (HDR do iPhone → BT.709 pelo VideoToolbox + curva da V2 do EXEMPLO_2), 300x534:
             o "vídeo parado no seu celular" (rotulado "gravação bruta real · exemplo")
- roll/rNN = quadros soltos da mesma gravação bruta em outros momentos (outras "tomadas" no rolo da câmera ilustrativo)
- seq/fin  = EXEMPLO_2 V2 0,0–4,4 + 12,0–15,2 + 15,45–17,95 s (a entrega que o Cortez fez a partir dessa gravação; só trechos com o
             apresentador e cena, sem os gráficos brancos e sem o trecho de filme de terceiros ≈23–26 s), 720x1280: "ele volta pronto"
Fontes Inter / IBM Plex Mono (ID08), three.js r186 + addons, GSAP e grão copiados de jobs/cortez-live-c2/comp/assets.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
RAW = WS / '<PREENCHER: fonte ou prova própria>'
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def seq(name, parts, size, hdr=False):
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


rep = {'raw': seq('raw', [(RAW, 0.98, 3.0)], '300:534', hdr=True), 'fin': seq('fin', [(EXEMPLO_2, 0.0, 4.4), (EXEMPLO_2, 12.0, 3.2), (EXEMPLO_2, 15.45, 2.5)], '720:1280')}
R = A / 'roll'
shutil.rmtree(R, ignore_errors=True); R.mkdir(parents=True)
STILLS = [9.0, 23.5, 36.0, 49.0, 62.5, 76.0, 88.0, 97.0]
for k, ss in enumerate(STILLS):
    run(['ffmpeg', '-v', 'error', '-y', '-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld', '-ss', f'{ss:.3f}', '-i', RAW,
         '-vf', f'{HDR},scale=300:534:flags=lanczos,format=yuvj420p', '-frames:v', 1, '-q:v', 3, R / f'r{k:02d}.jpg'])
rep['roll'] = {'frames': len(STILLS), 'source': RAW.name, 'times': STILLS}

for f in ['gsap.min.js', 'grain.png', 'inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2', 'inter-OFL.txt']:
    shutil.copyfile(C2 / f, A / f)
F = SYS / 'assets/fonts/portable'
for f in ['ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt', 'inter-700-latin.woff2', 'inter-700-latin-ext.woff2', 'inter-800-latin-ext.woff2']:
    shutil.copyfile(F / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v.get('frames') if isinstance(v, dict) else v) for k, v in rep.items()}))
