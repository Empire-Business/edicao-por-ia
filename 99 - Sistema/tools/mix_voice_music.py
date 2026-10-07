#!/usr/bin/env python3
"""Mix a cleaned voice track with a music bed (ducked under the voice) and mux onto a render.

usage: python3 tools/mix_voice_music.py jobs/<id> --voice renders/x-voice.wav --music PATH \
         --base-video renders/draft-v4.mp4 --out renders/draft-v5.mp4 [--music-db -11]
Music: loudnorm to -16 LUFS, then --music-db (relative), sidechain-ducked by the voice, 2.5 s fade-out.
Picture is stream-copied.
"""
import argparse, subprocess

ap = argparse.ArgumentParser()
ap.add_argument('job'); ap.add_argument('--voice', required=True); ap.add_argument('--music', required=True)
ap.add_argument('--base-video', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--music-db', type=float, default=-11.0)
a = ap.parse_args()
J = a.job.rstrip('/')
voice = f'{J}/{a.voice}'
D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', voice], capture_output=True, text=True).stdout)
fc = (f"[1:a]atrim=0:{D:.4f},asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-2:LRA=11,volume={a.music_db}dB,"
      f"afade=t=in:d=0.3,afade=t=out:st={D - 2.5:.3f}:d=2.5[m];"
      "[0:a]asplit[v][sc];[m][sc]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=420:makeup=1[md];"
      f"[v][md]amix=inputs=2:normalize=0,alimiter=limit=0.84:level=disabled,apad=whole_dur={D:.4f}[o]")
mix = f'{J}/' + a.out.replace('.mp4', '-mix.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', voice, '-i', a.music, '-filter_complex', fc, '-map', '[o]', '-t', f'{D:.4f}',
                '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', mix], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{J}/{a.base_video}', '-i', mix, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', f'{J}/{a.out}'], check=True)
print('ok', f'{J}/{a.out}', round(D, 3))
