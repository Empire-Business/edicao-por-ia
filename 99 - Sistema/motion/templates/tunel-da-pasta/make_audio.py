#!/usr/bin/env python3
"""EXEMPLO_1 — trilha de voz: narração de IA do Cortez (jobs/material-compartilhado/audio/tts/d7-v1.wav; ElevenLabs, voz plASsyS7JE6GCAvx9uIc,
gerada a pedido do usuário; texto d7.txt; tempos de d7-v1.words.json). Usada inteira, sem alterar palavras; entra em N0 (um respiro de
imagem antes da primeira palavra). Normalizada a −16 LUFS.
Saídas: renders/voice.wav (48 kHz mono), analysis/voice_words.json (palavras em tempo absoluto) e analysis/voice_levels.json.
Run: ../../../.venv/bin/python src/make_audio.py
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
TTS = J.parent / 'material-compartilhado/audio/tts/d7-v1.wav'
TTSW = J.parent / 'material-compartilhado/audio/tts/d7-v1.words.json'
FPS = 30
N0 = round(8 / FPS, 4)          # 0,267 s: o primeiro quadro já mostra a pasta e o título
TMP = J / 'tmp/audio'; TMP.mkdir(parents=True, exist_ok=True)


def run(a):
    subprocess.run(a, check=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]), float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1])


tI, _ = lufs(TTS)
out = J / 'renders/voice.wav'; out.parent.mkdir(exist_ok=True)
ms = int(round(N0 * 1000))
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TTS), '-af', f'aformat=sample_rates=48000:channel_layouts=mono,volume={-16.0 - tI:.2f}dB,adelay={ms},'
     'alimiter=limit=0.9:level=disabled', '-ar', '48000', '-c:a', 'pcm_s16le', str(out)])
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(out)], capture_output=True, text=True).stdout)
words = [{'w': w['word'], 's': round(w['start'] + N0, 3), 'e': round(w['end'] + N0, 3), 'src': 'ia'} for w in json.loads(TTSW.read_text())['words']]
(J / 'analysis/voice_words.json').write_text(json.dumps({'n0': N0, 'duration': round(dur, 3), 'speech_end': round(words[-1]['e'], 3), 'words': words},
                                                       ensure_ascii=False, indent=1))
vI, vP = lufs(out)
(J / 'analysis/voice_levels.json').write_text(json.dumps({'tts_lufs_before': tI, 'voice_lufs': vI, 'voice_peak': vP, 'n0': N0}, indent=1))
print(json.dumps({'dur': round(dur, 3), 'n0': N0, 'speech_end': words[-1]['e'], 'voice_lufs': vI, 'peak': vP}))
