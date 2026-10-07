#!/usr/bin/env python3
"""Verify the physical layout and present only daily folders in the project root."""
from __future__ import annotations
import argparse,json,os,stat
from pathlib import Path
from project_layout import engine_root,surface_root
ROOT=Path(__file__).resolve().parents[1]
VISIBLE=('00 - COMECE AQUI.html','01 - Enviar vídeos','02 - Ver vídeos','03 - Ajuda','04 - Formatos','05 - IDs Visuais','99 - Sistema')
BOOTSTRAP=('AGENTS.md','CLAUDE.md','README.md','factory.py')


def organize(root=ROOT,apply=False,restore=False):
    root=surface_root(root)
    for name in VISIBLE:
        p=root/name
        if apply and not p.exists() and name in VISIBLE[1:-1]:p.mkdir()
        if not p.exists() or p.is_symlink():raise ValueError('Expected real user entry: '+name)
    from service_keys import KEY_FILE, prepare
    if apply:prepare(root)
    hidden=[p.name for p in root.iterdir() if p.is_symlink()]+list(BOOTSTRAP)
    report={'ok':True,'applied':apply,'action':'show_compatibility' if restore else 'present','visible_entries':list(VISIBLE)+[KEY_FILE],'technical_folder_is_real':True}
    if not apply:return report
    if hasattr(os,'chflags'):
        for name in hidden:
            p=root/name
            if not os.path.lexists(p):continue
            flags=p.lstat().st_flags
            flags=(flags & ~stat.UF_HIDDEN) if restore else (flags | stat.UF_HIDDEN)
            os.chflags(p,flags,follow_symlinks=False)
    elif os.name=='nt':
        import ctypes
        from ctypes import wintypes
        get=ctypes.windll.kernel32.GetFileAttributesW;get.argtypes=[wintypes.LPCWSTR];get.restype=wintypes.DWORD
        put=ctypes.windll.kernel32.SetFileAttributesW;put.argtypes=[wintypes.LPCWSTR,wintypes.DWORD];put.restype=wintypes.BOOL
        for name in hidden+[p.name for p in root.iterdir() if p.name.startswith('.')]:
            p=root/name
            flags=get(str(p))
            if flags==0xFFFFFFFF:continue
            flags=(flags & ~2) if restore else (flags | 2)
            if not put(str(p),flags):raise OSError('Could not update presentation: '+name)
    (root/'.hidden').write_text('' if restore else '\n'.join(sorted(set(hidden)))+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--apply',action='store_true');p.add_argument('--restore',action='store_true');a=p.parse_args()
    print(json.dumps(organize(a.root,a.apply,a.restore),ensure_ascii=False,indent=2))
