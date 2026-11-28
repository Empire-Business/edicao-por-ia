#!/usr/bin/env python3
"""EXEMPLO_1 — mídia da composição ("o arquivo do Cortez").
1) PiP do Apresentador: webcam da live do YouTube (canto inferior direito da tela compartilhada; recorte quadrado no rosto, nunca a barra
   lateral, o aviso de limite nem o vídeo de terceiro que estava na tela), cada trecho do EDL com o número exato de quadros.
2) Prova — só entregas do próprio usuário editadas pelo Cortez (02 - Ver vídeos), conferidas quadro a quadro:
   - notícias: prints reais de matérias pesquisadas que aparecem no vídeo longo LONGO_1 (recorte sem a etiqueta da fonte no rodapé);
   - prints: telas reais dos produtos do próprio usuário nos criativos EXEMPLO_2 (CRM, conversa de WhatsApp, jornada dos clientes);
   - cenas: as cenas pesquisadas na internet que o Cortez usou no EXEMPLO_3 (agenda, escritório vazio, call center), sem a legenda queimada;
     os trechos do EXEMPLO_3 com cena de filme (6–9 s e 22–25 s) ficam de fora;
   - "repara": EXEMPLO_4 (CRM e conversa com IA, apresentador), entrega inteira 9:16;
   - resultados: 16 entregas 9:16 (EXEMPLO_4, EXEMPLO_2, EXEMPLO_3 e motions institucionais).
Saídas em comp/assets/ e analysis/proof_assets.json. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
V = WS / '<PREENCHER: fonte ou prova própria>'
YT = WS / '<PREENCHER: fonte ou prova própria>'
LONGO_1 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_4 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / '<PREENCHER: fonte ou prova própria>'
M = V / '<PREENCHER: fonte ou prova própria>'
E81V = M / '07 - PRODUTO/E81_produto-lp_9x16_F07_ID05_V2.mp4'
GT3V = M / '<PREENCHER: fonte ou prova própria>'
SDRV = M / '<PREENCHER: fonte ou prova própria>'
TYPEV = M / '<PREENCHER: fonte ou prova própria>'
CLIV = M / '<PREENCHER: fonte ou prova própria>'
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
PIP = 'crop=232:232:1599:773,scale=320:320:flags=lanczos,hqdn3d=1.2:1.2:3:3,unsharp=5:5:0.5:5:5:0,fps=30,setsar=1,format=yuv420p'
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
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    if len(fs) != n:
        raise SystemExit(f'{name}: {len(fs)} quadros != {n}')
    return {'src': str(src.relative_to(WS)), 'ss': ss, 'frames': n, 'fps': fps, 'vf': vf}


NOTAG = 'crop=1920:944:0:0,'                    # tira a etiqueta da fonte no rodapé dos prints do LONGO_1
UI = 'crop=960:1020:60:120,scale=600:638:flags=lanczos'
rep = {}
# gancho: matéria real com o grifo animado (LONGO_1), 16:9 sem a etiqueta
rep['h_hook'] = seq('h_hook', LONGO_1, 472.3, 120, NOTAG + 'scale=960:472:flags=lanczos')
# notícias (15 qps, 2 s)
rep['n1'] = seq('n1', LONGO_1, 92.4, 30, NOTAG + 'scale=640:315:flags=lanczos', 15)
rep['n2'] = seq('n2', LONGO_1, 476.6, 30, NOTAG + 'scale=640:315:flags=lanczos', 15)
rep['n3'] = seq('n3', LONGO_1, 208.6, 30, NOTAG + 'scale=640:315:flags=lanczos', 15)
# prints reais (telas dos produtos do usuário no EXEMPLO_2)
rep['p1'] = seq('p1', EXEMPLO_2, 47.4, 30, UI, 15)
rep['p2'] = seq('p2', EXEMPLO_2, 51.6, 30, 'crop=960:1110:60:150,scale=600:694:flags=lanczos', 15)
rep['p3'] = seq('p3', EXEMPLO_2, 59.6, 30, UI, 15)
# cenas pesquisadas pelo Cortez para o EXEMPLO_3 (sem a legenda queimada)
rep['s1'] = seq('s1', EXEMPLO_3, 0.05, 30, 'crop=1080:608:0:20,scale=480:270:flags=lanczos', 15)
rep['s2'] = seq('s2', EXEMPLO_3, 15.45, 22, 'crop=1080:608:0:60,scale=480:270:flags=lanczos', 15)
rep['s3'] = seq('s3', EXEMPLO_3, 17.25, 21, 'crop=1080:608:0:330,scale=480:270:flags=lanczos', 15)
# entregas inteiras 9:16 (30 qps)
rep['r_e91'] = seq('r_e91', EXEMPLO_4, 34.8, 240, 'scale=540:960:flags=lanczos')
rep['e117'] = seq('e117', EXEMPLO_3, 15.0, 114, 'scale=540:960:flags=lanczos')
# resultados (15 qps, 2 s, 216x384)
T = 'scale=216:384:flags=lanczos'
RES = [('t01', EXEMPLO_4, 24.0), ('t02', EXEMPLO_2, 6.5), ('t03', EXEMPLO_3, 3.0), ('t04', E81V, 51.6), ('t05', EXEMPLO_2, 13.5), ('t06', EXEMPLO_3, 28.0),
       ('t07', GT3V, 65.0), ('t08', EXEMPLO_4, 63.0), ('t09', EXEMPLO_2, 72.0), ('t10', SDRV, 53.5), ('t11', EXEMPLO_3, 42.0), ('t12', TYPEV, 48.2),
       ('t13', EXEMPLO_4, 9.0), ('t14', CLIV, 7.6), ('t15', EXEMPLO_3, 56.0), ('t16', EXEMPLO_2, 33.0)]
for name, src, ss in RES:
    rep[name] = seq(name, src, ss, 30, T, 15)
rep['apresentador_pip_frames'] = frames(A / 'apresentador_pip.mp4')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) else v) for k, v in rep.items()}))
