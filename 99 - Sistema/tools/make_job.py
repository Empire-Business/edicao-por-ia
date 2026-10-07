#!/usr/bin/env python3
"""Create an isolated job. JSON serialization inside .yaml avoids unsafe unescaped user paths."""
from __future__ import annotations
import argparse
import datetime
import json
import re
from pathlib import Path
from client_memory import Memory, ROOT
from resolve_client_context import write_resolution
from workspace_files import resolve_file, portable
from project_layout import engine_root
from design_catalog import select_pair
from edition_codes import code_for


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', action='append', required=True)
    ap.add_argument('--pattern')
    ap.add_argument('--name', help='Nome curto do vídeo usado nos arquivos de saída; por padrão, usa o nome do arquivo de origem')
    ap.add_argument('--root', default=str(ROOT))
    identity=ap.add_mutually_exclusive_group()
    identity.add_argument('--format',dest='format_id',metavar='ID',help='ID do formato deste vídeo')
    identity.add_argument('--client',dest='format_id',metavar='ID',help=argparse.SUPPRESS)
    ap.add_argument('--visual-id',required=True,help='ID visual escolhida, como ID01')
    ap.add_argument('--project')
    ap.add_argument('--session')
    ap.add_argument('--anonymous', action='store_true', help='Legacy flag; editing without a registered format is no longer allowed')
    ap.add_argument('--include-logo',action='store_true',help='Only when explicitly requested for this job')
    ap.add_argument('--logo-file')
    ap.add_argument('--id')
    ap.add_argument('--jobs-dir')
    ap.add_argument('--expected-outputs', type=int, default=1)
    ap.add_argument('--reference-script', action='append', default=[])
    ap.add_argument('--script-mode', choices=['flexible', 'strict', 'off'], default=None)
    ap.add_argument('--silence-mode', choices=['pattern_default', 'natural', 'tight', 'relaxed', 'off'], default=None)
    a = ap.parse_args()
    a.root=str(engine_root(a.root))
    if a.expected_outputs < 1:
        raise ValueError('Expected outputs must be positive')
    slug = re.sub(r'[^a-z0-9]+', '-', Path(a.source[0]).stem.lower()).strip('-') or 'video'
    jid = a.id or f'{datetime.date.today().isoformat()}-{slug[:40]}'
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', jid):
        raise ValueError('Job ID must be a safe single path component')
    sources = [str(resolve_file(p,a.root)) for p in a.source]
    scripts = [str(resolve_file(p,a.root)) for p in a.reference_script]
    marker=Path(a.root)/'.factory/workspace.json'
    if not marker.exists():
        marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text('{"version":1,"material_paths":"workspace_relative"}\n')
    memory = Memory(a.root)
    # New edits always name a confirmed format. Historical owners/session bindings
    # remain stored for compatibility, but never select a format for a new video.
    if a.anonymous or not a.format_id:
        raise ValueError('Qual formato devo usar neste vídeo? Informe um formato cadastrado ou cadastre um novo antes de editar.')
    editing,identity=select_pair(a.root,a.format_id,a.visual_id)
    client, project = editing['memory_store'], a.project
    memory.name(client)
    if project and not client:
        raise ValueError('A project must belong to an explicitly identified format')
    pattern = a.pattern or editing['pattern']
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', pattern) or not (Path(a.root)/'patterns'/(pattern+'.yaml')).is_file():
        raise ValueError('Unknown pattern: '+pattern+'. Choose an existing named pattern before creating a job.')
    logo_path=str(resolve_file(a.logo_file,a.root)) if a.logo_file else None
    pins = ['branding.logos_enabled'] if a.include_logo else []
    if logo_path:pins.append('branding.logo_path')
    if a.pattern: pins.append('pattern')
    if a.script_mode: pins.append('reference_script.mode')
    if a.silence_mode: pins += ['silence_removal.mode', 'silence_removal.enabled']
    base = (Path(a.jobs_dir) if a.jobs_dir else Path(a.root)/'jobs') / jid
    if base.exists():
        raise ValueError('This job folder already exists. Do not overwrite it. Use factory.py resume for managed jobs, or inspect progress before continuing a legacy job.')
    base.mkdir(parents=True, exist_ok=False)
    for d in ['analysis/chunks', 'edit', 'qa', 'renders', 'frames', 'tmp', 'references']:
        (base/d).mkdir(parents=True, exist_ok=True)
    video_name=a.name or Path(a.source[0]).stem
    job = {'edition_code':code_for(a.root,jid,video_name),'id': jid, 'name': video_name, 'status': 'created', 'pattern': pattern, 'format': client, 'client': client,
           'selection_version':2,'format_code':editing['code'],'visual_identity':identity['code'],'project': project, 'explicit_fields': pins, 'branding': {'logos_enabled': a.include_logo, 'logo_path': logo_path},
           'expected_outputs': a.expected_outputs, 'sources': [{'path': p, 'role': 'primary'} for p in sources],
           'reference_script': {'enabled': bool(scripts) and a.script_mode != 'off', 'paths': scripts,
                                'mode': a.script_mode or 'flexible', 'reorder_policy': 'preserve_unless_requested',
                                'missing_content_policy': 'report_do_not_invent'},
           'silence_removal': {'enabled': a.silence_mode != 'off', 'mode': a.silence_mode or 'pattern_default',
                               'protected_ranges_path': None},
           'requirements': {'speech_cleanup': True, 'split_source': len(sources) == 1 and a.expected_outputs > 1,
                            'captions': 'pattern_default', 'preserve_phrases': []}, 'notes': ''}
    if len(scripts) > 1 or a.expected_outputs > 1:
        job['reference_assignments'] = []
        job['notes'] = 'Assign each script/block scope to a child job before comparison; do not assume file order.'
    (base/'job.yaml').write_text(json.dumps(portable(job,a.root), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (base/'edit/decision_log.md').write_text('# Decision Log\n\n', encoding='utf-8')
    if client:
        if a.session:
            memory.bind(a.session, client, project, jid, pattern)
        write_resolution(memory, base/'job.yaml', base/'job.effective.json')
    print(str(base.resolve()))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as e:
        raise SystemExit(str(e))
