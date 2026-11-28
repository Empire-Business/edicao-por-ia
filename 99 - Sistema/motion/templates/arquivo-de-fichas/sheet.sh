#!/bin/bash
# monta uma folha com as prévias PNG de uma pasta: sheet.sh <dir> <saida.jpg> <colunas>
cd "$(dirname "$0")/.."
ffmpeg -v error -y -pattern_type glob -i "$1/t*.png" -vf "scale=270:480,tile=${3:-6}x2" -frames:v 1 "$2"
