#!/usr/bin/env python3
"""EXEMPLO_1 — voz final: narração de IA do Cortez (ElevenLabs, voz plASsyS7JE6GCAvx9uIc, eleven_multilingual_v2; gerada antes, pedido
explícito do usuário) sem alterar palavras. A fala começa em 0,08 s e termina em 21,03 s no arquivo (medido no envelope); nenhum
corte interno. Cadeia leve: atraso VOFF → passa-altas 70 Hz → compressor suave 2:1 → ganho fixo para −16 LUFS → limitador.
Saídas: renders/voice.wav, edit/edl.json (trecho único da narração), analysis/voice_levels.json, analysis/narration_words.json."""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado/audio/tts'
SRC = SH / 'd4-v1.wav'
WORDS = json.loads((SH / 'd4-v1.words.json').read_text())['words']
VOFF = 0.10
SPEECH_END_FILE = 21.03                # fim real do "eu." no envelope (o arquivo segue em silêncio digital até 21,40)
SPEECH = round(round((VOFF + SPEECH_END_FILE + 0.47) * 30) / 30, 4)   # fim da fala no vídeo (com respiro), alinhado a quadro
OUT = J / 'renders/voice.wav'
OUT.parent.mkdir(exist_ok=True)


def lufs(p):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])


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
(J / 'analysis/narration_words.json').write_text(json.dumps({'voff': VOFF, 'speech': SPEECH, 'words': words}, ensure_ascii=False, indent=1))
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps({'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'format_code': 'F10', 'visual_identity': 'ID08', 'fps': 30,
    'note': 'Narração de IA inteira, sem cortes internos; a imagem é composição 3D com provas reais (entregas do usuário e exemplos originais do Cortez).',
    'segments': [{'source': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d4-v1.wav', 'src': 'tts', 'take': 'n01', 'in': 0.0,
                  'out': round(SPEECH - VOFF, 4), 'start': VOFF}], 'duration': SPEECH}, ensure_ascii=False, indent=1))
(J / 'analysis/voice_levels.json').write_text(json.dumps({'before': {'lufs': I0, 'peak': P0}, 'gain_db': round(g, 2), 'final_lufs': I1, 'final_true_peak': P1,
    'voff': VOFF, 'speech_end_video': SPEECH, 'chain': CHAIN + ' → ganho fixo → alimiter'}, ensure_ascii=False, indent=1))
print(json.dumps({'voice_lufs': I1, 'tp': P1, 'speech': SPEECH}))
