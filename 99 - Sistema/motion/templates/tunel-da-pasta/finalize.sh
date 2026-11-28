#!/bin/bash
# EXEMPLO_1 cortez-ia-d7 — voz → materiais → composição → HyperFrames (PNG, CRF 15, fila compartilhada) → mixagem → mux.
# Uso: src/finalize.sh [--cta comment] [--skip-render] [--skip-assets]   (saída com nome de tools/output_naming.py em renders/)
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
CTA=saiba; SKIPR=0; SKIPA=0
while [ $# -gt 0 ]; do case "$1" in --cta) CTA="$2"; shift;; --skip-render) SKIPR=1;; --skip-assets) SKIPA=1;; esac; shift; done
export CTA
SUF=""; VAR=(); [ "$CTA" = "comment" ] && SUF="-comment" && VAR=(--variant comente-cortez)
PIC="renders/picture$SUF.mp4"
if [ $SKIPR = 0 ]; then
  $P src/make_audio.py | tail -c 160; echo
  [ $SKIPA = 0 ] && $P src/make_assets.py | tail -c 80 && echo
  $P src/build.py | head -c 80; echo
  rm -f "$PIC"
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp -o "$PIC" -w 4 --video-frame-format png --crf 15 > "renders/render$SUF.log" 2>&1
  $P src/build.py > /dev/null     # deixa comp/ na variante pedida (o render já terminou)
fi
$P src/mix.py
OUT=$($P ../../tools/output_naming.py --name cortez-ia-pasta --proportion 9:16 --format F10 --visual-id ID06 --edition-code EXEMPLO_1 --kind preview --version 1 "${VAR[@]}" --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan$SUF.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -i "$PIC" -i "renders/mix$SUF.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
