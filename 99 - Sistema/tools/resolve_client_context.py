#!/usr/bin/env python3
"""Resolve format-profile preferences into a NEW job manifest, preserving explicit overrides.

The original job and named pattern are never overwritten. Use the resulting
job.effective-*.json for the edit, plus the generated silence-settings-*.json.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
from client_memory import Memory, ROOT, SCOPES, digest
from edit_support import read_data, check_output, write_json
from plan_silence_cuts import settings_for
from design_catalog import editing_context, effective_visual, visual_identity, visual_receipt


def has(obj, dotted):
    cur=obj
    for key in dotted.split('.'):
        if not isinstance(cur,dict) or key not in cur:
            return False
        cur=cur[key]
    return True


def get(obj, dotted, default=None):
    cur=obj
    for key in dotted.split('.'):
        if not isinstance(cur,dict) or key not in cur:return default
        cur=cur[key]
    return cur


def put(obj, dotted, value):
    parts=dotted.split('.');cur=obj
    for key in parts[:-1]:
        if key not in cur:cur[key]={}
        if not isinstance(cur[key],dict):raise ValueError('Non-object setting ancestor: '+key)
        cur=cur[key]
    cur[parts[-1]]=copy.deepcopy(value)


def is_pinned(key, pins):
    return any(key==p or key.startswith(p+'.') or p.startswith(key+'.') for p in pins)


def format_id(job):
    current = job.get('format')
    legacy = job.get('client')
    if current and legacy and current != legacy:
        raise ValueError('Job format conflicts with its legacy client identity')
    return current or legacy


def resolve(memory, job):
    format_name=format_id(job)
    if not format_name:raise ValueError('Job has no format; identify the format before applying its memory')
    modern=job.get('selection_version')==2
    ctx=editing_context(memory,format_name,job.get('project'),job.get('id'),job.get('pattern')) if modern else memory.context(format_name,job.get('project'),job.get('id'),job.get('pattern'))
    if modern and job.get('format_uid') and job['format_uid']!=ctx['definition'].get('uid'):
        raise ValueError('A identidade do formato não corresponde à geração registrada neste trabalho.')
    pins=job.get('explicit_fields')
    legacy=pins is None
    if pins is not None and (not isinstance(pins,list) or not all(isinstance(p,str) for p in pins)):
        raise ValueError('explicit_fields must be an array of dotted paths')
    if pins is not None and any(not has(job,p) for p in pins):
        raise ValueError('An explicit_fields path is missing from the source job')
    out=copy.deepcopy(job);out.pop('_memory',None)
    out['format']=format_name
    if modern:
        identity,identity_receipt=effective_visual(memory.root,job)
        out['visual_identity']=identity['code']
        out['design']={'palette':identity['palette'],'typography':identity['typography'],'logos_enabled':False}
    out['client']=format_name  # Compatibility alias for existing resolvers and saved jobs.
    applied=[];overridden=[];review=[]
    for r in sorted(ctx['active'],key=lambda x:(SCOPES[x['scope']],x['seq'])):
        p=r['payload']
        if 'setting' not in p:continue
        key=p['setting']
        if key=='defaults.pattern':continue # Selected at creation, never silently change a live edit's pattern.
        detail={'id':r['id'],'key':key,'value':p['value'],'scope':r['scope']}
        if (legacy and has(job,key)) or (pins is not None and is_pinned(key,pins)):
            overridden.append({**detail,'reason':'current_job_explicit_or_legacy_pin'})
        elif key=='reference_script.mode' and not job.get('reference_script',{}).get('paths'):
            review.append({**detail,'reason':'not_applicable_without_reference_script'})
        else:
            put(out,key,p['value']);applied.append(detail)
    # A format's historical logo/brand signature never authorizes a new job's logo.
    logo_explicit = pins is not None and any(p in {'branding', 'branding.logos_enabled'} for p in pins)
    logo_enabled = bool(logo_explicit and job.get('branding', {}).get('logos_enabled') is True)
    out.setdefault('branding', {})['logos_enabled'] = logo_enabled
    if not logo_enabled:
        out['branding']['logo_path'] = None
        out['branding']['policy'] = 'no_automatic_logos'
    retained=[]
    for detail in applied:
        if detail['key']=='branding.logos_enabled' and detail['value'] is True and not logo_enabled:
            overridden.append({**detail,'reason':'logo_requires_current_explicit_job_request'})
        else:retained.append(detail)
    applied=retained
    # Stronger current enable/off switches take precedence over inherited pace settings.
    s=out.setdefault('silence_removal',{})
    if s.get('enabled') is False:
        s['mode']='off'
    elif s.get('mode')=='off':
        # Explicit enabled:true beats inherited off mode, but two explicit conflicts require a question.
        enabled_pin=(legacy and has(job,'silence_removal.enabled')) or (pins is not None and is_pinned('silence_removal.enabled',pins))
        mode_pin=(legacy and has(job,'silence_removal.mode')) or (pins is not None and is_pinned('silence_removal.mode',pins))
        if s.get('enabled') is True and enabled_pin and mode_pin:
            raise ValueError('Conflicting explicit silence settings: enabled=true and mode=off')
        if s.get('enabled') is True and enabled_pin:
            s['mode']='pattern_default'
        else:s['enabled']=False
    retained_applied=[]
    for detail in applied:
        if get(out,detail['key']) == detail['value']:
            retained_applied.append(detail)
        else:
            overridden.append({**detail,'reason':'stronger_silence_switch'})
    applied=retained_applied
    receipt={'format':format_name,'client':format_name,'project':job.get('project'),'job':job.get('id'),'pattern':job.get('pattern'),
             'fingerprint':ctx['fingerprint'],'applied':applied,'overridden':overridden,'review':review,
             'legacy_pinning':legacy,'context_omitted_ids':ctx['omitted_ids'],
             'candidate_count':ctx['candidate_count'],
             'notes':['Only allowlisted mechanical settings are merged. Other preferences require editorial QA.',
                      'Read the source job for current instructions; do not remove explicit pins to force memory.',
                      'Artifacts approved by the user are references, not evidence of measured performance.']}
    if modern:receipt['visual_identity']=identity_receipt
    out['_memory']=receipt
    return out,ctx


def check(memory,effective):
    old=effective.get('_memory')
    if not old:raise ValueError('Effective job lacks a memory receipt')
    format_name=format_id(effective)
    if not format_name:raise ValueError('Effective job has no format identity')
    modern=effective.get('selection_version')==2
    ctx=editing_context(memory,format_name,effective.get('project'),effective.get('id'),effective.get('pattern')) if modern else memory.context(format_name,effective.get('project'),effective.get('id'),effective.get('pattern'))
    failures=[]
    if ctx['fingerprint']!=old['fingerprint']:failures.append('Memory changed since resolution; resolve again before final delivery')
    if modern:
        identity=visual_identity(memory.root,effective.get('visual_identity'))
        if old.get('visual_identity')!=visual_receipt(identity):failures.append('A ID visual mudou; resolva uma nova revisão.')
        if effective.get('design',{}).get('palette')!=identity['palette'] or effective.get('design',{}).get('typography')!=identity['typography']:failures.append('Cores/fontes não correspondem à ID visual escolhida.')
    for item in old.get('applied',[]):
        key=item['key']
        # Silence switches are normalized; allow only that intentional normalization.
        if key.startswith('silence_removal.') and (effective.get('silence_removal',{}).get('enabled') is False):
            continue
        if get(effective,key)!=item['value']:failures.append('Applied preference no longer matches: '+key)
    return {'ok':not failures,'mechanical_memory_gate':'ATENDIDO' if not failures else 'PRECISA DE AJUSTE',
            'failures':failures,'editorial_preferences':'Not evaluated by this mechanical check'}


def write_resolution(memory,job_path,output):
    job_path=Path(job_path).resolve(strict=True);output=check_output(output,[job_path])
    job=read_data(job_path)
    effective,ctx=resolve(memory,job)
    # Select only the exact named pattern; no whole-library load.
    pat=memory.root/'patterns'/(job['pattern']+'.yaml')
    if not pat.is_file():
        raise ValueError('Named base pattern is missing; do not invent defaults: '+str(pat))
    pattern=read_data(pat)
    silence=effective.get('silence_removal',{})
    mode=silence.get('mode','pattern_default')
    mode=None if mode=='pattern_default' else mode
    overrides=copy.deepcopy(silence.get('settings',{}))
    if 'enabled' in silence:overrides['enabled']=silence['enabled']
    silence_settings=settings_for(pattern,mode,overrides)
    stem=output.stem
    context_path=output.with_name(stem+'.context.md')
    receipt_path=output.with_name(stem+'.receipt.json')
    silence_path=output.with_name(stem+'.silence-settings.json')
    for p in (context_path,receipt_path,silence_path):check_output(p,[job_path,output])
    write_json(output,effective)
    write_json(receipt_path,effective['_memory'])
    write_json(silence_path,silence_settings)
    with context_path.open('x',encoding='utf-8') as f:f.write(ctx['text'])
    return {'effective_job':str(output),'context':str(context_path),'receipt':str(receipt_path),
            'silence_settings':str(silence_path),'applied_count':len(effective['_memory']['applied'])}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',default=str(ROOT));ap.add_argument('--job',required=True)
    ap.add_argument('--output');ap.add_argument('--check',action='store_true')
    a=ap.parse_args();m=Memory(a.root)
    if a.check:r=check(m,read_data(a.job))
    elif a.output:r=write_resolution(m,a.job,a.output)
    else:raise ValueError('Provide --output for a new file, or --check for a memory QA check')
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0 if r.get('ok',True) else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False),file=sys.stderr);raise SystemExit(1)
