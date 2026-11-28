#!/bin/bash
# EXEMPLO_1 cortez-ia-d6 — EDL → voz (IA + Convidado) → materiais → composição → HyperFrames (PNG, CRF 15, fila compartilhada) → mixagem → mux.
# Uso: src/finalize.sh [--skip-render]          → versão "Saiba mais"
#      CTA=comment src/finalize.sh [--skip-render] → variante "Comente CORTEZ" (comp-cta-comment)
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
MODE=${CTA:-saiba}
if [ "$MODE" = "saiba" ]; then COMP=comp; PIC=renders/picture.mp4; VAR=""; else COMP=comp-cta-$MODE; PIC=renders/picture-$MODE.mp4; VAR="--variant comente-cortez"; fi
if [ "$1" != "--skip-render" ]; then
  if [ "$MODE" = "saiba" ] && [ "$REBUILD" = "1" ]; then $P src/make_edl.py > /dev/null; $P src/make_voice.py | tail -c 200; echo; $P src/make_assets.py; fi
  $P src/build.py | head -c 80; echo
  rm -f $PIC
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render $COMP -o $PIC -w 4 --video-frame-format png --crf 15 > renders/render-$MODE.log 2>&1
  if [ "$MODE" != "saiba" ]; then CTA=saiba $P src/build.py > /dev/null; fi
fi
$P src/mix.py
MIX=renders/mix.wav; [ "$MODE" != "saiba" ] && MIX=renders/mix-$MODE.wav
OUT=$($P ../../tools/output_naming.py --name cortez-ia-ouve-quem-usa --proportion 9:16 --format F10 --visual-id ID04 --edition-code EXEMPLO_1 --kind preview --version 2 $VAR --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -n -i $PIC -i $MIX -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
