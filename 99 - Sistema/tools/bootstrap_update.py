#!/usr/bin/env python3
"""Fetch a pinned, checksum-verified standalone updater without changing active code.

AI-operated only. No launcher/user commands. Enables old installations to receive large
reference libraries or newer update support, while the transaction still owns activation.
"""
from __future__ import annotations
import argparse,ast,base64,hashlib,json,os,re,shutil,subprocess,sys,tempfile,urllib.request
from pathlib import Path
REPO='Empire-Business/edicao-por-ia';REPOSITORY_ID=1408655066


def remote(repo,path):
 if shutil.which('gh'):
  call=subprocess.run(['gh','api','repos/'+repo+('/'+path if path else '')],capture_output=True,text=True,timeout=30)
  if call.returncode:raise ValueError('Não foi possível acessar o GitHub; nenhuma chave foi lida ou impressa.')
  return json.loads(call.stdout)
 request=urllib.request.Request('https://api.github.com/repos/'+repo+('/'+path if path else ''),headers={'User-Agent':'VideoFactory-Bootstrap'})
 with urllib.request.urlopen(request,timeout=30) as result:return json.load(result)


def prepare(root):
 root=Path(root).resolve();engine=root/'99 - Sistema' if (root/'99 - Sistema').is_dir() else root
 config=engine/'config/update-source.json';settings=json.loads(config.read_text()) if config.exists() else {}
 repo=settings.get('repository',REPO)
 if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo) or settings.get('branch','main')!='main':raise ValueError('Origem inválida; instalação ficou intacta.')
 if remote(repo,'').get('id')!=settings.get('repository_id',REPOSITORY_ID):raise ValueError('O repositório mudou; instalação ficou intacta.')
 revision=remote(repo,'commits/main')['sha']
 if not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('Revisão inválida.')
 from urllib.parse import quote
 def content(path):
  value=remote(repo,'contents/'+quote('99 - Sistema/'+path,safe='/')+'?ref='+revision)
  return base64.b64decode(value['content'],validate=False)
 manifest=json.loads(content('PACKAGE_MANIFEST.json'))
 if manifest.get('package')!='claude-video-factory':raise ValueError('Pacote inválido.')
 minimum=tuple(int(x) for x in manifest.get('minimum_python','3.11').split('.')[:2])
 if sys.version_info[:2]<minimum:raise ValueError('Prepare Python '+manifest['minimum_python']+' antes de atualizar.')
 digest=manifest.get('files',{}).get('tools/update_local.py','')
 if not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Atualizador não declarado no manifesto.')
 code=content('tools/update_local.py')
 if len(code)>2*1024*1024 or hashlib.sha256(code).hexdigest()!=digest:raise ValueError('A cópia do atualizador não confere; código ativo ficou intacto.')
 ast.parse(code,filename='update_local.py')
 directory=engine/'.factory/bootstrap'/revision
 if not directory.resolve().is_relative_to(engine) or any(p.is_symlink() for p in (directory,*directory.parents) if p.is_relative_to(engine) and p!=engine):raise ValueError('Atalho inválido no destino temporário.')
 directory.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=directory)
 try:
  with os.fdopen(fd,'wb') as stream:stream.write(code);stream.flush();os.fsync(stream.fileno())
  target=directory/'update_local.py';os.replace(name,target)
 finally:Path(name).unlink(missing_ok=True)
 return {'ok':True,'updater':str(target),'engine':str(engine),'revision':revision,'sha256':digest,'active_code_unchanged':True}


def execute(root,check=False,apply=False):
 receipt=prepare(root);command=[sys.executable,receipt['updater'],'--root',receipt['engine']]
 if check:command.append('--check')
 elif apply:command.append('--apply')
 # The outer assistant tool yields while download/validation is running.
 result=subprocess.run(command,capture_output=True,text=True,timeout=600)
 try:output=json.loads(result.stdout)
 except (json.JSONDecodeError,ValueError):raise ValueError('O atualizador não retornou um recibo válido; revisar a operação antes de continuar.')
 output['bootstrap_revision']=receipt['revision'];return output

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--check',action='store_true');p.add_argument('--apply',action='store_true');p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
 try:
  result=prepare(a.root) if a.prepare_only else execute(a.root,a.check,a.apply)
  print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result.get('ok') else 2)
 except (ValueError,OSError,subprocess.SubprocessError) as exc:
  print(json.dumps({'ok':False,'status':'failed','message':str(exc)},ensure_ascii=False));raise SystemExit(2)
