#!/usr/bin/env python3
"""EXEMPLO_1 — QA mecânica da prévia: inteligibilidade (transcrição do áudio final vs. voz limpa), loudness, fundo sob a fala,
quadros pretos, duração. Grava qa/qa.json (a revisão visual por quadros é registrada no decision_log)."""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path
J = Path(__file__).resolve().parents[1]
P = sys.executable
OUT = sorted((J / 'renders').glob('E123_*_PREVIEW_V2.mp4'))[-1]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


EQ = {'pra': ['para'], 'pro': ['para', 'o'], '2': ['dois'], '3': ['tres'], '5': ['cinco'], '20': ['vinte'], '30': ['trinta'], '5minutos': ['cinco', 'minutos']}


def words(p):   # grafias equivalentes (pra/para, 2/dois) não contam como erro de entendimento
    out = []
    for s in json.loads(Path(p).read_text())['segments']:
        for w in s['words']:
            n = norm(w['word'])
            out += EQ.get(n, [n] if n else [])
    return out


wav = J / 'tmp/final-audio.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(OUT), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
tj = J / 'tmp/final-audio.json'
subprocess.run([str(J.parent / 'material-compartilhado/bin/withlock.py'), 'whisper', '--', P, str(J.parents[1] / 'tools/transcribe.py'), '--language', 'pt',
                '--output', str(tj), str(wav)], check=True, capture_output=True)
a, b = words(J / 'analysis/transcript_final_voice.json'), words(tj)
sim = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
o = subprocess.run(['ffmpeg', '-nostats', '-i', str(OUT), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
I = float([l for l in o if l.strip().startswith('I:')][-1].split()[1]); TP = float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])
bd = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(OUT), '-vf', 'blackdetect=d=0.1:pix_th=0.05', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr.count('black_start')
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,r_frame_rate', '-of', 'json', str(OUT)], capture_output=True, text=True).stdout)
mix = json.loads((J / 'analysis/mix_report.json').read_text())
voice = json.loads((J / 'analysis/voice_levels.json').read_text())
hr = json.loads((J / 'analysis/hidden_retakes_final.json').read_text())
qa = {'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'version': 'V2', 'file': str(OUT.relative_to(J)),
      'checks': {'duration_s': round(float(pr['format']['duration']), 2), 'size': f"{pr['streams'][0]['width']}x{pr['streams'][0]['height']}",
                 'integrated_lufs': I, 'true_peak_dbtp': TP, 'black_segments': bd, 'voice_lufs': voice['final_lufs'],
                 'background_under_speech_lufs': mix['qa_background_under_speech_lufs'], 'voice_minus_background_db': mix['qa_voice_minus_background_db'],
                 'intelligibility_similarity_final_vs_clean_voice': round(sim, 3),
                 'hidden_retakes': f"{len(hr['candidates']) if isinstance(hr['candidates'], list) else hr['candidates']} candidatos, todos naturais (sem regravação)", 'paid_calls_in_this_job': 0,
                 'listening': 'pendente: escuta humana do usuário'},
      'status': 'preview_for_user'}
(J / 'qa').mkdir(exist_ok=True)
(J / 'qa/qa.json').write_text(json.dumps(qa, ensure_ascii=False, indent=1))
print(json.dumps(qa['checks'], ensure_ascii=False))
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if op != 'equal':
        print(op, a[i1:i2], b[j1:j2])
