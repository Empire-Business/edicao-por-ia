"""Read integration credentials locally without executing text or exposing values.

Used only by an explicitly requested/authorized external-service operation. Configuration
checks and setup never read the user's credentials. Existing .env/local JSON remain usable.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from project_layout import engine_root, surface_root

KEY_FILE = 'CHAVES DAS INTEGRAÇÕES.txt'
KEY_NAMES = ('SCRAPECREATORS_API_KEY', 'ELEVENLABS_API_KEY')
TEMPLATE = '''# CHAVES DAS INTEGRAÇÕES
# Cole cada chave depois do sinal =, sem apagar o nome à esquerda.
# Salve este arquivo. Não é preciso usar terminal nem renomear o arquivo.
# ScrapeCreators: https://app.scrapecreators.com/
# ElevenLabs: https://elevenlabs.io/app/settings/api-keys
# Este arquivo é privado: não o envie junto com a fábrica para outras pessoas.

SCRAPECREATORS_API_KEY=
ELEVENLABS_API_KEY=
'''


def prepare(root):
    """Create an empty visible file if missing. Never open/replace an existing secret file."""
    path = surface_root(root) / KEY_FILE
    if path.is_symlink():
        raise ValueError('O arquivo de chaves deve ser um arquivo real, sem atalho.')
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(TEMPLATE)
    elif not path.is_file():
        raise ValueError('O destino das chaves não é um arquivo regular.')
    return path


def read_assignments(path):
    if path.is_symlink():
        raise ValueError('O arquivo de chaves deve ser um arquivo real, sem atalho.')
    if not path.is_file():
        return {}
    try:
        content = path.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError):
        raise ValueError('Não foi possível ler a configuração; salve o arquivo de chaves como texto UTF-8.') from None
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].lstrip()
        name, sep, value = line.partition('=')
        if not sep or name.strip() not in KEY_NAMES:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if value and not value.startswith('#'):
            if any(c.isspace() for c in value):
                raise ValueError('Chave inválida: cole apenas a chave depois do sinal =.')
            result[name.strip()] = value
    return result


def api_key(name, root=None):
    if name not in KEY_NAMES:
        raise ValueError('Integração desconhecida.')
    engine = engine_root(root or Path(__file__).resolve().parents[1])
    surface = surface_root(engine)
    # A populated visible file wins, so a novice can replace a stale exported key.
    value = read_assignments(surface / KEY_FILE).get(name) or os.environ.get(name)
    if not value:
        for base in dict.fromkeys((surface, engine)):
            value = read_assignments(base / '.env').get(name)
            if value:
                break
    if not value and name == 'SCRAPECREATORS_API_KEY':
        old = engine / 'config/scrapecreators.local.json'
        if old.is_symlink():
            raise ValueError('Configuração de integração não pode ser um atalho.')
        if old.is_file():
            try:
                value = json.loads(old.read_text(encoding='utf-8')).get('api_key')
            except (ValueError, OSError):
                raise ValueError('Configuração antiga do ScrapeCreators inválida.') from None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Preencha {name} no arquivo visível “{KEY_FILE}” e salve para continuar.')
    value = value.strip()
    if any(c.isspace() for c in value):
        raise ValueError('Chave inválida: cole apenas a chave depois do sinal =.')
    return value
