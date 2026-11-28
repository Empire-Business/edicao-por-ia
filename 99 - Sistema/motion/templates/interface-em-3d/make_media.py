#!/usr/bin/env python3
"""EXEMPLO_1 — mídia da composição "Modelo pronto, um clique" (F22 + ID05 Roxo).
1) PiP do Apresentador: webcam da live do YouTube (canto inferior direito da tela compartilhada; recorte quadrado no rosto, nunca a barra
   lateral nem o aviso de limite), cada trecho do EDL com o número exato de quadros.
2) Prova — só entregas do próprio usuário feitas pelo Cortez, cada uma no formato que ela realmente usou:
   F16 → EXEMPLO_2 V2 (OFERTA, F16 + ID07: é o vídeo editado na própria live com o pedido F16 + ID07 Laranja);
   "só a gravação" → base de câmera do EXEMPLO_2 (jobs/video-18157f4a38d1/renders/base-v2.mp4, mesmo relógio do EXEMPLO_2, sem legenda/gráfico);
   F10 → EXEMPLO_3 V2; F22 → EXEMPLO_4 V1; F07 → motion vertical do PRODUTO PRODUTO; F08 → EXEMPLO_5 (criativo Namoral 01); F18 → LONGO_1 (vídeo longo do Apresentador,
   recorte vertical central num trecho com o próprio Apresentador). Nenhum material de terceiros: os exemplos da galeria (referências externas)
   NÃO são usados — os cartões são recriados no visual da galeria com essas entregas.
3) Interface real do painel público (https://cortez.highticketai.com.br, produto do próprio usuário), capturada com playwright em
   tmp/gal (src/capture_gallery.py): título da página de modelos, botões das IDs, prévia "Clareza em cada cena" em cada ID, botão
   "Copiar pedido de edição" e o aviso "Copiado." — só elementos de interface, sem os vídeos de referência.
Saídas em comp/assets/. Run: ../../../.venv/bin/python src/make_media.py
"""
import json, shutil, subprocess
from pathlib import Path
from PIL import Image

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
V = WS / '<PREENCHER: fonte ou prova própria>'
YT = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = V / '<PREENCHER: fonte ou prova própria>'
BASE = J.parent / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_3 = V / 'EXEMPLO_3 - Cortes das lives do Cortez/EXEMPLO_3 V2 - Corte 1 Editor caro (prévia para aprovação).mp4'
EXEMPLO_4 = V / 'EXEMPLO_3 - Cortes das lives do Cortez/EXEMPLO_4 V1 - Corte 2 Nao e possivel que exista (previa).mp4'
GT3V = V / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_5 = V / '<PREENCHER: fonte ou prova própria>'
LONGO_1 = V / '<PREENCHER: fonte ou prova própria>'
GAL = J / 'tmp/gal'
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


# 2) sequências de quadros (texturas determinísticas do three.js)
def seq(name, src, ss, n, vf, fps=30):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', str(src), '-frames:v', str(n), '-vf', f'fps={fps},{vf}', '-q:v', '3', str(d / '%04d.jpg')])
    k = len(list(d.glob('*.jpg')))
    for i, f in enumerate(sorted(d.glob('*.jpg'))):
        f.rename(d / f'{i:04d}.jpg')
    return {'src': src.name, 'ss': ss, 'frames': k, 'fps': fps}


H9 = 'scale=540:960:flags=lanczos'
C9 = 'scale=360:640:flags=lanczos'
rep = {}
rep['h_raw'] = seq('h_raw', BASE, 12.0, 195, H9)           # "só a gravação" (base de câmera do EXEMPLO_2, mesmo relógio)
rep['h_ed'] = seq('h_ed', EXEMPLO_2, 12.0, 195, H9)             # o mesmo instante editado pelo Cortez (apresentador → B-roll do escritório)
rep['h_fin'] = seq('h_fin', EXEMPLO_2, 22.3, 135, H9)           # final: o vídeo desse pedido (apresentador + B-roll do relógio)
rep['c_f16'] = seq('c_f16', EXEMPLO_2, 33.0, 60, C9, 15)
rep['c_f10'] = seq('c_f10', EXEMPLO_3, 16.5, 60, C9, 15)
rep['c_f22'] = seq('c_f22', EXEMPLO_4, 18.0, 60, C9, 15)
rep['c_f07'] = seq('c_f07', GT3V, 1.0, 60, C9, 15)
rep['c_f08'] = seq('c_f08', EXEMPLO_5, 45.5, 60, C9, 15)
rep['c_f18'] = seq('c_f18', LONGO_1, 270.0, 60, 'crop=608:1080:656:0,' + C9, 15)

# 3) interface real do painel (recortes das capturas)
U = A / 'ui'
shutil.rmtree(U, ignore_errors=True); U.mkdir(parents=True)
im = Image.open(GAL / 'modelos.png')                      # 2560×1800 (2×): título da página de modelos, sem os cartões
im.crop((128, 236, 1900, 560)).save(U / 'header.png')
im = Image.open(GAL / 'after_copy2.png')                  # 3840×2700 (3×): só o aviso "Copiado."
im.crop((1372, 2452, 2468, 2636)).save(U / 'toast.png')
shutil.copyfile(GAL / 'copy_btn.png', U / 'copy_btn.png')
for f in GAL.glob('idbtn_*.png'):
    shutil.copyfile(f, U / f.name)
shutil.copyfile(GAL / 'id07_sel.png', U / 'idbtn_Laranja_sel.png')
for f in GAL.glob('prev_*.png'):
    shutil.copyfile(f, U / f.name)
rep['ui'] = sorted(p.name for p in U.iterdir())
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
print(json.dumps({k: (v['frames'] if isinstance(v, dict) else len(v)) for k, v in rep.items()}))
