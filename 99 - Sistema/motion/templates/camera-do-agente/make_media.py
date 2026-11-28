#!/usr/bin/env python3
"""EXEMPLO_1 — mídia da composição.
1) PiP do Apresentador: webcam da live do YouTube (canto inferior direito da tela compartilhada; recorte quadrado no rosto, nunca a barra
   lateral nem o aviso de limite), cada trecho do EDL com o número exato de quadros.
2) Prova — só os motions institucionais do próprio usuário feitos pelo Cortez ("<PREENCHER: fonte ou prova própria>"), conferidos
   quadro a quadro (telas dos produtos do próprio usuário com dados de demonstração; nenhum trecho com pessoas nem material de terceiros):
   painéis da constelação (sequências curtas a 15 qps, 360×203), heróis 16:9 (960 px) e motions verticais 9:16 (324×576 a 15 qps).
   Os nomes de produto que aparecem (PRODUTO, PRODUTO) são o assunto real da fala, não assinatura adicionada.
Saídas em comp/assets/. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
YT = WS / '<PREENCHER: fonte ou prova própria>'
M = WS / '<PREENCHER: fonte ou prova própria>'
E81H = M / '07 - PRODUTO/E81_produto-lp_16x9_F07_ID05_V2.mp4'
E81V = M / '07 - PRODUTO/E81_produto-lp_9x16_F07_ID05_V2.mp4'
GT3H = M / '<PREENCHER: fonte ou prova própria>'
GT3V = M / '<PREENCHER: fonte ou prova própria>'
SELLV = M / '<PREENCHER: fonte ou prova própria>'
SDRH = M / '<PREENCHER: fonte ou prova própria>'
SDRV = M / '<PREENCHER: fonte ou prova própria>'
TYPEH = M / '<PREENCHER: fonte ou prova própria>'
TYPEV = M / '<PREENCHER: fonte ou prova própria>'
CLIH = M / '<PREENCHER: fonte ou prova própria>'
CLIV = M / '<PREENCHER: fonte ou prova própria>'
DESKH = M / '08 - PRODUTO Desk tutoriais/E82_desk-tutorial-01-primeiro-acesso_16x9_F07_ID06_V2.mp4'
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


# 1) PiP do Apresentador
PIP = 'crop=232:232:1599:773,scale=320:320:flags=lanczos,hqdn3d=1.2:1.2:3:3,unsharp=5:5:0.5:5:5:0,eq=saturation=1.0,fps=30,setsar=1,format=yuv420p'
lst = []
for i, s in enumerate(edl['segments']):
    p = TMP / f'pip{i:02d}.mp4'
    run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f"{s['in']:.4f}", '-i', str(YT), '-t', f"{s['frames'] / FPS + 0.2:.4f}", '-an', '-vf', PIP,
         '-frames:v', str(s['frames']), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
    if frames(p) != s['frames']:
        raise SystemExit(f'pip seg {i}: quadros {frames(p)} != {s["frames"]}')
    lst.append(f"file '{p}'")
(TMP / 'pip.txt').write_text('\n'.join(lst) + '\n')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / 'pip.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
     '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(A / 'apresentador_pip.mp4')])


def seq(name, src, ss, n, vf, fps=30):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', str(src), '-frames:v', str(n), '-vf', f'fps={fps},{vf}', '-q:v', '3', str(d / '%04d.jpg')])
    for k, f in enumerate(sorted(d.glob('*.jpg'))):
        f.rename(d / f'{k:04d}.jpg')
    return {'src': str(src.relative_to(WS)), 'ss': ss, 'frames': n, 'fps': fps}


P = 'scale=360:203:flags=lanczos'
H = 'scale=960:540:flags=lanczos'
V = 'scale=324:576:flags=lanczos'
rep = {}
# constelação (15 qps, 4 s)
for name, src, ss in [('c_dash', E81H, 6.0), ('c_orac', E81H, 14.6), ('c_type', E81H, 21.4), ('c_wa', E81H, 25.6), ('c_funil', E81H, 33.0),
                      ('c_gt3p', GT3H, 69.2), ('c_gt3t', GT3H, 21.0), ('c_desk', DESKH, 24.5), ('c_cli', CLIH, 29.5), ('c_sdr', SDRH, 106.8),
                      ('c_type2', TYPEH, 44.3)]:
    rep[name] = seq(name, src, ss, 60, P, 15)
# heróis 16:9 (30 qps)
rep['h_hook'] = seq('h_hook', E81H, 51.0, 105, H)                       # colagem 3D dos módulos (motion pronto)
rep['h_mods'] = seq('h_mods', E81H, 17.1, 66, H)                       # "Plataformas PRODUTO" dentro do PRODUTO
rep['h_ui'] = seq('h_ui', GT3H, 13.4, 108, 'crop=1920:844:0:236,scale=960:422:flags=lanczos')   # a plataforma (só a interface, sem o título do motion)
rep['h_fin'] = seq('h_fin', GT3H, 13.4, 132, H)                         # o mesmo instante do motion pronto (com título animado)
rep['h_in'] = seq('h_in', E81H, 41.3, 96, H)                           # o trecho do PRODUTO dentro do vídeo do PRODUTO
# verticais 9:16 (15 qps, 4 s)
# janelas inteiras dentro de uma única cena de cada motion (sem transição no meio do laço), conferidas em folhas de 2 qps
for name, src, ss, n in [('v_gt3', GT3V, 65.0, 45), ('v_sdr', SDRV, 53.5, 38), ('v_type', TYPEV, 48.2, 42), ('v_cli', CLIV, 7.6, 54),
                         ('v_site', E81V, 51.6, 66)]:
    rep[name] = seq(name, src, ss, n, V, 15)
rep['apresentador_pip_frames'] = frames(A / 'apresentador_pip.mp4')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) else v) for k, v in rep.items()}))
