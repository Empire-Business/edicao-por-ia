#!/bin/bash
# EXEMPLO_1 — variante de CTA "Comente CORTEZ" (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md): mesmo vídeo e áudio; só a tela final muda.
# Usa a composição em comp-comment/ (build com CTA=comment), mesmas configurações de render da versão "Saiba mais" (PNG, CRF 15).
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
CTA=comment $P src/build.py
if [ "$1" != "--skip-render" ]; then
  rm -f renders/picture-comment.mp4
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp-comment -o renders/picture-comment.mp4 -w 4 --video-frame-format png --crf 15 > renders/render-comment.log 2>&1
fi
CTA=comment $P src/mix.py
OUT=$($P ../../tools/output_naming.py --name cortez-live-5-minutos --proportion 9:16 --format F10 --visual-id ID08 --edition-code EXEMPLO_1 --kind preview --version 2 --variant comente-cortez --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -n -i renders/picture-comment.mp4 -i renders/mix-comment.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
