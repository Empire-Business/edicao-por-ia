#!/usr/bin/env python3
"""Agent-facing single command router. User-facing explanations are in COMECE-AQUI.md."""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
from factory_common import ROOT, FactoryError, read_json
from factory_state import State, STAGES, CHANGE_START
from project_layout import engine_root
from edition_codes import job_key
from factory_setup import setup, upgrade, rollback, dependencies, bind_model
from factory_doctor import collect
from factory_runner import route, run

def main(argv=None):
    p=argparse.ArgumentParser(description='Video Factory — preparar, editar, continuar e controlar consumo.')
    p.add_argument('--root',default=str(ROOT),help='Workspace root; put before the subcommand')
    sp=p.add_subparsers(dest='cmd',required=True)
    c=sp.add_parser('studio',help='Estúdio local de motion com referência e crítica');c.add_argument('arguments',nargs=argparse.REMAINDER)
    c=sp.add_parser('doctor');c.add_argument('--smoke',action='store_true')
    c=sp.add_parser('cleanup',help='Prévia ou remoção de segmentos de render de trabalhos entregues');c.add_argument('--job');c.add_argument('--apply',action='store_true');c.add_argument('--confirm')
    c=sp.add_parser('setup');c.add_argument('--host',choices=['both','claude','codex'],default='both');c.add_argument('--profile',choices=['economico','equilibrado','elaborado'],default='equilibrado');c.add_argument('--apply',action='store_true')
    c=sp.add_parser('dependencies');c.add_argument('--capability',choices=['base','speech','motion','studio-audio','ffmpeg'],default='speech');c.add_argument('--apply',action='store_true')
    c=sp.add_parser('update');c.add_argument('--from',dest='source');c.add_argument('--check',action='store_true');c.add_argument('--apply',action='store_true');c.add_argument('--rollback')
    c=sp.add_parser('upgrade');c.add_argument('--from',dest='source',required=True);c.add_argument('--apply',action='store_true')
    c=sp.add_parser('rollback');c.add_argument('--receipt-id',required=True);c.add_argument('--apply',action='store_true')
    c=sp.add_parser('intake');c.add_argument('--request',required=True);c.add_argument('--new-version',action='store_true')
    c=sp.add_parser('resume');c.add_argument('--job')
    identity=c.add_mutually_exclusive_group()
    identity.add_argument('--format',dest='format_id',metavar='ID',help='Filtra trabalhos pelo formato')
    identity.add_argument('--client',dest='format_id',metavar='ID',help=argparse.SUPPRESS)
    c=sp.add_parser('assign-format');c.add_argument('--job',required=True);c.add_argument('--format',dest='format_id',required=True);c.add_argument('--note',required=True)
    c=sp.add_parser('assign-design');c.add_argument('--job',required=True);c.add_argument('--format',required=True);c.add_argument('--visual-id',required=True);c.add_argument('--note',required=True)
    c=sp.add_parser('checkpoint');c.add_argument('--job',required=True);c.add_argument('--stage',required=True,choices=STAGES);c.add_argument('--artifact',action='append',default=[]);c.add_argument('--note',required=True);c.add_argument('--skip',action='store_true');c.add_argument('--user-approved',action='store_true')
    c=sp.add_parser('change');c.add_argument('--job',required=True);c.add_argument('--kind',required=True,choices=CHANGE_START);c.add_argument('--note',required=True)
    c=sp.add_parser('refresh-inputs');c.add_argument('--batch',required=True);c.add_argument('--note',required=True)
    c=sp.add_parser('refresh-context');c.add_argument('--job',required=True);c.add_argument('--note',required=True)
    c=sp.add_parser('validate-edl');c.add_argument('--job',required=True);c.add_argument('--edl',required=True)
    c=sp.add_parser('assign-script');c.add_argument('--job',required=True);c.add_argument('--path');c.add_argument('--without-script',action='store_true');c.add_argument('--note',required=True)
    c=sp.add_parser('budget');c.add_argument('--batch',required=True)
    c=sp.add_parser('budget-set');c.add_argument('--batch',required=True);c.add_argument('--mode',choices=['subscription','usd'],required=True);c.add_argument('--limit-usd');c.add_argument('--cap-mode',choices=['native','estimate'],default='native');c.add_argument('--note',required=True)
    c=sp.add_parser('authorize');c.add_argument('--batch',required=True);c.add_argument('--note',required=True);c.add_argument('--revoke',action='store_true')
    c=sp.add_parser('settle');c.add_argument('--call',required=True);c.add_argument('--actual-usd',required=True);c.add_argument('--note',required=True);c.add_argument('--failed',action='store_true')
    c=sp.add_parser('unfreeze');c.add_argument('--batch',required=True);c.add_argument('--note',required=True)
    c=sp.add_parser('model-bind');c.add_argument('--host',choices=['claude','codex'],required=True);c.add_argument('--tier',choices=['triage','standard','premium'],required=True);c.add_argument('--model',required=True);c.add_argument('--effort',required=True);c.add_argument('--note',required=True)
    c=sp.add_parser('route');c.add_argument('--host',choices=['claude','codex'],required=True);c.add_argument('--task',required=True);c.add_argument('--profile',default='equilibrado');c.add_argument('--approve-premium',action='store_true')
    c=sp.add_parser('run');c.add_argument('--job',required=True);c.add_argument('--task',required=True);c.add_argument('--prompt-file',required=True);c.add_argument('--host',choices=['claude','codex'],required=True);c.add_argument('--quote-usd');c.add_argument('--execute',action='store_true');c.add_argument('--retry',action='store_true');c.add_argument('--approve-premium',action='store_true')
    a=p.parse_args(argv)
    try:
        root=engine_root(a.root)
        if getattr(a,'job',None):a.job=job_key(root,a.job)
        if a.cmd=='studio':
            from studio_cli import main as studio_main
            return studio_main(a.arguments)
        if a.cmd=='doctor':out=collect(root,a.smoke)
        elif a.cmd=='cleanup':
            from factory_cleanup import cleanup
            out=cleanup(root,a.job,a.apply,a.confirm)
        elif a.cmd=='setup':out=setup(root,a.host,a.profile,a.apply)
        elif a.cmd=='dependencies':out=dependencies(root,a.capability,a.apply)
        elif a.cmd=='update':
            from update_local import install,github_package,rollback as update_rollback
            if a.rollback:out=update_rollback(root,a.rollback)
            elif a.source:out=install(root,a.source,a.apply)
            else:
                from bootstrap_update import execute as update_latest
                out=update_latest(root,a.check,a.apply)
        elif a.cmd=='upgrade':out=upgrade(a.source,root,a.apply)
        elif a.cmd=='rollback':out=rollback(root,a.receipt_id,a.apply)
        elif a.cmd=='model-bind':out=bind_model(root,a.host,a.tier,a.model,a.effort,a.note)
        elif a.cmd=='route':out=route(root,a.host,a.task,a.profile,a.approve_premium)
        elif a.cmd=='run':out=run(root,a.job,a.task,a.prompt_file,a.host,a.quote_usd,a.execute,a.retry,a.approve_premium)
        else:
            state=State(root)
            if a.cmd=='intake':out=state.intake(read_json(a.request),a.new_version)
            elif a.cmd=='resume':out=state.resume(a.job,a.format_id)
            elif a.cmd=='assign-format':out=state.assign_format(a.job,a.format_id,a.note)
            elif a.cmd=='assign-design':out=state.assign_design(a.job,a.format,a.visual_id,a.note)
            elif a.cmd=='checkpoint':out=state.checkpoint(a.job,a.stage,a.artifact,a.note,a.skip,a.user_approved)
            elif a.cmd=='change':out=state.change(a.job,a.kind,a.note)
            elif a.cmd=='refresh-inputs':out=state.refresh_inputs(a.batch,a.note)
            elif a.cmd=='refresh-context':out=state.refresh_context(a.job,a.note)
            elif a.cmd=='validate-edl':out=state.validate_edl(a.job,a.edl)
            elif a.cmd=='assign-script':out=state.assign_script(a.job,a.path,a.note,a.without_script)
            elif a.cmd=='budget':out=state.budget(a.batch)
            elif a.cmd=='budget-set':out=state.configure_budget(a.batch,a.mode,a.limit_usd,a.cap_mode,a.note)
            elif a.cmd=='authorize':out=state.authorize(a.batch,a.note,not a.revoke,not a.revoke)
            elif a.cmd=='settle':out=state.settle(a.call,a.actual_usd,success=not a.failed,note=a.note)
            elif a.cmd=='unfreeze':out=state.unfreeze(a.batch,a.note)
            else:raise ValueError('Unknown command')
        print(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False));return 0 if out.get('ok',True) else 1
    except FactoryError as e:
        print(json.dumps(e.as_dict(),ensure_ascii=False,indent=2));return 2
    except (ValueError,OSError,KeyError,TypeError,sqlite3.Error) as e:
        print(json.dumps({'ok':False,'code':'LOCAL_ERROR','message':str(e),'next_action':'Corrija o item indicado; não repita instalações ou chamadas pagas automaticamente.'},ensure_ascii=False,indent=2));return 2
if __name__=='__main__':raise SystemExit(main())
