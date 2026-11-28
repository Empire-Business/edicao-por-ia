#!/bin/bash
# EXEMPLO_1 cortez-live-c6 — EDL → voz limpa → materiais → composição → HyperFrames (PNG, CRF 12, fila compartilhada) → mixagem → mux.
# Uso: src/finalize.sh [--skip-render]   (saída: prévia com nome de tools/output_naming.py em renders/)
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
if [ "$1" != "--skip-render" ]; then
  $P src/make_edl.py | head -1
  $P src/make_voice.py | head -1
  [ -d comp/assets/seq/live ] || $P src/make_assets.py
  $P src/build.py | head -1
  rm -f renders/picture.mp4
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp -o renders/picture.mp4 -w 4 --video-frame-format png --crf 15 > renders/render.log 2>&1
fi
$P src/mix.py
OUT=$($P ../../tools/output_naming.py --name cortez-live-5-minutos --proportion 9:16 --format F10 --visual-id ID08 --edition-code EXEMPLO_1 --kind preview --version 2 --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -n -i renders/picture.mp4 -i renders/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
