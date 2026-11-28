#!/usr/bin/env python3
"""EXEMPLO_1 — QA do arquivo final: folha de contato (1 quadro/s), quadros cheios dos momentos-chave, detecção de preto,
loudness, e inteligibilidade (transcrição da mixagem final ≈ transcrição da voz limpa). Saídas em qa/ e tmp/qa/.
Uso: ../../../.venv/bin/python src/qa.py renders/<arquivo>.mp4"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path
J = Path(__file__).resolve().parents[1]
F = Path(sys.argv[1]).resolve()
O = J / 'tmp/qa'; O.mkdir(parents=True, exist_ok=True)
T = json.loads((J / 'analysis/motion_plan.json').read_text())['T']
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(F)], capture_output=True, text=True).stdout)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vf', 'fps=1,scale=216:384,tile=8x4', '-frames:v', '1', str(O / 'sheet.jpg')], check=True)
keys = {'hook0': 0.0, 'hook': 0.6, 'flap': T['flap'] + 0.1, 'sinistro': T['sinistro'] + 0.4, 'styles': T['cor'], 'dive': T['v3'] + 0.45,
        'slice': T['ten'] + 0.25, 'grid': T['bom'] - 0.3, 'ring': T['k2'] + 0.3, 'exit': T['p0'] - 0.1, 'pct': T['pct'] + 0.2, 'fim': T['f0'] + 0.4,
        'cta': T['cta0'] + 2.0, 'last': dur - 0.05}
for k, t in keys.items():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', str(F), '-frames:v', '1', str(O / f'{k}.png')], check=True)
bd = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(F), '-vf', 'blackdetect=d=0.1:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:(\S+) black_end:(\S+)', bd)
o = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
I = float([l for l in o if l.strip().startswith('I:')][-1].split()[1]); P = float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])
wav = O / 'final.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-t', f"{T['speechEnd']:.3f}", '-ac', '1', '-ar', '16000', str(wav)], check=True)
subprocess.run([str(J.parents[1] / 'jobs/material-compartilhado/bin/withlock.py'), 'whisper', '--', str(J.parents[2] / '.venv/bin/python'), str(J.parents[1] / 'tools/transcribe.py'),
                '--language', 'pt', '--output', str(O / 'final.transcript.json'), str(wav)], check=True, capture_output=True)
def toks(p):
    d = json.loads(Path(p).read_text()); ws = [w['word'] for s in d['segments'] for w in s['words']]
    n = lambda w: re.sub(r'[^a-z0-9]', '', ''.join(c for c in unicodedata.normalize('NFD', w.lower()) if unicodedata.category(c) != 'Mn'))
    return [n(w) for w in ws if n(w)]
a, b = toks(J / 'analysis/transcript_final_voice.json'), toks(O / 'final.transcript.json')
sim = difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()
rep = {'file': str(F.relative_to(J)), 'duration_s': round(dur, 3), 'integrated_lufs': I, 'true_peak_dbtp': P, 'black_segments': blacks,
       'intelligibility_similarity': round(sim, 3), 'final_transcript': ' '.join(b), 'frames': {k: str((O / f'{k}.png').relative_to(J)) for k in keys}}
(O / 'qa_raw.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rep.items() if k not in ('frames', 'final_transcript')}, ensure_ascii=False))
