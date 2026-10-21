#!/usr/bin/env python3
"""Fetch only selected public stock references into the portable factory, checking every hash."""
from __future__ import annotations
import argparse,json,re,os,tempfile,hashlib
from pathlib import Path
from update_local import locate,target_path,sha,atomic,remote_json,download_verified

REPOSITORY='Empire-Business/edicao-por-ia'
REPOSITORY_ID=1408655066
MAX_REFERENCE_FILE=512*1024*1024
MAX_REFERENCE_BATCH=2*1024*1024*1024


def ensure(root,paths):
 engine,surface=locate(root)
 library=json.loads((engine/'config/reference-library.json').read_text())
 paths=list(dict.fromkeys(paths));pending=[]
 for name in paths:
  digest=library.get('files',{}).get(name)
  if not name.startswith('examples/reference-library/') or not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Referência fora do índice público aprovado.')
  path=target_path(engine,surface,name)
  if path.exists():
   if not path.is_file() or sha(path)!=digest:raise ValueError('Referência local alterada; original preservado para revisão: '+name)
  else:pending.append((name,digest))
 if not pending:return {'ok':True,'downloaded':[],'cached':len(paths)}
 manifest_path=engine/'PACKAGE_MANIFEST.json'
 manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
 revision=manifest.get('source_revision')
 # A fresh Git checkout has no updater receipt. Resolve the active public origin once.
 if not revision:
  if remote_json(REPOSITORY,'').get('id')!=REPOSITORY_ID:raise ValueError('Origem de referências mudou; download bloqueado.')
  revision=remote_json(REPOSITORY,'commits/main')['sha']
 if not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('Revisão de referências inválida.')
 byte_sizes={r['path']:r.get('bytes') for g in library['formats'].values() for r in g.get('references',[])}
 sizes=[byte_sizes.get(name) for name,_ in pending]
 if any(type(size) is not int or not 0<=size<=MAX_REFERENCE_FILE for size in sizes) or sum(sizes)>MAX_REFERENCE_BATCH:raise ValueError('Tamanho da referência ausente ou acima do limite seguro.')
 downloaded=[]
 for (name,digest),size in zip(pending,sizes):
  content=download_verified(REPOSITORY,revision,'99 - Sistema/'+name,digest,size,size)
  path=target_path(engine,surface,name)
  if path.exists():
   if sha(path)!=digest:raise ValueError('A referência mudou durante o download; cópia local preservada.')
  else:
   if hashlib.sha256(content).hexdigest()!=digest:raise ValueError('Integridade da referência não confere.')
   path.parent.mkdir(parents=True,exist_ok=True)
   fd,temporary=tempfile.mkstemp(dir=path.parent)
   try:
    with os.fdopen(fd,'wb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
    try:os.link(temporary,path)
    except FileExistsError:
     if sha(path)!=digest:raise ValueError('Cópia local mudou; original preservado.')
   finally:Path(temporary).unlink(missing_ok=True)
  downloaded.append(name)
 return {'ok':True,'downloaded':downloaded,'cached':len(paths)-len(downloaded),'revision':revision}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--format',required=True);a=p.parse_args()
 library=json.loads((locate(a.root)[0]/'config/reference-library.json').read_text());group=library['formats'].get(a.format)
 if not group:raise SystemExit('Formato público ausente no índice.')
 print(json.dumps(ensure(a.root,[r['path'] for r in group['references']]),ensure_ascii=False))
