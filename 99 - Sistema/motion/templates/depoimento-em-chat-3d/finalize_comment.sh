#!/bin/bash
# EXEMPLO_1 — variante "Comente CORTEZ" (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md): mesmo vídeo e áudio; só a tela final muda.
# Usa o EDL/voz/materiais já prontos da versão principal. Uso: src/finalize_comment.sh [--skip-render]
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
if [ "$1" != "--skip-render" ]; then
  CTA=comment $P src/build.py
  rm -f renders/picture-comente-cortez.mp4
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp -o renders/picture-comente-cortez.mp4 -w 4 --video-frame-format png --crf 12 > renders/render-comente-cortez.log 2>&1
  $P src/build.py > /dev/null        # devolve comp/index.html à versão principal ("Saiba mais")
fi
CTA=comment $P src/mix.py
OUT=$($P ../../tools/output_naming.py --name cortez-live-isso-e-sinistro --proportion 9:16 --format F10 --visual-id ID01 --edition-code EXEMPLO_1 --kind preview --version 2 --variant comente-cortez --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -n -i renders/picture-comente-cortez.mp4 -i renders/mix-comente-cortez.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
