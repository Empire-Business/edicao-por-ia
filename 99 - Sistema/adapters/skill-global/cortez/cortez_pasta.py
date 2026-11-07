#!/usr/bin/env python3
"""Acha e registra as pastas de trabalho do Cortez. Só biblioteca padrão; macOS, Windows e Linux.

Uso:
  cortez_pasta.py onde                 # caminho da pasta, ou {"estado": "nenhuma" | "varias" | "sumiu"}
  cortez_pasta.py listar               # todas as pastas registradas e se ainda existem
  cortez_pasta.py registrar "<pasta>"  # registra uma pasta do Cortez já instalada

O registro fica em ~/.config/cortez/config.json (no Windows, %USERPROFILE%\\.config\\cortez).
Nada aqui cria, move ou apaga pasta de trabalho.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SISTEMA = '99 - Sistema'


def config_path(home: Path | None = None) -> Path:
    return Path(home or Path.home()) / '.config' / 'cortez' / 'config.json'


def e_pasta_do_cortez(pasta: Path) -> bool:
    pasta = Path(pasta)
    return (pasta / '.factory-root.json').is_file() and (pasta / SISTEMA / 'tools' / 'factory_common.py').is_file()


def ler(home: Path | None = None) -> dict:
    p = config_path(home)
    if not p.is_file():
        return {'versao': 1, 'pastas': []}
    try:
        dados = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'versao': 1, 'pastas': [], 'aviso': 'registro ilegível; nada foi alterado'}
    if not isinstance(dados.get('pastas'), list):
        dados['pastas'] = []
    return dados


def gravar(dados: dict, home: Path | None = None) -> None:
    p = config_path(home)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.config-', suffix='.json', dir=str(p.parent))
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(tmp, p)


def registrar(pasta, home: Path | None = None, versao: str | None = None) -> dict:
    pasta = Path(pasta).expanduser().resolve()
    if not e_pasta_do_cortez(pasta):
        return {'ok': False, 'motivo': 'Essa pasta não parece uma instalação do Cortez (falta .factory-root.json ou o motor em "99 - Sistema").', 'pasta': str(pasta)}
    dados = ler(home)
    if dados.get('aviso'):
        return {'ok': False, 'motivo': dados['aviso'], 'pasta': str(pasta)}
    agora = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for item in dados['pastas']:
        if Path(item.get('caminho', '')).expanduser() == pasta:
            item['visto_em'] = agora
            if versao:
                item['versao'] = versao
            break
    else:
        dados['pastas'].append({'caminho': str(pasta), 'registrada_em': agora, 'visto_em': agora, **({'versao': versao} if versao else {})})
    gravar(dados, home)
    return {'ok': True, 'pasta': str(pasta), 'total_registradas': len(dados['pastas'])}


def listar(home: Path | None = None) -> list[dict]:
    return [{**item, 'existe': e_pasta_do_cortez(Path(item.get('caminho', '')).expanduser())} for item in ler(home)['pastas']]


def onde(home: Path | None = None):
    itens = listar(home)
    vivas = [i for i in itens if i['existe']]
    if len(vivas) == 1:
        return vivas[0]['caminho']
    if len(vivas) > 1:
        return {'estado': 'varias', 'pastas': [i['caminho'] for i in vivas]}
    if itens:
        return {'estado': 'sumiu', 'pastas': [i['caminho'] for i in itens]}
    return {'estado': 'nenhuma'}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ('onde', 'listar', 'registrar'):
        print(__doc__)
        return 1
    if argv[0] == 'onde':
        r = onde()
        print(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False))
        return 0
    if argv[0] == 'listar':
        print(json.dumps(listar(), ensure_ascii=False, indent=2))
        return 0
    if len(argv) < 2:
        print('Diga qual pasta registrar: cortez_pasta.py registrar "<pasta>"')
        return 1
    r = registrar(argv[1])
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
