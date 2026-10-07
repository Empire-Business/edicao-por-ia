#!/usr/bin/env python3
"""Readiness by capability. Presence, import success and real end-to-end tests are distinct."""
from __future__ import annotations
import json, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path
from factory_common import ROOT, inside
from project_layout import surface_root
MODULES=('yaml','faster_whisper','mlx_whisper','playwright')
def interpreter(root):
    p=Path(root)/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if p.is_file():return str(p)
    p=surface_root(root)/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    return str(p) if p.is_file() else sys.executable
def collect(root=ROOT, smoke=False):
    root=Path(root).resolve();py=interpreter(root)
    code='import importlib.util,json; print(json.dumps({k:bool(importlib.util.find_spec(k)) for k in '+repr(MODULES)+'}))'
    try:
        r=subprocess.run([py,'-c',code],capture_output=True,text=True,timeout=10,check=True)
        modules=json.loads(r.stdout)
    except (OSError,subprocess.SubprocessError,ValueError):modules={k:False for k in MODULES}
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    tools={k:shutil.which(k) for k in ('ffmpeg','ffprobe','node','codex','claude')}
    writable=False
    try:
        with tempfile.NamedTemporaryFile(dir=root):writable=True
    except OSError:pass
    cuts=bool(ffmpeg and ffprobe)
    asr=modules['faster_whisper'] or modules['mlx_whisper']
    caps={
      'package_setup':{'available':sys.version_info>=(3,11) and writable,'end_to_end_tested':False},
      'cuts':{'available':cuts,'end_to_end_tested':False},
      'speech_editing':{'available':cuts and asr and modules['yaml'],'end_to_end_tested':False,'weights':'NOT_CHECKED'},
      'javascript_motion':{'available':cuts and bool(tools['node']) and modules['playwright'],'end_to_end_tested':False,'browser':'NOT_CHECKED'},
      'format_memory':{'available':writable,'end_to_end_tested':False},
      'client_memory':{'available':writable,'end_to_end_tested':False}}
    checks=[]
    if smoke and cuts:
        with tempfile.TemporaryDirectory(prefix='vf-check-') as d:
            f=Path(d)/'check.mp4'
            try:
                subprocess.run([ffmpeg,'-v','error','-n','-f','lavfi','-i','color=size=128x128:rate=10:duration=0.3','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','0.3','-c:v','libx264','-c:a','aac',str(f)],check=True,capture_output=True,timeout=30)
                subprocess.run([ffprobe,'-v','error','-show_format','-of','json',str(f)],check=True,capture_output=True,timeout=10)
                caps['cuts']['end_to_end_tested']=True;checks.append('synthetic_cut_export')
            except (OSError,subprocess.SubprocessError):caps['cuts']['available']=False;checks.append('synthetic_cut_export_FAILED')
    messages=[]
    if not caps['package_setup']['available']:messages.append('É necessário Python 3.11+ e permissão de escrita para a nova preparação assistida.')
    if not cuts:messages.append('Faltam FFmpeg/FFprobe para executar cortes.')
    elif not caps['speech_editing']['available']:messages.append('Cortes disponíveis; falta preparar a análise da fala. Não chamar a fábrica inteira de pronta.')
    else:messages.append('Componentes de fala encontrados; valide o backend e os pesos antes do primeiro vídeo.')
    return {'ok':True,'python':sys.version.split()[0],'interpreter':py,'system':platform.system(),'machine':platform.machine(),
      'tools':tools,'modules':modules,'capabilities':caps,'messages':messages,'tests_executed':checks,
      'authentication':'NOT_VERIFIED','model_access':'NOT_VERIFIED','provider_extra_credits':'NOT_VERIFIED',
      'no_network_requests':True}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(ROOT));p.add_argument('--smoke',action='store_true');a=p.parse_args()
    print(json.dumps(collect(a.root,a.smoke),ensure_ascii=False,indent=2))
