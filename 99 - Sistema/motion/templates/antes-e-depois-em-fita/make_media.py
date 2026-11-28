#!/usr/bin/env python3
"""EXEMPLO_1 — materiais da composição (tudo derivado de originais imutáveis; só material próprio do usuário, sem logotipos).
1) PiP do Apresentador: webcam da live do YouTube recortada (só a câmera, nunca a barra lateral nem avisos da tela), um trecho por segmento
   do EDL com o número exato de quadros; nos segmentos sem o Apresentador o PiP fica escondido (quadro do próximo trecho dele).
2) Sequências de quadros (texturas three.js, um JPG por quadro, índice = tempo):
   antes = gravação bruta do EXEMPLO_2 (HDR do iPhone → BT.709 pelo VideoToolbox + a mesma curva/saturação da V2 do EXEMPLO_2);
   depA/depB = a entrega EXEMPLO_2 V2 nos trechos do EDL; m1/m3/m4 = cenas animadas da própria entrega (calendário, "Publicar todo dia",
   "Oferta clara"), sem banco de imagens nem pessoas de terceiros.
3) Miniaturas de cada ilha de fala da gravação bruta (para a fita 3D) e o envelope de áudio real (bruto × limpo) a cada 0,1 s.
4) Fontes da ID03 (Inter + IBM Plex Mono), three.js r186 (ESM) + addons, GSAP, grão.
Run: ../../../.venv/bin/python src/make_media.py
"""
import json, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
WS = SYS.parent
A = J / 'comp/assets'
A.mkdir(parents=True, exist_ok=True)
TMP = J / 'tmp/media'
TMP.mkdir(parents=True, exist_ok=True)
E117J = J.parent / '<PREENCHER: fonte ou prova própria>'
YT = WS / '<PREENCHER: fonte ou prova própria>'
RAW = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
GRADE = "curves=all='0/0 0.25/0.27 0.5/0.55 0.75/0.79 1/1',eq=saturation=1.04"      # = visual/grade-v2.txt do EXEMPLO_2
HDR = 'scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,hwdownload,format=p010le,format=rgb48le,' + GRADE


def run(a):
    subprocess.run(a, check=True)


def frames(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip())


# 1) PiP do Apresentador — a live muda de layout; recorte quadrado no rosto conforme o trecho (medido nos quadros reais):
#    "tela + câmera" (1279–1350 s e ≥ 1678,08 s): câmera no canto inferior direito; "vídeo bruto na tela" (1560–1668,78 s): câmera
#    dentro da tela compartilhada; "câmera cheia" (1668,78–1678,08 s). Nunca entra barra lateral, aviso de uso ou o vídeo bruto da tela.
LOOK = 'scale=400:400:flags=lanczos,hqdn3d=1.2:1.2:3:3,unsharp=5:5:0.5:5:5:0,fps=30,setsar=1,format=yuv420p'
def crop_at(t):
    if 1560 <= t < 1668.78:
        return 'crop=270:270:875:810'
    if 1668.78 <= t < 1678.08:
        return 'crop=640:640:660:60'
    if t >= 1678.08:
        return 'crop=240:240:1565:805'
    return 'crop=232:232:1574:773'
BOUNDS = [1668.78, 1678.08]
lst = []
ytsegs = [s for s in edl['segments'] if s['src'] == 'yt']
k = 0
for i, s in enumerate(edl['segments']):
    n = s['frames']
    src_in = s['in'] if s['src'] == 'yt' else next((y['in'] for y in ytsegs if y['start'] > s['start']), ytsegs[-1]['in'])
    cuts = [0] + [round((b - src_in) * FPS) for b in BOUNDS if s['src'] == 'yt' and 0 < round((b - src_in) * FPS) < n] + [n]
    for c0, c1 in zip(cuts, cuts[1:]):
        p = TMP / f'pip{k:03d}.mp4'; k += 1
        t0 = src_in + c0 / FPS
        run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-ss', f'{t0:.4f}', '-i', str(YT), '-t', f'{(c1 - c0) / FPS + 0.2:.4f}', '-an',
             '-vf', crop_at(t0 + 0.02) + ',' + LOOK, '-frames:v', str(c1 - c0), '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', str(p)])
        if frames(p) != c1 - c0:
            raise SystemExit(f'pip {i}: {frames(p)} != {c1 - c0}')
        lst.append(f"file '{p}'")
(TMP / 'pip.txt').write_text('\n'.join(lst) + '\n')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / 'pip.txt'), '-vf', 'tpad=stop_mode=clone:stop_duration=1',
     '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '15', '-pix_fmt', 'yuv420p', str(A / 'apresentador_pip.mp4')])
print('pip', frames(A / 'apresentador_pip.mp4'))


# 2) sequências de quadros
def seq(name, src, ss, n, size, hdr=False):
    d = A / 'seq' / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    if hdr:
        a = ['ffmpeg', '-v', 'error', '-y', '-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld', '-ss', f'{ss:.4f}', '-i', str(src),
             '-vf', f'{HDR},scale={size}:flags=lanczos,format=yuvj420p', '-frames:v', str(n), '-q:v', '3', str(d / '%04d.jpg')]
    else:
        a = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.4f}', '-i', str(src), '-vf', f'fps=30,scale={size}:flags=lanczos', '-frames:v', str(n),
             '-q:v', '3', str(d / '%04d.jpg')]
    run(a)
    fs = sorted(d.glob('*.jpg'))
    for k, f in enumerate(fs):
        f.rename(d / f'{k:04d}.jpg')
    return len(fs)


rep = {}
seg = {s['take']: s for s in edl['segments'] if s['src'] != 'yt'}
# V2: a tela do ANTES continua tocando a gravação bruta (sem som) enquanto o Apresentador comenta, até deitar na mesa (~6 s)
rep['antes'] = seq('antes', RAW, seg['a01']['in'], 186, '720:1280', hdr=True)
# DEPOIS: a mesma frase do ANTES, inteira, na entrega EXEMPLO_2 (apresentador na tela; no começo a entrega divide a tela com a agenda)
rep['depois'] = seq('depois', EXEMPLO_2, seg['d01']['in'], seg['d01']['frames'], '720:1280')
# cenas animadas da entrega para o leque do fechamento, em laço (sem banco de imagens, param antes de a entrega voltar ao apresentador)
for name, ss, n in (('m1', 10.30, 50), ('m3', 29.75, 48)):
    rep[name] = seq(name, EXEMPLO_2, ss, n, '540:960')
shutil.rmtree(A / 'seq' / 'depA', ignore_errors=True); shutil.rmtree(A / 'seq' / 'depB', ignore_errors=True); shutil.rmtree(A / 'seq' / 'm4', ignore_errors=True)

# 3) fita: ilhas de fala reais da gravação bruta (job EXEMPLO_2) × trechos mantidos na entrega
isl = json.loads((E117J / 'analysis/islands.json').read_text())['islands']
kept = [(s['in'], s['out']) for s in json.loads((E117J / 'edit/edl.json').read_text())['segments']]
ERR = {1.12: ('começo repetido', '“É assim.”'), 1.88: ('começo repetido', '“É assim que…”'),
       7.80: ('tomada repetida', '“Tem consultor com mais de 15 anos…”'), 18.61: ('frase interrompida', '“Tem consultor com 15 anos de mercado, que…”'),
       40.77: ('frase interrompida', '“Aí ele volta a postar…”'), 60.62: ('trecho repetido', '“falando com quem pode pagar o meu preço.”')}
TXT = {21.16: 'Tem consultor com 15 anos de mercado, que resolve um problema caro, entrega resultado…', 26.32: 'passa o ano entre mês cheio',
       42.32: 'Aí ele volta a postar por umas semanas, para em março, espera o telefone tocar.', 77.98: 'A Oferta Alto Valor do Acelerador de Audiência foi montada para essas duas coisas.',
       87.46: 'A oferta completa sai num grupo gratuito do WhatsApp na terça, 24/11, às 10h da manhã.', 71.85: 'clara, com preço, página e um caminho que leva quem me acompanha…',
       28.78: 'Ele fecha 4 clientes por indicação.', 75.85: 'até ela!', 100.14: 'que lá você vai receber a oferta.'}
blocks, t = [], 0.0
RAWDUR = 103.0
for x in isl:
    st, en = x['start'], x['end']
    if st - t >= 0.25:
        blocks.append({'s': round(t, 2), 'e': round(st, 2), 'k': 'sil', 'txt': f'silêncio · {st - t:.1f} s'.replace('.', ',')})
    ov = sum(max(0, min(b, en) - max(a, st)) for a, b in kept) / (en - st)
    key = round(st, 2)
    if key in ERR:
        k, txt = 'err', ERR[key][1]
    elif ov > 0.5:
        k, txt = 'keep', TXT.get(key, x['text'])
    else:
        k, txt = 'hes', 'hesitação'          # o texto dessas ilhas curtas é incerto ("E aí", ruído); não citamos
    b = {'s': round(st, 2), 'e': round(en, 2), 'k': k, 'txt': txt}
    if k == 'err':
        b['why'] = ERR[key][0]
    blocks.append(b)
    t = en
if RAWDUR - t >= 0.25:
    blocks.append({'s': round(t, 2), 'e': RAWDUR, 'k': 'sil', 'txt': f'silêncio · {RAWDUR - t:.1f} s'.replace('.', ',')})
# miniaturas (ilhas com ≥ 0,9 s)
th = A / 'thumb'
shutil.rmtree(th, ignore_errors=True); th.mkdir(parents=True)
for i, b in enumerate(blocks):
    if b['k'] in ('keep', 'err') and b['e'] - b['s'] >= 0.9:
        o = th / f'{i:03d}.jpg'
        run(['ffmpeg', '-v', 'error', '-y', '-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld', '-ss', f"{(b['s'] + b['e']) / 2:.3f}", '-i', str(RAW),
             '-vf', f'{HDR},scale=216:384:flags=lanczos,format=yuvj420p', '-frames:v', '1', '-q:v', '3', str(o)])
        b['thumb'] = f'assets/thumb/{i:03d}.jpg'


# envelope real (0,1 s): bruto (som original, com o ruído da sala) × limpo (voz tratada localmente no job EXEMPLO_2)
def env(p, off=0.0):
    sr, x = wavfile.read(p)
    x = x.astype(np.float32) / 32768
    x = x.mean(1) if x.ndim > 1 else x
    h = int(sr * 0.1); n = int(RAWDUR * 10)
    v = []
    for i in range(n):
        s = x[i * h:(i + 1) * h]
        v.append(float(20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9)) if len(s) else -90.0)
    return v


raw_db = env(J / 'tmp/audio/raw-bf.wav')
cln_db = env(E117J / 'tmp/source-clean-a18-declip.wav')
pk = np.percentile(raw_db, 97)
norm = lambda d: [round(float(np.clip((v - (pk - 50)) / 50, 0, 1)), 3) for v in d]     # 50 dB de faixa abaixo do pico típico
removed = sum(b['e'] - b['s'] for b in blocks if b['k'] != 'keep')
stats = {'raw_s': RAWDUR, 'delivery_s': 63.38, 'errors': sum(1 for b in blocks if b['k'] == 'err'),
         'silences': sum(1 for b in blocks if b['k'] == 'sil'), 'silence_s': round(sum(b['e'] - b['s'] for b in blocks if b['k'] == 'sil'), 1),
         'hesitations': sum(1 for b in blocks if b['k'] == 'hes'), 'removed_blocks_s': round(removed, 1),
         'noise_floor_raw_db': round(float(np.percentile(raw_db, 5)), 1), 'noise_floor_clean_db': round(float(np.percentile(cln_db, 5)), 1)}
tape = {'blocks': blocks, 'wave_raw': norm(raw_db), 'wave_clean': norm(cln_db), 'stats': stats}
(J / 'analysis/tape.json').write_text(json.dumps(tape, ensure_ascii=False))
rep['tape'] = stats

# 4) fontes, three.js, gsap, grão
F = SYS / 'assets/fonts/portable'
for f in ['inter-400-latin.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2', 'inter-400-latin-ext.woff2', 'inter-OFL.txt',
          'ibm-plex-mono-500-latin.woff2', 'ibm-plex-mono-OFL.txt']:
    shutil.copyfile(F / f, A / f)
T3 = J.parent / 'material-compartilhado/motion/vendor/three186/package'
dst = A / 'three'
shutil.rmtree(dst, ignore_errors=True); dst.mkdir(parents=True)
for f in ['three.module.js', 'three.core.js']:
    shutil.copyfile(T3 / 'build' / f, dst / f)
for d in ['postprocessing', 'shaders', 'environments', 'geometries']:
    shutil.copytree(T3 / 'examples/jsm' / d, dst / 'addons' / d)
shutil.copyfile(T3 / 'LICENSE', dst / 'LICENSE')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'gsap.min.js')
shutil.copyfile(J.parent / '<PREENCHER: fonte ou prova própria>', A / 'grain.png')
(J / 'analysis/proof_assets.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep, ensure_ascii=False))
