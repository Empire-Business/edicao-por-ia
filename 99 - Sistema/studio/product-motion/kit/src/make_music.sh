#!/bin/zsh
# Music bed: loops a track on bar boundaries until it covers TOTAL seconds, then fades out.
# usage: src/make_music.sh TOTAL_SECONDS   (track constants below are for assets/audio/music.mp3)
set -e
cd "$(dirname $0)/.."
TOTAL=$1
BPM=114.84; DOWNBEAT=1.6022; A_BARS=36; LOOP_FROM_BAR=8   # first pass plays bars 0..36, each repeat re-enters at bar 8
python3 - "$TOTAL" $BPM $DOWNBEAT $A_BARS $LOOP_FROM_BAR <<'PY' > /tmp/pm_music_filter.txt
import sys, math
total, bpm, d, a, lf = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
bar = 4 * 60 / bpm
first = d + a * bar                       # end of first pass
body = (a - lf) * bar                     # net length added by each repeat (crossfade = 1 bar)
n = max(0, math.ceil((total - first) / body))
parts = [f"[0:a]atrim=0:{first:.4f},asetpts=PTS-STARTPTS[p0]"]
for i in range(n):
    parts.append(f"[{i+1}:a]atrim={d + (lf - 1) * bar:.4f}:{first:.4f},asetpts=PTS-STARTPTS[p{i+1}]")
cur = "p0"
for i in range(n):
    parts.append(f"[{cur}][p{i+1}]acrossfade=d={bar:.4f}:c1=tri:c2=tri[x{i+1}]"); cur = f"x{i+1}"
parts.append(f"[{cur}]atrim=0:{total},afade=t=in:st=0:d=0.3,afade=t=out:st={total-3:.3f}:d=3,loudnorm=I=-16:TP=-1.5:LRA=11[o]")
print(n + 1); print(";".join(parts))
PY
N=$(sed -n 1p /tmp/pm_music_filter.txt); F=$(sed -n 2p /tmp/pm_music_filter.txt)
INPUTS=(); for i in $(seq 1 $N); do INPUTS+=(-i assets/audio/music.mp3); done
ffmpeg -y -v error "${INPUTS[@]}" -filter_complex "$F" -map "[o]" -ar 48000 -c:a pcm_s16le assets/audio/bed.wav
ffprobe -v error -show_entries format=duration -of csv=p=0 assets/audio/bed.wav
