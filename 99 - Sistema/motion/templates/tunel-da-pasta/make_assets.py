#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição ("dentro da pasta": a pasta 01, o túnel de dentro da máquina e a pasta 02).
Prova: só material do próprio usuário — a gravação bruta real do EXEMPLO_2 (01 - Enviar vídeos/OFERTA/<gravacao-bruta>.mp4, iPhone HLG
→ BT.709 pelo mesmo caminho do EXEMPLO_2: VideoToolbox scale_vt + curva leve) e a entrega EXEMPLO_2 V2 editada pelo Cortez.
- seq/raw: bruto 0,90–9,90 s, 30 fps, 360x640 (o cartão "vídeo bruto" toca de verdade, cinza e granulado no shader).
- seq/e117: EXEMPLO_2 0–4,55 s + 6,45–8,45 s (720x1280), sem o gráfico branco do contador (mesma seleção do EXEMPLO_3).
- broll/*.jpg: cenas que o Cortez achou para o EXEMPLO_2 (agenda, reunião, escritório vazio, call center), sem a legenda queimada.
- analysis/raw_wave.json: envelope real bruto × limpo (0,1 s) do mesmo trecho (medido no EXEMPLO_4).
- fontes ID06 (Inter + IBM Plex Mono), three.js r186 + addons, GSAP e grão copiados do EXEMPLO_3.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
RAW = WS / '<PREENCHER: fonte ou prova própria>'
D2 = J.parent / '<PREENCHER: fonte ou prova própria>'
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"      # = visual/grade-v2.txt do EXEMPLO_2
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE
HW = ['-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld']
RAW0, RAWD = 0.90, 9.0


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, a)], check=True)


rep = {}
d = A / 'seq/raw'; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
ff(*HW, '-ss', RAW0, '-i', RAW, '-t', RAWD, '-vf', f'{HDR},fps=30,scale=360:640:flags=lanczos,format=yuvj420p', '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
rep['raw'] = len(list(d.glob('*.jpg')))
for sub in ['seq/e117', 'broll']:
    shutil.rmtree(A / sub, ignore_errors=True); shutil.copytree(D2 / 'comp/assets' / sub, A / sub)
rep['e117'] = len(list((A / 'seq/e117').glob('*.jpg'))); rep['broll'] = sorted(p.name for p in (A / 'broll').glob('*.jpg'))
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-500-latin.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2', 'inter-800-latin.woff2',
          'inter-OFL.txt', 'ibm-plex-mono-400-latin.woff2', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt', 'gsap.min.js', 'grain.png']:
    shutil.copyfile(D2 / 'comp/assets' / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True); shutil.copytree(D2 / 'comp/assets/three', A / 'three')
rb = json.loads((D2 / 'analysis/raw_blocks.json').read_text())
i0 = int(round(RAW0 * 10)); n = int(RAWD * 10)
(J / 'analysis/raw_wave.json').write_text(json.dumps({'source': '<PREENCHER: fonte ou prova própria>', 'raw_from_s': RAW0,
    'wave_raw': rb['wave_raw'][i0:i0 + n], 'wave_clean': rb['wave_clean'][i0:i0 + n],
    'blocks': [b for b in rb['blocks'] if b['e'] > RAW0 and b['s'] < RAW0 + RAWD]}, ensure_ascii=False, indent=1))
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
