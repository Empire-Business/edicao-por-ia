#!/usr/bin/env python3
"""EXEMPLO_1 — trilha de voz: [tomada real que trava] + [narração de IA, parte A] + [a mesma frase limpa na entrega EXEMPLO_2] + [narração, parte B].
- Gancho: a gravação bruta real do apresentador (01 - Enviar vídeos/OFERTA/<gravacao-bruta>.mp4), 18,50–20,62 s:
  "Tem consultor com 15 anos de mercado, que…" — ele mesmo interrompe a frase (silêncio de −52 dB em 20,60 s, retomada só em 21,15 s):
  nenhuma palavra cortada por nós. Fica com o som da sala (é o "antes"), só passa-alta 80 Hz.
- Narração: jobs/material-compartilhado/audio/tts/d8-v1.wav (ElevenLabs, voz plASsyS7JE6GCAvx9uIc, gerada a pedido do usuário; texto d8.txt;
  palavras de d8-v1.words.json). Usada inteira e sem alterar palavras; só dividida no silêncio entre "frase." e "Ninguém" para a
  frase limpa entrar ali. Normalizada a −16 LUFS.
- Prova sonora (V1 revisada pelo diretor): a entrega EXEMPLO_2 V2 (feita pelo Cortez a partir da gravação bruta) com o apresentador na câmera
  dizendo limpa a frase em que ele gaguejou no bruto, 0,00–4,56 s: "É assim que eu encheria a minha agenda se eu fosse consultor e
  vivesse de indicação." ("indicação." termina em 4,42; o próximo "Tem" só em 4,70). Vem com a mixagem da própria entrega; −18 LUFS.
Saídas: renders/voice.wav (48 kHz mono), analysis/voice_words.json, analysis/voice_levels.json, edit/edl.json.
Run: ../../../.venv/bin/python src/make_audio.py
"""
import json, subprocess
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
RAW = WS / '<PREENCHER: fonte ou prova própria>'
EXEMPLO_2 = WS / '<PREENCHER: fonte ou prova própria>'
TTS = J.parent / 'material-compartilhado/audio/tts/d8-v1.wav'
TTSW = J.parent / 'material-compartilhado/audio/tts/d8-v1.words.json'
FPS = 30
RAW_IN, RAW_OUT = 18.50, 20.62
E_IN, E_OUT = 0.00, 4.56
GAP0, GAP1, GAP2 = 0.13, 0.20, 0.24          # bruto→narração, narração→entrega, entrega→narração
TMP = J / 'tmp/audio'; TMP.mkdir(parents=True, exist_ok=True)


def run(a):
    subprocess.run(a, check=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]), float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1])


def pcm(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 's16le', '-ac', '1', '-ar', '48000', '-'], capture_output=True).stdout
    return np.frombuffer(r, np.int16).astype(np.float32) / 32768


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout)


q = lambda x: round(round(x * FPS) / FPS, 4)

# 1) tomada bruta (gancho)
rb = TMP / 'raw.wav'
run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{RAW_IN}', '-i', str(RAW), '-t', f'{RAW_OUT - RAW_IN:.3f}', '-vn', '-ac', '1', '-ar', '48000',
     '-af', f'highpass=f=80,afade=t=in:d=0.015,afade=t=out:st={RAW_OUT - RAW_IN - 0.02:.3f}:d=0.02', '-c:a', 'pcm_s16le', str(rb)])
rI, _ = lufs(rb)
rbn = TMP / 'raw-n.wav'; run(['ffmpeg', '-v', 'error', '-y', '-i', str(rb), '-af', f'volume={-17.5 - rI:.2f}dB', '-c:a', 'pcm_s16le', str(rbn)])

# 2) narração: divisão no mínimo de energia entre "frase." e "Ninguém"
tw = json.loads(TTSW.read_text())['words']
iA = next(i for i, w in enumerate(tw) if w['word'].startswith('Ningu')) - 1          # "frase." final (não o "frase" de "mesma frase")
a0, a1 = tw[iA]['end'], tw[iA + 1]['start']
x = pcm(TTS); h = 240                                   # 5 ms
seg = x[int(a0 * 48000):int(a1 * 48000)]
e = np.sqrt((seg[:len(seg) // h * h].reshape(-1, h) ** 2).mean(1) + 1e-12)
SPLIT = round(a0 + (int(np.argmin(e)) + 0.5) * h / 48000, 3)
tI, _ = lufs(TTS)
TD = dur(TTS)
ta, tb = TMP / 'tts-a.wav', TMP / 'tts-b.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TTS), '-t', f'{SPLIT}', '-ac', '1', '-ar', '48000',
     '-af', f'volume={-16.0 - tI:.2f}dB,afade=t=out:st={SPLIT - 0.012:.3f}:d=0.012', '-c:a', 'pcm_s16le', str(ta)])
run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{SPLIT}', '-i', str(TTS), '-ac', '1', '-ar', '48000',
     '-af', f'volume={-16.0 - tI:.2f}dB,afade=t=in:d=0.012', '-c:a', 'pcm_s16le', str(tb)])

# 3) a frase limpa na entrega EXEMPLO_2
eb = TMP / 'e117.wav'
run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{E_IN}', '-i', str(EXEMPLO_2), '-t', f'{E_OUT - E_IN:.3f}', '-vn', '-ac', '1', '-ar', '48000',
     '-af', f'afade=t=in:d=0.02,afade=t=out:st={E_OUT - E_IN - 0.09:.3f}:d=0.09', '-c:a', 'pcm_s16le', str(eb)])
eI, _ = lufs(eb)
ebn = TMP / 'e117-n.wav'; run(['ffmpeg', '-v', 'error', '-y', '-i', str(eb), '-af', f'volume={-18.0 - eI:.2f}dB', '-c:a', 'pcm_s16le', str(ebn)])

# 4) montagem (tempos no quadro)
R0 = 0.0
N0 = q(RAW_OUT - RAW_IN + GAP0)
EB0 = q(N0 + SPLIT + GAP1)
EB1 = round(EB0 + (E_OUT - E_IN), 3)
NB0 = q(EB1 + GAP2)
END_VOICE = round(NB0 + (TD - SPLIT), 3)
parts = [(rbn, R0), (ta, N0), (ebn, EB0), (tb, NB0)]
ins, fl = [], []
for k, (p, t0) in enumerate(parts):
    ins += ['-i', str(p)]; ms = int(round(t0 * 1000)); fl.append(f'[{k}:a]adelay={ms}[a{k}]')
fl.append(''.join(f'[a{k}]' for k in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0:duration=longest,alimiter=limit=0.9:level=disabled[o]')
out = J / 'renders/voice.wav'; out.parent.mkdir(exist_ok=True)
run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(fl), '-map', '[o]', '-ar', '48000', '-c:a', 'pcm_s16le', str(out)])

# 5) palavras com tempo absoluto
raw_words = [('Tem', 18.58, 18.70), ('consultor', 18.70, 19.06), ('com', 19.06, 19.16), ('15', 19.16, 19.52), ('anos', 19.52, 19.70), ('de', 19.70, 19.82),
             ('mercado,', 19.82, 20.18), ('que…', 20.28, 20.52)]
words = [{'w': w, 's': round(s - RAW_IN + R0, 3), 'e': round(e2 - RAW_IN + R0, 3), 'src': 'bruto'} for w, s, e2 in raw_words]
for w in tw:
    if w['start'] < SPLIT:
        words.append({'w': w['word'], 's': round(w['start'] + N0, 3), 'e': round(w['end'] + N0, 3), 'src': 'ia'})
e117w = json.loads((J / 'analysis/e117_12.words.json').read_text())
for w in e117w:
    if E_IN <= w['s'] and w['e'] <= E_OUT:
        words.append({'w': w['w'], 's': round(w['s'] - E_IN + EB0, 3), 'e': round(w['e'] - E_IN + EB0, 3), 'src': 'entrega'})
for w in tw:
    if w['start'] >= SPLIT:
        words.append({'w': w['word'], 's': round(w['start'] - SPLIT + NB0, 3), 'e': round(w['end'] - SPLIT + NB0, 3), 'src': 'ia'})
vd = dur(out)
(J / 'analysis/voice_words.json').write_text(json.dumps({'n0': N0, 'split': SPLIT, 'eb0': EB0, 'eb1': EB1, 'nb0': NB0, 'speech_end': words[-1]['e'],
                                                        'voice_end': END_VOICE, 'duration': round(vd, 3), 'words': words}, ensure_ascii=False, indent=1))
vI, vP = lufs(out)
(J / 'analysis/voice_levels.json').write_text(json.dumps({'raw_lufs_before': rI, 'tts_lufs_before': tI, 'e117_lufs_before': eI, 'voice_lufs': vI, 'voice_peak': vP},
                                                         indent=1))
# EDL (fontes e trechos, para reprodução)
edl = {'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'format_code': 'F10', 'visual_identity': 'IDP02', 'fps': FPS,
       'segments': [
           {'take': 'r01', 'src': 'raw', 'source': '<PREENCHER: fonte ou prova própria>', 'in': RAW_IN, 'out': RAW_OUT, 'start': R0,
            'role': 'gancho · tomada que trava (o apresentador interrompe a própria frase)'},
           {'take': 'n01', 'src': 'tts', 'source': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d8-v1.wav', 'in': 0.0, 'out': SPLIT, 'start': N0,
            'role': 'narração de IA, parte A'},
           {'take': 'e01', 'src': 'e117', 'source': '<PREENCHER: fonte ou prova própria>', 'in': E_IN, 'out': E_OUT,
            'start': EB0, 'role': 'a frase da gagueira, limpa, na entrega feita pelo Cortez (apresentador na câmera)'},
           {'take': 'n02', 'src': 'tts', 'source': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d8-v1.wav', 'in': SPLIT, 'out': round(TD, 3), 'start': NB0,
            'role': 'narração de IA, parte B'}]}
(J / 'edit').mkdir(exist_ok=True); (J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
print(json.dumps({'N0': N0, 'split': SPLIT, 'EB0': EB0, 'EB1': EB1, 'NB0': NB0, 'end_voice': END_VOICE, 'voice_lufs': vI, 'peak': vP}))
