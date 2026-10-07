#!/usr/bin/env python3
"""Open factory folders and register formats on macOS, Windows and Linux."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

from project_layout import engine_root, surface_root
ROOT = Path(__file__).resolve().parents[1]


def open_path(path, platform=None):
    path = Path(path).resolve()
    if not path.exists():
        raise ValueError(f'Pasta ou arquivo não encontrado: {path.name}')
    platform = platform or sys.platform
    if platform == 'win32':
        os.startfile(str(path))
    elif platform == 'darwin':
        subprocess.run(['open', str(path)], check=True)
    else:
        opener = shutil.which('xdg-open')
        if opener:
            subprocess.run([opener, str(path)], check=True)
        elif shutil.which('gio'):
            subprocess.run([shutil.which('gio'), 'open', str(path)], check=True)
        else:
            raise ValueError(f'Não encontrei o programa que abre pastas. Abra este caminho no seu gerenciador de arquivos: {path}')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--action', required=True, choices=('input', 'output', 'hub', 'create-format', 'refresh-formats', 'technical'))
    p.add_argument('--section', choices=('tools', 'jobs', 'context', 'patterns', 'workflows', 'method', 'motion', 'studio', 'tests', 'config', 'adapters', 'examples', 'sources', 'interface-lab', 'output'))
    args = p.parse_args(argv)
    root = engine_root(args.root)
    surface = surface_root(root)
    if sys.version_info < (3, 11):
        print('É necessário Python 3.11 ou mais recente. Peça a preparação desta fábrica na conversa.')
        return 1
    try:
        if args.action == 'create-format':
            from format_catalog import interactive
            return interactive(root)
        if args.action == 'refresh-formats':
            from format_catalog import refresh
            result = refresh(root)
            open_path(result['output'])
            return 0 if result['ok'] else 1
        if args.action == 'technical' and not args.section:
            p.error('--section is required for technical navigation')
        if args.action in ('input','output'):
            label='01 - Enviar vídeos' if args.action=='input' else '02 - Ver vídeos'
            legacy='entrada' if args.action=='input' else 'saida'
            open_path(surface/label if (surface/label).is_dir() else root/legacy)
        elif args.action=='hub':open_path(surface)
        else:
            section={'interface-lab':'prototipos/interface-lab','output':'arquivo/entregas-antigas'}.get(args.section,args.section)
            open_path(root/section)
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        print(f'Não foi possível abrir: {e}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
