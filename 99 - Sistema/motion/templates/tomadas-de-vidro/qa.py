#!/usr/bin/env python3
"""EXEMPLO_1 — QA da prévia: inteligibilidade (transcrição do áudio final × texto real: tomada bruta + narração + frase da entrega), loudness,
fundo sob a fala, quadros pretos e folha de contato (1 quadro/s). Uso: ../../../.venv/bin/python src/qa.py <arquivo.mp4> [sufixo]"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SYS = J.parents[1]
P = SYS.parent / '.venv/bin/python'
F = Path(sys.argv[1]).resolve()
SUF = sys.argv[2] if len(sys.argv) > 2 else ''
TMP = J / 'tmp/qa'; TMP.mkdir(parents=True, exist_ok=True)


def norm(t):
    t = unicodedata.normalize('NFD', t.lower()); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', ' ', t).split()


subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vn', '-ac', '1', '-ar', '16000', str(TMP / f'final{SUF}.wav')], check=True)
subprocess.run([str(J.parent / 'material-compartilhado/bin/withlock.py'), 'whisper', '--', str(P), str(SYS / 'tools/transcribe.py'), '--language', 'pt',
                '--output', str(TMP / f'final{SUF}.json'), str(TMP / f'final{SUF}.wav')], check=True, capture_output=True, cwd=SYS)
segs = json.loads((TMP / f'final{SUF}.json').read_text())['segments']
fin = ' '.join(s['text'] for s in segs)
_t = (J.parent / 'material-compartilhado/audio/tts/d8.txt').read_text().strip(); _i = _t.index('Ninguém')
ref = 'Tem consultor com 15 anos de mercado, que ' + _t[:_i] + ' É assim que eu encheria a minha agenda se eu fosse consultor e vivesse de indicação. ' + _t[_i:]
sim = difflib.SequenceMatcher(None, norm(ref), norm(fin)).ratio()
o = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
I = float([l for l in o if l.strip().startswith('I:')][-1].split()[1]); TP = float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1])
bd = subprocess.run(['ffmpeg', '-nostats', '-i', str(F), '-vf', 'blackdetect=d=0.05:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:(\S+) black_end:(\S+)', bd)
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=width,height,r_frame_rate,codec_name', '-of', 'json', str(F)],
                               capture_output=True, text=True).stdout)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vf', 'fps=1,scale=216:384,tile=10x3', '-frames:v', '1', str(TMP / f'sheet{SUF}.jpg')], check=True)
mix = json.loads((J / f'analysis/mix_report{SUF}.json').read_text())
rep = {'file': str(F.relative_to(J)), 'duration': float(pr['format']['duration']), 'size_mb': round(int(pr['format']['size']) / 1e6, 1), 'streams': pr['streams'],
       'integrated_lufs': I, 'true_peak': TP, 'black_segments': blacks, 'intelligibility_similarity': round(sim, 3), 'final_transcript': fin,
       'bg_under_narration_lufs': mix['qa_background_stem_lufs_under_narration'], 'voice_lufs': mix['qa_voice_lufs']}
(TMP / f'qa_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rep.items() if k not in ('streams', 'final_transcript')}, ensure_ascii=False)); print(fin)
