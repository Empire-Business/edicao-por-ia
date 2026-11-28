#!/usr/bin/env python3
"""EXEMPLO_1 — QA da prévia: inteligibilidade (transcrição do áudio final × voz limpa), loudness, fundo sob a fala, quadros pretos,
folha de contato (1 quadro/s) e recortes em tamanho real. Uso: ../../../.venv/bin/python src/qa.py <arquivo.mp4>"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
P = SYS.parent / '.venv/bin/python'
F = Path(sys.argv[1]).resolve()
TMP = J / 'tmp/qa'; TMP.mkdir(parents=True, exist_ok=True)


def norm(t):
    t = unicodedata.normalize('NFD', t.lower()); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', ' ', t).split()


subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vn', '-ac', '1', '-ar', '16000', str(TMP / 'final.wav')], check=True)
subprocess.run([str(J.parent / 'material-compartilhado/bin/withlock.py'), 'whisper', '--', str(P), str(SYS / 'tools/transcribe.py'), '--language', 'pt',
                '--output', str(TMP / 'final.json'), str(TMP / 'final.wav')], check=True, capture_output=True, cwd=SYS)
fin = ' '.join(s['text'] for s in json.loads((TMP / 'final.json').read_text())['segments'])
ref = ' '.join(s['text'] for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'])
sim = difflib.SequenceMatcher(None, norm(ref), norm(fin)).ratio()
o = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
I = float([l for l in o if l.strip().startswith('I:')][-1].split()[1]); TP = float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])
bd = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-vf', 'blackdetect=d=0.05:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:(\S+) black_end:(\S+)', bd)
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,r_frame_rate,codec_name', '-of', 'json', str(F)],
                               capture_output=True, text=True).stdout)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vf', 'fps=1,scale=216:384,tile=10x3', '-frames:v', '1', str(TMP / (F.stem + '.sheet.jpg'))], check=True)
mix = json.loads((J / ('analysis/mix_report-comment.json' if 'COMENTE' in F.name else 'analysis/mix_report.json')).read_text())
rep = {'file': str(F.relative_to(J)), 'duration': float(pr['format']['duration']), 'streams': pr['streams'], 'integrated_lufs': I, 'true_peak': TP,
       'black_segments': blacks, 'intelligibility_similarity': round(sim, 3), 'final_transcript': fin,
       'bg_under_speech_lufs': mix['qa_background_under_speech_lufs'], 'voice_in_mix_lufs': mix['qa_voice_in_mix_lufs'], 'voice_minus_bg_db': mix['qa_voice_minus_bg_db']}
(TMP / (F.stem + '.qa.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rep.items() if k not in ('streams', 'final_transcript')}, ensure_ascii=False)); print(fin)
