#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição 3D (tudo dentro do trabalho, nada externo em tempo de render).
- `live`: time-lapse REAL do Cortez trabalhando na live do YouTube (painel central da conversa recortado: x 430–1430, y 80–840 do 1920x1080;
  sem a barra lateral com nomes de sessões, sem o painel de ambiente/caminho, sem o aviso de limite de uso e sem a webcam).
  Só os trechos em que a janela da tarefa está na tela (580–697, 1376–1419, 1678–1787, 2148–2208 s; conferidos em folha de contato);
  1 quadro por segundo da live → tocado a 30 q/s (≈30x acelerado).
- Prova (só entregas do próprio usuário editadas pelo Cortez, quadros conferidos sem logotipos/terceiros): sequências 9:16 de EXEMPLO_2 V2
  (o vídeo editado naquela live), EXEMPLO_3 e EXEMPLO_4; fotos (stills) de EXEMPLO_3, EXEMPLO_5, EXEMPLO_4, EXEMPLO_2 e do exemplo F16 para a agenda da semana.
- Convidado (live do Instagram) para o cartão do depoimento e PiP do Apresentador (webcam da live do YouTube / quadro de cima da live do Instagram),
  com o número exato de quadros de cada trecho do EDL.
- Fontes da ID08 (Inter + IBM Plex Mono), three.js r186 (ESM) + addons, GSAP, granulação.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/assets'
TMP.mkdir(parents=True, exist_ok=True)
V = WS / '<PREENCHER: fonte ou prova própria>'
YT = WS / '<PREENCHER: fonte ou prova própria>'
IG = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
F16 = V / '2026-10-08_tutorial-edicao/exemplo_9x16_F16_ID07_V3.mp4'
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
rep = {}


def run(a):
    subprocess.run(a, check=True)


def seq(name, parts, size, q=3):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    k = 0
    for src, ss, dur, vf in parts:
        tmp = TMP / f'seq-{name}'
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.4f}', '-i', str(src), '-t', f'{dur:.4f}', '-an', '-vf', f'{vf}scale={size}:flags=lanczos,format=yuvj420p',
             '-q:v', str(q), str(tmp / '%04d.jpg')])
        for f in sorted(tmp.glob('*.jpg')):
            f.rename(d / f'{k:04d}.jpg'); k += 1
        shutil.rmtree(tmp)
    rep[name] = {'frames': k, 'parts': [(Path(p[0]).name, p[1], p[2]) for p in parts]}
    return k


# 1) time-lapse do Cortez trabalhando (1 quadro por segundo da live, só a janela da tarefa)
RUNS = [(610, 697), (1376, 1419), (1678, 1787), (2148, 2208)]
d = A / 'seq/live'
shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
k = 0
for a, b in RUNS:
    tmp = TMP / 'live'
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a), '-i', str(YT), '-t', str(b - a + 1), '-an', '-vf', 'fps=1,crop=1000:760:430:80,format=yuvj420p',
         '-q:v', '3', str(tmp / '%04d.jpg')])
    for f in sorted(tmp.glob('*.jpg')):
        f.rename(d / f'{k:04d}.jpg'); k += 1
rep['live'] = {'frames': k, 'runs_live_seconds': RUNS, 'crop': '1000x760+430+80 (painel central)', 'rate': '1 quadro = 1 s da live'}

# 2) prova: sequências 9:16 (3 s) e stills
seq('e117a', [(EXEMPLO_2, 32.0, 6.0, '')], '432:768')   # só o apresentador (31,25–40 s conferido; sem B-roll de terceiros)
seq('e117b', [(EXEMPLO_2, 0.4, 4.0, '')], '432:768')    # 0–4,5 s: só o apresentador
seq('e91', [(EXEMPLO_3, 40.5, 3.0, '')], '432:768')
seq('e93', [(EXEMPLO_4, 9.0, 3.0, '')], '432:768')
STILLS = [(EXEMPLO_2, 10.0), (EXEMPLO_3, 46.0), (EXEMPLO_4, 3.6), (EXEMPLO_5, 15.0), (F16, 10.0), (EXEMPLO_2, 31.5), (EXEMPLO_3, 57.0), (EXEMPLO_5, 45.0), (F16, 20.0), (EXEMPLO_4, 24.5),
          (EXEMPLO_2, 47.5), (EXEMPLO_3, 14.0), (EXEMPLO_5, 5.0), (F16, 30.0), (EXEMPLO_4, 50.0), (EXEMPLO_2, 21.0), (EXEMPLO_3, 60.0), (EXEMPLO_5, 65.0), (F16, 15.0), (EXEMPLO_4, 41.0),
          (EXEMPLO_2, 54.55), (EXEMPLO_3, 67.0), (EXEMPLO_5, 25.0), (F16, 25.0)]
sd = A / 'stills'
shutil.rmtree(sd, ignore_errors=True); sd.mkdir(parents=True)
for i, (src, t) in enumerate(STILLS):
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(src), '-frames:v', '1', '-vf', 'scale=288:512:flags=lanczos,format=yuvj420p', '-q:v', '3', str(sd / f'{i:02d}.jpg')])
rep['stills'] = [(s.name, t) for s, t in STILLS]

# 3) Convidado (cartão do depoimento) — quadro de baixo da live do Instagram, só os trechos dele no EDL
LOOK = 'hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.55:5:5:0,'
jparts = [(IG, s['in'], s['frames'] / FPS, 'crop=420:370:6:394,') for s in edl['segments'] if s['speaker'] == 'convidado']
for i, p in enumerate(jparts):
    jparts[i] = (p[0], p[1], p[2], p[3] + LOOK)
nj = seq('convidado', jparts, '640:564', q=2)
rep['convidado']['expected'] = sum(s['frames'] for s in edl['segments'] if s['speaker'] == 'convidado')

# 4) PiP do Apresentador (vídeo HTML): cada trecho com o número exato de quadros; Convidado não aparece no PiP (cartão próprio)
CROPS = {'yt': 'crop=270:270:1532:806', 'ig': 'crop=360:360:36:8'}
SRCF = {'yt': YT, 'ig': IG}
lst = []
for i, s in enumerate(edl['segments']):
    n = s['frames']
    p = TMP / f'pip{i:02d}.mp4'
    run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f"{s['in']:.4f}", '-i', str(SRCF[s['src']]), '-t', f'{n / FPS + 0.2:.4f}', '-an',
         '-vf', f"{CROPS[s['src']]},scale=360:360:flags=lanczos,hqdn3d=1:1:2:2,unsharp=5:5:0.4:5:5:0,fps=30,setsar=1,format=yuv420p", '-frames:v', str(n),
         '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
    lst.append(f"file '{p}'")
(TMP / 'pip.txt').write_text('\n'.join(lst) + '\n')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / 'pip.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
     '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(A / 'pip.mp4')])

# 5) fontes, three.js, gsap, granulação
F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2', 'inter-800-latin.woff2',
          'inter-800-latin-ext.woff2', 'inter-700-latin-ext.woff2', 'inter-600-latin-ext.woff2', 'inter-OFL.txt', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); (dst / 'addons/loaders').mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for dd in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / dd, dst / 'addons' / dd)
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'grain.png')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) and 'frames' in v else len(v)) for k, v in rep.items()}), 'convidado expected', rep['convidado']['expected'])
