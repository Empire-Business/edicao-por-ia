#!/usr/bin/env python3
"""Recoverable directory relocation. Original file contents and SQLite schemas stay intact."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import stat

from project_layout import SYSTEM

CORE = ('adapters','config','context','examples','factory.py','interface-lab','jobs','memory','method',
        'motion','output','patterns','sources','studio','tests','tools','tutorial-omnx-sell','visual','workflows',
        'ENTREGA-PARA-COMPARTILHAR','--help','AGENTS.md','CLAUDE.md','README.md','BACKUP_AND_SYNC.md',
        'BUILD_REPORT.md','COMECE-AQUI.md','DIRECAO-VISUAL-COMO-USAR.md','MEMORIA-COMO-USAR.md',
        'MEMORY_REVISION_REPORT.md','MOTION_REVISION_REPORT.md','PACKAGE_MANIFEST.json','REVISAO_V1_6.md',
        'REVISAO_V1_7.md','REVISION_REPORT.md','START-HERE.md','VERSION','VISUAL_REVISION_REPORT.md',
        'requirements-optional.txt','FÁBRICA DE VÍDEOS','.factory')


def destinations(root):
    moves = {name:f'{SYSTEM}/{name}' for name in CORE if (root/name).exists() and not (root/name).is_symlink()}
    moves.update({name:dest for name,dest in [('entrada','01 - Enviar vídeos'),('saida','02 - Ver vídeos')]
                  if (root/name).is_dir() and not (root/name).is_symlink()})
    moves.update({
        'tutorial-omnx-sell':f'{SYSTEM}/motion/projetos/tutorial-omnx-sell',
        'interface-lab':f'{SYSTEM}/prototipos/interface-lab',
        'output':f'{SYSTEM}/arquivo/entregas-antigas',
        'ENTREGA-PARA-COMPARTILHAR':f'{SYSTEM}/arquivo/entrega-compartilhada-antiga',
        '--help':f'{SYSTEM}/arquivo/pasta-antiga-help',
        'FÁBRICA DE VÍDEOS':f'{SYSTEM}/arquivo/navegacao-anterior',
    })
    return {name:rel for name,rel in moves.items() if (root/name).exists() and not (root/name).is_symlink()}


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)


def migrate(root, apply=False, compatibility=True):
    root=Path(root).resolve();system=root/SYSTEM
    journal=system/'.factory/structure-migration.json'
    pending=system/'structure-migration.pending.json'
    existing=journal if journal.exists() else pending
    if existing.exists():
        receipt=json.loads(existing.read_text())
        if receipt['status']=='complete':return receipt
        moves=receipt['moves']
    else:
        moves=destinations(root)
        receipt={'version':1,'status':'preview','root':str(root),'moves':moves,'completed':[],'compatibility':compatibility}
    # Preflight ALL moves before modifying any existing item.
    for name,rel in moves.items():
        source=root/name;target=root/rel
        if name in receipt['completed']:
            continue
        if target.exists():
            raise ValueError(f'Existing destination preserved: {rel}')
        if source.is_symlink():
            raise ValueError(f'Existing shortcut preserved: {name}')
        if not source.exists():raise ValueError(f'Missing source: {name}')
    if not apply:return receipt
    system.mkdir(exist_ok=True)
    # Journal is outside .factory until that directory has itself been moved.
    receipt['status']='in_progress';write(pending,receipt)
    for name,rel in moves.items():
        if name in receipt['completed']:continue
        source=root/name;target=root/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        source.rename(target)
        receipt['completed'].append(name);write(pending,receipt)
        if compatibility and name not in ('AGENTS.md','CLAUDE.md','README.md','factory.py'):
            source.symlink_to(rel,target_is_directory=target.is_dir())
            if hasattr(os,'chflags'):
                os.chflags(source,getattr(stat,'UF_HIDDEN',0x8000),follow_symlinks=False)
    layout={'version':1,'legacy_paths':{str(root/name):rel for name,rel in moves.items()}}
    # The fallback maps the former project root; native configuration and venv stay on the surface.
    layout['legacy_paths'][str(root)]=SYSTEM
    for name in ('.agents','.codex','.claude','.venv','.env','.git','.githooks'):
        layout['legacy_paths'][str(root/name)]=name
    write(system/'.factory/layout.json',layout)
    receipt['status']='complete';write(journal,receipt)
    pending.unlink(missing_ok=True)
    return receipt


def rollback(root):
    root=Path(root).resolve();system=root/SYSTEM
    path=system/'.factory/structure-migration.json'
    if not path.exists():path=system/'structure-migration.pending.json'
    receipt=json.loads(path.read_text())
    # Reverse only recorded moves. Preserve subsequent edits by moving, never overwriting.
    for name in reversed(receipt['completed']):
        source=root/receipt['moves'][name];target=root/name
        if target.is_symlink() and os.readlink(target)==receipt['moves'][name]:target.unlink()
        if os.path.lexists(target):raise ValueError(f'Rollback conflict; existing item preserved: {name}')
        source.rename(target)
    return {'status':'rolled_back','moves':len(receipt['completed'])}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--apply',action='store_true');p.add_argument('--without-compatibility',action='store_true')
    args=p.parse_args()
    print(json.dumps(migrate(args.root,args.apply,not args.without_compatibility),ensure_ascii=False,indent=2))
