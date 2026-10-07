#!/usr/bin/env python3
"""Check packaged files, JSON/YAML syntax and the optional integrity manifest. No installs."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--installed",action="store_true",help="Report edited managed files as local customizations; missing/syntax errors still fail")
parser.add_argument('--repository',action='store_true',help='Check a Git code backup; packaged demo renders and the private-store example are optional')
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
from project_layout import managed_path, surface_root
required=[
'AGENTS.md','CLAUDE.md','README.md','START-HERE.md','VERSION','REVISION_REPORT.md',
'method/METHOD.md','method/DECISION_ENGINE.md','method/QUALITY_BAR.md','method/FACTUALITY.md',
'method/MODEL_ROUTING.md','method/TOKEN_ECONOMY.md','method/SPEECH_ERROR_POLICY.md','method/MULTI_VIDEO_POLICY.md',
'method/REFERENCE_SCRIPT_POLICY.md','method/SILENCE_POLICY.md',
'workflows/EDIT_VIDEO.md','workflows/CLEAN_SPEECH.md','workflows/SPLIT_MULTI_VIDEO.md','workflows/BATCH_FACTORY.md',
'workflows/QA.md','workflows/MATCH_REFERENCE_SCRIPT.md','workflows/REMOVE_SILENCE.md',
'patterns/INDEX.md','patterns/_TEMPLATE.yaml','patterns/talking-head-clean-v2.yaml',
'patterns/reels-dynamic-v2.yaml','patterns/longform-clean-v2.yaml',
'jobs/JOB_SCHEMA.json','jobs/EDL_SCHEMA.json','jobs/REFERENCE_SCRIPT_TEMPLATE.json',
'jobs/REFERENCE_GUIDED_JOB_TEMPLATE.yaml','jobs/PROTECTED_RANGES_TEMPLATE.json',
'examples/INDEX.md','examples/annotated/reference-and-pauses.md',
'tests/ACCEPTANCE.md','tests/TEST_CASES.json','tests/test_script_and_silence.py','tests/smoke_script_silence.py',
'tools/doctor.py','tools/probe_media.py','tools/render_edl.py','tools/qa_media.py','tools/transcribe.py',
'tools/edit_support.py','tools/detect_silence.py','tools/plan_silence_cuts.py','tools/prepare_script_comparison.py',
'.claude/skills/video-factory/SKILL.md','.claude/agents/transcript-screener.md',
'.claude/agents/assembly-editor.md','.claude/agents/video-director.md'
]
required += ['method/MOTION_POLICY.md', 'workflows/CREATE_JS_ANIMATIONS.md', 'motion/README.md', 'motion/SPEC.md', 'motion/MOTION_PLAN_TEMPLATE.json', 'motion/browser/motion.js', 'motion/examples/keyphrase.json', 'motion/examples/steps.json', 'motion/examples/lower-third.json', 'motion/examples/proof-frame.template.json', 'motion/remotion/README.md', 'motion/remotion/package.json', 'motion/remotion/src/index.jsx', 'patterns/motion/INDEX.md', 'patterns/motion/clean-explainer-v1.yaml', 'tools/render_motion.py', 'tools/composite_motion.py', 'tools/doctor_motion.py', 'tests/test_motion.cjs', 'tests/test_motion_plan.py', 'tests/smoke_motion.py', '.claude/agents/motion-designer.md', '.claude/agents/motion-builder.md', '.claude/skills/video-motion/SKILL.md', 'sources/MOTION_RESEARCH.md', 'MOTION_REVISION_REPORT.md']
required += ['MEMORIA-COMO-USAR.md', 'MEMORY_REVISION_REPORT.md', 'method/FORMAT_MEMORY_POLICY.md', 'workflows/FORMAT_MEMORY.md', 'method/CLIENT_MEMORY_POLICY.md', 'workflows/CLIENT_MEMORY.md', 'workflows/PERSONALIZATION_QA.md', 'memory/README.md', 'memory/RECORD_SCHEMA.json', 'memory/CAPTURE_EXAMPLE.json', '.claude/settings.json', '.claude/skills/video-memory/SKILL.md', 'tools/format_memory.py', 'tools/resolve_format_context.py', 'tools/client_memory.py', 'tools/resolve_client_context.py', 'tools/memory_hook.py', 'tools/install_memory_hooks.py', 'tests/test_client_memory.py', 'tests/smoke_memory.py', 'tests/MEMORY_BEHAVIOR_CASES.json', 'sources/MEMORY_AUDIT_V1_3.md', 'sources/MEMORY_RESEARCH.md']
required += ['method/VISUAL_DIRECTION.md', 'workflows/DIRECT_VISUALS.md', 'visual/SPEC.md', 'visual/VISUAL_QA.md', 'visual/PLAN_TEMPLATE.json', 'tools/visual_direction.py', 'DIRECAO-VISUAL-COMO-USAR.md', 'sources/VISUAL_RESEARCH.md', 'tests/test_visual_direction.py']
required += ['factory.py','COMECE-AQUI.md','adapters/README.md','method/EXECUTION_AND_COSTS.md','method/OUTPUT_RULES.md','tools/output_naming.py','tests/test_output_naming.py',
'workflows/ASSISTED_START.md','workflows/RESUME_JOB.md','config/execution-profiles.json','config/model-catalog.json',
'.agents/skills/video-factory/SKILL.md','.agents/skills/video-setup/SKILL.md','.codex/config.toml',
'jobs/INTAKE_TEMPLATE.json','tests/test_factory_control.py','tests/smoke_factory_control.py','tests/fixtures/fake_host.py',
'sources/CONTROL_RESEARCH_V1_6.md','REVISAO_V1_6.md']
required += ['tools/factory_'+name+'.py' for name in ['cli','common','doctor','setup','state','runner']]
required += ['.codex/agents/'+name+'.toml' for name in ['transcript-screener','assembly-editor','video-qa','video-director','motion-designer','motion-builder','visual-director']]
required += ['studio/README.md', 'studio/CONTRACT.md', 'studio/MODO_LEIGO.md', 'studio/lib/motion.js', 'studio/examples/decision-flow.html', 'studio/examples/decision-flow.json', 'studio/templates/PLAN_TEMPLATE.json', 'studio/templates/REVIEW_TEMPLATE.json', 'studio/templates/STYLE_GUIDE_TEMPLATE.md', 'config/studio-profiles.json', 'tools/studio_cli.py', 'tools/studio_render.py', 'tools/studio_review.py', 'tools/studio_audio.py', 'workflows/MOTION_STUDIO.md', '.agents/skills/video-studio/SKILL.md', '.claude/skills/video-studio/SKILL.md', 'tests/test_studio.py', 'tests/test_studio.cjs', 'tests/smoke_studio.py', 'sources/MOVEZ_COURSE_NOTES.md', 'sources/MOVEZ_ADOPTION.md', 'sources/STUDIO_RESEARCH_V1_7.md', 'REVISAO_V1_7.md']
def runtime(p):
    rel=p.relative_to(ROOT).as_posix()
    return rel.startswith(('context/','sources/repos/','sources/reference-material/','arquivo/','prototipos/')) or (rel.startswith('jobs/') and '/' in rel[len('jobs/'):]) or p.name.endswith('.local.json') or p.name.startswith('.env') or any(part in ('.factory','.venv','node_modules','__pycache__','.git','.runtime','projetos') for part in p.relative_to(ROOT).parts)
errors=[];warnings=[]
if (ROOT/'PACKAGE_MANIFEST.json').exists():
    packaged = json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text()).get('files', {})
    for rel in packaged:
        if '.sqlite3' in rel or '__pycache__' in rel or rel.endswith('.pyc') or rel.startswith(('.factory/','.venv/')):
            errors.append('private/runtime material in generic manifest: '+rel)
for rel in required:
    p=managed_path(ROOT,rel)
    if not p.is_file(): errors.append(f'missing: {rel}')
    elif p.stat().st_size==0: errors.append(f'empty: {rel}')
for p in ROOT.rglob('*.json'):
    if runtime(p):continue
    try: json.loads(p.read_text(encoding='utf-8-sig'))
    except Exception as e: errors.append(f'invalid JSON {p.relative_to(ROOT)}: {e}')
if importlib.util.find_spec('yaml'):
    import yaml
    for p in ROOT.rglob('*.yaml'):
        if runtime(p):continue
        try: yaml.safe_load(p.read_text(encoding='utf-8'))
        except Exception as e: errors.append(f'invalid YAML {p.relative_to(ROOT)}: {e}')
else: warnings.append('YAML parsing skipped: optional PyYAML not installed')
try:
    import tomllib
    for p in (surface_root(ROOT)/'.codex/agents').rglob('*.toml'):
        try:tomllib.loads(p.read_text(encoding='utf-8'))
        except Exception as e:errors.append(f'invalid TOML {p.relative_to(ROOT)}: {e}')
except ImportError:warnings.append('TOML parsing requires Python 3.11+')
manifest_path=ROOT/'PACKAGE_MANIFEST.json' 
if manifest_path.exists():
    manifest=json.loads(manifest_path.read_text())
    for rel, expected in manifest['files'].items():
        path=managed_path(ROOT,rel)
        if not path.resolve().is_relative_to(surface_root(ROOT)): errors.append(f'unsafe path: {rel}');continue
        if args.repository and not path.is_file() and rel in {'context/clients/_template/CLIENT.md','motion/examples/rendered/synthetic-motion-demo.mp4','studio/examples/rendered/conceptual-test.mp4'}:
            warnings.append('optional packaged artifact omitted from Git backup: '+rel);continue
        if not path.is_file(): errors.append(f'manifest missing: {rel}');continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected:
            (warnings if args.installed else errors).append(f'integrity changed / local customization: {rel}')
print(json.dumps({'root':str(ROOT),'version':(ROOT/'VERSION').read_text().strip(),
                  'required_count':len(required),'errors':errors,'warnings':warnings,'ok':not errors},indent=2))
sys.exit(1 if errors else 0)
