#!/usr/bin/env python3
"""Idempotent local setup / safe upgrades. Dry run by default, explicit consent to apply.
No auth files, dot-env, global settings, subscriptions or credit settings are read or changed.
"""
from __future__ import annotations
import copy, hashlib, json, os, platform, re, shlex, shutil, subprocess, sys, tomllib, uuid
from pathlib import Path
from factory_common import ROOT, fail, inside, read_json, atomic_json, atomic_bytes, sha, stamp, workspace_lock, validate_profile, safe_text
from factory_doctor import interpreter, collect
from install_memory_hooks import merge
from project_layout import managed_path, surface_root

ROLES={
 'transcript-screener':('triage',6), 'assembly-editor':('standard',12), 'video-qa':('standard',8),
 'motion-builder':('standard',12), 'video-director':('premium',10),
 'motion-designer':('premium',12), 'visual-director':('premium',10)}

def bindings(root):
    c=read_json(Path(root)/'config/model-catalog.json')
    p=inside(root,'.factory/models.json')
    if p.exists():
        for host,values in read_json(p).items():
            if host in ('codex','claude'):
                for tier,value in values.items():
                    if tier in ('triage','standard','premium'):c[host][tier]=value
    return c

def bind_model(root,host,tier,model,effort,note):
    if host not in ('codex','claude') or tier not in ('triage','standard','premium'):fail('MODEL_BINDING','Host ou nível inválido.')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:\[\]-]{0,179}',model):fail('MODEL_BINDING','ID de modelo inválido.')
    if effort not in ('low','medium','high','xhigh','max'):fail('MODEL_BINDING','Esforço inválido; use apenas um nível suportado pelo modelo.')
    safe_text(note,'evidência de disponibilidade')
    with workspace_lock(root,'models'):
        p=inside(root,'.factory/models.json');c=read_json(p) if p.exists() else {}
        c.setdefault(host,{})[tier]={'model':model,'effort':effort,'availability':'user_confirmed','evidence':note,'confirmed_at':stamp()}
        atomic_json(p,c)
    return {'ok':True,'status':'saved','binding':c[host][tier],'next_action':'Execute setup --apply para atualizar também os subagentes nativos; run já consulta este vínculo.'}

def toml_agents(existing,models,limit):
    """Add only missing defaults, cap concurrency downward. Preserve other settings/comments."""
    doc=tomllib.loads(existing) if existing.strip() else {}
    current=doc.get('agents',{})
    if not isinstance(current,dict):fail('CODEX_CONFIG','O campo agents existente não é uma tabela TOML.')
    defaults={'max_concurrent_threads_per_session':limit,'default_subagent_model':models['triage']['model'],
              'default_subagent_reasoning_effort':models['triage']['effort']}
    # Honor explicit disabling / model choices; neither a permission nor a global provider is changed.
    old_limit=current.get('max_concurrent_threads_per_session',current.get('max_threads'))
    if old_limit is not None:
        if isinstance(old_limit,bool) or not isinstance(old_limit,int) or old_limit<1:fail('CODEX_CONFIG','Limite de concorrência existente inválido.')
        defaults['max_concurrent_threads_per_session']=min(limit,old_limit)
    if 'agents' in doc and not re.search(r'(?m)^\s*\[agents\]\s*(?:#.*)?$',existing):
        fail('CODEX_CONFIG_COMPLEX','Configuração agents usa forma inline/dotted. Mescle manualmente preservando a configuração existente.')
    if 'agents' not in doc:existing=existing.rstrip()+'\n\n[agents]\n'
    existing=existing.rstrip('\n')+'\n'
    lines=existing.splitlines(keepends=True)
    start=next(i for i,line in enumerate(lines) if re.match(r'^\s*\[agents\]\s*(?:#.*)?$',line.strip()))+1
    end=next((i for i in range(start,len(lines)) if re.match(r'^\s*\[',lines[i])),len(lines))
    section=lines[start:end]
    for k,v in defaults.items():
        if k in current and k!='max_concurrent_threads_per_session':continue
        text=json.dumps(v,ensure_ascii=False)
        found=False
        for i,line in enumerate(section):
            if re.match(r'^\s*'+re.escape(k)+r'\s*=',line):
                if current[k]!=v:section[i]=f'{k} = {text}\n'
                found=True;break
        if not found:section.append(f'{k} = {text}\n')
    result=''.join(lines[:start]+section+lines[end:]);tomllib.loads(result)
    return result

def desired_setup(root,host='both',profile='equilibrado'):
    root=Path(root).resolve();p=validate_profile(root,profile);models=bindings(root);files={}
    if host not in ('claude','codex','both'):fail('HOST','Host desconhecido.')
    if host in ('claude','both'):
        settings=managed_path(root,'.claude/settings.json');old=read_json(settings) if settings.exists() else {}
        args=[interpreter(root),str(root/'tools/memory_hook.py'),'--root',str(root)]
        cmd=subprocess.list2cmdline(args) if os.name=='nt' else shlex.join(args)
        merged=merge(old,cmd)
        files['.claude/settings.json']=(json.dumps(merged,ensure_ascii=False,indent=2)+'\n').encode()
        for role,(tier,turns) in ROLES.items():
            template=root/'adapters/claude'/(role+'.md')
            text=template.read_text(encoding='utf-8')
            text=re.sub(r'(?m)^model: .*$', 'model: '+models['claude'][tier]['model'],text)
            text=re.sub(r'(?m)^maxTurns: .*$', 'maxTurns: '+str(min(turns,p['max_turns']*2)),text)
            files['.claude/agents/'+role+'.md']=text.encode()
    if host in ('codex','both'):
        cfg=managed_path(root,'.codex/config.toml');old=cfg.read_text(encoding='utf-8') if cfg.exists() else ''
        files['.codex/config.toml']=toml_agents(old,models['codex'],p['max_parallel']).encode()
        for role,(tier,turns) in ROLES.items():
            prompt=(root/'adapters/roles'/(role+'.md')).read_text(encoding='utf-8')
            text='\n'.join([f'name = {json.dumps(role)}',f'description = {json.dumps("Video Factory: "+role)}',
              f'model = {json.dumps(models["codex"][tier]["model"])}',f'model_reasoning_effort = {json.dumps(models["codex"][tier]["effort"])}',
              'sandbox_mode = "read-only"',f'developer_instructions = {json.dumps(prompt,ensure_ascii=False)}',''])
            tomllib.loads(text);files['.codex/agents/'+role+'.toml']=text.encode()
    return files

def apply_files(root,files,kind='setup',apply=False,known=None):
    """known supplies the trusted previous hashes. Modified managed files become conflicts."""
    root=Path(root).resolve();changes=[];conflicts=[]
    for rel,data in files.items():
        p=managed_path(root,rel)
        if p.exists() and not p.is_file():fail('NON_FILE_TARGET','Destino não é um arquivo regular.',path=rel)
        before=sha(p) if p.exists() else None;after=hashlib.sha256(data).hexdigest()
        if before==after:continue
        if known is not None and before is not None and before!=known.get(rel):
            conflicts.append(rel);continue
        changes.append({'path':rel,'before':before,'after':after})
    out={'ok':True,'status':'preview','kind':kind,'changes':changes,'conflicts':conflicts,'permissions_expanded':False}
    if not apply:return out
    if not changes and not conflicts:return {**out,'status':'already_configured'}
    rid=kind+'-'+uuid.uuid4().hex[:12];backup=inside(root,'.factory/installs/'+rid)
    with workspace_lock(root):
        for c in changes:
            p=managed_path(root,c['path']);actual=sha(p) if p.exists() else None
            if actual!=c['before']:fail('CHANGED_DURING_SETUP','Um arquivo mudou durante a preparação. Gere outra prévia.')
        backup.mkdir(parents=True,exist_ok=False)
        receipt={**out,'id':rid,'at':stamp(),'applied':[]}
        atomic_json(backup/'receipt.json',receipt)
        try:
            for c in changes:
                p=managed_path(root,c['path'])
                if c['before'] is not None:atomic_bytes(inside(backup,'before/'+c['path']),p.read_bytes())
                # Write-ahead journal allows rollback even if interrupted between write and receipt.
                receipt['applied'].append(c);atomic_json(backup/'receipt.json',receipt)
                atomic_bytes(p,files[c['path']])
            for rel in conflicts:atomic_bytes(inside(backup,'incoming/'+rel),files[rel])
        except BaseException:
            receipt['status']='interrupted';atomic_json(backup/'receipt.json',receipt);raise
        receipt['status']='needs_merge' if conflicts else 'installed'
        atomic_json(backup/'receipt.json',receipt)
    return {**out,'status':receipt['status'],'receipt':str(backup/'receipt.json'),'message':'Reabra o agente para carregar configurações. Disponibilidade de modelos e cobrança ainda precisam ser confirmadas.'}

def setup(root=ROOT,host='both',profile='equilibrado',apply=False):
    if sys.version_info<(3,11):fail('PYTHON_VERSION','Use Python 3.11 ou superior para a preparação assistida.')
    access_policy=inside(root,'config/github-access.json')
    if apply and access_policy.is_file() and read_json(access_policy).get('require_authenticated_guided_setup'):
        from github_access import verify
        try:verify(root)
        except (ValueError,OSError,subprocess.SubprocessError) as exc:fail('GITHUB_AUTH_REQUIRED',str(exc))
    files=desired_setup(root,host,profile)
    # Configuration merge is explicit; edited agent files must be preserved, not silently replaced.
    manifest=read_json(Path(root)/'PACKAGE_MANIFEST.json').get('files',{}) if (Path(root)/'PACKAGE_MANIFEST.json').exists() else {}
    known=dict(manifest)
    recorded=inside(root,'.factory/managed-adapters.json')
    if recorded.exists():known.update(read_json(recorded))
    for rel in ('.claude/settings.json','.codex/config.toml'):
        path=managed_path(root,rel)
        if path.exists():known[rel]=sha(path) # these two were structurally merged above
    result=apply_files(root,files,'setup',apply,known)
    if apply:
        from service_keys import prepare
        prepare(root)
        from design_catalog import initialize_defaults,import_legacy_formats
        initialize_defaults(root)
        import_legacy_formats(root)
        from update_local import record_base
        record_base(root)
        saved=read_json(recorded) if recorded.exists() else {}
        for rel in files:
            p=managed_path(root,rel)
            if rel not in result['conflicts'] and p.exists():saved[rel]=sha(p)
        atomic_json(recorded,saved)
        atomic_json(inside(root,'.factory/setup.json'),{'host':host,'profile':profile,'at':stamp(),'status':result['status'],'model_access':'NOT_VERIFIED'})
        if (surface_root(root)/'.factory-root.json').is_file():
            from organize_workspace import organize
            organize(root,apply=True)
    return result

def rollback(root,rid,apply=False):
    if not re.fullmatch(r'(?:setup|upgrade)-[a-f0-9]{12}',rid):fail('RECEIPT_ID','Recibo de instalação inválido.')
    backup=inside(root,'.factory/installs/'+rid);r=read_json(backup/'receipt.json')
    conflicts=[]
    for c in r['applied']:
        p=managed_path(root,c['path']);actual=sha(p) if p.exists() else None
        if actual not in (c['after'],c['before']):conflicts.append(c['path'])
    if conflicts:fail('ROLLBACK_CONFLICT','Há arquivos alterados após a instalação. Não serão sobrescritos.',conflicts=conflicts)
    if apply:
        with workspace_lock(root):
            for c in r['applied']:
                p=managed_path(root,c['path']);actual=sha(p) if p.exists() else None
                if actual not in (c['after'],c['before']):fail('ROLLBACK_CONFLICT','Arquivo mudou durante a reversão; gere outra prévia.')
            for c in reversed(r['applied']):
                p=managed_path(root,c['path'])
                if c['before'] is None:p.unlink(missing_ok=True)
                else:atomic_bytes(p,inside(backup,'before/'+c['path']).read_bytes())
            r['status']='rolled_back';atomic_json(backup/'receipt.json',r)
            registry=inside(root,'.factory/managed-adapters.json')
            if registry.exists():
                known=read_json(registry)
                for c in r['applied']:
                    if c['path'] not in known:continue
                    current=managed_path(root,c['path'])
                    if current.exists():known[c['path']]=sha(current)
                    else:known.pop(c['path'],None)
                atomic_json(registry,known)
            status=inside(root,'.factory/setup.json')
            if status.exists():
                saved=read_json(status);saved['status']='rolled_back_recheck_setup';atomic_json(status,saved)
    return {'ok':True,'status':'rolled_back' if apply else 'preview','files':[c['path'] for c in r['applied']]}

def upgrade(source,target,apply=False):
    source=Path(source).resolve();target=Path(target).resolve()
    if source==target:fail('SAME_DIRECTORY','Extraia a nova versão em outra pasta para atualizar a instalação anterior.')
    old=read_json(target/'PACKAGE_MANIFEST.json');new=read_json(source/'PACKAGE_MANIFEST.json')
    if new.get('release_schema',1)>=2:
        from update_local import install
        return install(target,source,apply)
    files={}
    for rel,expected in new['files'].items():
        p=inside(source,rel)
        if not p.is_file() or sha(p)!=expected:fail('CORRUPT_PACKAGE','Pacote novo não passou na verificação de integridade.',path=rel)
        if rel.startswith(('.factory/','.venv/')) or '.sqlite' in rel or rel.endswith('.pyc'):fail('PRIVATE_IN_PACKAGE','O pacote contém dados privados/de execução; não será aplicado.')
        files[rel]=p.read_bytes()
    # Runtime/client data never occur in the manifest of a generic package. Never delete unknown files.
    # Preserve actual hook and project config until setup structurally merges them on the target machine.
    files.pop('.claude/settings.json',None);files.pop('.codex/config.toml',None)
    # Include the manifest in the journal so rollback restores the baseline too.
    preview=apply_files(target,files,'upgrade',False,old['files'])
    baseline=dict(old['files'])
    for rel in files:
        if rel not in preview['conflicts']:baseline[rel]=new['files'][rel]
    new_manifest={'package':new['package'],'version':new['version'],'files':baseline,
                  'upgrade_status':'needs_merge' if preview['conflicts'] else 'installed'}
    files['PACKAGE_MANIFEST.json']=(json.dumps(new_manifest,ensure_ascii=False,indent=2)+'\n').encode()
    known={**old['files'],'PACKAGE_MANIFEST.json':sha(target/'PACKAGE_MANIFEST.json')}
    result=apply_files(target,files,'upgrade',apply,known)
    result['next_action']='Execute factory.py setup --apply na instalação atualizada; resolva os conflitos listados sem apagar suas personalizações.'
    return result

def dependency_plan(root,capability='speech',system=None,machine=None):
    system=system or platform.system();machine=machine or platform.machine();root=Path(root).resolve()
    if capability not in ('base','speech','motion','studio-audio','ffmpeg'):fail('CAPABILITY','Capacidade de instalação desconhecida.')
    py=root/'.venv'/('Scripts/python.exe' if system=='Windows' else 'bin/python')
    commands=[];notes=[]
    if capability=='ffmpeg':
        if shutil.which('ffmpeg') and shutil.which('ffprobe'):notes.append('FFmpeg/FFprobe já encontrados no PATH.')
        elif system=='Darwin' and shutil.which('brew'):commands=[['brew','install','ffmpeg']]
        elif system=='Windows' and shutil.which('winget'):commands=[['winget','install','--id','Gyan.FFmpeg','--exact','--source','winget']]
        elif system=='Linux' and shutil.which('apt-get'):
            if hasattr(os,'geteuid') and os.geteuid()==0:commands=[['apt-get','update'],['apt-get','install','-y','ffmpeg']]
            else:notes.append('Instale FFmpeg pelo gerenciador autorizado da máquina. Não executarei sudo nem pedirei senha silenciosamente.')
        else:notes.append('Gerenciador compatível não encontrado. O agente deve apresentar um caminho de instalação para este sistema e pedir autorização.')
    else:
        if not py.is_file():commands.append([sys.executable,'-m','venv',str(root/'.venv')])
        packages=['PyYAML>=6,<7']
        if capability=='speech':packages+=['mlx-whisper'] if system=='Darwin' and machine.lower() in ('arm64','aarch64') else ['faster-whisper']
        if capability=='motion':packages+=['playwright','Pillow>=10,<13','numpy>=1.26,<3']
        if capability=='studio-audio':packages+=['numpy>=1.26,<3','librosa>=0.11,<0.12','soundfile>=0.12,<1']
        commands.append([str(py),'-m','pip','install',*packages])
        if capability=='motion':
            commands.append([str(py),'-m','playwright','install','chromium'])
            if not shutil.which('node'):notes.append('Node.js não encontrado: necessário para testes JS e rotas React/Node. O renderer HTML/Canvas por Python não depende de Node.')
        if capability=='speech':notes.append('Os pesos do transcritor ainda podem precisar de download autorizado no primeiro uso. Importar a biblioteca não testa reconhecimento de fala.')
    return {'ok':True,'status':'preview','capability':capability,'commands':commands,'notes':notes,'downloads':bool(commands),'no_llm_calls':True}

def dependencies(root,capability='speech',apply=False):
    plan=dependency_plan(root,capability)
    if not apply:return plan
    with workspace_lock(root,'dependencies'):
        for cmd in plan['commands']:
            try:subprocess.run(cmd,cwd=root,check=True,timeout=900)
            except (OSError,subprocess.SubprocessError) as e:fail('INSTALL_FAILED','A instalação parou; componentes anteriores podem já ter sido instalados.','Execute o diagnóstico antes de tentar novamente.',command=cmd,error=type(e).__name__)
    return {**plan,'status':'commands_executed','doctor':collect(root),'note':'Dependências são instalações reais na máquina; rollback de configurações não desinstala pacotes.'}
