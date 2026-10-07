#!/usr/bin/env python3
"""Maintainer export of explicitly selected format references for distribution.

This is not run on end-user installations. Originals, jobs and memory stay untouched.
Only reference directories and named reference exports are read; never credentials/stores.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,zipfile
from pathlib import Path
from update_local import atomic,json_write,sha
from project_layout import engine_root,surface_root

TEXT={'.md','.json','.html','.csv','.txt','.svg'}
EXT=TEXT|{'.png','.jpg','.jpeg','.webp','.mp4','.mp3','.wav','.zip'}
STORE_REFS={
 'F01':['context/clients/bruno-wpp/DIRECTION-v1.md','context/clients/bruno-wpp/assets/identity/bruno-profile-v1.jpeg'],
 'F03':['context/clients/brunoguzela1/references'],
 'F04':['context/clients/brunoguzela2/references','context/clients/brunoguzela2/assets/brand-board.svg','context/clients/brunoguzela2/brand-direction.md'],
 'F05':['context/clients/empire2/references','context/clients/empire2/brand-direction.md'],
 'F06':['context/clients/htai1/references'],
 'F07':['sources/reference-material/clients-boards'],
 'F08':['context/clients/omnxgt3/assets/music'],
 'F09':['sources/reference-material/attendance-boards','context/clients/omnxsdrai/assets/music'],
 'F10':['context/clients/omnxsell/assets/music'],
 'F11':['sources/reference-material/form-boards'],
 'F12':['context/clients/documentario-visual-animado/references/greco-v1','context/clients/documentario-visual-animado/DIRECTION-v1.md'],
}


def clean_text(data,mapping):
 def visit(v):
  if isinstance(v,str):
   for source,target in sorted(mapping.items(),key=lambda x:-len(x[0])):v=v.replace(source,target)
   # Evidence bytes remain in the private source. Distributed metadata cannot depend on it.
   if v.startswith(('workspace://','/Volumes/','/Users/','/private/','/var/')):return None
   return v
  if isinstance(v,list):return [visit(x) for x in v]
  if isinstance(v,dict):return {k:visit(x) for k,x in v.items()}
  return v
 return visit(data)


def export(root):
 root=engine_root(root);surface=surface_root(root)
 defaults=json.loads((root/'config/design-defaults.json').read_text());local_path=root/'context/catalog/examples.json'
 local=json.loads(local_path.read_text()) if local_path.exists() else {}
 target=root/'examples/reference-library';target.mkdir(exist_ok=True)
 index={'version':1,'scope':'author_published_stock_references','authorization':'User explicitly requires all format references on GitHub.','formats':{},'files':{}}
 plans=[];seen=set()
 for item in defaults['formats']:
  code=item['code'];group={'code':code,'name':item['name'],'uid':item['uid'],'references':[],'missing_sources':[]}
  index['formats'][code]=group
  for slot,source_name in enumerate(STORE_REFS.get(code,[]),1):
   source=root/source_name
   if not source.exists():group['missing_sources'].append(source_name);continue
   paths=[x for x in source.rglob('*') if x.is_file()] if source.is_dir() else [source]
   for source_file in sorted(paths):
    if source_file.is_symlink() or source_file.name.startswith('.') or source_file.suffix.lower() not in EXT:continue
    if any(p in ('.env','.git','node_modules','.venv') for p in source_file.parts) or source_file.suffix.lower() in ('.key','.pem'):raise ValueError('Credential/runtime path rejected.')
    name=source_file.relative_to(source).as_posix() if source.is_dir() else source_file.name
    dest=f'examples/reference-library/{code}/collection-{slot:02d}/'+name
    kind='reference_analysis' if source_file.suffix.lower() in TEXT else 'original_reference_video' if source_file.suffix.lower()=='.mp4' else 'music_reference' if source_file.suffix.lower() in ('.mp3','.wav') else 'visual_reference' if source_file.suffix.lower() in ('.png','.jpg','.jpeg','.webp') else 'reference_material'
    plans.append((source_file,dest,group,kind,None));seen.add((code,str(source_file)))
  for number,entry in enumerate(local.get(code,[]),1):
   source=root/entry['path']
   if source.is_file():plans.append((source,f'examples/reference-library/{code}/example-{number:02d}.jpg',group,'actual_reference_image',entry.get('caption')))
   if entry.get('source_video'):
    video=surface/entry['source_video']
    if not video.resolve().is_relative_to(surface) or not video.is_file():group['missing_sources'].append('reference video for example '+str(number));continue
    if (code,str(video)) not in seen:
     plans.append((video,f'examples/reference-library/{code}/video-example-{number:02d}.mp4',group,'actual_reference_video',None));seen.add((code,str(video)))
 # A UI motion preview is explicitly marked as preview, never presented as approved.
 preview=root/'jobs/omnx-type-motion/renders/omnx-type-motion_9x16_omnxtype_PREVIEW_V1.mp4'
 if preview.is_file():plans.append((preview,'examples/reference-library/F11/interface-preview.mp4',index['formats']['F11'],'existing_motion_preview',None))
 mapping={}
 for source,dest,group,kind,caption in plans:
  mapping[str(source.resolve())]=dest;mapping['workspace://'+source.relative_to(surface).as_posix()]=dest
  if source.is_relative_to(root):mapping[source.relative_to(root).as_posix()]=dest
 for source,dest,group,kind,caption in plans:
  if source.stat().st_size>100*1024*1024:raise ValueError('Reference exceeds GitHub file limit; use a separate asset release before publishing: '+group['code'])
  if source.suffix.lower()=='.zip':
   with zipfile.ZipFile(source) as archive:
    for member in archive.infolist():
     parts=Path(member.filename).parts
     if member.filename.startswith('/') or '..' in parts or any(p.startswith('.env') or p in ('.git','node_modules') for p in parts):raise ValueError('Unsafe contents in reference archive.')
  output=root/dest
  if source.suffix.lower() in TEXT:
   value=source.read_text(encoding='utf-8-sig')
   if source.suffix.lower()=='.json':value=json.dumps(clean_text(json.loads(value),mapping),ensure_ascii=False,indent=2)+'\n'
   else:
    for original,replacement in sorted(mapping.items(),key=lambda x:-len(x[0])):value=value.replace(original,replacement)
    value=re.sub(r'workspace://[^\s`"<>]+','[origem preservada no acervo privado]',value)
    value=re.sub(r'/(?:Volumes|Users)/[^\s`"<>]+','[origem preservada no acervo privado]',value)
   atomic(output,value.encode())
  else:
   output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,output)
   if sha(output)!=sha(source):raise ValueError('Reference copy checksum differs.')
  record={'path':dest,'kind':kind,'sha256':sha(output),'bytes':output.stat().st_size,'source_sha256':sha(source)}
  if caption:record['caption']=caption
  group['references'].append(record);index['files'][dest]=record['sha256']
 for group in index['formats'].values():
  code=group['code'];readme=target/code/'README.md';readme.parent.mkdir(exist_ok=True)
  lines=['# '+code+' — '+group['name'],'','Referências históricas para entender a edição. Pessoas, marcas, cores, fontes e música destes exemplos não são escolhas automáticas para um novo vídeo. Escolha F e ID; logotipos só entram quando pedidos.','', 'Os arquivos são cópias de referências selecionadas para distribuição pelo autor. Trabalhos, bancos de memória e chaves não fazem parte desta biblioteca.','', '## Materiais disponíveis','']
  for ref in group['references']:
   relative=Path(ref['path']).relative_to(Path('examples/reference-library')/code).as_posix()
   lines.append('- ['+relative+']('+relative.replace(' ','%20')+') — '+ref['kind'])
  if not group['references']:lines.append('Nenhum material real disponível no acervo selecionado. Há uma ilustração e a receita do formato, sem alegação de execução comprovada.')
  if not any(r['kind'] in ('actual_reference_video','original_reference_video') for r in group['references']):lines+=['','Não há um vídeo completo de referência cadastrado neste conjunto. Fotos, pranchas e prévias são identificadas pelo tipo.']
  readme.write_text('\n'.join(lines)+'\n');index['files']['examples/reference-library/'+code+'/README.md']=sha(readme)
 (target/'README.md').write_text('# Biblioteca de referências dos formatos\n\nTodos os formatos distribuídos têm seu próprio índice F. A biblioteca acompanha a instalação e a atualização. Ela não impõe identidade visual, marca, pessoa ou logo. Ilustrações e materiais reais são identificados separadamente.\n\n'+'\n'.join(f"- [{x['code']} — {x['name']}]({x['code']}/README.md)" for x in index['formats'].values())+'\n')
 index['files']['examples/reference-library/README.md']=sha(target/'README.md')
 json_write(root/'config/reference-library.json',index)
 receipt={'ok':True,'format_count':len(index['formats']),'reference_files':len(index['files']),'bytes':sum((root/name).stat().st_size for name in index['files']),'source_originals_preserved':True,'private_stores_and_jobs_not_published':True}
 json_write(root/'.factory/publication/reference-library.json',receipt)
 return receipt

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();print(json.dumps(export(a.root),ensure_ascii=False,indent=2))
