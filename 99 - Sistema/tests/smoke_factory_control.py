#!/usr/bin/env python3
"""Real filesystem/process/FFmpeg integration. Provider CLI protocols are FAKE fixtures.
No model calls, account billing, ASR or genuine human artistic approval are tested.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from client_memory import Memory
from design_catalog import register_visual
from factory_state import State
from factory_setup import setup, rollback, bind_model
from factory_runner import run
from factory_common import FactoryError, atomic_json, sha

def execute(cmd):return subprocess.run(cmd,capture_output=True,text=True,check=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workdir',required=True,type=Path);a=ap.parse_args()
    w=a.workdir.resolve();w.mkdir(exist_ok=False,parents=True)
    root=w/'Fábrica em teste';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__','.factory','.venv','*.local.json','.env*','CHAVES DAS INTEGRAÇÕES.txt','jobs','context','sources','arquivo','prototipos'))
    # Baseline of this build for installer testing. This is not a user's existing workspace.
    atomic_json(root/'PACKAGE_MANIFEST.json',{'package':'claude-video-factory','version':'1.6-test','files':{str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.json'}})
    checks={}
    def check(name,value):
        checks[name]=bool(value)
        if not value:raise AssertionError(name)
    source=root/'Gravação com acentos e espaços.mp4'
    execute(['ffmpeg','-v','error','-n','-f','lavfi','-i','testsrc2=size=320x180:rate=24:duration=4','-f','lavfi','-i','sine=frequency=330:sample_rate=48000:duration=4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(source)])
    before=sha(source);s=State(root)
    Memory(root).init('fixture','Synthetic smoke format')
    register_visual(root,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
    request={'id':'lote-ficticio','sources':[str(source)],'expected_outputs':2,'format':'fixture','visual_identity':'IDP01',
             'budget':{'mode':'usd','limit_usd':'0.50','cap_mode':'native'}}
    out=s.intake(request);check('two_child_jobs_one_batch',len(out['jobs'])==2 and all(s.job(j)['batch']=='lote-ficticio' for j in out['jobs']))
    check('repeat_request_resumes',s.intake(request)['status']=='resume')
    r=setup(root,apply=True);check('setup_no_unexpected_conflicts',not r['conflicts'])
    check('setup_rerun_idempotent',setup(root,apply=True)['status']=='already_configured')
    check('two_native_agent_directories',len(list((root/'.codex/agents').glob('*.toml')))==7 and len(list((root/'.claude/agents').glob('*.md')))==7)
    check('no_models_inferred_as_available',json.loads((root/'.factory/setup.json').read_text())['model_access']=='NOT_VERIFIED')
    for i,jid in enumerate(out['jobs']):
        jp=root/'jobs'/jid
        probe=json.loads(execute(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(source)]).stdout)
        pp=jp/'analysis/probe.json';atomic_json(pp,probe);s.checkpoint(jid,'probe',[pp],'Real FFprobe on synthetic source')
        s.checkpoint(jid,'transcript',note='Synthetic sine signal contains no speech. ASR not tested.',skip=True)
        scope=jp/'analysis/scope.json';segments=[{'source':str(source),'in':2*i,'out':2*i+2}]
        atomic_json(scope,{'job_id':jid,'segments':segments});s.checkpoint(jid,'scope',[scope],'Fixture boundaries, not detected by a model')
        s.checkpoint(jid,'script',note='No reference script in this mechanical integration',skip=True)
        edl=jp/'edit/edl.json';atomic_json(edl,{'segments':segments,'output':{'width':320,'height':180,'fps':24,'fit':'contain'}})
        s.checkpoint(jid,'assembly',[edl],'Actual EDL for this synthetic child')
        s.checkpoint(jid,'silence',note='Continuous sine wave; no silence requested for this fixture',skip=True)
        s.checkpoint(jid,'visual',note='No visuals requested in this integration',skip=True)
        s.checkpoint(jid,'captions',note='No speech in this fixture',skip=True)
        draft=jp/'renders/draft.mp4';execute([sys.executable,str(ROOT/'tools/render_edl.py'),str(edl),'--output',str(draft)])
        s.checkpoint(jid,'preview',[draft],'Real FFmpeg render, not an artistic review')
        duration=float(json.loads(execute(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(draft)]).stdout)['format']['duration'])
        check(f'child_{i+1}_real_render_duration',abs(duration-2)<.1)
        check(f'child_{i+1}_waits_for_approval',s.resume(jid)['next_stages']==['approval'])
        check(f'child_{i+1}_scope_enforced',s.validate_edl(jid,edl)['scope_checked'])
    check('original_hash_preserved',sha(source)==before)
    # Native CLI protocol adapter exercise, using a deliberately named fake executable.
    fake=w/'synthetic-provider-cli';fake.write_text('#!'+sys.executable+'\n'+(ROOT/'tests/fixtures/fake_host.py').read_text());fake.chmod(0o700)
    prompt=w/'packet.txt';prompt.write_text('Synthetic timing review; no real customer data.')
    bind_model(root,'claude','standard','synthetic-claude','medium','SYNTHETIC binding for protocol test only')
    bind_model(root,'codex','standard','synthetic-codex','medium','SYNTHETIC binding for protocol test only')
    s.authorize('lote-ficticio','SYNTHETIC authorization to exercise fixture CLI; no real billing')
    with patch('factory_runner.shutil.which',return_value=str(fake)):
        c=run(root,out['jobs'][0],'edit',prompt,'claude','.20',True)
        check('claude_fixture_subprocess_success',c['ok'] and c['cost_usd']==.08)
        check('reported_model_not_assumed_alias',c['observed_models']==['SYNTHETIC-reported-model'])
        check('completed_packet_reused',run(root,out['jobs'][0],'edit',prompt,'claude','.20',True)['status']=='reuse')
        try:run(root,out['jobs'][1],'edit',prompt,'codex','.20',True);blocked=False
        except FactoryError as e:blocked=e.code=='NO_NATIVE_CAP'
        check('codex_dollar_native_fails_closed',blocked)
        s.configure_budget('lote-ficticio','usd','.50','estimate','SYNTHETIC explicit estimate-mode opt-in')
        c2=run(root,out['jobs'][1],'edit',prompt,'codex','.20',True)
        check('tokens_only_cost_stays_unknown',c2['status']=='unknown' and c2['cost_usd'] is None)
        check('unknown_retains_reservation',s.budget('lote-ficticio')['committed_usd']=='0.280000')
        s.settle(c2['call'],'.07',note='SYNTHETIC provider reconciliation fixture')
        check('shared_budget_reconciled',s.budget('lote-ficticio')['remaining_usd']=='0.350000')
    # A completely separate Python process resumes the same job and budget.
    x=json.loads(execute([sys.executable,str(ROOT/'factory.py'),'--root',str(root),'resume','--job',out['jobs'][1]]).stdout)
    check('cross_process_resume_without_retranscribing',x['next_stages']==['approval'])
    check('cross_process_budget_not_reset',x['budget']['committed_usd']=='0.150000')
    # Interrupt a fake process; reserve must remain until verified.
    profiles=json.loads((root/'config/execution-profiles.json').read_text());profiles['equilibrado']['timeout_seconds']=.2;atomic_json(root/'config/execution-profiles.json',profiles)
    with patch.dict(os.environ,{'VF_SYNTHETIC_SCENARIO':'timeout'}),patch('factory_runner.shutil.which',return_value=str(fake)):
        try:run(root,out['jobs'][0],'qa',prompt,'claude','.10',True);interrupted=False
        except FactoryError as e:interrupted=e.code=='RUN_INTERRUPTED'
    check('timeout_kills_fake_process_and_records_unknown',interrupted and s.budget('lote-ficticio')['calls'][-1]['status']=='unknown')
    check('timeout_not_assumed_free',s.budget('lote-ficticio')['committed_usd']=='0.250000')
    before_transcript=s.resume(out['jobs'][0])['stages'][1]['status'];change=s.change(out['jobs'][0],'asset','SYNTHETIC change of insertion only')
    check('asset_change_keeps_transcription',before_transcript==s.resume(out['jobs'][0])['stages'][1]['status'] and 'transcript' in change['preserved'])
    report={'kind':'Local FFmpeg/filesystem/subprocess integration; provider protocols are synthetic fixtures','checks':checks,'passed':sum(checks.values()),'total':len(checks),
       'limitations':['No live Codex/Claude invocation, login, model access or paid consumption.','No actual speech transcription or semantic/visual recognition.','Approval gate waits; no human artistic approval was simulated as real.','Windows/macOS installers not executed; tested on this Linux container.']}
    atomic_json(w/'results.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
