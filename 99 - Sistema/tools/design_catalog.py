"""Independent editing formats (Fxx) and visual identities (IDxx); no implicit pair."""
from __future__ import annotations
import copy,json,re,uuid,subprocess,shutil
from datetime import datetime,timezone
from urllib.parse import urlsplit
from pathlib import Path
from project_layout import engine_root
from factory_common import inside,atomic_json,workspace_lock,fingerprint


def catalogue(root):
    path=inside(engine_root(root),'context/catalog/registry.json')
    return json.loads(path.read_text()) if path.exists() else {'version':2,'formats':[],'visual_identities':[]}


def save(root,data):atomic_json(inside(engine_root(root),'context/catalog/registry.json'),data)


def next_code(items,prefix,reserved=()):
    pattern=re.compile(re.escape(prefix)+r'([0-9]+)$')
    values=[int(match.group(1)) for x in [*items,*(reserved if prefix!='F' else ())] if (match:=pattern.fullmatch(x['code']))]
    if prefix in ('F','ID'):
        candidate=1
        while candidate in values:candidate+=1
        return prefix+f'{candidate:02d}'
    return prefix+f'{max(values,default=0)+1:02d}'


def publisher_can_write(root):
    # The local user can edit their own files; authority comes from the central repository.
    if not shutil.which('gh'):raise ValueError('Não foi possível verificar a conta do GitHub. FP funciona localmente; F exige autenticação de mantenedor.')
    result=subprocess.run(['gh','api','repos/Empire-Business/edicao-por-ia'],capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('Não foi possível confirmar acesso ao GitHub; nenhum formato oficial foi alterado.')
    metadata=json.loads(result.stdout)
    return metadata.get('id')==1408655066 and bool((metadata.get('permissions') or {}).get('push'))


def require_publisher(root):
    if not publisher_can_write(root):
        raise ValueError('Sua conta tem apenas leitura ou não está autorizada como mantenedor. F é do catálogo oficial; crie um formato particular FP.')


def retirement_path(root,entry):
    base=inside(engine_root(root),'context/catalog/retired/'+entry['code'])
    old=base/'entry.json'
    if old.is_file() and json.loads(old.read_text()).get('memory_store')!=entry['memory_store']:
        generation=entry.get('uid') or fingerprint(entry)
        if not re.fullmatch(r'[A-Za-z0-9._-]+',generation):raise ValueError('Identidade interna inválida.')
        return inside(engine_root(root),base/'generations'/generation)
    return base


def validate_example_url(value):
    if not isinstance(value,str) or len(value)>2000:raise ValueError('Envie o link de um vídeo de exemplo para cadastrar o novo formato.')
    parsed=urlsplit(value.strip())
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use um link HTTP/HTTPS de exemplo, sem credenciais.')
    return value.strip()


def register_format(root,store,name,description='',pattern='talking-head-clean-v2',example_url=None,legacy=False,official=False):
    root=engine_root(root)
    if official:require_publisher(root)
    with workspace_lock(root,'design-catalog'):
        data=catalogue(root)
        if any(store in [x['memory_store'],*x.get('legacy_stores',[])] for x in data.get('retired_formats',[])):
            raise ValueError('Este formato foi removido do catálogo; o histórico foi preservado.')
        old=next((x for x in data['formats'] if x['memory_store']==store),None)
        if old:return old
        example_url=validate_example_url(example_url) if example_url else None
        if not example_url and not legacy:raise ValueError('Novo formato precisa de um link de exemplo. Envie o link antes de cadastrar.')
        prefix='F' if official else 'FP'
        code=next_code(data['formats'],prefix,data.get('retired_formats',[]))
        item={'code':code,'name':name,'memory_store':store,'pattern':pattern,'description':description,
              'uid':('official.' if official else 'personal.')+uuid.uuid4().hex,'origin':'official' if official else 'personal',
              'design_independent':True,'default_visual_identity':None,'example_url':example_url,
              'example_link_status':'provided' if example_url else 'legacy_exempt'}
        if not legacy:item['validation_status']='reference_analysis_pending'
        data['formats'].append(item);save(root,data)
        return item


def editing_format(root,value,register_legacy=True):
    if not isinstance(value,str) or not value.strip():raise ValueError('Qual formato de edição devo usar? Escolha um código F, como F01.')
    text=value.strip();match=re.fullmatch(r'(FP|F)([0-9]+)',text,re.I)
    if match:text=match.group(1).upper()+f'{int(match.group(2)):02d}'
    data=catalogue(root)
    result=next((x for x in data['formats'] if text.casefold() in [x['code'].casefold(),x['name'].casefold(),x['memory_store'].casefold(),*[v.casefold() for v in x.get('legacy_stores',[])]]),None)
    if result:return result
    if any(text.casefold() in [x['code'].casefold(),x['name'].casefold(),x['memory_store'].casefold(),*[v.casefold() for v in x.get('legacy_stores',[])]] for x in data.get('retired_formats',[])):
        raise ValueError('Formato removido do catálogo: '+text+'. Escolha outro formato ativo.')
    if register_legacy and not re.fullmatch(r'(?:FP|F)\d+',text,re.I):
        from client_memory import Memory
        memory=Memory(root);name=memory.name(text)
        preferences=memory.context(text)['active']
        pattern=next((r['payload']['value'] for r in preferences if r['key']=='defaults.pattern'),'talking-head-clean-v2')
        return register_format(root,text,name,pattern=pattern,legacy=True)
    raise ValueError('Formato desconhecido. Escolha um código F ou FP cadastrado.')


def retire_format(root,value,reason):
    """Remove an active entry without erasing its code, records, recipes or past jobs."""
    root=engine_root(root)
    with workspace_lock(root,'design-catalog'):
        data=catalogue(root)
        def matches(x):return value.casefold() in [x['code'].casefold(),x['name'].casefold(),x['memory_store'].casefold(),*[v.casefold() for v in x.get('legacy_stores',[])]]
        entry=next((x for x in data['formats'] if matches(x)),None)
        if entry is None:
            old=next((x for x in data.get('retired_formats',[]) if matches(x)),None)
            if old:return {'ok':True,'status':'already_removed','code':old['code'],'entry':old}
            raise ValueError('Formato não encontrado: '+value)
        if re.fullmatch(r'F[0-9]+',entry['code']):require_publisher(root)
        archived=copy.deepcopy(entry);archived['retired_at']=datetime.now(timezone.utc).isoformat();archived['retirement_reason']=reason
        data['formats']=[x for x in data['formats'] if x['code']!=entry['code']]
        data.setdefault('retired_formats',[]).append(archived)
        directory=retirement_path(root,entry)
        archive=inside(root,directory/'entry.json');atomic_json(archive,archived)
        save(root,data)
    return {'ok':True,'status':'removed','code':entry['code'],'entry':archived,'archive_directory':str(directory.relative_to(root)),'code_reserved':entry['code'].startswith('FP'),'historical_records_preserved':True,'generation_identity_preserved':True}


def register_visual(root,name,palette,typography,code=None,notes='',assets=None,official=False):
    if not isinstance(name,str) or not name.strip() or len(name)>50:raise ValueError('Use um nome simples para a ID visual.')
    required={'background','text','primary'}
    if not isinstance(palette,dict) or not required<=set(palette) or any(not re.fullmatch(r'#[0-9a-fA-F]{6}',v) for v in palette.values()):raise ValueError('A paleta precisa de background, text e primary em hexadecimal.')
    if not isinstance(typography,dict) or not {'headline','body','labels'}<=set(typography):raise ValueError('Informe fontes de título, texto e etiquetas.')
    if any(not isinstance(v,str) or not v.strip() or len(v)>100 for k,v in typography.items() if k!='assets'):raise ValueError('Fonte inválida.')
    root=engine_root(root)
    if official:require_publisher(root)
    with workspace_lock(root,'design-catalog'):
        prefix='ID' if official else 'IDP'
        data=catalogue(root);code=code or next_code(data['visual_identities'],prefix)
        if not re.fullmatch(re.escape(prefix)+r'[0-9]{2,}',code):raise ValueError('ID é oficial; identidades particulares usam IDP.')
        if any(x['code']==code or x['name'].casefold()==name.casefold() for x in data['visual_identities']):raise ValueError('Essa ID visual já existe; crie uma revisão, não substitua sua história.')
        identity={'code':code,'name':name.strip(),'version':1,'palette':palette,'typography':typography,
                  'logos_enabled':False,'notes':notes,'assets':assets or []}
        path=f'context/visual-identities/{code}/identity-v1.json';atomic_json(inside(root,path),identity)
        data['visual_identities'].append({'code':code,'name':name.strip(),'path':path,'version':1});save(root,data)
        return {'ok':True,'status':'created','code':code,'path':path,'verified':visual_identity(root,code)==identity}


def visual_identity(root,value):
    if not isinstance(value,str) or not value.strip():raise ValueError('Qual ID visual devo usar? Escolha um código ID, como ID01. Nenhuma cor/fonte é escolhida pelo formato.')
    text=value.strip();match=re.fullmatch(r'(IDP|ID)([0-9]+)',text,re.I)
    if match:text=match.group(1).upper()+f'{int(match.group(2)):02d}'
    entry=next((x for x in catalogue(root)['visual_identities'] if text.casefold() in (x['code'].casefold(),x['name'].casefold())),None)
    if not entry:raise ValueError('ID visual desconhecida. Escolha uma ID cadastrada.')
    identity=json.loads(inside(engine_root(root),entry['path']).read_text())
    if identity['code']!=entry['code']:raise ValueError('O código do arquivo da ID visual não confere.')
    return identity


def select_pair(root,format_value,visual_value):
    # Check both choices before reading a historical format's private context.
    identity=visual_identity(root,visual_value)
    editing=editing_format(root,format_value)
    return editing,identity


def visual_receipt(identity):
    return {'code':identity['code'],'version':identity['version'],'fingerprint':fingerprint(identity)}


def editing_context(memory,format_value,project=None,job=None,pattern=None,max_chars=7500):
    editing=editing_format(memory.root,format_value)
    legacy=memory.context(editing['memory_store'],project,job,pattern,max_chars=max_chars)
    # Only mechanical editing settings cross the old mixed-profile boundary.
    allowed=lambda r: not r['key'].startswith(('brand.','identity.','visuals.brand','typography.','palette.','colors.','assets.'))
    active=[r for r in legacy['active'] if allowed(r) and r['key']!='defaults.pattern']
    recipe_path=inside(memory.root,'patterns/'+editing['pattern']+'.yaml')
    reference_path=f"examples/reference-library/{editing.get('uid','').removeprefix('factory.').upper()}/README.md"
    stock_references=reference_path if inside(memory.root,reference_path).is_file() else None
    text='\n'.join([f"# {editing['code']} — {editing['name']}",editing['description'],
      'Formato de edição sem cores, fontes, logotipos ou identidade pessoal. A aparência vem somente da ID visual selecionada.',
      f"Receita: patterns/{editing['pattern']}.yaml",'Referências: '+(stock_references or 'sem biblioteca distribuída; consultar o exemplo informado'),'O acervo é evidência histórica: não copiar sua pessoa, marca, logo, paleta ou fonte. A edição usa a pessoa e os materiais fornecidos no trabalho e a ID escolhida.','Exemplo: '+(editing.get('example_url') or 'cadastro antigo sem link'),*[f"- {r['key']}: {json.dumps(r['payload']['value'],ensure_ascii=False)}" for r in active]])+'\n'
    text+='Antes da montagem, inspecionar cenas reais da referência e preencher analysis/format-plan.json. Antes da entrega, comparar frames do render, composição e ritmo em qa/format-fidelity.json. Os campos do contrato de formato no job indicam os critérios obrigatórios. Não declarar semelhança artística apenas por um teste mecânico.\n'
    return {**legacy,'text':text,'active':active,'references':[],
            'fingerprint':fingerprint({'definition':{k:v for k,v in editing.items() if k not in ('name','registration_receipt','legacy_stores')},'records':active}),'omitted_ids':[],
            'reference_library':stock_references,'format_code':editing['code'],'design_filtered':True,'definition':editing}


def effective_visual(root,job):
    identity=visual_identity(root,job.get('visual_identity'))
    return identity,visual_receipt(identity)


def update_visual(root,code,changes,reason):
    """Versioned visual-only edit; editing formats and past identity revisions are untouched."""
    root=engine_root(root)
    if not isinstance(changes,dict) or set(changes)-{'palette','typography','notes','font_faces','assets'}:raise ValueError('A ID visual guarda somente paleta, tipografia e seus materiais.')
    previous=visual_identity(root,code);new=copy.deepcopy(previous);new.update(changes);new['version']=previous['version']+1;new['logos_enabled']=False
    if re.fullmatch(r'ID[0-9]+',previous['code']):require_publisher(root)
    if not isinstance(new['palette'],dict) or not {'background','text','primary'}<=set(new['palette']) or any(not re.fullmatch(r'#[0-9a-fA-F]{6}',v) for v in new['palette'].values()):raise ValueError('Paleta inválida.')
    if not isinstance(new['typography'],dict) or not {'headline','body','labels'}<=set(new['typography']):raise ValueError('Tipografia inválida.')
    with workspace_lock(root,'design-catalog'):
        data=catalogue(root);entry=next(x for x in data['visual_identities'] if x['code']==previous['code'])
        path=f"context/visual-identities/{entry['code']}/identity-v{new['version']}.json";atomic_json(inside(root,path),new)
        entry.update(path=path,version=new['version']);save(root,data)
        receipt={'ok':True,'status':'saved','code':entry['code'],'version':new['version'],'before':visual_receipt(previous),'after':visual_receipt(new),'reason':reason,'path':path}
        atomic_json(inside(root,f"context/visual-identities/{entry['code']}/receipt-v{new['version']}.json"),receipt)
        return receipt


def initialize_defaults(root):
    """Seed missing bundled definitions without replacing a user's codes, identities or memory."""
    root=engine_root(root);source=inside(root,'config/design-defaults.json')
    if not source.exists():return {'ok':True,'added':[]}
    defaults=json.loads(source.read_text());added=[];conflicts=[]
    from client_memory import Memory
    from shutil import copyfile
    with workspace_lock(root,'design-catalog'):
        current=catalogue(root)
        for key,prefix in [('formats','F'),('visual_identities','ID')]:
            for template in defaults[key]:
                if key=='formats' and any((template.get('uid') and x.get('uid')==template['uid']) or (not template.get('uid') and x['code']==template['code']) for x in current.get('retired_formats',[])):continue
                if any(x.get('uid')==template.get('uid') for x in current[key]):continue
                item=copy.deepcopy(template)
                if any(x['code']==item['code'] for x in current[key]):
                    if key=='formats':
                        conflicts.append({'code':item['code'],'uid':item.get('uid'),'reason':'existing_local_code_preserved'});continue
                    item['code']=next_code(current[key],prefix)
                if key=='formats':
                    item['memory_store']='format-'+item['code'].lower()
                    if Memory(root).path(item['memory_store']).exists() and any(x['memory_store']==item['memory_store'] for x in current.get('retired_formats',[])):
                        item['memory_store']='format-'+item['code'].lower()+'-'+fingerprint(item.get('uid'))[:12]
                    if not Memory(root).path(item['memory_store']).exists():Memory(root).init(item['memory_store'],item['name'])
                else:
                    seed=inside(root,f"config/visual-presets/{template['code']}/identity-v1.json")
                    identity=json.loads(seed.read_text());identity['code']=item['code']
                    item['path']=f"context/visual-identities/{item['code']}/identity-v1.json"
                    destination=inside(root,item['path'])
                    if destination.exists():raise ValueError('Uma ID visual local existe sem cadastro; não foi sobrescrita.')
                    atomic_json(destination,identity)
                current[key].append(item);added.append(item['code'])
        save(root,current)
    return {'ok':True,'added':added,'conflicts':conflicts,'local_definitions_preserved':True}


def product_tokens(identity):
    """Semantic UI colors derive exclusively from the chosen visual identity."""
    p=identity['palette'];bg=p['background'];fg=p['text'];primary=p['primary'];surface=p.get('surface',bg)
    def mix(a,b,n):
        aa=[int(a[i:i+2],16) for i in (1,3,5)];bb=[int(b[i:i+2],16) for i in (1,3,5)]
        return '#'+''.join(f'{round(x*(1-n)+y*n):02x}' for x,y in zip(aa,bb))
    def contrast(color):
        rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)];l=sum(c*w for c,w in zip(rgb,(.2126,.7152,.0722)))
        return '#101010' if l>.58 else '#FFFFFF'
    dark=mix(primary,'#000000',.88)
    return {'bg':bg,'fg':fg,'card':surface,'cardFg':contrast(surface),'muted':mix(bg,surface,.65),'mutedFg':p.get('muted',mix(bg,fg,.65)),
      'border':mix(bg,fg,.18),'input':mix(surface,fg,.12),'accent':mix(surface,primary,.12),'brand10':mix(surface,primary,.1),
      'primary':primary,'primaryFg':contrast(primary),'gold':primary,'gold2':mix(primary,fg,.2),
      'success':p.get('success',primary),'successBg':mix(surface,p.get('success',primary),.12),
      'warning':p.get('warning',primary),'warningBg':mix(surface,p.get('warning',primary),.12),
      'destructive':p.get('error',primary),'destructiveBg':mix(surface,p.get('error',primary),.12),
      'info':primary,'infoBg':mix(surface,primary,.12),'room':dark,'roomPanel':mix(dark,primary,.08),'roomPanel2':mix(dark,primary,.12),
      'roomBorder':mix(dark,primary,.2),'roomFg':contrast(dark),'roomMuted':mix(dark,contrast(dark),.65),'roomGold':primary,'roomRed':p.get('error',primary)}


def import_legacy_formats(root):
    """Add clean numbered projections for pre-v2 custom stores; original rows remain intact."""
    import sqlite3
    root=engine_root(root);directory=inside(root,'context/clients');data=catalogue(root)
    known_entries=[*data['formats'],*data.get('retired_formats',[])]
    known={x['memory_store'] for x in known_entries}|{v for x in known_entries for v in x.get('legacy_stores',[])}
    added=[]
    from client_memory import Memory
    memory=Memory(root)
    if not directory.exists():return {'ok':True,'imported':[]}
    safe_keys={'motion.enabled','motion.intensity','requirements.captions','requirements.speech_cleanup','silence_removal.enabled','silence_removal.mode','reference_script.mode',
       *['silence_removal.settings.'+x for x in ('minimum_silence_seconds','keep_pause_seconds','word_handle_seconds','minimum_cut_seconds','trim_edges')]}
    for folder in sorted(directory.iterdir()):
        if folder.name in known or folder.name.startswith(('_','.')) or folder.is_symlink() or not (folder/'memory.sqlite3').is_file():continue
        old=folder.name
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',old):continue
        with sqlite3.connect((folder/'memory.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
            try:rows=db.execute("SELECT payload FROM records WHERE scope='client' AND scope_id=? AND status='active' AND key IN ("+",".join("?" for _ in safe_keys)+")",(old,*sorted(safe_keys))).fetchall()
            except sqlite3.OperationalError:rows=[]
        with workspace_lock(root,'design-catalog'):
            data=catalogue(root);code=next_code(data['formats'],'FP',data.get('retired_formats',[]));fresh='format-'+code.lower();name='Personalizado '+code
            memory.init(fresh,name)
            entry={'uid':'imported.'+old,'code':code,'name':name,'memory_store':fresh,'legacy_stores':[old],'pattern':'talking-head-clean-v2',
                   'description':'Cadastro anterior importado. Preferências mecânicas preservadas; o acervo original continua disponível para consulta.',
                   'design_independent':True,'default_visual_identity':None,'example_url':None,'example_link_status':'legacy_exempt','memory_domain':'editing_only'}
            data['formats'].append(entry);save(root,data)
        copied=[]
        for (raw,) in rows:
            try:
                payload=json.loads(raw)
                if payload.get('key') not in safe_keys:continue
                payload['scope']='format';payload['scope_id']=fresh;memory.validate(fresh,payload);copied.append(payload)
            except (ValueError,KeyError):continue
        if copied:memory.commit(fresh,copied,'legacy-projection-v2-'+old)
        added.append({'code':code,'original_store':old,'new_store':fresh,'preferences_preserved':len(copied)})
    return {'ok':True,'imported':added,'original_stores_unchanged':True}


def complete_stock_examples(root):
    """Add missing stock illustrative links only; preserve every supplied/custom link."""
    root=engine_root(root);defaults=json.loads(inside(root,'config/design-defaults.json').read_text())
    templates={x.get('uid'):x for x in defaults['formats']};changed=[]
    with workspace_lock(root,'design-catalog'):
        current=catalogue(root)
        for entry in current['formats']:
            template=templates.get(entry.get('uid'))
            if not template or not template.get('example_url'):continue
            previous_stock='https://github.com/Empire-Business/edicao-por-ia/blob/main/99%20-%20Sistema/examples/formats/'+template['code']+'.png'
            if entry.get('example_url') and entry['example_url']!=previous_stock:continue
            before={k:entry.get(k) for k in ('example_url','example_link_status','example_kind')}
            entry.update({k:template[k] for k in ('example_url','example_link_status','example_kind')})
            changed.append({'code':entry['code'],'before':before,'after':{k:entry[k] for k in before}})
        if changed:save(root,current)
    receipt={'ok':True,'changed':changed,'source':'author-published reference collections','existing_links_preserved':True}
    if changed:atomic_json(inside(root,'.factory/migrations/stock-examples-v2-1-0.json'),receipt)
    return receipt
