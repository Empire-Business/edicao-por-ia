#!/usr/bin/env python3
"""Transactional code-only updates from a pinned GitHub commit or an offline package.

User data is never replaced. Conflicts leave the active version untouched; local code has
three-way merge support when Git is available. Every applied file has a verified backup and
write-ahead receipt. Removed pristine code is retired; unknown/user files are never deleted.
This bootstrap uses only the Python standard library and does not import the running engine.
"""
from __future__ import annotations
import argparse,ast,base64,hashlib,json,os,re,shutil,sqlite3,stat,subprocess,tempfile,time,urllib.request,urllib.error,uuid,zipfile
from pathlib import Path,PurePosixPath

PACKAGE='claude-video-factory'
PROTECTED=('.factory/','context/','jobs/','sources/repos/','sources/reference-material/','arquivo/','prototipos/','.venv/','node_modules/')
JOB_FILES={'jobs/JOB_SCHEMA.json','jobs/EDL_SCHEMA.json','jobs/INTAKE_TEMPLATE.json','jobs/REFERENCE_SCRIPT_TEMPLATE.json','jobs/REFERENCE_GUIDED_JOB_TEMPLATE.yaml','jobs/PROTECTED_RANGES_TEMPLATE.json','jobs/JOB_TEMPLATE.yaml'}
SURFACE_FILES={'.factory-root.json','00 - COMECE AQUI.html','03 - Ajuda/AJUDA.html','factory.py','README.md','03 - Ajuda/ATUALIZAR SEM PERDER TRABALHOS.html','AGENTS.md','CLAUDE.md','.gitignore'}
# Accepted only when retiring/rolling back an older manifest, never in a new release.
RETIRED_SURFACE_FILES={'@surface/Atualizar Fábrica.command','@surface/Atualizar Fábrica.cmd','@surface/Atualizar Fábrica.sh','@surface/ATUALIZACAO.md','@surface/CHANGELOG.md'}
MAX_ARCHIVE=1024*1024*1024


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
 return h.hexdigest()


def locate(root):
 root=Path(root).resolve();engine=root/'99 - Sistema'
 return (engine,root) if engine.is_dir() else (root,root.parent if root.name=='99 - Sistema' else root)


def safe_relative(name):
 if not isinstance(name,str) or not name or '\\' in name or ':' in name or name.startswith('/') or any(x in ('','.','..') for x in name.split('/')):raise ValueError('Caminho inválido no pacote.')
 return name


def allowed(name):
 safe_relative(name)
 if name in RETIRED_SURFACE_FILES:return True
 if name.startswith('@surface/'):
  return name[len('@surface/'):] in SURFACE_FILES
 if name in JOB_FILES:return True
 if name.startswith(PROTECTED) or any(x in name for x in ('.sqlite','.env','.local.json','CHAVES DAS INTEGRAÇÕES')):return False
 if name.startswith(('.agents/skills/','.claude/agents/','.claude/skills/','.codex/agents/')):return True
 if name in ('.gitignore','.claude/settings.json','.codex/config.toml'):return True
 if name.startswith(('tools/','method/','workflows/','patterns/','motion/','studio/','adapters/','examples/','visual/','assets/','config/','memory/','tests/')):return not any(p in ('node_modules','.venv','__pycache__') for p in name.split('/'))
 return '/' not in name and Path(name).suffix.lower() in ('.md','.json','.txt','.py') and not name.startswith('.') or name=='VERSION'


def target_path(engine,surface,name):
 safe_relative(name)
 if name.startswith('@surface/'):base=surface;name=name[len('@surface/'):]
 elif name=='.gitignore' or name.startswith(('.agents/','.claude/','.codex/')):base=surface
 else:base=engine
 target=base/name
 if not target.resolve().is_relative_to(base.resolve()) or any(p.is_symlink() for p in (target,*target.parents) if p!=base and p.is_relative_to(base)):raise ValueError('Atalho ou caminho escapando da instalação.')
 return target


def atomic(path,content):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
  os.replace(tmp,path)
 finally:Path(tmp).unlink(missing_ok=True)


def json_write(path,data):atomic(path,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())


def validate_manifest(manifest):
 if manifest.get('package')!=PACKAGE or not isinstance(manifest.get('files'),dict):raise ValueError('Pacote de atualização inválido.')
 minimum=tuple(int(v) for v in manifest.get('minimum_python','3.9').split('.')[:2])
 if sys.version_info[:2]<minimum:raise ValueError('Prepare Python '+manifest['minimum_python']+' ou mais recente antes de atualizar; a pasta não foi alterada.')
 if int(manifest.get('release_schema',1))>2:raise ValueError('Este pacote exige um atualizador mais recente; a instalação não foi alterada.')
 for name,digest in manifest['files'].items():
  if name in RETIRED_SURFACE_FILES or not allowed(name) or not re.fullmatch(r'[0-9a-f]{64}',digest):raise ValueError('O pacote tenta substituir dados pessoais ou contém um caminho inválido: '+name)
 migrations=manifest.get('migrations',[])
 if any(step not in ('initialize-design-v2','refresh-guides-v2') for step in migrations):raise ValueError('Migração desconhecida: a atualização foi bloqueada antes de alterar arquivos.')
 return manifest


def package_files(source,manifest):
 source_engine,source_surface=locate(source);files={}
 for name,digest in manifest['files'].items():
  file=target_path(source_engine,source_surface,name)
  if not file.is_file() or sha(file)!=digest:raise ValueError('Arquivo do pacote não confere: '+name)
  files[name]=file.read_bytes()
 return files


def record_base(root):
 engine,surface=locate(root);path=engine/'PACKAGE_MANIFEST.json'
 if not path.exists():return
 manifest=json.loads(path.read_text())
 for name,digest in manifest.get('files',{}).items():
  if not allowed(name):continue
  current=target_path(engine,surface,name)
  if current.is_file() and sha(current)==digest:atomic(engine/'.factory/update-base'/digest,current.read_bytes())


def merge_local(engine,local,trusted,incoming):
 base=engine/'.factory/update-base'/str(trusted)
 if not base.exists() or not shutil.which('git') or b'\0' in incoming:return None
 directory=engine/'.factory/updates/merge-work';directory.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=directory);os.close(fd);new=Path(name)
 try:
  new.write_bytes(incoming)
  merged=subprocess.run(['git','merge-file','-p',str(local),str(base),str(new)],capture_output=True,timeout=15)
  return merged.stdout if merged.returncode==0 else None
 finally:new.unlink(missing_ok=True)


def plan(engine,surface,manifest,files):
 installed=engine/'PACKAGE_MANIFEST.json';old=json.loads(installed.read_text()) if installed.exists() else {'files':{}}
 changes=[];conflicts=[];preserved=[]
 for name,content in files.items():
  if name in ('.claude/settings.json','.codex/config.toml') or name=='@surface/.factory-root.json' and (surface/'.factory-root.json').exists():preserved.append(name);continue
  path=target_path(engine,surface,name);before=sha(path) if path.exists() else None;after=hashlib.sha256(content).hexdigest()
  if before==after:continue
  trusted=old.get('files',{}).get(name)
  if before is not None and before!=trusted:
   merged=merge_local(engine,path,trusted,content)
   if merged is None:conflicts.append(name)
   else:files[name]=merged;after=hashlib.sha256(merged).hexdigest()
  changes.append({'path':name,'before':before,'after':after,'action':'write'})
 for name,digest in old.get('files',{}).items():
  if name in files or not allowed(name) or name in ('.claude/settings.json','.codex/config.toml'):continue
  path=target_path(engine,surface,name)
  if path.is_file() and sha(path)==digest:changes.append({'path':name,'before':digest,'after':None,'action':'retire'})
  elif path.exists():preserved.append(name)
 return {'ok':True,'status':'preview','version':manifest['version'],'changes':changes,'conflicts':conflicts,'preserved_local_files':preserved,'user_data_changed':False}


def busy(engine):
 state=engine/'.factory/state.sqlite3'
 if not state.exists():return False
 with sqlite3.connect(state.as_uri()+'?mode=ro',uri=True) as db:
  try:return bool(db.execute("SELECT 1 FROM calls WHERE status='running' LIMIT 1").fetchone())
  except sqlite3.OperationalError:return False


def restore(engine,surface,receipt,path):
 # Never reverse a file edited after the update, and never touch project data.
 conflicts=[]
 for item in receipt['applied']:
  current=target_path(engine,surface,item['path']);actual=sha(current) if current.exists() else None
  if actual not in (item['before'],item['after']):conflicts.append(item['path'])
 if conflicts:return {'ok':False,'status':'rollback_conflict','conflicts':conflicts}
 for item in reversed(receipt['applied']):
  current=target_path(engine,surface,item['path'])
  if item['before'] is None:current.unlink(missing_ok=True)
  else:atomic(current,(path/'before'/item['path']).read_bytes())
 receipt['status']='rolled_back';json_write(path/'receipt.json',receipt)
 return {'ok':True,'status':'rolled_back','receipt_id':receipt['id'],'user_data_changed':False}


def snapshot_migration_data(engine,surface,backup):
    paths=[engine/'context/catalog/registry.json',engine/'.factory/format-folders.json']
    for name in ('04 - Formatos','05 - IDs Visuais'):
        directory=surface/name
        if directory.exists():paths.extend(p for p in directory.rglob('*.html') if not p.is_symlink())
    saved=[]
    for path in paths:
        if not path.exists():continue
        relative=path.relative_to(surface).as_posix() if path.is_relative_to(surface) else path.relative_to(engine).as_posix()
        atomic(backup/'data-before'/relative,path.read_bytes());saved.append(relative)
    directories={name:sorted(p.name for p in (engine/name).iterdir() if p.is_dir()) if (engine/name).exists() else [] for name in ('context/clients','context/visual-identities')}
    guide_names={name:[p.name for p in (surface/name).iterdir() if p.is_dir() and not p.is_symlink()] if (surface/name).exists() else [] for name in ('04 - Formatos','05 - IDs Visuais')}
    return {'files':saved,'directories':directories,'guide_directories':guide_names,'surface_is_engine':surface==engine}


def restore_migration_data(engine,surface,backup,snapshot):
    base=engine if snapshot.get('surface_is_engine') else surface
    old_registry_file=(engine/'.factory/format-folders.json').relative_to(base).as_posix()
    old_registry_path=backup/'data-before'/old_registry_file
    current_registry_path=engine/'.factory/format-folders.json'
    if old_registry_path.exists() and current_registry_path.exists():
        old_registry=json.loads(old_registry_path.read_text());current_registry=json.loads(current_registry_path.read_text())
        current_catalog=engine/'context/catalog/registry.json';definitions=json.loads(current_catalog.read_text()).get('formats',[]) if current_catalog.exists() else []
        for old_label,old_store in old_registry.items():
            stores={old_store}|{f['memory_store'] for f in definitions if old_store in f.get('legacy_stores',[])}
            match=next((label for label,store in current_registry.items() if store in stores),None)
            old_folder=surface/'04 - Formatos'/old_label
            if match and match!=old_label and not old_folder.exists():
                new_folder=surface/'04 - Formatos'/match
                if new_folder.is_dir() and not new_folder.is_symlink():new_folder.rename(old_folder)
    for name,previous in snapshot.get('guide_directories',{}).items():
        directory=surface/name
        if not directory.exists():continue
        for folder in list(directory.iterdir()):
            if folder.name in previous or not folder.is_dir() or folder.is_symlink():continue
            destination=backup/'migration-created'/name/folder.name;destination.parent.mkdir(parents=True,exist_ok=True);folder.rename(destination)
    for relative in snapshot['files']:atomic(base/relative,(backup/'data-before'/relative).read_bytes())
    for name,previous in snapshot['directories'].items():
        directory=engine/name
        if not directory.exists():continue
        for folder in list(directory.iterdir()):
            if folder.name in previous or not folder.is_dir() or folder.is_symlink():continue
            if name=='context/clients' and not folder.name.startswith('format-f'):continue
            destination=backup/'migration-created'/name/folder.name;destination.parent.mkdir(parents=True,exist_ok=True);folder.rename(destination)


def install(root,source,apply=False):
 engine,surface=locate(root);source_engine,_=locate(source)
 manifest=validate_manifest(json.loads((source_engine/'PACKAGE_MANIFEST.json').read_text()))
 files=package_files(source,manifest)
 if engine==surface and '@surface/factory.py' in files and source_engine.name=='99 - Sistema':raise ValueError('Instalação com layout antigo: o assistente deve aplicar a migração de pasta com tools/reorganize_project.py da versão nova antes de atualizar. Nenhum dado foi alterado.')
 remote_files=dict(files);result=plan(engine,surface,manifest,files)
 for name,content in files.items():
  if name.endswith('.py'):ast.parse(content,filename=name)
 if not apply:return result
 if busy(engine):return {**result,'ok':False,'status':'busy','message':'Uma edição está em execução. Retome a atualização quando ela terminar.'}
 id='update-'+uuid.uuid4().hex[:12];backup=engine/'.factory/updates'/id;backup.mkdir(parents=True)
 if result['conflicts']:
  for name in result['conflicts']:atomic(backup/'incoming'/name,files[name])
  json_write(backup/'receipt.json',{**result,'id':id,'status':'needs_merge','applied':[]})
  return {**result,'ok':False,'status':'needs_merge','receipt_id':id,'message':'Sua versão ficou intacta. O assistente deve revisar as personalizações usando os arquivos novos guardados no recibo, antes de ativar a atualização.'}
 lock=engine/'.factory/update.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
 migration_snapshot=snapshot_migration_data(engine,surface,backup) if manifest.get('migrations') else None
 receipt={**result,'id':id,'status':'applying','applied':[],'migrations':manifest.get('migrations',[])}
 # Include package baseline in the rollback, rather than resetting local history.
 baseline=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();files['PACKAGE_MANIFEST.json']=baseline
 changes=result['changes']+[{'path':'PACKAGE_MANIFEST.json','before':sha(engine/'PACKAGE_MANIFEST.json') if (engine/'PACKAGE_MANIFEST.json').exists() else None,'after':hashlib.sha256(baseline).hexdigest(),'action':'write'}]
 json_write(backup/'receipt.json',receipt)
 try:
  for item in changes:
   path=target_path(engine,surface,item['path']);actual=sha(path) if path.exists() else None
   if actual!=item['before']:raise ValueError('Um arquivo mudou durante a atualização; operação cancelada.')
   if item['before'] is not None:atomic(backup/'before'/item['path'],path.read_bytes())
   receipt['applied'].append(item);json_write(backup/'receipt.json',receipt)
   if item['action']=='retire':path.unlink()
   else:atomic(path,files[item['path']])
  if manifest.get('migrations'):
   migration=engine/'tools/post_update.py'
   if not migration.exists():raise ValueError('O pacote declarou migrações sem um executor.')
   process=subprocess.run([sys.executable,str(migration),'--root',str(engine)],capture_output=True,text=True,timeout=60)
   if process.returncode:raise ValueError('A migração falhou; o código foi recuperado, e os dados originais foram preservados.')
  for name,content in remote_files.items():atomic(engine/'.factory/update-base'/hashlib.sha256(content).hexdigest(),content)
  receipt['status']='installed';json_write(backup/'receipt.json',receipt)
  return {**result,'status':'installed','receipt_id':id,'message':'Atualização concluída. Trabalhos, memória, IDs visuais, chaves e configurações locais foram preservados.'}
 except BaseException:
  if migration_snapshot:restore_migration_data(engine,surface,backup,migration_snapshot)
  recovered=restore(engine,surface,receipt,backup)
  if not recovered['ok']:
   receipt['status']='needs_recovery';receipt['recovery_conflicts']=recovered.get('conflicts',[]);json_write(backup/'receipt.json',receipt)
  raise
 finally:
  if receipt['status']!='needs_recovery':lock.unlink(missing_ok=True)


def rollback(root,receipt_id):
 if not re.fullmatch(r'update-[0-9a-f]{12}',receipt_id):raise ValueError('Recibo inválido.')
 engine,surface=locate(root);path=engine/'.factory/updates'/receipt_id
 receipt=json.loads((path/'receipt.json').read_text());result=restore(engine,surface,receipt,path)
 if result['ok']:(engine/'.factory/update.lock').unlink(missing_ok=True)
 return result


def remote_json(repo,path):
 if shutil.which('gh'):
  response=subprocess.run(['gh','api',f'repos/{repo}'+('/'+path if path else '')],capture_output=True,text=True,timeout=30)
  if response.returncode:raise ValueError('Não foi possível acessar o GitHub. Verifique conexão e acesso à conta; nenhuma chave foi lida ou impressa.')
  return json.loads(response.stdout)
 request=urllib.request.Request('https://api.github.com/repos/'+repo+('/'+path if path else ''),headers={'User-Agent':'VideoFactory-Updater'})
 with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)


def github_package(root,check_only=False):
 engine,_=locate(root);configuration=engine/'config/update-source.json'
 config=json.loads(configuration.read_text());repo=config['repository'];branch=config.get('branch','main')
 if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo) or branch!='main':raise ValueError('Origem de atualização inválida.')
 metadata=remote_json(repo,'')
 if config.get('repository_id') is not None and metadata.get('id')!=config['repository_id']:raise ValueError('O endereço aponta para outro repositório; atualização bloqueada.')
 commit=remote_json(repo,'commits/main')['sha']
 if not re.fullmatch(r'[a-f0-9]{40}',commit):raise ValueError('Revisão inválida do GitHub.')
 from urllib.parse import quote
 encoded_path=quote('99 - Sistema/PACKAGE_MANIFEST.json',safe='/')
 remote=remote_json(repo,f'contents/{encoded_path}?ref={commit}');manifest=validate_manifest(json.loads(base64.b64decode(remote['content'])))
 installed_path=engine/'PACKAGE_MANIFEST.json'
 if not installed_path.exists():raise ValueError('Versão antiga ou sem manifesto confiável. Siga 99 - Sistema/ATUALIZACAO.md da versão nova e use recuperação em uma pasta separada; não sincronize por cima.')
 installed=json.loads(installed_path.read_text())
 if check_only:
  _,surface=locate(root)
  local_changes=[name for name,digest in installed.get('files',{}).items() if allowed(name) and (not target_path(engine,surface,name).is_file() or sha(target_path(engine,surface,name))!=digest)]
  return {'ok':True,'status':'up_to_date' if installed.get('files')==manifest['files'] else 'update_available','version':manifest['version'],'revision':commit,'repository':repo,'local_changes':local_changes}
 stage=engine/'.factory/updates'/('download-'+uuid.uuid4().hex[:12]);stage.mkdir(parents=True)
 archive=stage/'source.zip'
 if shutil.which('gh'):
  with archive.open('wb') as stream:result=subprocess.run(['gh','api',f'repos/{repo}/zipball/{commit}'],stdout=stream,stderr=subprocess.PIPE,timeout=300)
  if result.returncode:raise ValueError('Não foi possível baixar a atualização do GitHub.')
 else:
  request=urllib.request.Request(f'https://api.github.com/repos/{repo}/zipball/{commit}',headers={'User-Agent':'VideoFactory-Updater'})
  with urllib.request.urlopen(request,timeout=30) as response,archive.open('wb') as output:
   total=0
   for block in iter(lambda:response.read(1024*1024),b''):
    total+=len(block)
    if total>MAX_ARCHIVE:raise ValueError('Pacote grande demais; atualização interrompida sem alterar dados.')
    output.write(block)
 if archive.stat().st_size>MAX_ARCHIVE:raise ValueError('Pacote grande demais.')
 package=stage/'package';package_engine=package/'99 - Sistema';package_engine.mkdir(parents=True)
 # Extract only declared code, never extractall. Private/unlisted ZIP contents stay unread.
 with zipfile.ZipFile(archive) as zip:
  members={m.filename:m for m in zip.infolist()};prefix=next(iter(members)).split('/')[0]+'/'
  for name,digest in manifest['files'].items():
   if name.startswith('@surface/'):relative=name[len('@surface/'):]
   elif name=='.gitignore' or name.startswith(('.agents/','.claude/','.codex/')):relative=name
   else:relative='99 - Sistema/'+name
   info=members.get(prefix+relative)
   if not info or stat.S_ISLNK(info.external_attr>>16) or info.file_size>100*1024*1024:raise ValueError('Arquivo ausente, grande ou atalho inválido no pacote.')
   content=zip.read(info)
   if hashlib.sha256(content).hexdigest()!=digest:raise ValueError('Integridade da atualização não confere.')
   atomic(target_path(package_engine,package,name),content)
 json_write(package_engine/'PACKAGE_MANIFEST.json',manifest);archive.unlink()
 return package


def human_message(result):
 status=result.get('status');version=result.get('version','')
 if status=='installed':message='Atualização concluída. Versão '+version+'. Trabalhos, memória, IDs, configurações e gastos foram preservados.'
 elif status=='up_to_date':message='O pacote instalado corresponde à versão '+version+' do GitHub.'
 elif status=='update_available':message='Há uma atualização disponível: versão '+version+'.'
 elif status=='needs_merge':message='A atualização NÃO foi aplicada: existem alterações locais de código que precisam de revisão. Sua versão ativa ficou intacta.'
 else:message=result.get('message','A atualização precisa de revisão.')
 if result.get('local_changes'):message+=' Há '+str(len(result['local_changes']))+' arquivos locais diferentes ou ausentes. Peça à IA para revisar; a igualdade do manifesto não prova que esses arquivos estejam íntegros.'
 if result.get('receipt_id'):message+='\nRecibo: '+result['receipt_id']
 if not result.get('ok'):message+='\nAbra 03 - Ajuda/ATUALIZAR SEM PERDER TRABALHOS.html ou peça à IA para consultar 99 - Sistema/ATUALIZACAO.md da versão nova. Para versões antigas ou pastas misturadas, peça recuperação em uma pasta nova. Não apague seus trabalhos.'
 return message


def main():
 import sys
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--from',dest='source',type=Path);parser.add_argument('--check',action='store_true');parser.add_argument('--apply',action='store_true');parser.add_argument('--rollback');parser.add_argument('--human',action='store_true')
 args=parser.parse_args()
 try:
  result=rollback(args.root,args.rollback) if args.rollback else install(args.root,args.source,args.apply) if args.source else github_package(args.root,True) if args.check else install(args.root,github_package(args.root),args.apply)
  if args.human:print(human_message(result))
  else:print(json.dumps(result,ensure_ascii=False,indent=2))
  return 0 if result.get('ok') else 2
 except (ValueError,OSError,subprocess.SubprocessError,urllib.error.URLError,zipfile.BadZipFile) as exc:
  result={'ok':False,'status':'failed','message':str(exc),'user_data_not_replaced':True}
  print(human_message(result) if args.human else json.dumps(result,ensure_ascii=False));return 2

import sys
if __name__=='__main__':raise SystemExit(main())
