"""Read integration credentials locally without executing text or exposing values.

Used only by an explicitly requested/authorized external-service operation. Configuration
checks and setup never read the user's credentials. Existing .env/local JSON remain usable.
The update migration (post_update.py) may append plain-language notes to an existing keys file
with annotate_services: append-only, values kept byte for byte and never returned.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from project_layout import engine_root, surface_root

KEY_FILE = 'CHAVES DAS INTEGRAÇÕES.txt'
KEY_NAMES = ('SCRAPECREATORS_API_KEY', 'ELEVENLABS_API_KEY', 'OPENROUTER_API_KEY', 'APIFY_API_TOKEN', 'VIMEO_ACCESS_TOKEN')
SERVICES_MARKER = '# CORTEZ: INTEGRACOES v2 (2026-11)'
SERVICES_NOTES = '''# O que é cada chave (em palavras simples):
#
# OpenRouter (RECOMENDADO): faz a música com IA, a narração (voz) e as capas.
#   É pago: você coloca créditos na conta e cada uso desconta um pouco (o Cortez sempre
#   mostra o custo e pede o seu sim antes de gastar).
#   Onde criar a chave: https://openrouter.ai/settings/keys
#   Dica: ao criar a chave, defina um limite de gasto (por exemplo, US$ 5).
#   Passo a passo: 03 - Ajuda/COMO CONFIGURAR O OPENROUTER.html
#
# ElevenLabs (OPCIONAL): só para tratar ruído da voz, quando você pedir.
#   A limpeza de ruído no seu computador já vem pronta e não precisa desta chave.
#   Onde criar a chave: https://elevenlabs.io/app/settings/api-keys
#   Passo a passo: 03 - Ajuda/COMO CONFIGURAR O ELEVENLABS.html
#
# ScrapeCreators: buscar cenas do TikTok e do YouTube. https://app.scrapecreators.com/
# Apify (OPCIONAL): baixar vídeo do YouTube quando o ScrapeCreators não entrega o arquivo.
#   https://console.apify.com/settings/integrations
#
# Pode deixar vazias as chaves que não usa. Ter uma chave aqui NÃO autoriza gasto.
# Nunca cole uma chave na conversa com a IA: cole só aqui, depois do sinal =.
'''
TEMPLATE = '''# CHAVES DAS INTEGRAÇÕES
# Cole cada chave depois do sinal =, sem apagar o nome à esquerda.
# Salve este arquivo. Não é preciso usar terminal nem renomear o arquivo.
# Este arquivo é privado: não o envie junto com a fábrica para outras pessoas.
''' + SERVICES_MARKER + '\n' + SERVICES_NOTES + '''
OPENROUTER_API_KEY=
ELEVENLABS_API_KEY=
SCRAPECREATORS_API_KEY=
APIFY_API_TOKEN=
VIMEO_ACCESS_TOKEN=
'''
OPENROUTER_GUIDE = '03 - Ajuda/COMO CONFIGURAR O OPENROUTER.html'


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


def _append_block(root, marker, comment, lock_name):
    """Append comments in one O_APPEND write: never replace the credential file, never return values."""
    from factory_common import workspace_lock
    path = prepare(root)
    with workspace_lock(engine_root(root), lock_name):
        if path.is_symlink(): raise ValueError('Arquivo de chaves não pode ser um atalho.')
        original = path.read_bytes()
        if marker in original: return None, original
        block = comment(original)
        # A human edit between check and write cannot be overwritten: same inode and bytes are required.
        before = path.stat()
        flags = os.O_WRONLY | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino) or path.read_bytes() != original:
                raise ValueError('As chaves mudaram durante a atualização; tente novamente sem substituir o arquivo.')
            if os.write(fd, block) != len(block): raise ValueError('Comentário incompleto; confira apenas as instruções do arquivo.')
            os.fsync(fd)
            after = path.stat()
            if (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino):
                raise ValueError('O arquivo foi salvo por outro programa; comentários podem precisar ser reaplicados.')
        finally:
            os.close(fd)
        return block, original


def annotate_optional(root):
    """Explicit user-requested comment update; preserve all credential bytes privately.

    Not called by setup: setup must never read existing credentials. No values,
    hashes of keys, or credential contents are returned to the caller.
    """
    marker = b'# CORTEZ: INTEGRACOES OPCIONAIS v1'
    comment = (marker + b'\n' +
        '# ElevenLabs é OPCIONAL: limpeza e narração locais e trilhas da biblioteca não precisam desta chave.\n'
        '# Apify é OPCIONAL: usado apenas para baixar YouTube quando ScrapeCreators não entrega o arquivo.\n'
        '# Você pode deixar ELEVENLABS_API_KEY e APIFY_API_TOKEN vazios.\n'
        '# Uma chave preenchida não autoriza gastos; ElevenLabs exige escolha e autorização para cada chamada.\n\n'.encode('utf-8'))
    block, _ = _append_block(root, marker, lambda original: b'\n' + comment, 'optional-key-comments')
    if block is None: return {'ok': True, 'status': 'already_documented', 'values_exposed': False}
    return {'ok': True, 'status': 'optional_comments_added', 'credential_bytes_preserved': True, 'values_exposed': False}


def has_assignment(content, name):
    """Whether a NAME= line exists (filled or empty). Only names are inspected, never values."""
    for line in content.decode('utf-8-sig', 'replace').splitlines():
        line = line.strip()
        if line.startswith('export '): line = line[7:].lstrip()
        if line.partition('=')[0].strip() == name and '=' in line: return True
    return False


def annotate_services(root, create=False):
    """Additive, idempotent update of an EXISTING keys file to the 09/11/2026 service map.

    Appends plain-language notes (OpenRouter = music, narration and covers; ElevenLabs = only noise)
    and an empty OPENROUTER_API_KEY= line when that name is absent. Existing bytes, values and
    permissions are kept; nothing is returned about the values. Without a file nothing is created
    unless `create` (setup creates it with the current template).
    """
    path = surface_root(root) / KEY_FILE
    if not create and not path.exists() and not path.is_symlink():
        return {'ok': True, 'status': 'no_keys_file', 'values_exposed': False}
    marker = SERVICES_MARKER.encode('utf-8')
    added = []

    def comment(original):
        parts = [marker, '# Atualizado em 09/11/2026: estas notas valem no lugar das anotações antigas acima.'.encode('utf-8'),
                 SERVICES_NOTES.rstrip('\n').encode('utf-8')]
        if not has_assignment(original, 'OPENROUTER_API_KEY'):
            parts += [b'# Cole a chave da OpenRouter na linha abaixo, depois do sinal =.', b'OPENROUTER_API_KEY=']
            added.append('OPENROUTER_API_KEY')
        lead = b'\n' if not original or original.endswith(b'\n') else b'\n\n'
        return lead + b'\n'.join(parts) + b'\n'

    block, _ = _append_block(root, marker, comment, 'optional-key-comments')
    if block is None: return {'ok': True, 'status': 'already_documented', 'values_exposed': False}
    return {'ok': True, 'status': 'service_notes_added', 'empty_lines_added': added,
            'credential_bytes_preserved': True, 'values_exposed': False}


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
    if name == 'VIMEO_ACCESS_TOKEN':
        private = engine / '.factory/secrets/vimeo-access-token'
        if any(p.is_symlink() for p in (private,*private.parents) if p!=engine and p.is_relative_to(engine)):
            raise ValueError('Credencial Vimeo não pode ser um atalho.')
        if private.is_file():
            value = private.read_text().strip()
            if value and not any(c.isspace() for c in value):
                return value
            raise ValueError('Credencial Vimeo inválida.')
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
        if name in ('ELEVENLABS_API_KEY', 'APIFY_API_TOKEN'):
            alternative = 'use a limpeza de ruído local' if name == 'ELEVENLABS_API_KEY' else 'envie o vídeo ou escolha outra cena disponível'
            raise ValueError(f'Integração opcional sem chave: {alternative}, ou preencha {name} em “{KEY_FILE}” para usar este serviço.')
        if name == 'OPENROUTER_API_KEY':
            raise ValueError(f'Falta a chave da OpenRouter: preencha OPENROUTER_API_KEY no arquivo visível “{KEY_FILE}” e salve. '
                             f'Passo a passo em {OPENROUTER_GUIDE}. Nunca cole a chave na conversa.')
        raise ValueError(f'Preencha {name} no arquivo visível “{KEY_FILE}” e salve para continuar.')
    value = value.strip()
    if any(c.isspace() for c in value):
        raise ValueError('Chave inválida: cole apenas a chave depois do sinal =.')
    return value
