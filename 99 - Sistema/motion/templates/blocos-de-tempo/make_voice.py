#!/usr/bin/env python3
"""EXEMPLO_1 — voz final: narração de IA do Cortez (ElevenLabs, voz plASsyS7JE6GCAvx9uIc, eleven_multilingual_v2; gerada antes por pedido
explícito do usuário, conferida por transcrição) sem alterar nem cortar palavras. O fim real da fala é medido no envelope (último trecho
acima de −46 dBFS), com respiro de 0,5 s antes do CTA. Cadeia leve: atraso VOFF → passa-altas 70 Hz → compressor suave 2:1 → ganho fixo
para −16 LUFS → limitador. Saídas: renders/voice.wav, edit/edl.json (trecho único), analysis/voice_levels.json, analysis/narration_words.json."""
import json, subprocess
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado/audio/tts'
SRC = SH / 'd5-v1.wav'
WORDS = json.loads((SH / 'd5-v1.words.json').read_text())['words']
VOFF = 0.12
OUT = J / 'renders/voice.wav'
OUT.parent.mkdir(exist_ok=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])


r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(SRC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
n = len(x) // 160
db = 20 * np.log10(np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9)
loud = np.where(db > -46)[0]
SPEECH_END_FILE = round(max(float((loud[-1] + 1) * 0.01), WORDS[-1]["end"] + 0.15), 3)   # nunca antes do fim alinhado da última palavra + folga
SPEECH = round(round((VOFF + SPEECH_END_FILE + 0.5) * 30) / 30, 4)
CHAIN = 'highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=160:makeup=1'
raw = J / 'tmp/voice-raw.wav'
raw.parent.mkdir(exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(SRC), '-af', f'adelay={int(VOFF * 1000)}:all=1,{CHAIN},apad=whole_dur={SPEECH + 6:.3f},atrim=0:{SPEECH:.3f},'
                'afade=t=out:st={:.3f}:d=0.08,aformat=sample_rates=48000:channel_layouts=mono'.format(SPEECH - 0.08), '-ar', '48000', str(raw)], check=True)
I0, P0 = lufs(raw)
g = -16.0 - I0
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled', '-ar', '48000', str(OUT)], check=True)
I1, P1 = lufs(OUT)
words = [{'w': w['word'], 's': round(w['start'] + VOFF, 3), 'e': round(w['end'] + VOFF, 3)} for w in WORDS]
(J / 'analysis').mkdir(exist_ok=True)
(J / 'analysis/narration_words.json').write_text(json.dumps({'voff': VOFF, 'speech': SPEECH, 'speech_end_file': SPEECH_END_FILE, 'words': words}, ensure_ascii=False, indent=1))
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps({'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'format_code': 'F10', 'visual_identity': 'ID01', 'fps': 30,
    'note': 'Narração de IA inteira, sem cortes internos; a imagem é composição 3D com provas reais (gravação bruta da Oferta, EXEMPLO_2 V2, EXEMPLO_3, EXEMPLO_4, EXEMPLO_5, EXEMPLO_6).',
    'segments': [{'source': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d5-v1.wav', 'src': 'tts', 'take': 'n01', 'in': 0.0,
                  'out': round(SPEECH - VOFF, 4), 'start': VOFF}], 'duration': SPEECH}, ensure_ascii=False, indent=1))
(J / 'analysis/voice_levels.json').write_text(json.dumps({'before': {'lufs': I0, 'peak': P0}, 'gain_db': round(g, 2), 'final_lufs': I1, 'final_true_peak': P1,
    'voff': VOFF, 'speech_end_file': SPEECH_END_FILE, 'speech_end_video': SPEECH, 'chain': CHAIN + ' → ganho fixo → alimiter'}, ensure_ascii=False, indent=1))
print(json.dumps({'voice_lufs': I1, 'tp': P1, 'speech_end_file': SPEECH_END_FILE, 'speech': SPEECH}))
