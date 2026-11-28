#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição ("linha de acabamento" 3D).
Prova: só material do próprio usuário — a gravação bruta real do EXEMPLO_2 (01 - Enviar vídeos/OFERTA/<gravacao-bruta>.mp4, iPhone HLG
→ BT.709 pelo mesmo caminho do EXEMPLO_2: VideoToolbox scale_vt + curva leve) e a entrega EXEMPLO_2 V2 editada pelo Cortez.
- Blocos reais da gravação (0–35,48 s): copiados de jobs/cortez-live-c5/analysis/tape.json (fala mantida, erro, hesitação, silêncio —
  medidos no job EXEMPLO_3 a partir da transcrição e do envelope reais) + envelope bruto × limpo (0,1 s).
- raw/NN.jpg: quadro do meio de cada bloco com fala (bruto, sem cortes); seq/hook: bruto 1,04–2,86 s (o tropeço do gancho, em sincronia).
- fin/NN.jpg: quadros da entrega EXEMPLO_2 correspondentes a cada trecho mantido (com legenda e animação do Cortez).
- broll/*.jpg: as cenas que o Cortez achou para o EXEMPLO_2 (agenda, reunião, escritório vazio, call center), recortadas sem a legenda queimada.
- seq/e117: EXEMPLO_2 0–6,6 s (720x1280) para o vídeo pronto no fim.
- fontes ID07 (Inter, IBM Plex Mono), three.js r186 + addons, GSAP e grão copiados do EXEMPLO_4.
Run: ../../../.venv/bin/python src/make_assets.py
"""
import json, shutil, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
RAW = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'
C8 = J.parent / '<PREENCHER: fonte ou prova própria>'
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"      # = visual/grade-v2.txt do EXEMPLO_2
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE
HW = ['-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld']


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, a)], check=True)


rep = {}
# 1) blocos reais (0–35,48 s da gravação)
tape = json.loads((J.parent / '<PREENCHER: fonte ou prova própria>').read_text())
blocks = [b for b in tape['blocks'] if b['e'] <= 35.5]
wave_raw = tape['wave_raw'][:356]; wave_clean = tape['wave_clean'][:356]
(J / 'analysis/raw_blocks.json').write_text(json.dumps({'source': '<PREENCHER: fonte ou prova própria>', 'blocks': blocks,
    'wave_raw': wave_raw, 'wave_clean': wave_clean, 'stats_full_take': tape['stats']}, ensure_ascii=False, indent=1))
# 2) quadros brutos (meio de cada bloco com fala)
d = A / 'raw'; shutil.rmtree(d, ignore_errors=True); d.mkdir()
for i, b in enumerate(blocks):
    if b['k'] == 'sil':
        continue
    t = (b['s'] + b['e']) / 2
    ff(*HW, '-ss', f'{t:.3f}', '-i', RAW, '-frames:v', 1, '-vf', f'{HDR},scale=360:640:flags=lanczos,format=yuvj420p', '-q:v', 3, d / f'{i:02d}.jpg')
# 3) sequência do gancho (o tropeço), 30 fps
d = A / 'seq/hook'; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
ff(*HW, '-ss', '1.04', '-i', RAW, '-t', '1.82', '-vf', f'{HDR},fps=30,scale=360:640:flags=lanczos,format=yuvj420p', '-q:v', 3, '-start_number', 0, d / '%04d.jpg')
rep['hook'] = len(list(d.glob('*.jpg')))
# 4) quadros da entrega (um por trecho mantido) — índice do bloco → tempo no EXEMPLO_2
FIN = {4: 2.4, 12: 5.75, 13: 9.4, 14: 11.0, 15: 11.55, 16: 13.25, 17: 14.3}
d = A / 'fin'; shutil.rmtree(d, ignore_errors=True); d.mkdir()
for i, t in FIN.items():
    ff('-ss', t, '-i', EXEMPLO_2, '-frames:v', 1, '-vf', 'scale=360:640:flags=lanczos', '-q:v', 3, d / f'{i:02d}.jpg')
rep['fin'] = FIN
# 5) cenas (sem legenda queimada)
BR = {'agenda': (0.45, 'crop=1080:700:0:0'), 'reuniao': (6.6, 'crop=900:400:90:712'), 'escritorio': (15.6, 'crop=1080:700:0:0'),
      'callcenter': (17.6, 'crop=1080:1060:0:20')}
d = A / 'broll'; shutil.rmtree(d, ignore_errors=True); d.mkdir()
for n, (t, cr) in BR.items():
    ff('-ss', t, '-i', EXEMPLO_2, '-frames:v', 1, '-vf', f'{cr},scale=640:-2:flags=lanczos', '-q:v', 3, d / f'{n}.jpg')
rep['broll'] = BR
# 6) o vídeo pronto: EXEMPLO_2 0–4,55 s (agenda + apresentador: a frase do tropeço, agora limpa) e 6,45–8,45 s (cena da reunião),
#    pulando o gráfico branco do contador (4,6–6,4 s), que no cartão pequeno parece um quadro vazio
d = A / 'seq/e117'; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
k = 0
for ss, du in [(0, 4.55), (6.45, 2.0)]:
    tmp = J / 'tmp/e117part'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    ff('-ss', ss, '-i', EXEMPLO_2, '-t', du, '-vf', 'fps=30,scale=720:1280:flags=lanczos', '-q:v', 3, '-start_number', 0, tmp / '%04d.jpg')
    for f in sorted(tmp.glob('*.jpg')):
        f.rename(d / f'{k:04d}.jpg'); k += 1
    shutil.rmtree(tmp)
rep['e117'] = k
# 7) fontes, three, gsap, grão (do EXEMPLO_4, mesma ID07)
for f in ['inter-400-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-500-latin.woff2', 'inter-600-latin.woff2', 'inter-700-latin.woff2', 'inter-800-latin.woff2',
          'inter-OFL.txt', 'ibm-plex-mono-400-latin.woff2', 'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt', 'gsap.min.js', 'grain.png']:
    shutil.copyfile(C8 / f, A / f)
shutil.rmtree(A / 'three', ignore_errors=True); shutil.copytree(C8 / 'three', A / 'three')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
