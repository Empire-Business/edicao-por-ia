"""Workspace-contained material files and relocatable persistent references.

An external input can only be imported, never retained as an editing dependency. Relative
persistent references use workspace://, resolved against the current copied folder at runtime.
Installed programs and their system libraries are environment dependencies, not media assets.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,tempfile
from pathlib import Path
from project_layout import engine_root,surface_root
PREFIX='workspace://'


def resolve_file(value,root,must_exist=True):
    surface=surface_root(root)
    if isinstance(value,str) and value.startswith(PREFIX):
        value=surface/value[len(PREFIX):]
    path=Path(value).expanduser()
    if not path.is_absolute():path=engine_root(root)/path
    path=path.resolve(strict=must_exist)
    if not path.is_relative_to(surface):
        raise ValueError('Arquivo fora de edicao-por-ia: importe uma cópia para a pasta antes de usar.')
    if must_exist and not path.is_file():raise ValueError('O material precisa ser um arquivo regular.')
    return path


def portable(value,root):
    surface=surface_root(root)
    def visit(item):
        if isinstance(item,str) and item.startswith(PREFIX):
            # Validate traversal even when this value was already serialized.
            resolve_file(item,root,False)
            return item
        if isinstance(item,str) and Path(item).is_absolute():
            path=resolve_file(item,root,False)
            return PREFIX+path.relative_to(surface).as_posix()
        if isinstance(item,list):return [visit(i) for i in item]
        if isinstance(item,dict):return {k:visit(v) for k,v in item.items()}
        return item
    return visit(value)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def remember_import(source,target,root):
    """Compatibility locator: hash the old path, retain only the internal copy's location."""
    path=resolve_file(engine_root(root)/'.factory/material-map.json',root,False)
    if path.is_symlink():raise ValueError('Mapa de materiais não pode ser um atalho.')
    data=json.loads(path.read_text()) if path.exists() else {}
    key=hashlib.sha256(str(source).encode('utf-8')).hexdigest()
    data[key]=PREFIX+target.relative_to(surface_root(root)).as_posix()
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
        os.replace(tmp,path)
    finally:Path(tmp).unlink(missing_ok=True)


def import_file(source,root,destination=None):
    surface=surface_root(root)
    source=Path(source).expanduser().resolve(strict=True)
    if not source.is_file():raise ValueError('Importe um arquivo de material, não uma pasta.')
    # Never use this importer to open auth/key files.
    if source.name.startswith('.env') or source.suffix.lower() in ('.key','.pem','.p12','.pfx') or source.name=='CHAVES DAS INTEGRAÇÕES.txt':
        raise ValueError('Este importador é para materiais de edição, não credenciais.')
    if source.is_relative_to(surface):
        return {'ok':True,'status':'already_internal','path':PREFIX+source.relative_to(surface).as_posix(),'sha256':digest(source)}
    target=resolve_file(destination,root,False) if destination else surface/'01 - Enviar vídeos/Importados'/source.name
    target=resolve_file(target,root,False)
    target.parent.mkdir(parents=True,exist_ok=True)
    content_hash=digest(source)
    if target.exists():
        if target.is_file() and digest(target)==content_hash:
            remember_import(source,target,root)
            return {'ok':True,'status':'existing','path':PREFIX+target.relative_to(surface).as_posix(),'sha256':content_hash}
        target=target.with_name(target.stem+'-'+content_hash[:12]+target.suffix)
        if target.exists():
            if not target.is_file() or digest(target)!=content_hash:raise ValueError('Conflito de nome ao importar; o arquivo existente foi preservado.')
            remember_import(source,target,root)
            return {'ok':True,'status':'existing','path':PREFIX+target.relative_to(surface).as_posix(),'sha256':content_hash}
    target=resolve_file(target,root,False)
    fd,tmp=tempfile.mkstemp(dir=target.parent);os.close(fd)
    try:
        shutil.copyfile(source,tmp)
        if digest(Path(tmp))!=content_hash:raise ValueError('A cópia do material não foi verificada.')
        # Exclusive publication avoids overwriting a concurrent import.
        with target.open('xb') as output,open(tmp,'rb') as data:shutil.copyfileobj(data,output)
    finally:Path(tmp).unlink(missing_ok=True)
    remember_import(source,target,root)
    return {'ok':True,'status':'imported','path':PREFIX+target.relative_to(surface).as_posix(),'sha256':content_hash,'original_name':source.name,'original_preserved':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);commands=parser.add_subparsers(dest='command',required=True)
    command=commands.add_parser('import');command.add_argument('source');command.add_argument('--destination')
    args=parser.parse_args()
    try:print(json.dumps(import_file(args.source,args.root,args.destination),ensure_ascii=False,indent=2))
    except (ValueError,OSError):parser.exit(2,'Não foi possível importar o material; confira o arquivo e um destino dentro da fábrica.\n')
