#!/usr/bin/env python3
"""EXEMPLO_1 — QA mecânico da prévia: retranscrição da voz final e da mixagem (fila "whisper" compartilhada), regravações escondidas,
inteligibilidade (mix × voz), loudness, fundo sob a fala, quadros pretos e folha de contato a cada 1 s.
Uso: ../../../.venv/bin/python src/qa.py renders/<arquivo>.mp4   → analysis/qa_mech.json + qa/contact_1s.jpg
"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
PY = str(SYS.parent / '.venv/bin/python')
LOCK = str(J.parent / 'material-compartilhado/bin/withlock.py')
VID = J / sys.argv[1]
TMP = J / 'tmp/qa'
TMP.mkdir(parents=True, exist_ok=True)


def tr(src, out):
    subprocess.run([LOCK, 'whisper', '--', PY, str(SYS / 'tools/transcribe.py'), str(src), '--output', str(out), '--language', 'pt'], check=True, capture_output=True)
    return json.loads(Path(out).read_text())


def words(d):
    return [w['word'].strip() for s in d['segments'] for w in s['words']]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(VID), '-vn', '-ac', '1', '-ar', '16000', str(TMP / 'final.wav')], check=True)
tv = tr(J / 'renders/voice.wav', J / 'analysis/transcript_final_voice.json')
tb = tr(J / 'renders/voice-apresentador-only.wav', TMP / 'apresentador-only.json')
tm = tr(TMP / 'final.wav', TMP / 'final-mix.json')
wv, wm = [norm(x) for x in words(tv)], [norm(x) for x in words(tm)]
sim = difflib.SequenceMatcher(None, [x for x in wv if x], [x for x in wm if x]).ratio()
hr = subprocess.run([PY, str(SYS / 'tools/find_hidden_retakes.py'), '--audio', str(J / 'renders/voice-apresentador-only.wav'), '--transcript', str(TMP / 'apresentador-only.json'),
                     '--out', str(J / 'analysis/hidden_retakes_final.json')], capture_output=True, text=True)


def lufs(path, extra=()):
    o = subprocess.run(['ffmpeg', '-nostats', *extra, '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])


I, TP = lufs(VID)
bd = subprocess.run(['ffmpeg', '-nostats', '-i', str(VID), '-vf', 'blackdetect=d=0.1:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', bd)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(VID)], capture_output=True, text=True).stdout)
(J / 'qa').mkdir(exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(VID), '-vf', 'fps=1,scale=216:384,tile=10x3', '-frames:v', '1', str(J / 'qa/contact_1s.jpg')], check=True)
mix = json.loads((J / 'analysis/mix_report.json').read_text())
rep = {'file': str(VID.relative_to(J)), 'duration_s': round(dur, 3), 'integrated_lufs': I, 'true_peak_dbtp': TP, 'black_segments': blacks,
       'voice_transcript': ' '.join(words(tv)), 'apresentador_only_transcript': ' '.join(words(tb)), 'final_mix_transcript': ' '.join(words(tm)),
       'intelligibility_mix_vs_voice': round(sim, 3), 'hidden_retakes_stdout_tail': hr.stdout[-600:], 'hidden_retakes_rc': hr.returncode,
       'background_under_apresentador_lufs_in_master': mix.get('qa_background_stem_lufs_under_apresentador_in_master')}
(J / 'analysis/qa_mech.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rep.items() if 'transcript' not in k}, ensure_ascii=False, indent=1))
print('VOZ :', rep['voice_transcript'])
print('MIX :', rep['final_mix_transcript'])
