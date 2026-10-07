#!/usr/bin/env python3
"""Independent, numbered visual identities: palette/fonts, never an editing format."""
import argparse,html,json
from pathlib import Path
from urllib.parse import quote
from project_layout import engine_root,surface_root
from design_catalog import catalogue,visual_identity,register_visual,update_visual


def refresh(root):
 from format_catalog import page
 root=engine_root(root);directory=surface_root(root)/'05 - IDs Visuais'
 if directory.is_symlink():raise ValueError('O catálogo de IDs visuais não pode ser um atalho.')
 directory.mkdir(parents=True,exist_ok=True)
 body='<a href="../00 - COMECE AQUI.html">Começo</a><h1>IDs visuais</h1><p>Escolha as cores e fontes separadamente do formato de edição. Exemplo: “Use F01 com ID03”.</p><table><thead><tr><th>Código</th><th>Nome</th><th>Fontes</th></tr></thead><tbody>'
 for entry in catalogue(root)['visual_identities']:
  identity=visual_identity(root,entry['code']);label=entry['code']+' - '+entry['name'];folder=directory/label
  if folder.is_symlink():raise ValueError('Pasta da ID visual não pode ser um atalho.')
  folder.mkdir(exist_ok=True)
  content='<a href="../00 - LEIA PRIMEIRO.html">Voltar</a><h1>'+html.escape(label)+'</h1><p>Pode ser usada com qualquer formato F.</p><table><tbody>'
  for role,color in identity['palette'].items():content+='<tr><td>'+html.escape(role)+'</td><td><span style="display:inline-block;width:28px;height:20px;border:1px solid #999;background:'+color+'"></span> '+color+'</td></tr>'
  content+='</tbody></table><p>Título: '+html.escape(identity['typography']['headline'])+' · Texto: '+html.escape(identity['typography']['body'])+' · Etiquetas: '+html.escape(identity['typography']['labels'])+'</p><p><a href="../../99%20-%20Sistema/'+quote(entry['path'])+'">Arquivo real da ID visual</a></p><p>Logotipo não é incluído automaticamente.</p>'
  (folder/'COMO USAR.html').write_text(page(label,content))
  body+='<tr><td>'+entry['code']+'</td><td><a href="'+quote(label,safe='')+'/COMO%20USAR.html">'+html.escape(entry['name'])+'</a></td><td>'+html.escape(identity['typography']['headline'])+'</td></tr>'
 body+='</tbody></table><p>Identidades oficiais usam ID. Para suas próprias cores e fontes, crie IDP01, IDP02 etc. Você pode copiar uma ID oficial para uma IDP particular sem alterar o original.</p>'
 (directory/'00 - LEIA PRIMEIRO.html').write_text(page('IDs visuais',body))
 return {'ok':True,'visual_identities':len(catalogue(root)['visual_identities'])}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);commands=p.add_subparsers(dest='command',required=True)
 commands.add_parser('refresh');commands.add_parser('list');s=commands.add_parser('show');s.add_argument('--code',required=True)
 s=commands.add_parser('update');s.add_argument('--code',required=True);s.add_argument('--input',type=Path,required=True);s.add_argument('--reason',required=True)
 s=commands.add_parser('create');s.add_argument('--name',required=True);s.add_argument('--input',type=Path,required=True);s.add_argument('--official',action='store_true')
 s=commands.add_parser('copy');s.add_argument('--from-code',required=True);s.add_argument('--name',required=True)
 a=p.parse_args()
 try:
  if a.command=='refresh':result=refresh(a.root)
  elif a.command=='list':result=catalogue(a.root)['visual_identities']
  elif a.command=='show':result=visual_identity(a.root,a.code)
  elif a.command=='update':result=update_visual(a.root,a.code,json.loads(a.input.read_text()),a.reason);refresh(a.root)
  elif a.command=='copy':
   source=visual_identity(a.root,a.from_code);result=register_visual(a.root,a.name,source['palette'],source['typography'],notes=source.get('notes',''),assets=source.get('assets',[]));refresh(a.root)
  else:
   data=json.loads(a.input.read_text());result=register_visual(a.root,a.name,data['palette'],data['typography'],notes=data.get('notes',''),assets=data.get('assets',[]),official=a.official);refresh(a.root)
  print(json.dumps(result,ensure_ascii=False,indent=2));return 0
 except (ValueError,OSError,KeyError) as exc:print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
