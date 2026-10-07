#!/usr/bin/env python3
"""Merge memory command hooks, preserving existing settings. Dry-run unless --apply.

Run after the user authorizes the local configuration change. No package install,
network request, external memory service, or permission expansion is performed.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from client_memory import ROOT, confined

EVENTS=('SessionStart','UserPromptSubmit','Stop')


def merge(settings, command):
    result=copy.deepcopy(settings)
    hooks=result.setdefault('hooks',{})
    if not isinstance(hooks,dict):raise ValueError('Existing hooks field is not an object')
    for event in EVENTS:
        groups=hooks.setdefault(event,[])
        if not isinstance(groups,list):raise ValueError('Existing hook groups must be an array')
        # Remove only this package's previous memory-hook handlers; preserve other hooks.
        cleaned=[]
        for group in groups:
            g=copy.deepcopy(group)
            g['hooks']=[h for h in g.get('hooks',[]) if 'tools/memory_hook.py' not in h.get('command','').replace('\\','/')]
            if g['hooks']:cleaned.append(g)
        cleaned.append({'hooks':[{'type':'command','command':command,'timeout':15}]})
        hooks[event]=cleaned
    return result


def install(root=ROOT, apply=False):
    root=Path(root).resolve();path=confined(root,'.claude/settings.json')
    original=path.read_bytes() if path.exists() else None
    old=json.loads(original) if original else {}
    # sys.executable works on the installed machine; rerun this installer after moving it.
    argv=[sys.executable,str(root/'tools/memory_hook.py'),'--root',str(root)]
    command=subprocess.list2cmdline(argv) if os.name=='nt' else shlex.join(argv)
    new=merge(old,command)
    status={'status':'preview','settings':str(path),'hooks':list(EVENTS),'permissions_changed':False,'changes':new!=old}
    if apply and new!=old:
        path.parent.mkdir(parents=True,exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        if original is not None:
            backup=path.with_name('settings.before-memory-'+stamp+'.json')
            with backup.open('xb') as f:f.write(original)
            status['backup']=str(backup)
        with tempfile.NamedTemporaryFile('w',dir=path.parent,encoding='utf-8',delete=False) as f:
            tmp=Path(f.name);json.dump(new,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        try:os.replace(tmp,path)
        finally:
            if tmp.exists():tmp.unlink()
        status['status']='installed'
    elif apply:status['status']='already_installed'
    return status


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',default=str(ROOT));ap.add_argument('--apply',action='store_true')
    a=ap.parse_args();print(json.dumps(install(a.root,a.apply),ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as e:raise SystemExit(str(e))
