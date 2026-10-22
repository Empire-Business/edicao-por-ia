#!/usr/bin/env python3
"""Install the Empire-controlled Cortez Voz revision selected by the Cortez release."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import stat
import subprocess
import sys
import tempfile
import zipfile
from factory_common import ROOT, workspace_lock, atomic_json, inside
from voice_distribution import download, extract, digest

def specification(root):
    value = json.loads((Path(root)/'config/cortez-voice.json').read_text())
    if value['repository'] != 'Empire-Business/cortez-voz' or not re.fullmatch('[0-9a-f]{40}',value['commit']):
        raise ValueError('Origem ou revisão de Cortez Voz inválida.')
    expected = f"https://codeload.github.com/{value['repository']}/zip/{value['commit']}"
    if value['archive']['url'] != expected: raise ValueError('O pacote precisa vir da revisão fixa da Empire-Business.')
    return value

def verify_source(source, archive, spec):
    """Recheck every distributed source file against the authenticated archive.

    Local receipt/marker content is never proof of the code or dependency locks.
    Generated runtimes and model data are not covered by this source check.
    """
    source = Path(source); archive = Path(archive)
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size != spec['archive']['size'] or digest(archive) != spec['archive']['sha256']:
        raise ValueError('Arquivo de origem ausente ou divergente; execute a preparação antes de iniciar.')
    if source.is_symlink(): raise ValueError('A pasta de código não pode ser um link.')
    expected_paths = set()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            parts = member.filename.rstrip('/').split('/')[1:]
            if not parts or member.is_dir(): continue
            if any(p in ('', '.', '..') or '\\' in p or ':' in p for p in parts):
                raise ValueError('Caminho inválido no arquivo de origem.')
            expected_paths.add('/'.join(parts))
            path = source
            for part in parts:
                path = path / part
                if path.is_symlink(): raise ValueError('Link encontrado no código instalado.')
            expected = hashlib.sha256()
            with bundle.open(member) as stream:
                while chunk := stream.read(1024 * 1024): expected.update(chunk)
            if not path.is_file() or digest(path) != expected.hexdigest():
                raise ValueError('Código de voz alterado: '+ '/'.join(parts)+'. Preserve a cópia; não execute arquivos divergentes.')
    # Only these build/dependency areas may add files. They are runtime artifacts,
    # not trusted source; do not traverse them or permit a symlink at their root.
    generated = {'.cortez', '.venv', 'node_modules', 'electron/node_modules', 'frontend/dist'}
    for folder, dirs, files in os.walk(source, followlinks=False):
        base = Path(folder)
        for name in dirs[:]:
            path = base/name; rel = path.relative_to(source).as_posix()
            if path.is_symlink(): raise ValueError('Link inesperado no código instalado: '+rel)
            if rel in generated: dirs.remove(name)
        for name in files:
            path=base/name; rel=path.relative_to(source).as_posix()
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise ValueError('Arquivo especial no código instalado: '+rel)
            if rel in expected_paths or rel == '.cortez-source.json': continue
            if '__pycache__' in path.relative_to(source).parts and path.suffix == '.pyc':
                # Cached bytecode could override verified source. It is derived,
                # disposable state, so evict it before any interpreter is started.
                path.unlink()
                continue
            raise ValueError('Arquivo extra no código instalado: '+rel+'. Preserve a cópia para diagnóstico.')

def prepare(root=ROOT, apply=False):
    root = Path(root).resolve(); spec = specification(root)
    machine = {'amd64':'x86_64','aarch64':'arm64'}.get(platform.machine().lower(),platform.machine().lower())
    target = f'{platform.system()}-{machine}'
    if target not in spec['platforms'] or sys.version_info[:2] not in ((3,11),(3,12)):
        return {'ok':True,'status':'unavailable','platform':target,'installed':False,
                'reason':'Cortez Voz requer Python 3.11/3.12 e Mac Apple Silicon, Windows x64 ou Linux x64/glibc; o restante do Cortez pode ser preparado.',
                'database_started':False,'models_downloaded':False}
    base = inside(root,'.factory/runtimes/cortez-voz'); source = base/spec['commit']
    data = inside(root,'.factory/cortez-voz-data')
    result = {'ok':True,'status':'preview','repository':spec['repository'],'commit':spec['commit'],
              'platform':target,'source':str(source),'data':str(data),'archive_bytes':spec['archive']['size'],
              'downloads':'fonte fixa, ferramentas e dependências; pode consumir vários GB',
              'database_started':False,'models_downloaded':False,'speech_tested':False,
              'platform_validation':spec['platforms'][target]}
    if not apply: return result
    with workspace_lock(root,'cortez-voice-install'):
        base.mkdir(parents=True,exist_ok=True)
        archive = base / (spec['commit']+'.zip')
        if not archive.exists():
            with tempfile.TemporaryDirectory(prefix='.download-',dir=base) as folder:
                downloaded = Path(folder)/'source.zip'
                download(spec['archive'],downloaded)
                os.replace(downloaded,archive)
        if archive.is_symlink() or archive.stat().st_size != spec['archive']['size'] or digest(archive) != spec['archive']['sha256']:
            raise ValueError('Arquivo de origem local divergente; preserve para diagnóstico antes de baixar novamente.')
        if not source.exists():
            with tempfile.TemporaryDirectory(prefix='.source-',dir=base) as folder:
                tmp = Path(folder)
                extract(archive,tmp/'extract')
                entries=list((tmp/'extract').iterdir())
                if len(entries)!=1 or not entries[0].is_dir(): raise ValueError('Estrutura inesperada no pacote de voz.')
                code=entries[0]
                if digest(code/'cortez/install.py') != spec['installer_sha256']: raise ValueError('Instalador divergente.')
                (code/'.cortez-source.json').write_text(json.dumps({'commit':spec['commit'],'archive_sha256':spec['archive']['sha256']}))
                os.rename(code,source)
        marker = source/'.cortez-source.json'
        if (not marker.is_file() or json.loads(marker.read_text()).get('archive_sha256') != spec['archive']['sha256']
                or digest(source/'cortez/install.py') != spec['installer_sha256']):
            raise ValueError('Instalação local divergente; preserve a pasta e prepare outra revisão.')
        verify_source(source, archive, spec)
        # Installer has its own bounded child-process handling; no backend startup.
        with subprocess.Popen([sys.executable,str(source/'cortez/install.py'),'--apply'],cwd=source, start_new_session=os.name!='nt') as child:
            try: code=child.wait(timeout=7200)
            except BaseException:
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=15)
                else:
                    child.terminate()
                    try: child.wait(timeout=30)
                    except subprocess.TimeoutExpired: os.killpg(child.pid,signal.SIGKILL)
                child.wait();raise
        if code: raise ValueError('Cortez Voz não terminou a instalação; consulte o diagnóstico. Nenhum backend foi iniciado.')
        receipt=source/'.cortez/installed.json'
        if not receipt.is_file(): raise ValueError('Recibo de instalação ausente.')
        result.update(status='installed',installation=json.loads(receipt.read_text()))
        atomic_json(base/'active.json',{'commit':spec['commit'],'source':str(source.relative_to(root)),
                                     'data':str(data.relative_to(root))})
    return result

def start(root=ROOT, initialize_data=False):
    root=Path(root).resolve(); spec=specification(root)
    if not initialize_data: raise ValueError('Iniciar o aplicativo cria/atualiza seu banco local. Falta autorização --initialize-data para .factory/cortez-voz-data.')
    active=json.loads(inside(root,'.factory/runtimes/cortez-voz/active.json').read_text())
    if active['commit']!=spec['commit']: raise ValueError('Prepare a revisão de voz selecionada por esta versão do Cortez.')
    source=inside(root,active['source']);data=inside(root,active['data'])
    if digest(source/'cortez/install.py')!=spec['installer_sha256']:raise ValueError('Instalador local modificado.')
    verify_source(source, inside(root,'.factory/runtimes/cortez-voz/'+spec['commit']+'.zip'), spec)
    return subprocess.call([sys.executable,str(source/'cortez/install.py'),'--start','--data-dir',str(data),'--initialize-data'],cwd=source)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--apply',action='store_true');p.add_argument('--start',action='store_true');p.add_argument('--initialize-data',action='store_true');a=p.parse_args()
    try:
        if a.start:sys.exit(start(a.root,a.initialize_data))
        print(json.dumps(prepare(a.root,a.apply),ensure_ascii=False,indent=2))
    except (ValueError,OSError,subprocess.SubprocessError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));sys.exit(1)
