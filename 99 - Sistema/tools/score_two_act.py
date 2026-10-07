#!/usr/bin/env python3
"""Two-act score cut to the speech: act 1 (tension) until the turn, act 2 (resolution) from the turn
to the end, with act 1's "drop" and act 2's final chord landing on chosen moments.

usage: python3 tools/score_two_act.py jobs/<id> --voice renders/x-voice.wav --base-video renders/a.mp4 --out renders/b.mp4 \
          --act1 A.mp3 --act2 B.mp3 --turn 34.6 --drop-at 10.9 [--music-lufs -22]
- act 1 is offset so its drop (first strong bass entry) lands at --drop-at, and fades out just before --turn
- act 2 enters on a kick at --turn and is slightly time-stretched (<=4%) so its real ending lands at the end of the video
- music is ducked under the voice (sidechain), picture is stream-copied
"""
import argparse, json, subprocess
import numpy as np

SR = 16000

def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768

def lowband(x, hop=320, win=1024):
    f = np.fft.rfftfreq(win, 1 / SR); m = f < 150; w = np.hanning(win)
    return np.array([np.sqrt((np.abs(np.fft.rfft(x[i:i + win] * w))[m] ** 2).sum()) for i in range(0, len(x) - win, hop)]), hop / SR

def real_end(x):
    h = 800; e = np.array([np.sqrt(np.mean(x[i:i + h] ** 2)) for i in range(0, len(x) - h, h)])
    return (np.where(20 * np.log10(e + 1e-9) > -45)[0][-1] + 1) * h / SR

def lufs(path, a, b):
    out = subprocess.run(['ffmpeg', '-nostats', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith('I:')][-1].split()[1])

ap = argparse.ArgumentParser()
ap.add_argument('job'); ap.add_argument('--voice', required=True); ap.add_argument('--base-video', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--act1', required=True); ap.add_argument('--act2', required=True)
ap.add_argument('--turn', type=float, required=True); ap.add_argument('--drop-at', type=float, required=True)
ap.add_argument('--music-lufs', type=float, default=-20.0)
ap.add_argument('--duck', default='0.1:8:900', help='sidechain threshold:ratio:release_ms')
ap.add_argument('--sc-boost', type=float, default=30.0, help='dB boost + limiter on the sidechain so soft words duck as much as loud ones')
a = ap.parse_args()
J = a.job.rstrip('/'); voice = f'{J}/{a.voice}'
D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', voice], capture_output=True, text=True).stdout)
T = a.turn

# --- act 1: locate the drop (bass energy jumps and stays)
x1 = load(a.act1); lb, dt = lowband(x1)
thr = 0.35 * np.percentile(lb, 90)
k = next(i for i in range(len(lb)) if lb[i] > thr and np.mean(lb[i:i + int(2 / dt)] > thr * 0.3) > 0.5)
drop = k * dt
off1 = drop - a.drop_at                      # file time = video time + off1
if off1 < 0: raise SystemExit(f'drop {drop:.2f}s is earlier than --drop-at; choose a later moment')
# --- act 2: enter on a kick, end on the real ending
x2 = load(a.act2); lb2, dt2 = lowband(x2); end2 = real_end(x2)
need = D + 0.35 - T                          # act-2 time needed in the video
target = end2 - need                         # ideal file offset
on = np.maximum(0, np.diff(lb2)); cand = [(on[i], i * dt2) for i in range(len(on)) if abs(i * dt2 - target) < 1.3]
off2 = max(cand)[1] - 0.02
tempo = (end2 - off2) / need                 # >1 = play faster
if not 0.96 <= tempo <= 1.04: raise SystemExit(f'act 2 would need tempo {tempo:.3f}; regenerate with another length')
g1 = a.music_lufs - lufs(a.act1, drop + 2, min(real_end(x1), off1 + T))
g2 = a.music_lufs + 1.0 - lufs(a.act2, off2, end2 - 4)  # the resolution sits 1 dB above the tension act
pre = 6.0                                    # the sparse intro before the drop is lifted so it is heard under the voice
fo = 0.7                                     # act-1 fade-out, ends 0.12 s before the turn (a breath before the solution)
fc = (f"[1:a]atrim={off1:.3f}:{off1 + T - 0.12:.3f},asetpts=PTS-STARTPTS,"
      f"volume='if(lt(t,{a.drop_at - 0.25:.3f}),{g1 + pre:.2f}dB,{g1:.2f}dB)':eval=frame,"
      f"afade=t=in:d=0.25,afade=t=out:st={T - 0.12 - fo:.3f}:d={fo}[a1];"
      f"[2:a]atrim={off2:.3f}:{end2 + 0.5:.3f},asetpts=PTS-STARTPTS,atempo={tempo:.5f},volume={g2:.2f}dB,afade=t=in:d=0.02,"
      f"adelay={int(round(T * 1000))}:all=1[a2];"
      # music bus: tame peaks, carve the voice band, then duck hard under every word (user: music was covering the voice)
      f"[a1][a2]amix=inputs=2:normalize=0:duration=longest,acompressor=threshold=0.1:ratio=3:attack=20:release=250,"
      f"equalizer=f=2500:t=q:w=1:g=-4[m];"
      f"[0:a]asplit[v][sc0];[sc0]volume={a.sc_boost}dB,alimiter=limit=0.5:attack=2:release=50:level=disabled[sc];" + "[m][sc]sidechaincompress=threshold={}:ratio={}:attack=10:release={}:makeup=1,asplit[md][stem];".format(*a.duck.split(":")) +
      f"[v][md]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.84:level=disabled,apad=whole_dur={D:.4f}[o]")
mix = f'{J}/' + a.out.replace('.mp4', '-mix.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', voice, '-i', a.act1, '-i', a.act2, '-filter_complex', fc, '-map', '[o]', '-t', f'{D:.4f}',
                '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', mix, '-map', '[stem]', '-t', f'{D:.4f}', '-ar', '48000', '-c:a', 'pcm_s16le', mix.replace('-mix.wav', '-music-stem.wav')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{J}/{a.base_video}', '-i', mix, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', f'{J}/{a.out}'], check=True)
v = load(voice); ms = load(mix.replace('-mix.wav', '-music-stem.wav')); n = min(len(v), len(ms)) // SR
rv = np.array([20 * np.log10(np.sqrt(np.mean(v[i * SR:(i + 1) * SR] ** 2)) + 1e-9) for i in range(n)])
rm = np.array([20 * np.log10(np.sqrt(np.mean(ms[i * SR:(i + 1) * SR] ** 2)) + 1e-9) for i in range(n)])
sp = rv > -35
dd = (rm - rv)[sp]
rep = dict(music_minus_voice_db=dict(p95=round(float(np.percentile(dd, 95)), 1), median=round(float(np.median((rm - rv)[sp])), 1), worst=round(float((rm - rv)[sp].max()), 1), worst_at_s=int(np.argmax(np.where(sp, rm - rv, -99)))),
           out=f'{J}/{a.out}', duration=round(D, 3), turn=T, drop_in_file=round(drop, 2), drop_at=a.drop_at, act1_offset=round(off1, 2),
           act2_offset=round(off2, 2), act2_tempo=round(tempo, 4), act2_real_end=round(end2, 2), gains_db=[round(g1, 1), round(g2, 1)])
json.dump(rep, open(f'{J}/analysis/music_edit.json', 'w'), indent=1)
print(json.dumps(rep))
