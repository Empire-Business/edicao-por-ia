#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição (lente 3D + pesquisa de cenas).
Prova: só entregas do próprio usuário feitas pelo Cortez (02 - Ver vídeos): EXEMPLO_2 V2 (OFERTA, cenas pesquisadas pelo Cortez no
TikTok via ScrapeCreators — escritório vazio, call center vazio, agenda), EXEMPLO_3/EXEMPLO_4/EXEMPLO_5 (criativos Namoral). Quadros escolhidos na folha de
contato: sem a marca "PRODUTO AI", sem cenas de filme/série (Feitiço do Tempo, Gotham) e sem conteúdo de terceiros.
- stills/NN.jpg (540x960): conteúdo "real" dos cartões do feed (aparece pela lente e quando o cartão vira).
- seq/hero (EXEMPLO_2 12,2–14,7 s, 540x960): o cartão revelado no "Aqui não".
- seq/r1 r2 r3 (480x270): resultados da "pesquisa de cenas" — recortes 16:9 das cenas usadas no EXEMPLO_2 (sem a legenda queimada).
- seq/card (EXEMPLO_2 15,45–16,95 s, 540x960): o vídeo que recebe a cena escolhida; e117_full.mp4 (1080x1920): continuação em tela cheia.
- apresentador_pip.mp4: Apresentador (live do Instagram) recortado em quadrado para o círculo, alinhado ao EDL (trechos do YouTube = quadro parado, oculto).
- fontes da ID07 (Inter, IBM Plex Mono), three.js r186 (+ addons) e GSAP copiados do EXEMPLO_6.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
V = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / '<PREENCHER: fonte ou prova própria>'
IG = WS / '<PREENCHER: fonte ou prova própria>'
TMP = J / 'tmp/assets'
TMP.mkdir(parents=True, exist_ok=True)


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, a)], check=True)


rep = {}
# 1) stills dos cartões
STILLS = [(EXEMPLO_2, 5.6), (EXEMPLO_2, 9.8), (EXEMPLO_2, 16.0), (EXEMPLO_2, 17.6), (EXEMPLO_2, 20.8), (EXEMPLO_2, 30.8), (EXEMPLO_2, 36.8), (EXEMPLO_2, 50.6), (EXEMPLO_2, 57.8),
          (EXEMPLO_3, 16.5), (EXEMPLO_3, 32.5), (EXEMPLO_3, 46.5), (EXEMPLO_3, 66.5), (EXEMPLO_4, 2.5), (EXEMPLO_4, 18.5), (EXEMPLO_4, 22.5), (EXEMPLO_5, 2.5), (EXEMPLO_5, 14.5), (EXEMPLO_5, 22.5)]
d = A / 'stills'
shutil.rmtree(d, ignore_errors=True); d.mkdir()
for i, (src, t) in enumerate(STILLS):
    ff('-ss', t, '-i', src, '-frames:v', 1, '-vf', 'scale=540:960:flags=lanczos', '-q:v', 3, d / f'{i:02d}.jpg')
rep['stills'] = [(s.name, t) for s, t in STILLS]

# 2) sequências (um JPG por quadro de 30 fps)
SEQ = {'hero': (EXEMPLO_2, 12.2, 2.5, 'scale=540:960:flags=lanczos'),
       'r1': (EXEMPLO_2, 15.45, 1.5, 'crop=1080:608:0:60,scale=480:270:flags=lanczos'),
       'r2': (EXEMPLO_2, 17.25, 1.4, 'crop=1080:608:0:330,scale=480:270:flags=lanczos'),
       'r3': (EXEMPLO_2, 0.05, 1.5, 'crop=1080:608:0:20,scale=480:270:flags=lanczos'),
       'card': (EXEMPLO_2, 15.45, 1.5, 'scale=540:960:flags=lanczos')}
for name, (src, ss, dur, vf) in SEQ.items():
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    ff('-ss', ss, '-i', src, '-t', dur, '-vf', f'fps=30,{vf}', '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
    rep[name] = {'src': src.name, 'ss': ss, 'frames': len(list(d.glob('*.jpg')))}

# 3) continuação em tela cheia (HTML <video>), quadros-chave densos. V1 revisada (direção): o fechamento não pode cair no gráfico
#    branco do EXEMPLO_2 (19 s em diante: grade "SEM 01…09" quase vazia e legenda queimada brigando com a nossa). Então:
#    A = EXEMPLO_2 16,95–18,817 s (continua o escritório e o call center vazio, até o último quadro antes do branco em 18,833 s);
#    B = EXEMPLO_2 0,00–2,10 s (abertura do EXEMPLO_2: agenda rosa sendo preenchida + apresentador; legenda dele no meio, longe da nossa no topo);
#    + 0,5 s do último quadro parado (fica sob a cortina do CTA).
CUTS = [(16.95, 56), (0.0, 63)]
parts = []
for k, (ss, n) in enumerate(CUTS):
    pp = TMP / f'full{k}.mp4'
    ff('-ss', ss, '-i', EXEMPLO_2, '-an', '-vf', 'fps=30,format=yuv420p', '-frames:v', n, '-c:v', 'libx264', '-crf', 12, '-g', 15, pp)
    parts.append(f"file '{pp}'")
(TMP / 'full.txt').write_text('\n'.join(parts) + '\n')
ff('-f', 'concat', '-safe', 0, '-i', TMP / 'full.txt', '-vf', 'tpad=stop_mode=clone:stop_duration=0.5,format=yuv420p', '-c:v', 'libx264', '-crf', 14,
   '-preset', 'medium', '-g', 15, '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', A / 'e117_full.mp4')
rep['e117_full'] = {'segments_e117_s': [(ss, round(ss + n / 30, 3)) for ss, n in CUTS], 'hold_s': 0.5}

# 4) Apresentador (live do Instagram) para o círculo: cada segmento do EDL com o número exato de quadros
edl = json.loads((J / 'edit/edl.json').read_text())
LOOK = 'crop=356:356:18:10,scale=440:440:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.5:5:5:0,fps=30,setsar=1,format=yuv420p'
lst, last = [], None
for i, s in enumerate(edl['segments']):
    n = s['frames']; p = TMP / f'pip{i:02d}.mp4'
    if s['src'] == 'ig':
        ff('-ss', f"{s['in']:.4f}", '-i', IG, '-t', f'{n / 30 + 0.2:.4f}', '-an', '-vf', LOOK, '-frames:v', n, '-c:v', 'libx264', '-crf', 12, '-g', 15, p)
        last = s
    else:   # trecho do YouTube: o círculo fica oculto; quadro parado só para manter o relógio
        ref = last or next(x for x in edl['segments'] if x['src'] == 'ig')
        ff('-ss', f"{ref['in']:.4f}", '-i', IG, '-an', '-vf', f'{LOOK},trim=end_frame=1,tpad=stop_mode=clone:stop_duration={n / 30 + 0.1:.4f}',
           '-frames:v', n, '-c:v', 'libx264', '-crf', 12, '-g', 15, p)
    lst.append(f"file '{p}'")
(TMP / 'pip.txt').write_text('\n'.join(lst) + '\n')
ff('-f', 'concat', '-safe', 0, '-i', TMP / 'pip.txt', '-vf', 'tpad=stop_mode=clone:stop_duration=1', '-c:v', 'libx264', '-crf', 12, '-g', 15,
   '-pix_fmt', 'yuv420p', A / 'apresentador_pip.mp4')
nf = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0',
                     str(A / 'apresentador_pip.mp4')], capture_output=True, text=True).stdout.strip()
rep['apresentador_pip_frames'] = int(nf); rep['edl_frames'] = sum(s['frames'] for s in edl['segments'])

# 5) fontes da ID07, three.js r186 e GSAP
F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-500-latin.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2',
          'inter-800-latin.woff2', 'inter-OFL.txt', 'ibm-plex-mono-400-latin.woff2', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
C2 = J.parent / '<PREENCHER: fonte ou prova própria>'
shutil.rmtree(A / 'three', ignore_errors=True)
shutil.copytree(C2 / 'three', A / 'three')
shutil.copyfile(C2 / 'gsap.min.js', A / 'gsap.min.js')
rep['seq'] = {k: len(list((A / 'seq' / k).glob('*.jpg'))) for k in SEQ}
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
print(json.dumps({k: rep[k] for k in ('seq', 'apresentador_pip_frames', 'edl_frames')}))
