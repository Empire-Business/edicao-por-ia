#!/usr/bin/env python3
"""Inspect the effects catalogue and prepare portable, reviewed studio layers. No install, upload or model call."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
import re
from pathlib import Path
from project_layout import engine_root, surface_root
from workspace_files import resolve_file

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'motion/effects'
ALLOWED = {'text','title','subtitle','words','wordCues','items','values','labels','value','countdownFrom','accent','foreground','background','fontFamily','duration','mode','seed','logosEnabled'}
COLORS = ('accent','foreground','background')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def catalogue():
    return json.loads((DIRECTORY/'catalog.json').read_text(encoding='utf-8'))

def effect(code):
    for item in catalogue()['effects']:
        if code.upper() == item['code'] or code == item['id']:
            return item
    raise ValueError('Efeito desconhecido: '+code)

def validate_props(props, demo=False):
    if not isinstance(props,dict) or set(props)-ALLOWED:
        raise ValueError('Parâmetros desconhecidos ou inválidos.')
    for key in COLORS:
        if not demo and key not in props:
            raise ValueError('Informe '+key+' a partir da ID escolhida; nenhuma aparência é herdada.')
        if key in props and not re.fullmatch(r'#[0-9a-fA-F]{6}',str(props[key])):
            raise ValueError(key+': cor hexadecimal #RRGGBB obrigatória.')
    if not demo and not props.get('fontFamily'):
        raise ValueError('Informe fontFamily a partir da ID escolhida.')
    for key in ('text','title','subtitle','fontFamily'):
        if key in props and (not isinstance(props[key],str) or len(props[key])>280):
            raise ValueError(key+': texto de até 280 caracteres.')
    for key in ('duration','value','seed','countdownFrom'):
        if key in props and (isinstance(props[key],bool) or not isinstance(props[key],(float,int)) or not math.isfinite(props[key])):
            raise ValueError(key+': número finito obrigatório.')
    if not .25 <= props.get('duration',3) <= 30:
        raise ValueError('duration: entre 0.25 e 30 segundos.')
    if 'countdownFrom' in props and (type(props['countdownFrom'])!=int or not 1<=props['countdownFrom']<=10):
        raise ValueError('countdownFrom: inteiro entre 1 e 10.')
    if props.get('mode','overlay') not in ('overlay','demo'):
        raise ValueError('mode: overlay ou demo.')
    if 'logosEnabled' in props and type(props['logosEnabled']) is not bool:
        raise ValueError('logosEnabled deve ser booleano.')
    for key in ('words','items','labels'):
        if key in props and (not isinstance(props[key],list) or len(props[key])>30 or any(not isinstance(v,str) or len(v)>140 for v in props[key])):
            raise ValueError(key+': lista curta de textos obrigatória.')
    if 'values' in props and (not isinstance(props['values'],list) or not 1<=len(props['values'])<=12 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in props['values'])):
        raise ValueError('values: lista de 1 a 12 números finitos não negativos.')
    if 'wordCues' in props:
        cues=props['wordCues']
        if not isinstance(cues,list) or len(cues)>100:
            raise ValueError('wordCues: lista de palavras com start/end em segundos locais.')
        previous=-1
        for cue in cues:
            if not isinstance(cue,dict) or set(cue)!={'text','start','end'} or not isinstance(cue['text'],str):
                raise ValueError('wordCues: cada palavra exige text, start e end.')
            start,end=cue['start'],cue['end']
            if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (start,end)) or not 0<=start<end<=props.get('duration',3) or start<previous:
                raise ValueError('wordCues: tempos fora da duração ou da ordem.')
            previous=start
    return props

def prepare(code, destination, props, *, child_id, width=540, height=960, fps=30, assets=None, demo=False, font_path=None):
    item=effect(code)
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,100}',child_id):
        raise ValueError('child_id inválido.')
    if any(type(v)!=int for v in (width,height,fps)) or not 64<=width<=3840 or not 64<=height<=3840 or not 1<=fps<=120:
        raise ValueError('Geometria/FPS inválidos; use inteiros compatíveis com o master.')
    if abs(width/height-9/16)>.002 or width*height>8_400_000:
        raise ValueError('Estes estudos usam composição 9:16. Outra proporção exige recomposição no estúdio, sem esticar a imagem.')
    settings={**item['demo'],**props} if demo else dict(props)
    if demo:
        settings={'accent':'#d8ef77','foreground':'#f3f1e9','background':'#101411','fontFamily':'sans-serif',**settings,'mode':'demo'}
    else:
        settings['mode']='overlay'
    validate_props(settings,demo)
    if round(settings.get('duration',3)*fps)<1:
        raise ValueError('A duração deve conter ao menos um frame na taxa escolhida.')
    if assets is not None and not isinstance(assets,dict):
        raise ValueError('Assets devem ser um mapa de identificador para caminho local.')
    if not demo and item.get('production_support')=='study-only':
        raise ValueError('Este item é um estudo do mecanismo; a operação real usa ferramentas de imagem apropriadas.')
    if item['id']=='logo-reveal' and not demo and (settings.get('logosEnabled') is not True or not assets or 'logo' not in assets):
        raise ValueError('Logotipo exige pedido atual explícito, logosEnabled=true e arquivo real.')
    if item['requires_assets'] and not demo and not assets:
        raise ValueError('Este efeito exige assets reais autorizados. Use --demo apenas para um estudo ilustrativo.')
    alternatives=item.get('asset_alternatives',[])
    if not demo and alternatives and not any(all(key in (assets or {}) for key in keys) for keys in alternatives):
        raise ValueError('Assets insuficientes. Conjuntos aceitos: '+json.dumps(alternatives,ensure_ascii=False))
    destination=resolve_file(destination,ROOT,False)
    if destination.exists():
        raise ValueError('A pasta de saída deve ser nova; versões anteriores são preservadas.')
    sources=[]
    for key,value in (assets or {}).items():
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,60}',key):
            raise ValueError('Identificador de asset inválido.')
        source=resolve_file(value,ROOT)
        if source.name.startswith('.env') or source.name=='CHAVES DAS INTEGRAÇÕES.txt' or source.suffix.lower() in ('.pem','.key','.p12','.pfx') or any(p in source.parts for p in ('.ssh','.aws')):
            raise ValueError('Credenciais não são assets de edição.')
        from PIL import Image
        with Image.open(source) as image:
            if image.format not in ('PNG','JPEG','WEBP') or getattr(image,'n_frames',1)!=1:
                raise ValueError('Use um asset raster estático autorizado.')
            image.verify()
            mime={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}[image.format]
        sources.append((key,source,mime))
    css=''
    if font_path:
        font=resolve_file(font_path,ROOT)
        if font.suffix.lower() not in ('.woff','.woff2','.ttf','.otf') or font.stat().st_size>5_000_000:
            raise ValueError('Use um arquivo local de fonte compatível de até 5 MB.')
        encoded=base64.b64encode(font.read_bytes()).decode()
        css="@font-face{font-family:EffectLocalFont;src:url(data:font/"+font.suffix[1:]+";base64,"+encoded+")}"
        settings['fontFamily']='EffectLocalFont'
    renderer=(DIRECTORY/'renderer.js').read_text(encoding='utf-8').replace('</script','<\\/script')
    def script_json(value):
        return json.dumps(value,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    asset_ids=[key for key,_,_ in sources]
    # Trusted renderer is embedded and hashed in the entry. User text is data, never markup/code.
    html='<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:transparent}'+css+'</style><canvas></canvas><script>'+renderer+'</script><script>const canvas=document.querySelector("canvas");canvas.width='+str(width)+';canvas.height='+str(height)+';const props='+script_json(settings)+';const assetIds='+script_json(asset_ids)+';props.assets={};window.__STUDIO_READY__=Promise.all(assetIds.map(async id=>{const img=new Image();img.src=studioAsset(id);await img.decode();props.assets[id]=img;}));window.seek=t=>CortezEffects.render(canvas,'+script_json(item['id'])+',t,props);</script>'
    destination.mkdir(parents=True)
    entry=destination/'effect.html';entry.write_text(html,encoding='utf-8')
    import os
    spec={'schema_version':1,'id':item['id'],'child_id':child_id,'entry':{'path':'effect.html','sha256':sha(entry)},'assets':[{'id':key,'path':os.path.relpath(source,destination),'sha256':sha(source),'mime':mime} for key,source,mime in sources], 'width':width,'height':height,'fps':fps,'duration_frames':round(settings.get('duration',3)*fps),'mode':'full_frame' if demo else 'overlay','cut_frames':[], 'effect':{'code':item['code'],'version':item['version'],'renderer_sha256':sha(DIRECTORY/'renderer.js'),'catalog_sha256':sha(DIRECTORY/'catalog.json'),'illustrative_demo':demo}}
    path=destination/'spec.json';path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'ok':True,'spec':str(path.relative_to(surface_root(ROOT))),'effect':item['code'],'demo':demo,'approval_required':'Inspect/review the generated bundle before rendering through studio_render.py.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list')
    show=commands.add_parser('show');show.add_argument('code')
    command=commands.add_parser('prepare');command.add_argument('code');command.add_argument('--outdir',type=Path,required=True);command.add_argument('--props',type=Path,required=True);command.add_argument('--child-id',required=True);command.add_argument('--width',type=int,default=540);command.add_argument('--height',type=int,default=960);command.add_argument('--fps',type=int,default=30);command.add_argument('--assets',type=Path);command.add_argument('--font',type=Path);command.add_argument('--demo',action='store_true')
    args=parser.parse_args()
    try:
        if args.command=='list':out=[{k:e[k] for k in ('code','id','name','category','status')} for e in catalogue()['effects']]
        elif args.command=='show':out=effect(args.code)
        else:
            props=json.loads(resolve_file(args.props,ROOT).read_text(encoding='utf-8'))
            assets=json.loads(resolve_file(args.assets,ROOT).read_text(encoding='utf-8')) if args.assets else {}
            out=prepare(args.code,args.outdir,props,child_id=args.child_id,width=args.width,height=args.height,fps=args.fps,assets=assets,demo=args.demo,font_path=args.font)
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,KeyError) as error:
        print(json.dumps({'ok':False,'error':str(error)},ensure_ascii=False));return 2

if __name__=='__main__':raise SystemExit(main())
