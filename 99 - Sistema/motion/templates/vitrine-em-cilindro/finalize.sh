#!/bin/bash
# EXEMPLO_1 cortez-live-c4 — EDL → voz limpa → rostos → materiais → composição → HyperFrames (PNG, CRF 12, fila compartilhada) → mixagem → mux.
# Uso: [CTA=comment] src/finalize.sh [--skip-render]   (saída: prévia com nome de tools/output_naming.py em renders/)
# CTA=comment gera a variante "Comente CORTEZ" (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md) em arquivos separados.
set -e -o pipefail
CTA=${CTA:-more}; export CTA
if [ "$CTA" = comment ]; then SUF=-comment; VAR="--variant comente-cortez --version 1"; else SUF=; VAR=; fi
cd "$(dirname "$0")/.."
P=../../../.venv/bin/python
export TMPDIR="$PWD/tmp/hf"; mkdir -p "$TMPDIR"
if [ "$1" != "--skip-render" ]; then
  $P src/make_edl.py
  $P src/make_voice.py | tail -c 120; echo
  $P src/make_media.py
  $P src/build.py | head -c 60; echo
  rm -f renders/picture$SUF.mp4
  ../material-compartilhado/bin/withlock.py render -- npx -y hyperframes@0.8.92 render comp -o renders/picture$SUF.mp4 -w 4 --video-frame-format png --crf 12 > renders/render$SUF.log 2>&1
fi
$P src/mix.py
OUT=$($P ../../tools/output_naming.py --name cortez-live-formatos --proportion 9:16 --format F10 --visual-id ID05 --edition-code EXEMPLO_1 --kind preview --directory renders $VAR)
DUR=$($P -c "import json;print(json.load(open('analysis/motion_plan$SUF.json'))['T']['end'])")
ffmpeg -v error -n -i renders/picture$SUF.mp4 -i renders/mix$SUF.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate,codec_name -of compact "$OUT"
