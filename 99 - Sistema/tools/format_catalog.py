#!/usr/bin/env python3
"""Numbered editing-format catalogue, independent from visual identities."""
from __future__ import annotations
import argparse,html,json,re,sqlite3,sys,unicodedata
from pathlib import Path
from urllib.parse import quote
from client_memory import Memory,ROOT,slug,text
from project_layout import engine_root,surface_root
from design_catalog import catalogue,register_format,editing_format,save,validate_example_url,retire_format,require_publisher,retirement_path
HUB=''
STYLE='''body{margin:0;background:#f7f6f3;color:#2f3437;font:18px/1.65 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif}main{max-width:940px;margin:auto;padding:40px 24px 64px}h1{font:normal 42px/1.15 Georgia,serif}h2{font-size:23px}section{border-bottom:1px solid #ddd;padding:20px 0}a{color:#315636}table{border-collapse:collapse;width:100%;background:#fff}th,td{text-align:left;padding:14px;border-bottom:1px solid #ddd}.note{font-size:16px;color:#5d5a54}a:focus-visible{outline:3px solid #956400;outline-offset:4px}@media(max-width:600px){table,tbody,tr,td{display:block}thead{display:none}tr{border-bottom:1px solid #ddd}td{border:0;padding:8px 14px}}'''


def page(title,body):return '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style><main>'+body+'</main></html>\n'


def read_name(memory,id):
 with sqlite3.connect(memory.path(id).as_uri()+'?mode=ro',uri=True) as db:row=db.execute("SELECT value FROM meta WHERE key='name'").fetchone()
 if not row or not row[0]:raise ValueError('Nome ausente no formato '+id)
 return row[0]


def formats(root):
 root=engine_root(root);memory=Memory(root);data=catalogue(root);items=[];problems=[]
 if data['formats']:
  for entry in data['formats']:
   try:
    name=read_name(memory,entry['memory_store'])
    items.append({**entry,'id':entry['memory_store'],'name':name})
   except (ValueError,OSError,sqlite3.Error) as exc:problems.append(str(exc))
  return items,problems
 retired={v for x in data.get('retired_formats',[]) for v in [x['memory_store'],*x.get('legacy_stores',[])]}
 directory=root/'context/clients'
 if directory.exists():
  for p in sorted(directory.iterdir()):
   if p.name in retired or p.name.startswith(('_','.')) or not p.is_dir() or not (p/'memory.sqlite3').exists():continue
   if p.is_symlink():problems.append(p.name+': atalho não consultado.');continue
   try:
    id=slug(p.name);entry=register_format(root,id,read_name(memory,id),legacy=True)
    items.append({**entry,'id':id})
   except (ValueError,OSError,sqlite3.Error) as exc:problems.append(str(exc))
 return items,problems


def id_for(name):
 name=text(name,'Nome do formato',50)
 value=re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()).strip('-')[:80]
 if not value:raise ValueError('Escolha um nome com letras ou números.')
 return slug(value)


def create(root,name,format_id=None,example_url=None,official=False):
 root=engine_root(root);name=text(name,'Nome simples do formato',50);id=slug(format_id) if format_id else id_for(name);m=Memory(root)
 if official:require_publisher(root)
 if m.path(id).exists():
  if read_name(m,id)!=name:raise ValueError('ID já usado por outro nome; o cadastro existente foi preservado.')
  entry=editing_format(root,id);status='existing'
 else:
  example_url=validate_example_url(example_url)
  # Validate the required reference before creating a new memory database.
  m.init(id,name);entry=register_format(root,id,name,example_url=example_url,official=official);status='created'
  entry['validation_status']='reference_analysis_pending'
  data=catalogue(root)
  for item in data['formats']:
   if item['memory_store']==id:item['validation_status']='reference_analysis_pending'
  save(root,data)
 return {'status':status,'format':id,'code':entry['code'],'name':name,'example_url':entry.get('example_url'),'store':str(m.path(id).relative_to(root)),'verified':read_name(m,id)==name}


def set_recipe(root,format_id,pattern,analysis_path):
 from factory_common import inside,sha,atomic_json,workspace_lock
 root=engine_root(root);entry=editing_format(root,format_id)
 if entry.get('validation_status')!='reference_analysis_pending':raise ValueError('Formato consolidado preservado. Uma revisão exige ordem expressa do autor e fluxo próprio, não completar cadastro.')
 if re.fullmatch(r'F[0-9]+',entry['code']):require_publisher(root)
 if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',pattern) or not inside(root,'patterns/'+pattern+'.yaml').is_file():raise ValueError('Informe a receita específica, existente e versionada.')
 source=inside(root,analysis_path);report=json.loads(source.read_text());details=report.get('mechanism_details') or {}
 if report.get('format_uid')!=entry.get('uid') or report.get('example_url')!=entry.get('example_url'):raise ValueError('A análise não corresponde a este cadastro/exemplo.')
 if not all(isinstance(details.get(k),str) and details[k].strip() for k in ('inputs','mechanism','avoid')) or not isinstance(details.get('steps'),list) or not details['steps'] or not all(isinstance(x,str) and x.strip() for x in details['steps']):raise ValueError('Complete o mecanismo e as etapas observadas, sem receita genérica.')
 references=report.get('references') or []
 if not isinstance(references,list) or not references or not report.get('observations'):raise ValueError('A análise precisa das referências locais e observações de cenas realmente inspecionadas.')
 for ref in references:
  path=inside(root,ref['path'])
  if path.suffix.lower() not in ('.mp4','.mov','.jpg','.jpeg','.png') or not path.is_file() or sha(path)!=ref.get('sha256'):raise ValueError('Referência ausente ou não verificada.')
 with workspace_lock(root,'design-catalog'):
  data=catalogue(root);target=next(x for x in data['formats'] if x['uid']==entry['uid'])
  target.update(pattern=pattern,mechanism_details=details,reference_materials=references,validation_status='reference_analyzed',analysis_receipt={'path':str(source.relative_to(root)),'sha256':sha(source)})
  save(root,data)
 receipt={'ok':True,'status':'reference_analyzed','code':entry['code'],'uid':entry['uid'],'pattern':pattern,'analysis_sha256':sha(source),'originals_preserved':True}
 atomic_json(inside(root,'.factory/format-registration/'+entry['uid']+'.json'),receipt)
 refresh(root)
 return receipt


def folder_label(name,format_id):
 label=re.sub(r'[<>:"/\\|?*\x00-\x1f]','-',name).strip(' .')[:100]
 if not label or label.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:label='Formato '+format_id
 return label


def rename(root,format_id,name,reason,token):
 root=engine_root(root);entry=editing_format(root,format_id);m=Memory(root);name=text(name,'Nome simples',50)
 if re.fullmatch(r'F[0-9]+',entry['code']):require_publisher(root)
 items,problems=formats(root)
 if problems:raise ValueError('; '.join(problems))
 if any(x['code']!=entry['code'] and x['name'].casefold()==name.casefold() for x in items):raise ValueError('Outro formato já usa esse nome.')
 target=surface_root(root)/'04 - Formatos'/folder_label(entry['code']+' - '+name,entry['memory_store'])
 registry_path=root/'.factory/format-folders.json';registry=json.loads(registry_path.read_text()) if registry_path.exists() else {}
 if target.exists() and registry.get(target.name)!=entry['memory_store']:raise ValueError('Pasta de destino existente preservada.')
 receipt=m.rename(entry['memory_store'],name,reason,token)
 data=catalogue(root)
 for item in data['formats']:
  if item['code']==entry['code']:item['name']=name
 save(root,data);refresh(root)
 return {**receipt,'code':entry['code'],'folder':str(target.relative_to(surface_root(root)))}


def remove(root,format_id,reason):
 root=engine_root(root);data=catalogue(root)
 entry=next((x for x in [*data['formats'],*data.get('retired_formats',[])] if format_id.casefold() in [x['code'].casefold(),x['memory_store'].casefold(),x['name'].casefold()]),None)
 if not entry:raise ValueError('Formato não encontrado.')
 directory=surface_root(root)/'04 - Formatos'
 source=directory/folder_label(entry['code']+' - '+entry['name'],entry['memory_store'])
 target=retirement_path(root,entry)/'visible-folder'
 if source.exists() and (source.is_symlink() or not source.is_dir() or target.exists()):raise ValueError('Conflito na pasta; nenhum conteúdo foi apagado.')
 result=retire_format(root,entry['code'],reason)
 if source.exists():
  target.parent.mkdir(parents=True,exist_ok=True);source.rename(target)
 refresh(root)
 return {k:v for k,v in result.items() if k!='entry'}|{'archived_folder':str(target.relative_to(root)),'visible_folder_removed':not source.exists()}


def refresh(root):
 root=engine_root(root);surface=surface_root(root);directory=surface/'04 - Formatos';items,problems=formats(root)
 if directory.is_symlink():raise ValueError('A pasta de formatos não pode ser um atalho.')
 registry_path=root/'.factory/format-folders.json'
 if registry_path.is_symlink():raise ValueError('Registro não pode ser um atalho.')
 registry=json.loads(registry_path.read_text()) if registry_path.exists() else {};desired=[]
 for item in items:
  label=folder_label(item['code']+' - '+item['name'],item['id']);target=directory/label
  aliases={item['id'],*item.get('legacy_stores',[])}
  previous=[directory/n for n,id in registry.items() if id in aliases and n!=label and (directory/n).exists()]
  if target.exists() and (target.is_symlink() or not target.is_dir() or registry.get(label) not in aliases):raise ValueError('Pasta existente preservada: '+label)
  if any(p.is_symlink() or not p.is_dir() for p in previous) or len(previous)>1:raise ValueError('Confira as pastas antigas de '+label)
  if previous and target.exists():raise ValueError('Duas pastas do mesmo formato; não serão mescladas.')
  desired.append((item,label,target,previous))
 directory.mkdir(parents=True,exist_ok=True)
 new_registry={}
 for item,label,target,previous in desired:
  if previous:previous[0].rename(target)
  target.mkdir(exist_ok=True);new_registry[label]=item['id'];name=html.escape(item['name']);code=item['code']
  example=item.get('example_url');example_html='<a href="'+html.escape(example,quote=True)+'">Ver exemplo</a>' if example else 'Cadastro anterior à regra: link de exemplo ainda não informado.'
  body='<a href="../00 - LEIA PRIMEIRO.html">Voltar</a><h1>'+code+' — '+name+'</h1><p>'+html.escape(item.get('description') or 'Estilo de edição cadastrado.')+'</p>'
  body+='<p><a href="GUIA%20DA%20EDI%C3%87%C3%83O.html">Ler o guia detalhado da edição</a></p>'
  body+='<section><h2>Como usar</h2><p>Escolha este formato e uma ID visual. Exemplo: <strong>“Use '+code+' com ID03 neste vídeo.”</strong></p><p>Você pode combinar qualquer formato com qualquer ID visual. O formato define cortes, ritmo, cenas e animações. A ID define cores e fontes.</p></section>'
  body+='<section><h2>Exemplo</h2><p>'+example_html+'</p><p>O exemplo orienta a edição; suas cores, fontes, pessoa e logo não são herdadas.</p></section>'
  from format_guides import reference_section
  body+=reference_section(item)
  body+='<section><h2>Onde ficam as regras de verdade?</h2><p><a href="../../99%20-%20Sistema/context/clients/'+quote(item['id'])+'/">Memória de edição</a> e <a href="../../99%20-%20Sistema/patterns/'+quote(item['pattern'])+'.yaml">receita deste formato</a>. A ID visual fica no cadastro separado, em 99 - Sistema/context/visual-identities.</p><p>Peça alterações na conversa; não é preciso editar o banco.</p></section><p>Logos ficam desligadas, exceto quando pedidas para o vídeo.</p>'
  (target/'COMO USAR.html').write_text(page(code+' - '+item['name'],body))
  (target/'ESTILO.html').write_text(page(code+' - '+item['name'],'<a href="COMO USAR.html">Como usar</a><h1>'+code+' — '+name+'</h1><p>'+html.escape(item.get('description',''))+'</p><p>Cores e fontes pertencem à ID visual selecionada, não a este formato.</p>'))
  from format_guides import guide
  (target/'GUIA DA EDIÇÃO.html').write_text(guide(root,item))
 registry_path.parent.mkdir(parents=True,exist_ok=True);registry_path.write_text(json.dumps(new_registry,ensure_ascii=False,indent=2)+'\n')
 guide='<a href="../00 - COMECE AQUI.html">Começo</a><h1>Formatos de edição</h1><p>Primeiro escolha um formato F e uma ID visual ID. Nenhuma dupla é escolhida automaticamente.</p><p><a href="../05%20-%20IDs%20Visuais/00%20-%20LEIA%20PRIMEIRO.html">Ver IDs visuais</a></p><table><thead><tr><th>Código</th><th>Nome</th><th>Edição</th></tr></thead><tbody>'
 for item,label,_,_ in desired:guide+='<tr><td>'+item['code']+'</td><td><a href="'+quote(label,safe='')+'/COMO%20USAR.html">'+html.escape(item['name'])+'</a></td><td>'+html.escape(item.get('description',''))+'</td></tr>'
 guide+='</tbody></table><section><h2>Novo formato</h2><p>Envie um nome simples e um link de exemplo. Seus formatos particulares recebem FP01, FP02 etc. F01, F02 etc. pertencem ao catálogo oficial e são cadastrados apenas pelo autor, no menor número livre. Os modelos atuais mantêm seus nomes e códigos.</p></section><p>Para pedir ajustes, use o código: “No F01, quero cortes mais suaves neste vídeo.” Para cores/fontes: “Na ID03, quero [mudança].”</p>'
 for name in ('00 - LEIA PRIMEIRO.html','01 - GUIA DOS FORMATOS.html'):(directory/name).write_text(page('Formatos de edição',guide))
 from visual_identity import refresh as refresh_visual
 refresh_visual(root)
 return {'ok':not problems,'formats':len(items),'problems':problems,'output':str(directory/'00 - LEIA PRIMEIRO.html'),'folders':[n for _,n,_,_ in desired]}


def interactive(root):
 try:
  name=input('Nome simples do formato (Enter cancela): ').strip()
  if not name:return 0
  example=input('Link de um vídeo de exemplo: ').strip();receipt=create(root,name,example_url=example);refresh(root)
  print('Registro confirmado: '+receipt['code']+' — '+receipt['name']);return 0
 except (ValueError,OSError,EOFError,KeyboardInterrupt) as exc:print('Cadastro não concluído: '+str(exc));return 1


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);commands=parser.add_subparsers(dest='command',required=True)
 commands.add_parser('refresh');commands.add_parser('interactive')
 p=commands.add_parser('create');p.add_argument('--name',required=True);p.add_argument('--format');p.add_argument('--example-url',required=True);p.add_argument('--official',action='store_true',help='Somente na instalação de publicação do autor')
 p=commands.add_parser('remove');p.add_argument('--format',required=True);p.add_argument('--reason',required=True)
 p=commands.add_parser('rename');p.add_argument('--format',required=True);p.add_argument('--name',required=True);p.add_argument('--reason',required=True);p.add_argument('--token',required=True)
 p=commands.add_parser('set-recipe');p.add_argument('--format',required=True);p.add_argument('--pattern',required=True);p.add_argument('--analysis',required=True)
 args=parser.parse_args()
 if args.command=='interactive':return interactive(args.root)
 try:
  result=set_recipe(args.root,args.format,args.pattern,args.analysis) if args.command=='set-recipe' else remove(args.root,args.format,args.reason) if args.command=='remove' else refresh(args.root) if args.command=='refresh' else rename(args.root,args.format,args.name,args.reason,args.token) if args.command=='rename' else create(args.root,args.name,args.format,args.example_url,args.official)
 except (ValueError,OSError,sqlite3.Error) as exc:print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False));return 1
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result.get('ok',True) else 1
if __name__=='__main__':raise SystemExit(main())
