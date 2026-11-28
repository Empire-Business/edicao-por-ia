#!/usr/bin/env python3
"""EXEMPLO_1 — trilha de voz: [estouro real da gravação bruta] + [narração de IA do Cortez].
- Gancho: o tropeço real do apresentador na gravação bruta (01 - Enviar vídeos/OFERTA/<gravacao-bruta>.mp4), 1,04–2,86 s:
  "É assim. … É assim que…" (o próprio apresentador interrompe; cortamos nos mínimos de energia, antes da retomada em 2,96 s —
  nenhuma palavra cortada por nós). Fica com o som da sala (é o "antes"), só passa-alta 80 Hz.
- Narração: jobs/material-compartilhado/audio/tts/d2-v1.wav (ElevenLabs, voz plASsyS7JE6GCAvx9uIc, gerada a pedido do usuário; texto d2.txt;
  palavras e tempos de d2-v1.words.json). Usada inteira, sem alterar palavras. Normalizada a −16 LUFS.
Saídas: renders/voice.wav (48 kHz mono), analysis/voice_words.json (palavras com tempo absoluto) e analysis/voice_levels.json.
Run: ../../../.venv/bin/python src/make_audio.py
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
WS = J.parents[2]
RAW = WS / '<PREENCHER: fonte ou prova própria>'
TTS = J.parent / 'material-compartilhado/audio/tts/d2-v1.wav'
TTSW = J.parent / 'material-compartilhado/audio/tts/d2-v1.words.json'
FPS = 30
RAW_IN, RAW_OUT = 1.04, 2.86          # mínimos de energia (−55 dB antes do "É"; −60 dB antes da retomada)
N0 = round(58 / FPS, 4)               # a narração entra no quadro 58 (1,933 s)
TMP = J / 'tmp/audio'; TMP.mkdir(parents=True, exist_ok=True)


def run(a):
    subprocess.run(a, check=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]), float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1])


# 1) estouro bruto
rb = TMP / 'raw-burst.wav'
run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{RAW_IN}', '-i', str(RAW), '-t', f'{RAW_OUT - RAW_IN:.3f}', '-vn', '-ac', '1', '-ar', '48000',
     '-af', f'highpass=f=80,afade=t=in:d=0.015,afade=t=out:st={RAW_OUT - RAW_IN - 0.02:.3f}:d=0.02', '-c:a', 'pcm_s16le', str(rb)])
rI, _ = lufs(rb)
rbn = TMP / 'raw-burst-n.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(rb), '-af', f'volume={-17.5 - rI:.2f}dB', '-c:a', 'pcm_s16le', str(rbn)])
# 2) narração (−16 LUFS)
tI, _ = lufs(TTS)
tn = TMP / 'tts-n.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TTS), '-ac', '1', '-ar', '48000', '-af', f'volume={-16.0 - tI:.2f}dB', '-c:a', 'pcm_s16le', str(tn)])
# 3) montagem: bruto em 0, narração em N0
ms = int(round(N0 * 1000))
out = J / 'renders/voice.wav'; out.parent.mkdir(exist_ok=True)
run(['ffmpeg', '-v', 'error', '-y', '-i', str(rbn), '-i', str(tn), '-filter_complex',
     f'[1:a]adelay={ms}[n];[0:a][n]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.9:level=disabled[o]', '-map', '[o]', '-ar', '48000',
     '-c:a', 'pcm_s16le', str(out)])
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(out)], capture_output=True, text=True).stdout)
words = [{'w': w['word'], 's': round(w['start'] + N0, 3), 'e': round(w['end'] + N0, 3), 'src': 'ia'} for w in json.loads(TTSW.read_text())['words']]
raw_words = [{'w': 'É', 's': 0.08, 'e': 0.2, 'src': 'bruto'}, {'w': 'assim.', 's': 0.2, 'e': 0.52, 'src': 'bruto'},
             {'w': 'É', 's': 0.98, 'e': 1.12, 'src': 'bruto'}, {'w': 'assim', 's': 1.12, 'e': 1.42, 'src': 'bruto'}, {'w': 'que…', 's': 1.42, 'e': 1.68, 'src': 'bruto'}]
(J / 'analysis/voice_words.json').write_text(json.dumps({'n0': N0, 'raw_in': RAW_IN, 'raw_out': RAW_OUT, 'duration': round(dur, 3),
                                                        'speech_end': round(words[-1]['e'], 3), 'words': raw_words + words}, ensure_ascii=False, indent=1))
vI, vP = lufs(out)
(J / 'analysis/voice_levels.json').write_text(json.dumps({'raw_burst_lufs_before': rI, 'tts_lufs_before': tI, 'voice_lufs': vI, 'voice_peak': vP, 'n0': N0}, indent=1))
print(json.dumps({'dur': round(dur, 3), 'n0': N0, 'speech_end': words[-1]['e'], 'voice_lufs': vI, 'peak': vP}))
