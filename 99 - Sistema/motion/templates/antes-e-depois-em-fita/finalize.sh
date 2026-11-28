#!/bin/bash
# EXEMPLO_1 cortez-live-c5 — EDL → voz → mídias/fita → composição → HyperFrames (PNG, CRF 12, fila compartilhada) → mixagem → mux.
# Uso: src/finalize.sh [--skip-render] [--version 1]   (saída: prévia com nome de tools/output_naming.py em renders/)
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
VER=1; SKIP=0; CTA=more
while [ $# -gt 0 ]; do case "$1" in --skip-render) SKIP=1;; --version) VER="$2"; shift;; --cta) CTA="$2"; shift;; esac; shift; done
SUF=""; VAR=""; [ "$CTA" = comment ] && SUF="-comment" && VAR="--variant comente-cortez"
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
if [ "$SKIP" = 0 ]; then
  $P src/make_edl.py | head -c 80; echo
  $P src/make_voice.py | head -c 120; echo
  $P src/make_media.py | tail -c 160; echo
  $P src/build.py --cta $CTA | head -c 60; echo
  rm -f renders/picture$SUF.mp4
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp -o renders/picture$SUF.mp4 -w 4 --video-frame-format png --crf 12 > renders/render$SUF.log 2>&1
fi
$P src/mix.py --cta $CTA
OUT=$($P ../../tools/output_naming.py --name cortez-live-antes-depois --proportion 9:16 --format F10 --visual-id ID03 --edition-code EXEMPLO_1 --kind preview --version "$VER" $VAR --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -n -i renders/picture$SUF.mp4 -i renders/mix$SUF.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
