#!/usr/bin/env python3
"""Retired: ElevenLabs Music is no longer used (owner decision, 09/11/2026).

AI music is generated with Google Lyria 3 on OpenRouter by tools/or_music.py. This file stays so
existing installations (additive updates) get a clear message instead of a missing command.
Nothing is called, no key is read and nothing is charged.
"""
import sys

MESSAGE = '''A música com IA do Cortez agora é feita pelo OpenRouter (modelos Google Lyria 3).
O ElevenLabs Music foi desligado em 09/11/2026; o ElevenLabs ficou só para tratar ruído.
Nada foi gerado e nada foi cobrado.

Use, depois do sim da pessoa para o gasto (cerca de US$ 0,04 até 30 s; US$ 0,08 acima disso):
  python3 tools/or_music.py --prompt "instrumentos, clima, BPM e estrutura" --seconds 60 --out CAMINHO.mp3 --accept-paid

Sem gasto: python3 tools/music_library.py list (biblioteca local de trilhas).
Chave: OPENROUTER_API_KEY no arquivo "CHAVES DAS INTEGRAÇÕES.txt" (guia em 03 - Ajuda/COMO CONFIGURAR O OPENROUTER.html).'''


def main():
    sys.stderr.write(MESSAGE + '\n')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
