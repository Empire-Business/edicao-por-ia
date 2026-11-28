#!/bin/bash
# EXEMPLO_1 cortez-live-c14 — EDL → voz limpa → mídia → composição → HyperFrames (PNG, CRF 15, fila compartilhada) → mixagem → mux.
# Uso: src/finalize.sh [--skip-render]             versão principal (CTA "Saiba mais")
#      CTA=comment src/finalize.sh [--skip-render]  variante "Comente CORTEZ" (mesma EDL/voz/mídia; só a tela final e o som do toque mudam)
set -e -o pipefail
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
CTA="${CTA:-saiba}"; export CTA
if [ "$CTA" = "comment" ]; then SUF="-comment"; VAR="--variant comente-cortez"; else SUF=""; VAR=""; fi
if [ "$1" != "--skip-render" ]; then
  if [ "$CTA" != "comment" ]; then
    $P src/make_edl.py | head -1
    $P src/make_voice.py | tail -c 160; echo
  fi
  $P src/build.py | head -1
  rm -f renders/picture$SUF.mp4
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp -o renders/picture$SUF.mp4 -w 3 --video-frame-format png --crf 15 > renders/render$SUF.log 2>&1
  CTA=saiba $P src/build.py > /dev/null          # deixa comp/index.html na versão principal
fi
$P src/mix.py
OUT=$($P ../../tools/output_naming.py --name cortez-live-pesquisa-de-verdade --proportion 9:16 --format F22 --visual-id ID07 --edition-code EXEMPLO_1 --kind preview --version 2 $VAR --directory renders)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan$SUF.json'))['T']['end'])")
rm -f "$OUT"
ffmpeg -v error -n -i renders/picture$SUF.mp4 -i renders/mix$SUF.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
