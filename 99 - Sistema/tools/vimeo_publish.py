#!/usr/bin/env python3
"""Maintainer-only, resumable uploads of explicitly selected public gallery references to Cortez."""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse
from update_local import atomic,json_write,locate,sha,target_path

class Vimeo:
 def __init__(self,token):self.token=token
 def api(self,path,method='GET',data=None):
  if not path.startswith('/') or path.startswith('//'):raise ValueError('Caminho Vimeo inválido.')
  req=urllib.request.Request('https://api.vimeo.com'+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json','Accept':'application/vnd.vimeo.*+json;version=3.4'})
  try:
   class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('API Vimeo redirecionada; acesso interrompido.')
   with urllib.request.build_opener(NoRedirect).open(req,timeout=60) as r:return json.load(r) if r.status!=204 else {}
  except urllib.error.HTTPError as e:raise ValueError('Vimeo HTTP '+str(e.code)+'; nenhuma credencial foi registrada.') from None
 def pages(self,path):
  while path:
   result=self.api(path)
   yield from result['data']
   path=result.get('paging',{}).get('next')
   if path and path.startswith('https://api.vimeo.com/'):path=path[len('https://api.vimeo.com'):]
 def upload(self,link,path):
  parsed=urlparse(link)
  if parsed.scheme!='https' or not (parsed.hostname=='vimeo.com' or (parsed.hostname or '').endswith('.vimeo.com')):raise ValueError('Destino de upload Vimeo inválido.')
  # Upload links are scoped capabilities. Never send the account token to the upload host.
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args,**kwargs):raise ValueError('Upload redirecionado; interrompido.')
  opener=urllib.request.build_opener(NoRedirect)
  with opener.open(urllib.request.Request(link,method='HEAD',headers={'Tus-Resumable':'1.0.0'}),timeout=60) as r:offset=int(r.headers['Upload-Offset'])
  size=path.stat().st_size
  if not 0<=offset<=size:raise ValueError('Offset de upload inválido.')
  with path.open('rb') as f:
   f.seek(offset)
   while offset<size:
    block=f.read(8*1024*1024)
    request=urllib.request.Request(link,data=block,method='PATCH',headers={'Tus-Resumable':'1.0.0','Upload-Offset':str(offset),'Content-Type':'application/offset+octet-stream'})
    with opener.open(request,timeout=120) as r:new=int(r.headers['Upload-Offset'])
    if new!=offset+len(block):raise ValueError('Vimeo não confirmou o bloco completo.')
    offset=new
  return offset

def selections(engine):
 site=engine/'web/modelos-edicao';pub=json.loads((site/'publication.json').read_text());lib=json.loads((engine/'config/reference-library.json').read_text());catalog=json.loads((site/'public/catalog.json').read_text());plans=[]
 for item in pub['formats']:
  code=item['code'];refs=pub.get('reference_media',{}).get(code,[])+lib['formats'][code]['references']
  primary=next((r for r in refs if r['path'].endswith('.mp4')),None)
  variants=([('primary',primary)] if primary else [])+[(v['id'],v['reference']) for v in pub.get('extra_examples',{}).get(code,[])]
  for variant,ref in variants:
   name=ref['path'];path=engine/name
   if not name.startswith('examples/reference-library/') or path.is_symlink() or not path.resolve().is_relative_to(engine) or not path.is_file() or lib['files'].get(name)!=ref['sha256'] or sha(path)!=ref['sha256']:raise ValueError('Referência pública não confere: '+name)
   plans.append({'code':code,'variant':variant,'name':item['name'],'path':name,'sha256':ref['sha256'],'bytes':path.stat().st_size})
 return plans

def publish(root,apply=False):
 engine,_=locate(root);plans=selections(engine)
 if not apply:return {'ok':True,'status':'preview','videos':plans,'total_bytes':sum(x['bytes'] for x in plans),'folder':'Cortez'}
 from service_keys import api_key
 api=Vimeo(api_key('VIMEO_ACCESS_TOKEN',engine));me=api.api('/me')
 folders=[f for f in api.pages('/me/projects?per_page=100') if f['name'].casefold()=='cortez']
 if len(folders)>1:raise ValueError('Mais de uma pasta Cortez: revisar a pasta antes de subir vídeos.')
 folder=folders[0] if folders else api.api('/me/projects','POST',{'name':'Cortez'})
 folder_uri=folder['uri'];receipt_path=target_path(engine,engine,'.factory/vimeo/cortez-uploads.json')
 receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {'folder_uri':folder_uri,'videos':{}}
 if receipt['folder_uri']!=folder_uri:raise ValueError('A pasta Vimeo mudou; revisar o recibo.')
 remote=list(api.pages(folder_uri+'/videos?per_page=100'))
 # Reconcile a lost POST response before creating anything again. Only inspect recent
 # video metadata for our exact source marker; other account videos are never edited.
 recent=api.api('/me/videos?sort=date&direction=desc&per_page=100')['data']
 remote+=recent
 pending=[]
 for plan in plans:
  marker='cortez-source-sha256='+plan['sha256']
  existing=next((v for v in remote if marker in (v.get('description') or '')),None)
  if existing and plan['sha256'] not in receipt['videos']:
   if existing.get('upload',{}).get('status')=='complete' or existing.get('transcode',{}).get('status')=='complete':receipt['videos'][plan['sha256']]={'uri':existing['uri'],'offset':plan['bytes']}
   else:raise ValueError('Upload remoto incompleto sem recibo local; revisar antes de duplicar.')
  if plan['sha256'] not in receipt['videos']:pending.append(plan)
 free=me.get('upload_quota',{}).get('space',{}).get('free')
 if type(free) is not int or free<sum(p['bytes'] for p in pending):raise ValueError('Cota Vimeo insuficiente ou desconhecida; nenhum plano foi contratado.')
 for plan in plans:
  digest=plan['sha256'];saved=receipt['videos'].get(digest)
  if not saved:
   created=api.api('/me/videos','POST',{'upload':{'approach':'tus','size':plan['bytes']},'name':plan['code']+' · '+plan['name']+(' — '+plan['variant'] if plan['variant']!='primary' else ''),'description':'Referência do Cortez. A pessoa, marca, cores e fontes do exemplo não são escolhas automáticas.\n'+'cortez-source-sha256='+digest,'privacy':{'view':'unlisted','embed':'public'}})
   saved={'uri':created['uri'],'upload_link':created['upload']['upload_link'],'offset':0};receipt['videos'][digest]=saved;json_write(receipt_path,receipt);receipt_path.chmod(0o600)
  video_id=saved['uri'].split('/')[-1]
  api.api(folder_uri+'/videos/'+video_id,'PUT')
  if saved.get('offset')!=plan['bytes']:
   saved['offset']=api.upload(saved['upload_link'],engine/plan['path']);json_write(receipt_path,receipt)
  current=api.api(saved['uri']);saved.update(link=current.get('link'),status=current.get('status'),transcode_status=current.get('transcode',{}).get('status'));json_write(receipt_path,receipt)
  print(json.dumps({'code':plan['code'],'variant':plan['variant'],'video_id':video_id,'uploaded_bytes':saved['offset'],'transcode':saved['transcode_status']}),flush=True)
 # Public output contains IDs and unlisted hashes only; no upload capabilities or credentials.
 mapping={}
 for plan in plans:
  saved=receipt['videos'][plan['sha256']];video_id=saved['uri'].split('/')[-1];parts=urlparse(saved['link']).path.strip('/').split('/')
  reference={'id':video_id,'source_sha256':plan['sha256'],'status':saved['transcode_status']}
  if len(parts)>1:reference['hash']=parts[1]
  key=plan['code'] if plan['variant']=='primary' else plan['code']+':'+plan['variant'];mapping[key]=reference
 json_write(engine/'web/modelos-edicao/vimeo.json',mapping)
 return {'ok':True,'folder_uri':folder_uri,'videos':len(plans),'mapping_written':True,'processing_pending':sum(v['status']!='complete' for v in mapping.values())}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--apply',action='store_true');a=p.parse_args()
 try:print(json.dumps(publish(a.root,a.apply),ensure_ascii=False,indent=2))
 except (ValueError,OSError,urllib.error.URLError) as exc:print(json.dumps({'ok':False,'message':str(exc) if isinstance(exc,ValueError) else 'Falha de rede/arquivo; recibo privado preservado.'}));raise SystemExit(2)
