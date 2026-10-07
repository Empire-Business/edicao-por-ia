#!/usr/bin/env python3
"""Resumable jobs and batch-wide reservations. SQLite transactions serialize concurrent writers.
This is a local controller, not a tamper-proof barrier against a host with filesystem access.
"""
from __future__ import annotations
from contextlib import contextmanager
import json, os, sqlite3, uuid, math, subprocess
from pathlib import Path
from factory_common import (ROOT, fail, ident, inside, read_json, atomic_json, canonical,
                            fingerprint, sha, stamp, usd_units, dollars, validate_profile, safe_text)
from client_memory import Memory
from project_layout import engine_root, translate
from workspace_files import resolve_file, portable
from design_catalog import select_pair, editing_format, editing_context
from edition_codes import code_for,job_key
STAGES={
    'probe':(), 'transcript':('probe',), 'scope':('transcript',),
    'script':('scope',), 'assembly':('script',), 'silence':('assembly',),
    'visual':('silence',), 'captions':('silence',),
    'preview':('visual','captions'), 'approval':('preview',),
    'final':('approval',), 'qa':('final',), 'delivery':('qa',)}
CHANGE_START={'source':'probe','script':'script','assembly':'assembly','silence':'silence',
              'asset':'visual','visual':'visual','captions':'captions','pattern':'assembly'}
OPTIONAL={'transcript','script','silence','visual','captions'}
TERMINAL={'completed','skipped'}
def descendants(stage):
    selected={stage}
    while True:
        new=selected|{s for s,deps in STAGES.items() if selected.intersection(deps)}
        if new==selected:return [s for s in STAGES if s in selected]
        selected=new

def input_file(raw,group,root):
    try:p=Path(raw).expanduser().resolve(strict=True)
    except (OSError,TypeError):fail('MISSING_INPUT','Um arquivo informado não foi encontrado.',file=str(raw))
    try:p=resolve_file(p,root)
    except ValueError:fail('EXTERNAL_ASSET','O material está fora de edicao-por-ia. Importe uma cópia para dentro da fábrica antes de editar.')
    if not p.is_file() or p.stat().st_size==0:fail('EMPTY_INPUT','Arquivo ausente, vazio ou não regular.',file=str(raw))
    return {'path':str(p),'sha256':sha(p),'group':group,'bytes':p.stat().st_size}

class State:
    def __init__(self,root=ROOT):
        self.root=engine_root(root)
        if (self.root/'.factory/update.lock').exists():fail('UPDATE_IN_PROGRESS','A fábrica está sendo atualizada ou recuperada. Aguarde a conclusão antes de iniciar uma edição.')
        if not self.root.is_dir():fail('MISSING_WORKSPACE','A pasta de trabalho não existe.')
        marker=inside(self.root,'.factory/workspace.json')
        if not marker.exists():atomic_json(marker,{'version':1,'material_paths':'workspace_relative'})
        self.path=inside(self.root,'.factory/state.sqlite3');self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as d:
            d.executescript('''
            CREATE TABLE IF NOT EXISTS batches (
             id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, request TEXT NOT NULL, profile TEXT NOT NULL,
             mode TEXT NOT NULL, cap_mode TEXT NOT NULL, limit_u INTEGER, remote_allowed INTEGER NOT NULL DEFAULT 0,
             billing_confirmed INTEGER NOT NULL DEFAULT 0, frozen INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS request_lookup ON batches(fingerprint);
            CREATE TABLE IF NOT EXISTS jobs (
             id TEXT PRIMARY KEY, batch TEXT NOT NULL, client TEXT, project TEXT, path TEXT NOT NULL,
             manifest TEXT NOT NULL, created TEXT NOT NULL, FOREIGN KEY(batch) REFERENCES batches(id));
            CREATE TABLE IF NOT EXISTS stages (
             job TEXT NOT NULL, stage TEXT NOT NULL, status TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0,
             evidence TEXT NOT NULL DEFAULT '[]', note TEXT NOT NULL DEFAULT '', updated TEXT NOT NULL,
             PRIMARY KEY(job,stage), FOREIGN KEY(job) REFERENCES jobs(id));
            CREATE TABLE IF NOT EXISTS calls (
             id TEXT PRIMARY KEY, batch TEXT NOT NULL, job TEXT NOT NULL, task TEXT NOT NULL, request_hash TEXT NOT NULL,
             host TEXT NOT NULL, model TEXT NOT NULL, tier TEXT NOT NULL, status TEXT NOT NULL,
             reserved_u INTEGER NOT NULL, actual_u INTEGER, usage TEXT, result TEXT, created TEXT NOT NULL,
             FOREIGN KEY(batch) REFERENCES batches(id), FOREIGN KEY(job) REFERENCES jobs(id));
            CREATE TABLE IF NOT EXISTS audit (
             seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT NOT NULL,
             subject TEXT NOT NULL, detail TEXT NOT NULL);
            ''')
        try:self.path.chmod(0o600)
        except OSError:pass
    @contextmanager
    def db(self,write=False):
        d=sqlite3.connect(str(self.path),timeout=20,isolation_level=None);d.row_factory=sqlite3.Row
        d.execute('PRAGMA foreign_keys=ON');d.execute('PRAGMA busy_timeout=20000')
        try:
            if write:d.execute('BEGIN IMMEDIATE')
            yield d
            if write:d.execute('COMMIT')
        except BaseException:
            if write:d.execute('ROLLBACK')
            raise
        finally:d.close()
    def serialize(self,value):return canonical(portable(value,self.root))
    def write_json(self,path,value):return atomic_json(path,portable(value,self.root))
    def event(self,d,kind,subject,detail):
        d.execute('INSERT INTO audit(at,kind,subject,detail) VALUES (?,?,?,?)',(stamp(),kind,subject,self.serialize(detail)))
    def normalize(self,request):
        if not isinstance(request,dict):fail('INVALID_REQUEST','O pedido estruturado precisa ser um objeto.')
        request=translate(request,self.root)
        r=json.loads(canonical(request))
        allowed={'id','name','sources','expected_outputs','reference_scripts','reference_assignments','supporting_assets','pattern',
                 'profile','format','client','project','anonymous','branding','visual_identity','budget','notes','speech_cleanup','captions','silence_mode','format_deviations'}
        unknown=set(r)-allowed
        if unknown:fail('UNKNOWN_FIELDS','Há campos de entrada desconhecidos; não foram ignorados.',fields=sorted(unknown))
        for k in ('anonymous','speech_cleanup'):
            if k in r and not isinstance(r[k],bool):fail('INVALID_FLAG',f'{k} precisa ser true ou false.')
        if 'captions' in r and not isinstance(r['captions'],bool) and r['captions']!='pattern_default':fail('INVALID_CAPTIONS','Use true, false ou pattern_default para legendas.')
        if 'budget' in r and not isinstance(r['budget'],dict):fail('INVALID_BUDGET','Orçamento precisa ser um objeto.')
        if 'format_deviations' in r and (not isinstance(r['format_deviations'],dict) or not all(isinstance(k,str) and isinstance(v,str) and v.strip() for k,v in r['format_deviations'].items())):fail('FORMAT_DEVIATIONS','Exceções precisam de critério e instrução explícita do usuário.')
        sources=r.get('sources',[])
        if not isinstance(sources,list) or not sources:fail('MISSING_SOURCE','Envie a gravação para começar.')
        n=r.get('expected_outputs',1)
        if isinstance(n,bool) or not isinstance(n,int) or not 1<=n<=50:fail('OUTPUT_COUNT','Informe de 1 a 50 vídeos por lote.')
        profile=r.get('profile','equilibrado');validate_profile(self.root,profile)
        if r.get('format') is not None and r.get('client') is not None and r['format']!=r['client']:
            fail('FORMAT_CONFLICT','O pedido informa dois formatos diferentes; mantenha apenas um ID ou use o mesmo nos dois campos.')
        client=r.get('format') if r.get('format') is not None else r.get('client')
        if r.get('anonymous') and (client or r.get('project')):fail('CLIENT_CONFLICT','Um trabalho anônimo não pode ter formato/projeto nomeado.')
        if r.get('anonymous') or not client:
            fail('FORMAT_REQUIRED','Qual formato devo usar neste vídeo? Informe um formato cadastrado ou cadastre um novo antes de editar.')
        project=r.get('project')
        if project and not client:fail('UNKNOWN_CLIENT','Qual formato reúne este projeto?')
        try:editing,identity=select_pair(self.root,client,r.get('visual_identity'))
        except ValueError as exc:
            fail('VISUAL_IDENTITY_REQUIRED' if not r.get('visual_identity') else 'DESIGN_SELECTION',str(exc))
        client=editing['memory_store']
        if editing.get('validation_status')=='reference_analysis_pending':fail('FORMAT_REFERENCE_ANALYSIS_REQUIRED','O cadastro ainda precisa da análise do exemplo e de uma receita específica antes de editar.')
        if project:ident(project,'projeto')
        preference=editing['pattern']
        from format_fidelity import snapshot
        format_contract=snapshot(self.root,editing)
        # New formats are color/font-independent; the ID is selected separately.
        pattern=r.get('pattern') or preference;ident(pattern,'padrão')
        pat=inside(self.root,'patterns/'+pattern+'.yaml')
        if not pat.is_file():fail('UNKNOWN_PATTERN','Não encontrei esse padrão.',patterns=sorted(p.stem for p in (self.root/'patterns').glob('*.yaml') if not p.name.startswith('_')))
        refs=r.get('reference_scripts',[])
        if not isinstance(refs,list):fail('INVALID_SCRIPTS','Roteiros precisam ser uma lista de arquivos.')
        inputs=[input_file(p,'source',self.root) for p in sources]+[input_file(p,'script',self.root) for p in refs]
        assignments=r.get('reference_assignments',{})
        if not isinstance(assignments,dict):fail('SCRIPT_ASSIGNMENT','Associações devem indicar o número do vídeo e o roteiro.')
        normalized_assignments={}
        for k,v in assignments.items():
            if not str(k).isdigit() or not 1<=int(k)<=n:fail('SCRIPT_ASSIGNMENT','Número de vídeo inválido na associação de roteiro.')
            f=input_file(v,'script',self.root)
            if f['path'] not in [p['path'] for p in inputs if p['group']=='script']:inputs.append(f)
            normalized_assignments[str(int(k))]=f['path']
        if n==1 and len(refs)==1 and not normalized_assignments:normalized_assignments['1']=str(Path(refs[0]).resolve())
        assets=r.get('supporting_assets',[])
        if not isinstance(assets,list):fail('INVALID_ASSETS','Materiais de apoio precisam ser uma lista.')
        normalized_assets=[]
        for a in assets:
            if not isinstance(a,(str,dict)):fail('INVALID_ASSETS','Cada material precisa ser um caminho ou objeto.')
            a={'path':a} if isinstance(a,str) else dict(a)
            f=input_file(a.get('path'),'asset',self.root);inputs.append(f);a['path']=f['path']
            child=a.get('output')
            if child is not None and (isinstance(child,bool) or not isinstance(child,int) or not 1<=child<=n):fail('ASSET_SCOPE','Número de vídeo inválido no material de apoio.')
            if a.get('notes'):safe_text(a['notes'],'nota do material')
            normalized_assets.append(a)
        b=r.get('budget',{});mode=b.get('mode','unknown');cap=b.get('cap_mode','native')
        if mode not in ('unknown','subscription','usd') or cap not in ('native','estimate'):fail('INVALID_BUDGET','Modo de orçamento inválido.')
        limit=usd_units(b.get('limit_usd')) if mode=='usd' else None
        if mode!='usd' and b.get('limit_usd') is not None:fail('INVALID_BUDGET','Um limite em dólares exige modo usd; assinatura não é fatura por tokens.')
        branding=r.get('branding',{'logos_enabled':False,'logo_path':None})
        if not isinstance(branding,dict) or set(branding)-{'logos_enabled','logo_path'}:
            fail('INVALID_BRANDING','Use apenas logos_enabled e logo_path para a marca do trabalho.')
        branding=dict(branding)
        if 'logos_enabled' in branding and not isinstance(branding['logos_enabled'],bool):fail('INVALID_BRANDING','logos_enabled precisa ser true ou false.')
        branding.setdefault('logos_enabled',False);branding.setdefault('logo_path',None)
        if branding['logo_path'] is not None:
            logo=input_file(branding['logo_path'],'asset',self.root);inputs.append(logo);branding['logo_path']=logo['path']
        notes=r.get('notes','')
        if notes:safe_text(notes,'notas')
        if r.get('silence_mode','pattern_default') not in ('pattern_default','natural','tight','relaxed','off'):fail('SILENCE_MODE','Modo de silêncio inválido.')
        video_name=safe_text(r.get('name') or Path(inputs[0]['path']).stem,'nome do vídeo',160)
        # Side effects are delayed until all input fields are validated.
        return {**r,'selection_version':2,'format_code':editing['code'],'format_uid':editing.get('uid'),'format_contract':format_contract,'visual_identity':identity['code'],'branding':branding,'name':video_name,'format':client,'client':client,'project':project,'pattern':pattern,'pattern_sha256':sha(pat),
          'profile':profile,'expected_outputs':n,'inputs':inputs,'sources':[f['path'] for f in inputs if f['group']=='source'],
          'reference_scripts':[f['path'] for f in inputs if f['group']=='script'],
          'reference_assignments':normalized_assignments,'supporting_assets':normalized_assets,
          'budget':{'mode':mode,'cap_mode':cap,'limit_u':limit}}
    def intake(self,request,new_version=False):
        r=self.normalize(request)
        # The format key is a public alias; excluding it keeps fingerprints of legacy
        # requests that used only "client" byte-for-byte stable.
        fingerprint_data={k:v for k,v in r.items() if k not in ('id','format','name','format_uid','format_contract')}
        if 'branding' not in request:fingerprint_data.pop('branding',None)
        # Explicit display-name changes identify a distinct request; the inferred legacy default
        # is excluded so older requests keep their existing fingerprints.
        if request.get('name') is not None:fingerprint_data['name']=r['name']
        key=fingerprint(portable(fingerprint_data,self.root))
        raw_key=fingerprint(fingerprint_data)
        try:old_portable_key=fingerprint(portable(translate(fingerprint_data,self.root,reverse=True),self.root))
        except ValueError:old_portable_key=raw_key  # Historical hash lookup only; no external file is accessed.
        legacy_key=fingerprint(translate(fingerprint_data,self.root,reverse=True))
        given=r.get('id')
        if given:ident(given)
        batch=given or 'video-'+key[:12]
        with self.db(True) as d:
            prior=d.execute('SELECT id, fingerprint FROM batches WHERE id=?',(batch,)).fetchone()
            identical=d.execute('SELECT id FROM batches WHERE fingerprint IN (?,?,?,?) ORDER BY created DESC LIMIT 1',(key,legacy_key,raw_key,old_portable_key)).fetchone()
            if not new_version and prior and prior['fingerprint'] not in (key,legacy_key,raw_key,old_portable_key):fail('JOB_CONFLICT','Esse nome já pertence a outro pedido.','Continue o trabalho existente, registre uma alteração ou peça uma nova versão.')
            if not new_version and identical:
                ids=[row['id'] for row in d.execute('SELECT id FROM jobs WHERE batch=?',(identical['id'],))]
                return {'ok':True,'status':'resume','batch':identical['id'],'jobs':ids,'message':'Esse material já está cadastrado. Continue de onde parou, sem repetir as etapas concluídas.'}
            if new_version:
                base=batch[:65];version=2
                while d.execute('SELECT 1 FROM batches WHERE id=?',(batch,)).fetchone():batch=f'{base}-v{version}';version+=1
            n=r['expected_outputs'];ids=[batch] if n==1 else [batch[:70]+f'-v{i:02d}' for i in range(1,n+1)]
            for jid in ids:
                if inside(self.root,'jobs/'+jid).exists():fail('EXISTING_FOLDER','A pasta já existe e não será sobrescrita.',job=jid)
            d.execute('INSERT INTO batches(id,fingerprint,request,profile,mode,cap_mode,limit_u,created) VALUES (?,?,?,?,?,?,?,?)',
                      (batch,key,self.serialize(r),r['profile'],r['budget']['mode'],r['budget']['cap_mode'],r['budget']['limit_u'],stamp()))
            for i,jid in enumerate(ids,1):
                assigned=r['reference_assignments'].get(str(i))
                pins=['pattern'] if request.get('pattern') else []
                if isinstance(request.get('captions'),bool):pins.append('requirements.captions')
                if 'branding' in request:pins.append('branding.logos_enabled')
                if request.get('branding',{}).get('logo_path') is not None:pins.append('branding.logo_path')
                if 'silence_mode' in request:pins+=['silence_removal.mode','silence_removal.enabled']
                video_name=r['name'] if n==1 else f'v{i:02d}-{r["name"]}'
                job={'edition_code':code_for(self.root,jid,video_name),'id':jid,'batch_id':batch,'name':video_name,'format':r['format'],'client':r['client'],'project':r['project'],'pattern':r['pattern'],'explicit_fields':pins,
                     'selection_version':2,'format_code':r['format_code'],'format_uid':r['format_uid'],'format_contract':r['format_contract'],'visual_identity':r['visual_identity'],'branding':r['branding'],'status':'created','sources':[{'path':p,'role':'primary'} for p in r['sources']],
                     'pattern_sha256':r['pattern_sha256'],'format_deviations':r.get('format_deviations',{}),
                     'expected_outputs':1,'output_index':i,'parent_expected_outputs':n,'scope_pending':n>1,
                     'reference_script':{'enabled':bool(assigned),'paths':[assigned] if assigned else [],'mode':'flexible',
                         'reorder_policy':'preserve_unless_requested','missing_content_policy':'report_do_not_invent'},
                     'script_assignment_pending':bool(r['reference_scripts']) and not assigned,
                     'silence_removal':{'enabled':r.get('silence_mode')!='off','mode':r.get('silence_mode','pattern_default'),'protected_ranges_path':None},
                     'supporting_assets':[a for a in r['supporting_assets'] if a.get('output') in (None,i)],
                     'requirements':{'speech_cleanup':r.get('speech_cleanup',True),'split_source':n>1,'captions':r.get('captions','pattern_default'),'preserve_phrases':[]},
                     'execution_profile':r['profile'],'notes':r.get('notes','')}
                # Store manifests first. Export files after commit; resume repairs interrupted exports.
                d.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',(jid,batch,r['client'],r['project'],'jobs/'+jid,self.serialize(job),stamp()))
                for s in STAGES:d.execute('INSERT INTO stages(job,stage,status,updated) VALUES (?,?,?,?)',(jid,s,'pending',stamp()))
            self.event(d,'intake',batch,{'jobs':ids,'simulated':False})
        for jid in ids:self.ensure_files(jid)
        return {'ok':True,'status':'created','batch':batch,'jobs':ids,'message':'Trabalho organizado. Agora verificar o ambiente e preparar a primeira prévia.'}
    def job(self,jid):
        jid=job_key(self.root,jid)
        with self.db() as d:row=d.execute('SELECT * FROM jobs WHERE id=?',(ident(jid),)).fetchone()
        if not row:fail('UNKNOWN_JOB','Trabalho não encontrado.',job=jid)
        result=dict(row);result['format']=result.get('client');result['edition_code']=code_for(self.root,jid)
        result['manifest']=canonical(translate(json.loads(result['manifest']),self.root))
        return result
    def ensure_files(self,jid):
        row=self.job(jid);path=inside(self.root,row['path']);job=translate(json.loads(row['manifest']),self.root)
        for s in ('analysis','edit','qa','renders','frames','references'):inside(path,s).mkdir(parents=True,exist_ok=True)
        # Existing manifests may have approved edits. Never overwrite them on resume.
        if not (path/'job.yaml').exists():self.write_json(path/'job.yaml',job)
        if not (path/'edit/decision_log.md').exists():(path/'edit/decision_log.md').write_text('# Decision Log\n',encoding='utf-8')
        if job.get('client') and not (path/'job.effective.json').exists():
            from resolve_client_context import write_resolution
            write_resolution(Memory(self.root),path/'job.yaml',path/'job.effective.json')
        return path
    def _invalidate(self,d,jid,stage,note):
        affected=descendants(stage)
        for s in affected:
            d.execute("UPDATE stages SET status=CASE WHEN status='pending' THEN 'pending' ELSE 'stale' END, revision=revision+1,note=?,updated=? WHERE job=? AND stage=?",(note,stamp(),jid,s))
        self.event(d,'invalidate',jid,{'stage':stage,'affected':affected,'reason':note})
        return affected
    def assign_format(self,jid,format_id,note):
        """Explicitly identify a historical unbound job without restarting its batch/budget."""
        ident(format_id,'formato');safe_text(note,'confirmação do formato')
        Memory(self.root).name(format_id)
        row=self.job(jid)
        if row['client'] and row['client']!=format_id:
            fail('CLIENT_MISMATCH','Este trabalho já pertence a outro formato; não foi reassociado.')
        if row['client']==format_id:
            return {'ok':True,'status':'already_bound','job':jid,'format':format_id,'budget_preserved':True}
        path=self.ensure_files(jid)
        from edit_support import read_data
        current=read_data(path/'job.yaml')
        if current.get('format') or current.get('client'):
            fail('CLIENT_MISMATCH','O manifesto já informa um formato; confira sua identidade antes de continuar.')
        current.update(format=format_id,client=format_id)
        recorded=translate(json.loads(row['manifest']),self.root)
        recorded.update(format=format_id,client=format_id)
        with self.db(True) as d:
            d.execute('UPDATE jobs SET client=?,manifest=? WHERE id=?',(format_id,self.serialize(recorded),jid))
            self._invalidate(d,jid,'assembly','Formato identificado pelo usuário: '+note)
            self.event(d,'assign_format',jid,{'format':format_id,'note':note,'budget_preserved':True})
        self.write_json(path/'job.yaml',current)
        # No batch, request fingerprint, calls, reservations or spend is reset.
        self.refresh_context(jid,'Formato confirmado: '+note)
        return {'ok':True,'status':'bound','job':jid,'format':format_id,'budget_preserved':True}

    def assign_design(self,jid,format_value,visual_value,note):
        jid=job_key(self.root,jid);safe_text(note,'escolha confirmada')
        editing,identity=select_pair(self.root,format_value,visual_value)
        row=self.job(jid);path=self.ensure_files(jid)
        from edit_support import read_data
        current=read_data(path/'job.yaml')
        version=1
        while (path/f'job.before-design-v{version}.json').exists():version+=1
        self.write_json(path/f'job.before-design-v{version}.json',current)
        current.update(selection_version=2,format=editing['memory_store'],client=editing['memory_store'],
                       format_code=editing['code'],visual_identity=identity['code'],pattern=editing['pattern'],
                       edition_code=row['edition_code'])
        from format_fidelity import snapshot
        current.update(format_uid=editing.get('uid'),format_contract=snapshot(self.root,editing))
        self.write_json(path/'job.yaml',current)
        with self.db(True) as d:
            d.execute('UPDATE jobs SET client=?,manifest=? WHERE id=?',(editing['memory_store'],self.serialize(current),jid))
            self._invalidate(d,jid,'assembly','Formato e ID visual escolhidos: '+note)
            self.event(d,'assign_design',jid,{'format':editing['code'],'visual_identity':identity['code'],'budget_preserved':True})
        self.refresh_context(jid,'Aplicar escolhas '+editing['code']+' + '+identity['code'])
        return {'ok':True,'job':jid,'edition_code':row['edition_code'],'format_code':editing['code'],'visual_identity':identity['code'],'budget_preserved':True}

    def change(self,jid,kind,note):
        self.job(jid);safe_text(note,'motivo')
        if kind not in CHANGE_START:fail('CHANGE_KIND','Tipo de alteração desconhecido.',kinds=list(CHANGE_START))
        with self.db(True) as d:affected=self._invalidate(d,jid,CHANGE_START[kind],note)
        return {'ok':True,'job':jid,'invalidated':affected,'preserved':[s for s in STAGES if s not in affected]}
    def checkpoint(self,jid,stage,artifacts=None,note='',skip=False,user_approved=False):
        row=self.job(jid)
        if not row['client']:fail('FORMAT_REQUIRED','Informe ou cadastre o formato deste trabalho antes de editar.')
        job_path=self.ensure_files(jid)
        if stage not in STAGES:fail('UNKNOWN_STAGE','Etapa desconhecida.',stages=list(STAGES))
        safe_text(note,'evidência ou observação')
        if skip and stage not in OPTIONAL:fail('REQUIRED_STAGE','Esta etapa não pode ser ignorada.')
        manifest=translate(json.loads(row['manifest']),self.root)
        if not manifest.get('visual_identity'):fail('VISUAL_IDENTITY_REQUIRED','Escolha um formato F e uma ID visual antes de editar este trabalho antigo.')
        if stage in ('script','assembly') and manifest.get('script_assignment_pending'):
            fail('SCRIPT_ASSIGNMENT_REQUIRED','Associe o roteiro a este vídeo antes de continuar; a ordem dos arquivos não foi presumida.')
        if stage=='script' and skip and manifest.get('reference_script',{}).get('enabled'):
            fail('REFERENCE_REQUIRED','Há um roteiro atribuído. Compare-o ou registre uma dispensa explícita com assign-script --without-script.')
        if stage=='approval' and not user_approved:fail('USER_APPROVAL_REQUIRED','A prévia precisa de uma aprovação explícita do usuário.')
        evidence=[]
        for a in artifacts or []:
            p=Path(a).resolve(strict=True)
            if not p.is_relative_to(job_path):fail('CROSS_JOB_ARTIFACT','A evidência deve pertencer a este vídeo, não a outro formato/trabalho.')
            inside(self.root,p)
            if not p.is_file() or not p.stat().st_size:fail('EMPTY_ARTIFACT','A evidência precisa ser um arquivo não vazio.')
            evidence.append({'path':str(p.relative_to(self.root)),'sha256':sha(p)})
        if not skip and stage!='approval' and not evidence:fail('MISSING_EVIDENCE','Informe o arquivo efetivamente produzido ou conferido nesta etapa.')
        if stage=='scope':self.validate_scope(jid,evidence)
        if stage in ('assembly','qa','delivery') and manifest.get('format_contract'):
            from format_fidelity import validate as fidelity_validate
            phase='plan' if stage=='assembly' else 'review'
            try:report=fidelity_validate(self.root,job_path,manifest,phase)
            except (ValueError,OSError,KeyError) as exc:fail('FORMAT_FIDELITY_REQUIRED',str(exc))
            if stage!='delivery' and report.get('report') not in [x['path'] for x in evidence]:
                fail('FORMAT_FIDELITY_REQUIRED','Registre a comparação real entre as evidências desta etapa.')
        if stage in ('assembly','silence') and not skip:
            plans=[f for f in evidence if f['path'].endswith('.json') and isinstance(read_json(inside(self.root,f['path'])),dict) and 'segments' in read_json(inside(self.root,f['path']))]
            if not plans:fail('EDL_REQUIRED','Registre a EDL real entre as evidências desta etapa.')
            self.validate_edl(jid,inside(self.root,plans[0]['path']))
        with self.db(True) as d:
            states={r['stage']:r['status'] for r in d.execute('SELECT stage,status FROM stages WHERE job=?',(jid,))}
            missing=[s for s in STAGES[stage] if states[s] not in TERMINAL]
            if missing:fail('STAGE_ORDER','Ainda há etapas anteriores pendentes.',stages=missing)
            # Updating a completed stage invalidates dependent artifacts, including approval.
            if states[stage] in TERMINAL:self._invalidate(d,jid,stage,'Etapa atualizada: '+note)
            d.execute('UPDATE stages SET status=?,evidence=?,note=?,updated=? WHERE job=? AND stage=?',('skipped' if skip else 'completed',self.serialize(evidence),note,stamp(),jid,stage))
            self.event(d,'checkpoint',jid,{'stage':stage,'status':'skipped' if skip else 'completed','evidence':evidence,'user_approved':user_approved})
            if stage=='scope':
                manifest['scope_pending']=False
                manifest['source_scope_path']=next(f['path'] for f in evidence if f['path'].endswith('.json'))
                d.execute('UPDATE jobs SET manifest=? WHERE id=?',(self.serialize(manifest),jid))
        if stage=='scope':
            from edit_support import read_data
            current=read_data(job_path/'job.yaml')
            current.update(scope_pending=False,source_scope_path=manifest['source_scope_path'])
            self.write_json(job_path/'job.yaml',current)
        return self.resume(jid)
    def media_duration(self,path):
        try:
            r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=30)
            value=float(json.loads(r.stdout)['format']['duration'])
        except (OSError,ValueError,KeyError,subprocess.SubprocessError):
            fail('PROBE_REQUIRED','Não foi possível verificar a duração da fonte; execute o diagnóstico antes de definir o recorte.')
        if not math.isfinite(value) or value<=0:fail('INVALID_DURATION','Duração de mídia inválida.')
        return value
    def validate_scope(self,jid,evidence):
        row=self.job(jid);manifest=translate(json.loads(row['manifest']),self.root)
        candidates=[f for f in evidence if f['path'].endswith('.json')]
        if not candidates:fail('SCOPE_REQUIRED','A etapa scope exige um JSON com job_id e segments (source/in/out).')
        scope=read_json(inside(self.root,candidates[0]['path']))
        if scope.get('job_id')!=jid:fail('SCOPE_MISMATCH','O recorte precisa identificar exatamente este vídeo.')
        segs=scope.get('segments');allowed={s['path'] for s in manifest['sources']}
        if not isinstance(segs,list) or not segs:fail('SCOPE_REQUIRED','O recorte precisa conter trechos reais da gravação.')
        durations={}
        for s in segs:
            if not isinstance(s,dict) or s.get('source') not in allowed:fail('SCOPE_SOURCE','Fonte do recorte não pertence à gravação deste trabalho.')
            a=s.get('in');b=s.get('out')
            if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in (a,b)) or not 0<=a<b:
                fail('SCOPE_RANGE','Tempos de recorte inválidos.')
            if s['source'] not in durations:durations[s['source']]=self.media_duration(s['source'])
            if b>durations[s['source']]+.05:fail('SCOPE_RANGE','O recorte ultrapassa a duração real da fonte.')
        # Duplicated time between independent outputs is not assumed. Explicit reuse belongs in the evidence.
        with self.db() as d:
            others=list(d.execute("SELECT s.job,s.evidence FROM stages s JOIN jobs j ON j.id=s.job WHERE j.batch=? AND j.id!=? AND s.stage='scope' AND s.status='completed'",(row['batch'],jid)))
        for other in others:
            for f in json.loads(other['evidence']):
                if not f['path'].endswith('.json'):continue
                other_scope=read_json(inside(self.root,f['path']))
                overlaps=[(a,b) for a in segs for b in other_scope.get('segments',[]) if a['source']==b['source'] and min(a['out'],b['out'])>max(a['in'],b['in'])+.001]
                if overlaps and not scope.get('shared_ranges_authorized'):
                    fail('CHILD_SCOPE_OVERLAP','Dois vídeos reutilizam a mesma fala. Confirme a separação ou registre autorização para essa reutilização.',other_job=other['job'])
        return scope
    def validate_edl(self,jid,edl_path):
        self.resume(jid)  # invalidate stale evidence before authorizing a render plan
        row=self.job(jid);path=Path(edl_path).resolve(strict=True)
        if not path.is_relative_to(self.ensure_files(jid)):fail('CROSS_JOB_ARTIFACT','A montagem precisa estar na pasta deste vídeo.')
        with self.db() as d:scope_row=d.execute("SELECT * FROM stages WHERE job=? AND stage='scope'",(jid,)).fetchone()
        if scope_row['status']!='completed':fail('SCOPE_REQUIRED','Delimite e confira este vídeo antes de validar a montagem.')
        scope=self.validate_scope(jid,json.loads(scope_row['evidence']))
        edl=read_json(path);segs=edl.get('segments')
        if not isinstance(segs,list) or not segs:fail('EDL_REQUIRED','A montagem precisa conter trechos.')
        def covered(source,a,b):
            windows=sorted((x['in'],x['out']) for x in scope['segments'] if x['source']==source)
            cursor=a
            for lo,hi in windows:
                if hi<cursor-.001:continue
                if lo>cursor+.001:return False
                cursor=max(cursor,hi)
                if cursor>=b-.001:return True
            return False
        for s in segs:
            a=s.get('in');b=s.get('out')
            if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in (a,b)) or not 0<=a<b:
                fail('EDL_RANGE','Tempos inválidos na montagem.')
            if not covered(s.get('source'),a,b):fail('EDL_OUTSIDE_SCOPE','A montagem usa fala de fora do recorte aprovado deste vídeo.',segment=s)
        return {'ok':True,'job':jid,'edl':str(path),'sha256':sha(path),'segments':len(segs),'scope_checked':True,
                'note':'Valida somente escopo e tempos; não comprova qualidade semântica ou audiovisual.'}
    def assign_script(self,jid,path=None,note='',without_script=False):
        row=self.job(jid);safe_text(note,'decisão de roteiro')
        if bool(path)==bool(without_script):fail('SCRIPT_ASSIGNMENT','Informe um roteiro ou uma dispensa explícita, nunca ambos.')
        f=input_file(path,'script',self.root) if path else None
        job_path=self.ensure_files(jid)
        from edit_support import read_data
        job=read_data(job_path/'job.yaml')
        if job.get('id')!=jid or job.get('client')!=row['client']:fail('MANIFEST_CHANGED','Identidade do trabalho foi alterada fora do controlador.')
        job['reference_script'].update({'enabled':bool(f),'paths':[f['path']] if f else []})
        job['script_assignment_pending']=False
        with self.db(True) as d:
            if f:
                batch=d.execute('SELECT request FROM batches WHERE id=?',(row['batch'],)).fetchone();r=translate(json.loads(batch['request']),self.root)
                if f['path'] not in [x['path'] for x in r['inputs']]:r['inputs'].append(f);r['reference_scripts'].append(f['path'])
                r['reference_assignments'][str(job['output_index'])]=f['path']
                d.execute('UPDATE batches SET request=? WHERE id=?',(self.serialize(r),row['batch']))
            d.execute('UPDATE jobs SET manifest=? WHERE id=?',(self.serialize(job),jid))
            self._invalidate(d,jid,'script',note);self.event(d,'assign_script',jid,{'script':f,'without_script':without_script,'note':note})
        self.write_json(job_path/'job.yaml',job)
        if row['client']:self.refresh_context(jid,'Nova associação de roteiro: '+note)
        return {'ok':True,'job':jid,'reference_script':job['reference_script']}
    def refresh_inputs(self,batch,note):
        safe_text(note,'autorização de versões de entrada')
        with self.db(True) as d:
            b=d.execute('SELECT request FROM batches WHERE id=?',(ident(batch),)).fetchone()
            if not b:fail('UNKNOWN_BATCH','Lote não encontrado.')
            r=translate(json.loads(b['request']),self.root);changes=[];inputs=[]
            for old in r['inputs']:
                new=input_file(old['path'],old['group'],self.root);inputs.append(new)
                if new['sha256']!=old['sha256']:changes.append(new['group'])
            pat=inside(self.root,'patterns/'+r['pattern']+'.yaml')
            if not pat.is_file():fail('UNKNOWN_PATTERN','O padrão foi removido; restaure-o ou crie outra versão do trabalho.')
            if sha(pat)!=r['pattern_sha256']:changes.append('pattern')
            r['inputs']=inputs;r['pattern_sha256']=sha(pat)
            ids=[x['id'] for x in d.execute('SELECT id FROM jobs WHERE batch=?',(batch,))]
            for jid in ids:
                for kind in set(changes):self._invalidate(d,jid,CHANGE_START[kind],note)
            d.execute('UPDATE batches SET request=?,fingerprint=? WHERE id=?',(self.serialize(r),fingerprint({k:v for k,v in r.items() if k!='id'}),batch))
            self.event(d,'refresh_inputs',batch,{'groups':changes,'note':note})
        return {'ok':True,'batch':batch,'changed_groups':sorted(set(changes)),'jobs':ids,'message':'Versões de entrada confirmadas; refazer somente as etapas invalidadas. Originais não foram modificados por esta operação.'}
    def refresh_context(self,jid,note):
        safe_text(note,'decisão de atualização de contexto');row=self.job(jid);path=self.ensure_files(jid)
        if not row['client']:return {'ok':True,'status':'not_applicable','job':jid}
        from resolve_client_context import write_resolution, read_data
        job=read_data(path/'job.yaml')
        if job.get('client')!=row['client'] or job.get('id')!=jid:fail('CLIENT_MISMATCH','Identidade do manifesto diverge do trabalho cadastrado.')
        # Approved artifacts remain on disk. A new effective version avoids overwrite.
        version=2
        while (path/f'job.effective-v{version}.json').exists():version+=1
        result=write_resolution(Memory(self.root),path/'job.yaml',path/f'job.effective-v{version}.json')
        self.write_json(path/'effective-current.json',{'path':str(Path(result['effective_job']).relative_to(self.root))})
        with self.db(True) as d:
            self._invalidate(d,jid,'assembly',note);self.event(d,'refresh_context',jid,{'effective':result,'note':note})
        return {'ok':True,'job':jid,**result,'message':'Contexto recuperado e versão efetiva criada. Confira decisões editoriais; transcrição original preservada.'}
    def resume(self,jid=None,client=None):
        jid=job_key(self.root,jid) if jid else None
        if not jid:
            with self.db() as d:
                rows=list(d.execute('SELECT id,client,batch FROM jobs WHERE client=? ORDER BY created DESC',(client,))) if client else list(d.execute('SELECT id,client,batch FROM jobs ORDER BY created DESC'))
            if not client or len(rows)!=1:
                jobs=[]
                for item in rows:
                    job_row=dict(item);job_row['format']=job_row.get('client');job_row['edition_code']=code_for(self.root,item['id']);jobs.append(job_row)
                return {'ok':True,'status':'choose_job','message':'Qual trabalho você quer continuar?','jobs':jobs}
            jid=rows[0]['id']
        row=self.job(jid)
        if not row['client']:fail('FORMAT_REQUIRED','Informe ou cadastre o formato deste trabalho antes de editar.')
        if client and row['client']!=client:fail('CLIENT_MISMATCH','Este trabalho pertence a outro formato.')
        path=self.ensure_files(jid)
        memory_stale=False
        if row['client']:
            from resolve_client_context import check
            pointer=path/'effective-current.json'
            effective=inside(self.root,read_json(pointer)['path']) if pointer.exists() else path/'job.effective.json'
            memory_stale=not check(Memory(self.root),read_json(effective))['ok']
        with self.db(True) as d:
            if memory_stale:self._invalidate(d,jid,'assembly','Feedback/contexto mudou; use refresh-context para conferir e aplicar a nova versão.')
            batch=d.execute('SELECT request FROM batches WHERE id=?',(row['batch'],)).fetchone();r=translate(json.loads(batch['request']),self.root)
            input_changes=[]
            for f in r['inputs']:
                try:p=resolve_file(f['path'],self.root,False)
                except ValueError:fail('EXTERNAL_ASSET','Este trabalho antigo ainda depende de material externo. Importe uma cópia interna antes de retomar; o lote e o orçamento foram preservados.')
                if not p.is_file() or sha(p)!=f['sha256']:input_changes.append({'path':f['path'],'group':f['group']})
            if not (self.root/'patterns'/(r['pattern']+'.yaml')).is_file() or sha(self.root/'patterns'/(r['pattern']+'.yaml'))!=r['pattern_sha256']:
                input_changes.append({'path':'patterns/'+r['pattern']+'.yaml','group':'pattern'})
            if input_changes:
                for kind in {i['group'] for i in input_changes}:self._invalidate(d,jid,CHANGE_START[kind],'Arquivo de entrada mudou ou está ausente; confirme a substituição antes de continuar.')
            for s in list(d.execute('SELECT * FROM stages WHERE job=?',(jid,))):
                if s['status']!='completed':continue
                for f in json.loads(s['evidence']):
                    p=inside(self.root,f['path'])
                    if not p.is_file() or sha(p)!=f['sha256']:
                        self._invalidate(d,jid,s['stage'],'Evidência ausente ou modificada.');break
            stages={s['stage']:dict(s) for s in d.execute('SELECT * FROM stages WHERE job=?',(jid,))}
        selection_missing=not json.loads(row['manifest']).get('visual_identity')
        ready=[s for s in STAGES if stages[s]['status'] not in TERMINAL and all(stages[x]['status'] in TERMINAL for x in STAGES[s])]
        out={'ok':True,'edition_code':row['edition_code'],'job':jid,'batch':row['batch'],'format':row['client'],'client':row['client'],
             'status':'design_selection_required' if selection_missing else ('inputs_changed' if input_changes else ('context_changed' if memory_stale else 'ready')),
             'context_changed':memory_stale,
             'next_stages':[] if selection_missing or input_changes or memory_stale else ready,'input_changes':input_changes,
             'stages':[{k:v for k,v in stages[s].items() if k not in ('job','evidence')} for s in STAGES],
             'budget':self.budget(row['batch']),
             'editorial_approval':'Not inferred from these mechanical records; reviewer must actually inspect the video.'}
        self.write_json(path/'progress.json',out)
        return out
    def authorize(self,batch,note,remote=True,billing_confirmed=True):
        safe_text(note,'autorização')
        with self.db(True) as d:
            b=d.execute('SELECT mode FROM batches WHERE id=?',(ident(batch),)).fetchone()
            if not b:fail('UNKNOWN_BATCH','Lote não encontrado.')
            if b['mode']=='unknown':fail('UNKNOWN_BILLING','Confirme assinatura ou API antes de autorizar chamadas.')
            d.execute('UPDATE batches SET remote_allowed=?,billing_confirmed=? WHERE id=?',(int(remote),int(billing_confirmed),batch))
            self.event(d,'authorize',batch,{'note':note,'remote':remote,'billing_confirmed_by_user':billing_confirmed})
        return self.budget(batch)
    def configure_budget(self,batch,mode,limit_usd,cap_mode,note):
        safe_text(note,'autorização de orçamento')
        if mode not in ('subscription','usd') or cap_mode not in ('native','estimate'):fail('INVALID_BUDGET','Modo de orçamento inválido.')
        limit=usd_units(limit_usd) if mode=='usd' else None
        with self.db(True) as d:
            b=d.execute('SELECT * FROM batches WHERE id=?',(ident(batch),)).fetchone()
            if not b:fail('UNKNOWN_BATCH','Lote não encontrado.')
            count=d.execute('SELECT COUNT(*) FROM calls WHERE batch=?',(batch,)).fetchone()[0]
            if count and mode!=b['mode']:fail('BILLING_MODE_LOCKED','Não altere o tipo de cobrança de um lote já iniciado; mantenha o histórico e abra outro lote.')
            if limit is not None and limit<self._used(d,batch):fail('BUDGET_BELOW_COMMITTED','O limite é menor que o total já consumido/reservado.')
            d.execute('UPDATE batches SET mode=?,cap_mode=?,limit_u=? WHERE id=?',(mode,cap_mode,limit,batch))
            self.event(d,'budget_config',batch,{'mode':mode,'limit_u':limit,'cap_mode':cap_mode,'note':note})
        return self.budget(batch)
    def _used(self,d,batch):
        # Cancelled-before-launch calls cost no budget; unsettled calls keep their entire reservation.
        return d.execute("SELECT COALESCE(SUM(CASE WHEN status='cancelled' THEN 0 ELSE COALESCE(actual_u,reserved_u) END),0) FROM calls WHERE batch=?",(batch,)).fetchone()[0]
    def budget(self,batch):
        with self.db() as d:
            b=d.execute('SELECT * FROM batches WHERE id=?',(ident(batch),)).fetchone()
            if not b:fail('UNKNOWN_BATCH','Lote não encontrado.')
            used=self._used(d,batch);calls=[dict(r) for r in d.execute('SELECT id,job,task,host,model,tier,status,reserved_u,actual_u,usage FROM calls WHERE batch=?',(batch,))]
        return {'batch':batch,'profile':b['profile'],'mode':b['mode'],'cap_mode':b['cap_mode'],
            'limit_usd':dollars(b['limit_u']) if b['limit_u'] is not None else None,
            'committed_usd':dollars(used) if b['mode']=='usd' else None,
            'remaining_usd':dollars(max(0,b['limit_u']-used)) if b['limit_u'] is not None else None,
            'remote_allowed':bool(b['remote_allowed']),'billing_confirmed_by_user':bool(b['billing_confirmed']),
            'frozen':bool(b['frozen']),'calls':calls,
            'scope':'Only calls registered in this controller. Main chat, other tools and provider billing settings are outside its enforcement.'}
    def reserve(self,jid,task,host,model,tier,request_hash,quote_usd=None,retry=False,premium_approval=False,native_cap=False):
        row=self.job(jid);ident(task,'tarefa');safe_text(model,'modelo',180)
        if host not in ('claude','codex') or tier not in ('triage','standard','premium'):fail('INVALID_ROUTE','Host ou papel desconhecido.')
        amount=usd_units(quote_usd) if quote_usd is not None else 0
        with self.db(True) as d:
            b=d.execute('SELECT * FROM batches WHERE id=?',(row['batch'],)).fetchone();p=validate_profile(self.root,b['profile'])
            if not b['remote_allowed'] or not b['billing_confirmed']:fail('CONSENT_REQUIRED','Preciso de autorização para enviar o pacote de texto/frames e usar a conta configurada.')
            if b['frozen']:fail('BATCH_FROZEN','Lote bloqueado após inconsistência de consumo.','Concilie o gasto e autorize o desbloqueio.')
            if b['mode']=='unknown':fail('UNKNOWN_BILLING','Cobrança ainda não confirmada.')
            if tier=='premium' and not (p['premium_allowed'] or premium_approval):fail('PREMIUM_APPROVAL','Esta tarefa pede mais capacidade.','Obtenha autorização para usar o modelo de maior capacidade ou proponha uma alternativa.')
            previous=d.execute('SELECT * FROM calls WHERE job=? AND task=? AND request_hash=? ORDER BY created DESC LIMIT 1',(jid,task,request_hash)).fetchone()
            if previous and previous['status']=='completed' and not retry:
                return {'ok':True,'status':'reuse','call':previous['id'],'result':json.loads(previous['result']) if previous['result'] else None}
            if previous and previous['status'] in ('reserved','running','unknown'):fail('UNRESOLVED_CALL','A chamada anterior ainda está em andamento ou sem consumo conciliado; não vou repeti-la.')
            if previous and previous['status']=='failed' and not retry:fail('RETRY_REQUIRED','A chamada anterior falhou. Uma nova tentativa precisa ser explícita.')
            total=d.execute('SELECT COUNT(*) FROM calls WHERE batch=?',(row['batch'],)).fetchone()[0]
            attempts=d.execute('SELECT COUNT(*) FROM calls WHERE job=? AND task=? AND request_hash=?',(jid,task,request_hash)).fetchone()[0]
            running=d.execute("SELECT COUNT(*) FROM calls WHERE batch=? AND status IN ('reserved','running')",(row['batch'],)).fetchone()[0]
            if total>=p['max_calls']:fail('CALL_LIMIT','O lote atingiu o limite de chamadas desse perfil.')
            if attempts>=p['max_attempts_per_task']:fail('ATTEMPT_LIMIT','A tarefa atingiu o limite de tentativas; revise a causa antes de gastar mais.')
            if running>=p['max_parallel']:fail('PARALLEL_LIMIT','Há trabalho suficiente em andamento. Aguarde a conclusão.')
            if b['mode']=='usd':
                unresolved=d.execute("SELECT 1 FROM calls WHERE batch=? AND status='unknown' LIMIT 1",(row['batch'],)).fetchone()
                if unresolved:fail('UNMETERED_COST','Há consumo desconhecido. A reserva continua retida até a conciliação.')
                if amount<=0:fail('QUOTE_REQUIRED','Informe uma reserva positiva para esta chamada.')
                if b['cap_mode']=='native' and not native_cap:fail('NO_NATIVE_CAP','Este adaptador não oferece teto monetário nativo nesta execução.','Use o modo assinatura, ou autorize conscientemente estimativas sem garantia de teto por chamada; não usar uma flag de outro programa.')
                if self._used(d,row['batch'])+amount>b['limit_u']:fail('BUDGET_EXHAUSTED','Saldo insuficiente. O orçamento é compartilhado por todos os vídeos deste lote.')
            cid=str(uuid.uuid4())
            d.execute('INSERT INTO calls(id,batch,job,task,request_hash,host,model,tier,status,reserved_u,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
              (cid,row['batch'],jid,task,request_hash,host,model,tier,'reserved',amount,stamp()))
            self.event(d,'reserve',cid,{'batch':row['batch'],'reserved_u':amount,'native_cap':native_cap,'premium_approval':premium_approval})
        return {'ok':True,'status':'reserved','call':cid,'reserved_usd':dollars(amount)}
    def mark_running(self,cid):
        with self.db(True) as d:
            n=d.execute("UPDATE calls SET status='running' WHERE id=? AND status='reserved'",(cid,)).rowcount
            if n!=1:fail('CALL_STATE','A chamada não está reservada ou já foi iniciada.')
    def settle(self,cid,actual_usd=None,usage=None,result=None,success=True,note='provider result'):
        amount=usd_units(actual_usd) if actual_usd is not None else None
        with self.db(True) as d:
            c=d.execute('SELECT * FROM calls WHERE id=?',(cid,)).fetchone()
            if not c:fail('UNKNOWN_CALL','Chamada não encontrada.')
            if c['status'] in ('completed','failed','cancelled'):fail('ALREADY_SETTLED','Essa chamada já foi conciliada; o valor não será somado novamente.')
            b=d.execute('SELECT * FROM batches WHERE id=?',(c['batch'],)).fetchone()
            # A missing price is not zero. Subscription may legitimately report tokens without dollars.
            unknown=(b['mode']=='usd' and amount is None) or (not success and amount is None)
            status='unknown' if unknown else ('completed' if success else 'failed')
            d.execute('UPDATE calls SET status=?,actual_u=?,usage=?,result=? WHERE id=?',(status,amount,self.serialize(usage) if usage is not None else c['usage'],self.serialize(result) if result is not None else c['result'],cid))
            overrun=amount is not None and b['mode']=='usd' and (amount>c['reserved_u'] or self._used(d,c['batch'])>b['limit_u'])
            if overrun:d.execute('UPDATE batches SET frozen=1 WHERE id=?',(c['batch'],))
            self.event(d,'settle',cid,{'actual_u':amount,'status':status,'overrun':overrun,'note':safe_text(note,'origem da conciliação')})
        return {'ok':True,'call':cid,'status':status,'overrun':overrun,'actual_usd':dollars(amount) if amount is not None else None}
    def cancel_before_launch(self,cid,note):
        with self.db(True) as d:
            n=d.execute("UPDATE calls SET status='cancelled',actual_u=0 WHERE id=? AND status='reserved'",(cid,)).rowcount
            if n!=1:fail('CANNOT_CANCEL_SPEND','Depois do início, uma chamada deve ser conciliada; não presumir gasto zero.')
            self.event(d,'cancel_before_launch',cid,{'note':safe_text(note,'motivo')})
        return {'ok':True,'status':'cancelled','call':cid}
    def unfreeze(self,batch,note):
        safe_text(note,'autorização de desbloqueio')
        with self.db(True) as d:
            b=d.execute('SELECT * FROM batches WHERE id=?',(ident(batch),)).fetchone()
            if not b:fail('UNKNOWN_BATCH','Lote não encontrado.')
            if d.execute("SELECT 1 FROM calls WHERE batch=? AND status IN ('reserved','running','unknown')",(batch,)).fetchone():fail('UNRESOLVED_CALL','Concilie chamadas abertas antes de desbloquear.')
            if b['limit_u'] is not None and self._used(d,batch)>b['limit_u']:fail('BUDGET_EXHAUSTED','Autorize um orçamento compatível com o gasto registrado antes de desbloquear.')
            d.execute('UPDATE batches SET frozen=0 WHERE id=?',(batch,));self.event(d,'unfreeze',batch,{'note':note})
        return self.budget(batch)
