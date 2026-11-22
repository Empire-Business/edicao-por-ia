#!/usr/bin/env bash
# Verificação antes de abrir PR — substitui o check-release.yml do GitHub Actions, que a empresa
# não usa mais (21/11/2026). Rode da raiz e cole o fim da saída na descrição do PR:
#
#   bash scripts/verificar.sh
#
# Mesmo passo do workflow antigo: `python tools/check_release.py --tests` em "99 - Sistema", com
# PyYAML 6.0.3, Pillow 12.3.0, numpy 2 e requests 2 num venv em ~/.cache (fora do repositório).
# Precisa de ffmpeg e node (os testes JS rodam com `node --test`); sem os dois na máquina, roda
# tudo num container python:3.12 com ffmpeg e nodejs (precisa de docker ou podman), com o cache
# de downloads (uv, bun, pip) em ~/.cache/edicao-por-ia-container. A instalação limpa que o teste
# faz baixa torch e whisperx: a primeira rodada demora uns 20 minutos. O antigo CI rodava em
# Python 3.11 e 3.12; aqui roda no python3 da máquina ou no 3.12 do container.
set -euo pipefail
cd "$(dirname "$0")/.."

deps=("PyYAML==6.0.3" "Pillow==12.3.0" "numpy>=2,<3" "requests>=2.31,<3")

if command -v ffmpeg >/dev/null && command -v node >/dev/null; then
  venv="${XDG_CACHE_HOME:-$HOME/.cache}/edicao-por-ia-venv"
  [ -x "$venv/bin/python" ] || python3 -m venv "$venv"
  "$venv/bin/pip" install -q --disable-pip-version-check "${deps[@]}"
  (cd "99 - Sistema" && "$venv/bin/python" tools/check_release.py --tests)
else
  echo "Sem ffmpeg ou node na máquina: rodando num container python:3.12 com ffmpeg e nodejs."
  cache="${XDG_CACHE_HOME:-$HOME/.cache}/edicao-por-ia-container"
  mkdir -p "$cache"
  docker run --rm -v "$cache":/root/.cache -v "$PWD":/repo -w "/repo/99 - Sistema" docker.io/library/python:3.12 bash -c \
    'set -e; apt-get update -qq >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg nodejs >/dev/null
     git config --global --add safe.directory /repo
     python -m pip install -q --disable-pip-version-check --root-user-action=ignore "$@"
     python tools/check_release.py --tests' bash "${deps[@]}"
fi

echo
echo "verificar.sh: tudo passou ($(git rev-parse --short HEAD))"
