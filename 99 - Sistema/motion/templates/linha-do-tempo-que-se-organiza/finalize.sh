#!/bin/bash
# EXEMPLO_1 cortez-ia-d12 — voz → materiais → composição → HyperFrames (PNG, CRF 15, fila compartilhada) → mixagem → mux.
# Uso: src/finalize.sh [saiba|comment] [--skip-render] [--skip-assets]   (nome de saída por tools/output_naming.py, V1)
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
MODE=${1:-saiba}; export CTA=$MODE
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
COMP=comp; PIC=renders/picture.mp4; VAR=""
if [ "$MODE" = "comment" ]; then COMP=comp-cta-comment; PIC=renders/picture-comment.mp4; VAR="--variant comente-cortez"; fi
if [[ " $* " != *" --skip-render "* ]]; then
  [[ " $* " == *" --skip-assets "* ]] || $P src/make_assets.py
  $P src/make_voice.py
  CTA=saiba $P src/build.py | head -c 80; echo
  [ "$MODE" = "comment" ] && $P src/build.py | head -c 80 && echo
  rm -f "$PIC"
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render $COMP -o "$PIC" -w 4 --video-frame-format png --crf 15 > renders/render-$MODE.log 2>&1
fi
$P src/mix.py
SUF=""; [ "$MODE" = "comment" ] && SUF="-comment"
OUT=$($P ../../tools/output_naming.py --name cortez-ia-horas-perdidas --proportion 9:16 --format F10 --visual-id ID07 --edition-code EXEMPLO_1 --kind preview --version 1 $VAR --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -i "$PIC" -i renders/mix$SUF.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
