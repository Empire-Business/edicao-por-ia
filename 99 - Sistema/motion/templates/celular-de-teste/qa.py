#!/usr/bin/env python3
"""EXEMPLO_1 — QA mecânico de uma saída: transcrição do áudio final × texto da narração, loudness, fundo sob a fala, quadros pretos e
folha de contato (1 quadro/s). Uso: qa.py <arquivo.mp4> <saiba|comment>  → qa/qa-<modo>.json e tmp/sheet-<modo>.jpg"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parents[1]
F, M = Path(sys.argv[1]), sys.argv[2]
suf = '' if M == 'saiba' else '-' + M
TXT = (J.parent / 'material-compartilhado/audio/tts/d14.txt').read_text().strip()


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('20', 'vinte').replace('30', 'trinta')
    return re.findall(r'[a-z]+', s)


def lufs(p, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    ls = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]), float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1])


wav = J / f'tmp/qa-mix{suf}.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
code = ("import mlx_whisper,json,sys;r=mlx_whisper.transcribe(sys.argv[1],path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='pt',"
        "word_timestamps=True);json.dump(r,open(sys.argv[2],'w'),ensure_ascii=False)")
tj = J / f'analysis/transcript_final_mix{suf}.json'
subprocess.run([str(J.parent / 'material-compartilhado/bin/withlock.py'), 'whisper', '--', sys.executable, '-c', code, str(wav), str(tj)], check=True)
tr = json.loads(tj.read_text())
heard = tr['text'].strip()
mp = json.loads((J / 'analysis/motion_plan.json').read_text())['T']
speech = [s['text'] for s in tr['segments'] if s['start'] < mp['speechEnd'] - 0.2]
sim = difflib.SequenceMatcher(None, norm(TXT), norm(' '.join(speech))).ratio()
I, P = lufs(F)
bd = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(F), '-vf', 'blackdetect=d=0.1:pix_th=0.06', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', bd)
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=width,height,r_frame_rate,codec_name', '-of', 'json', str(F)],
                               capture_output=True, text=True).stdout)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(F), '-vf', 'fps=1,scale=216:384,tile=8x3', '-frames:v', '1', str(J / f'tmp/sheet-{M}.jpg')], check=True)
mix = json.loads((J / f'analysis/mix_report{suf}.json').read_text())
rep = {'file': F.name, 'cta': M, 'duration': float(pr['format']['duration']), 'size_mb': round(int(pr['format']['size']) / 1e6, 1),
       'streams': [{k: s.get(k) for k in ('codec_name', 'width', 'height', 'r_frame_rate')} for s in pr['streams']],
       'loudness_lufs': I, 'true_peak_dbtp': P, 'voice_lufs': mix['voice_lufs'], 'bg_stem_lufs_under_speech': mix['bg_stem_lufs_under_speech'],
       'bg_stem_lufs_cta': mix['bg_stem_lufs_cta'], 'black_segments': blacks, 'transcript_final_mix': heard, 'speech_similarity_vs_narration_text': round(sim, 3)}
(J / 'qa').mkdir(exist_ok=True)
(J / f'qa/qa-{M}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: rep[k] for k in ('duration', 'size_mb', 'loudness_lufs', 'true_peak_dbtp', 'bg_stem_lufs_under_speech', 'bg_stem_lufs_cta', 'black_segments',
                                      'speech_similarity_vs_narration_text')}, ensure_ascii=False))
print(heard)
