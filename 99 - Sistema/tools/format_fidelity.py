#!/usr/bin/env python3
"""Pin the selected recipe/reference contract and validate real planning/review evidence.

These gates validate provenance and completeness, not subjective visual similarity.
No source/reference is mutated and no remote service is called.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from factory_common import inside,sha,fingerprint
from project_layout import engine_root


def validate_locks(root):
    root=engine_root(root);path=inside(root,'config/format-locks.json')
    if not path.is_file():return {'ok':True,'locked':0}
    locks=json.loads(path.read_text())['formats']
    defaults=json.loads(inside(root,'config/design-defaults.json').read_text())
    active={x['uid']:x for x in defaults['formats']}
    for uid,lock in locks.items():
        item=active.get(uid)
        if not item or fingerprint(item)!=lock['definition_sha256']:
            raise ValueError('Formato consolidado alterado sem revisão expressa do autor: '+lock['code'])
        if sha(inside(root,'patterns/'+item['pattern']+'.yaml'))!=lock['pattern_sha256']:
            raise ValueError('Receita consolidada alterada sem revisão expressa do autor: '+lock['code'])
    return {'ok':True,'locked':len(locks)}


def snapshot(root,entry):
    root=engine_root(root);index=inside(root,'config/reference-library.json')
    library=json.loads(index.read_text()) if index.is_file() else {'formats':{},'files':{}}
    group=library['formats'].get(entry['code'])
    if (not group or not entry.get('uid') or group.get('uid')!=entry['uid']) and entry.get('reference_materials'):
        group={'uid':entry['uid'],'references':entry['reference_materials']}
        library={'formats':{},'files':{x['path']:x['sha256'] for x in group['references']}}
    if not group or not entry.get('uid') or group.get('uid')!=entry['uid']:
        # A new generation must never inherit an old reference merely by F code.
        return None
    from format_guides import DETAILS
    key=entry['uid'].removeprefix('factory.').upper()
    spec=entry.get('mechanism_details') or DETAILS.get(key)
    if not spec or not spec.get('steps'):raise ValueError('Guia de mecanismo incompleto: '+entry['code'])
    selection_path=inside(root,'config/format-reference-selection.json')
    selected=json.loads(selection_path.read_text()).get('formats',{}).get(entry['uid'],{}) if selection_path.is_file() else {}
    preferred=selected.get('primary_reference')
    references=[r for r in group['references'] if r['path'].endswith(('.mp4','.mov','.m4v','.webm'))]
    if preferred:references=[preferred]+[r for r in references if r['path']!=preferred['path']]
    references+= [r for r in group['references'] if r['path'].endswith(('.jpg','.jpeg','.png'))][:4]
    if not references:raise ValueError('Referência real indisponível para '+entry['code'])
    for item in references:
        path=inside(root,item['path'])
        if not path.is_file() or sha(path)!=library['files'].get(item['path']) or sha(path)!=item['sha256']:
            raise ValueError('Referência ausente ou modificada: '+item['path'])
    from edit_support import read_data
    recipe=read_data(inside(root,'patterns/'+entry['pattern']+'.yaml'))
    rules={key:recipe[key] for key in ('visual','motion','captions','audio','research','layouts') if key in recipe}
    result={'schema':1,'format_code':entry['code'],'format_uid':entry['uid'],
            'pattern':entry['pattern'],'pattern_sha256':sha(inside(root,'patterns/'+entry['pattern']+'.yaml')),
            'definition_sha256':fingerprint(entry),
            'criteria':[{'id':'mechanism','description':spec['mechanism']},
                        *[{'id':f'step-{i}','description':text} for i,text in enumerate(spec['steps'],1)],
                        {'id':'pace-and-composition','description':'Comparar ritmo, duração dos estados, hierarquia e composição com cenas reais da referência; ID visual e assunto vêm do trabalho.'},
                        {'id':'constraints-and-identity','description':spec['avoid']+' A pessoa e materiais vêm do trabalho; cores/fontes vêm da ID explícita. Não inserir logo, EMPIRE ou outra assinatura herdada.'},
                        {'id':'recipe-specific-rules','description':'Conferir na execução as regras específicas desta receita, incluindo cenas, legenda, áudio, pesquisa e layouts quando aplicáveis.'}],
            'recipe_rules':rules,
            'primary_reference':references[0],
            'reference_conflicts':selected.get('reference_conflicts',[]),
            'references':[{'path':x['path'],'sha256':x['sha256']} for x in references],
            'no_brand_or_identity_inheritance':True,'required':True}
    result['sha256']=fingerprint(result)
    return result


def _job_file(root,job_path,value,digest,image=False):
    if not isinstance(value,str) or not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Evidência precisa de caminho e SHA-256 reais.')
    path=inside(root,value)
    if not path.is_relative_to(job_path) or not path.is_file() or sha(path)!=digest:raise ValueError('Evidência ausente, alterada ou de outro trabalho: '+value)
    if image:
        header=path.read_bytes()[:8]
        if not (header.startswith(b'\xff\xd8\xff') or header==b'\x89PNG\r\n\x1a\n'):raise ValueError('A comparação exige um frame real em PNG/JPEG.')
    return path


def _reference(root,job_path,contract,evidence):
    if not isinstance(evidence,dict):raise ValueError('Indique a cena de referência realmente inspecionada.')
    ref=next((x for x in contract['references'] if x['path']==evidence.get('path')),None)
    if not ref or ref['sha256']!=evidence.get('sha256') or sha(inside(root,ref['path']))!=ref['sha256']:raise ValueError('Referência não corresponde ao formato selecionado.')
    at=evidence.get('at_seconds')
    if isinstance(at,bool) or not isinstance(at,(int,float)) or not 0<=at<1e8:raise ValueError('Tempo da cena de referência inválido.')
    _job_file(root,job_path,evidence.get('frame_path'),evidence.get('frame_sha256'),True)


def validate(root,job_path,manifest,phase):
    root=engine_root(root);job_path=Path(job_path).resolve()
    contract=manifest.get('format_contract')
    if not contract or not contract.get('required'):return {'ok':True,'status':'legacy_or_no_indexed_reference','required':False}
    if fingerprint({k:v for k,v in contract.items() if k!='sha256'})!=contract.get('sha256'):raise ValueError('Contrato de formato foi alterado.')
    if manifest.get('format_uid')!=contract['format_uid'] or manifest.get('format_code')!=contract['format_code']:raise ValueError('O contrato pertence a outra geração/formato.')
    chosen_pattern=manifest.get('pattern');expected_hash=contract['pattern_sha256']
    if chosen_pattern!=contract['pattern']:
        if 'pattern' not in manifest.get('explicit_fields',[]):raise ValueError('A receita foi substituída sem uma escolha explícita para este trabalho.')
        expected_hash=manifest.get('pattern_sha256')
    if sha(inside(root,'patterns/'+chosen_pattern+'.yaml'))!=expected_hash:raise ValueError('A receita mudou depois da criação do trabalho.')
    filename='analysis/format-plan.json' if phase=='plan' else 'qa/format-fidelity.json'
    path=inside(root,job_path/filename)
    if not path.is_file():raise ValueError('Falta a comparação obrigatória com a referência: '+filename)
    report=json.loads(path.read_text())
    if report.get('job_id')!=manifest['id'] or report.get('contract_sha256')!=contract['sha256']:raise ValueError('Comparação desatualizada ou de outro trabalho.')
    comparisons=report.get('comparisons')
    if not isinstance(comparisons,list) or {c.get('criterion') for c in comparisons}!= {c['id'] for c in contract['criteria']} or len(comparisons)!=len(contract['criteria']):raise ValueError('Compare todos os critérios do formato, sem duplicatas.')
    if contract.get('reference_conflicts') and not (manifest.get('format_deviations') or {}).get('recipe-specific-rules'):
        raise ValueError('Há divergência registrada entre receita e referência. Obtenha uma instrução atual para esta edição ou uma ordem do autor para revisar o modelo; não escolher silenciosamente.')
    if phase=='review':
        render=report.get('render') or {}
        _job_file(root,job_path,render.get('path'),render.get('sha256'))
        if report.get('status')!='pass':raise ValueError('A revisão de fidelidade está pendente ou reprovada.')
    for comparison in comparisons:
        _reference(root,job_path,contract,comparison.get('reference'))
        if not isinstance(comparison.get('decision'),str) or not comparison['decision'].strip():raise ValueError('Descreva a decisão de edição para cada critério.')
        if phase=='review':
            output=comparison.get('output') or {}
            _job_file(root,job_path,output.get('frame_path'),output.get('frame_sha256'),True)
            if comparison.get('status')!='matched':
                authorization=(manifest.get('format_deviations') or {}).get(comparison['criterion'])
                if comparison.get('status')!='authorized_deviation' or not authorization or comparison.get('user_instruction')!=authorization:raise ValueError('Critério não atendido ou exceção não autorizada: '+comparison['criterion'])
    return {'ok':True,'required':True,'criteria_checked':len(comparisons),'phase':phase,
            'report':str(path.relative_to(root)),'editorial_similarity':'Requires actual reference/render inspection; this validator does not certify taste.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--job',required=True);p.add_argument('--phase',choices=['plan','review'],required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
    root=engine_root(a.root);job=inside(root,'jobs/'+a.job)
    manifest=json.loads((job/'job.yaml').read_text())
    if a.prepare:
        from factory_common import atomic_json
        contract=manifest.get('format_contract')
        if not contract:raise ValueError('Este trabalho não tem contrato de referência indexada; registrar o escopo real antes de avaliar.')
        path=inside(root,job/('analysis/format-plan.json' if a.phase=='plan' else 'qa/format-fidelity.json'))
        if path.exists():raise ValueError('Comparação existente preservada; revise esse arquivo em vez de substituí-lo.')
        report={'job_id':manifest['id'],'contract_sha256':contract['sha256'],'status':'pending','comparisons':[{'criterion':c['id'],'description':c['description'],'reference':None,'decision':'','status':'pending','output':None} for c in contract['criteria']]}
        if a.phase=='review':report['render']=None
        atomic_json(path,report);result={'ok':True,'status':'pending','path':str(path.relative_to(root)),'approval_implied':False}
    else:result=validate(root,job,manifest,a.phase)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError) as exc:raise SystemExit(str(exc))
