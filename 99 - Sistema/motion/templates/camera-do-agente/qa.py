#!/usr/bin/env python3
"""EXEMPLO_1 — QA de uma prévia: inteligibilidade (transcrição do áudio final × voz limpa), loudness, quadros pretos e folha de contato.
Uso: ../../../.venv/bin/python src/qa.py <arquivo.mp4> <rótulo>  → qa/qa_<rótulo>.json e qa/frames/sheet_<rótulo>.jpg"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
P = SYS.parent / '.venv/bin/python'
F = Path(sys.argv[1]).resolve(); LAB = sys.argv[2]
TMP = J / 'tmp/qa'; TMP.mkdir(parents=True, exist_ok=True)
EQ = {'pra': 'para', 'ta': 'esta', 'PRODUTO': 'PRODUTO', 'air': 'ai', 'cortes': 'cortez', 'cortex': 'cortez'}


def norm(t):
    t = unicodedata.normalize('NFD', t.lower()); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return [EQ.get(w, w) for w in re.sub(r'[^a-z0-9 ]', ' ', t).split()]


subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vn', '-ac', '1', '-ar', '16000', str(TMP / f'final_{LAB}.wav')], check=True)
subprocess.run([str(J.parent / 'material-compartilhado/bin/withlock.py'), 'whisper', '--', str(P), str(SYS / 'tools/transcribe.py'), '--language', 'pt', '--backend', 'mlx',
                '--output', str(TMP / f'final_{LAB}.json'), str(TMP / f'final_{LAB}.wav')], check=True, capture_output=True, cwd=SYS)
fin = ' '.join(s['text'] for s in json.loads((TMP / f'final_{LAB}.json').read_text())['segments'])
ref = ' '.join(s['text'] for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'])
sim = difflib.SequenceMatcher(None, norm(ref), norm(fin)).ratio()
o = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
I = float([l for l in o if l.strip().startswith('I:')][-1].split()[1]); TP = float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])
bd = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-vf', 'blackdetect=d=0.05:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:(\S+) black_end:(\S+)', bd)
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=width,height,r_frame_rate,codec_name', '-of', 'json', str(F)],
                               capture_output=True, text=True).stdout)
(J / 'qa/frames').mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vf', 'fps=1,scale=216:384,tile=10x4', '-frames:v', '1', str(J / f'qa/frames/sheet_{LAB}.jpg')], check=True)
rep = {'file': F.name, 'duration': float(pr['format']['duration']), 'size_mb': round(int(pr['format']['size']) / 1e6, 1),
       'streams': [{k: s.get(k) for k in ('codec_name', 'width', 'height', 'r_frame_rate')} for s in pr['streams']],
       'loudness_lufs': I, 'true_peak_dbtp': TP, 'black_segments': blacks, 'intelligibility_similarity': round(sim, 3),
       'final_mix_transcript': fin.strip(), 'clean_voice_transcript': ref.strip()}
(J / f'qa/qa_{LAB}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: rep[k] for k in ('duration', 'size_mb', 'loudness_lufs', 'true_peak_dbtp', 'black_segments', 'intelligibility_similarity')}))
