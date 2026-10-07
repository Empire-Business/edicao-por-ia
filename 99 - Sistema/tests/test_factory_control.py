"""Local tests for novice setup, jobs, cost ledger and CLI protocol. No live model calls."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile, tomllib, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from factory_common import FactoryError, atomic_json, inside, sha, usd_units
from factory_state import State, STAGES
from factory_setup import setup, desired_setup, rollback, upgrade, dependency_plan, toml_agents, bind_model
from factory_runner import route, command_for, parse_response, run, host_check
from factory_doctor import collect
from client_memory import Memory
from project_layout import surface_root
from design_catalog import register_visual


def manifest(root):
    files={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and not any(s in p.parts for s in ('__pycache__','.factory')) and p.name!='PACKAGE_MANIFEST.json'}
    atomic_json(root/'PACKAGE_MANIFEST.json',{'package':'claude-video-factory','version':'test','files':files})
    return files

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        tmp_root=Path(self.tmp.name).resolve()
        self.root=tmp_root/'Fábrica de vídeos';self.root.mkdir()
        for name in ('config','patterns','adapters','.claude'):
            source=(surface_root(ROOT) if name=='.claude' else ROOT)/name
            if source.exists():shutil.copytree(source,self.root/name,ignore=shutil.ignore_patterns('__pycache__','*.local.json','.env*','CHAVES DAS INTEGRAÇÕES.txt','github-access.json'))
        for name in ('AGENTS.md','CLAUDE.md','VERSION'):
            if (ROOT/name).exists():shutil.copy2(ROOT/name,self.root/name)
        manifest(self.root)
        self.media=self.root/'Gravação com espaços.mp4';self.media.write_bytes(b'synthetic fixture, not video')
        self.script=self.root/'Roteiro A.txt';self.script.write_text('Texto fictício para teste.',encoding='utf8')
        self.state=State(self.root)
        Memory(self.root).init('fixture','Synthetic test format')
        register_visual(self.root,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
    def intake(self,**kw):
        return self.state.intake({'id':'teste','sources':[str(self.media)],'visual_identity':'IDP01','format':'fixture','visual_identity':'IDP01',**kw})
    def error(self,code,fn,*a,**kw):
        with self.assertRaises(FactoryError) as r:fn(*a,**kw)
        self.assertEqual(r.exception.code,code)
    def evidence(self,jid,stage,content=None):
        p=self.root/'jobs'/jid/'analysis'/(stage+'.json')
        atomic_json(p,content or {'fixture':True,'stage':stage});return str(p)
    def stage(self,jid,s):
        ev=self.evidence(jid,s,{'job_id':jid,'segments':[{'source':str(self.media),'in':0,'out':1}]} if s in ('scope','assembly','silence') else None)
        with patch.object(State,'media_duration',return_value=10):
            return self.state.checkpoint(jid,s,[ev],'Synthetic evidence; not real editorial QA',user_approved=s=='approval')
    def through(self,jid,last):
        for s in STAGES:
            self.stage(jid,s)
            if s==last:break
    def money(self,**kw):
        x=self.intake(budget={'mode':'usd','limit_usd':'1.00','cap_mode':'native'},**kw)
        self.state.authorize(x['batch'],'Synthetic authorization for local accounting test only')
        return x
    def reserve(self,jid='teste',key='q1',quote='.4',**kw):
        return self.state.reserve(jid,'edit','claude','mock-model','standard',key,quote,native_cap=True,**kw)

class InputTests(Base):
    def test_format_manifest_and_client_fingerprint_alias(self):
        Memory(self.root).init('alpha','Synthetic Alpha')
        req={'id':'format-job','sources':[str(self.media)],'visual_identity':'IDP01','format':'alpha'}
        created=self.state.intake(req)
        self.assertEqual(created['status'],'created')
        manifest=json.loads((self.root/'jobs/format-job/job.yaml').read_text())
        self.assertEqual(manifest['format'],'alpha');self.assertEqual(manifest['client'],'alpha')
        resumed=self.state.intake({'id':'format-job','sources':[str(self.media)],'visual_identity':'IDP01','client':'alpha'})
        self.assertEqual(resumed['status'],'resume')
        self.assertEqual(resumed['batch'],'format-job')
        self.assertEqual(manifest['name'],'Gravação com espaços')

    def test_explicit_video_name_is_saved_for_export_filenames(self):
        result=self.state.intake({'id':'named-video','name':'Aula de proporção','sources':[str(self.media)],'visual_identity':'IDP01','format':'fixture'})
        manifest=json.loads((self.root/'jobs/named-video/job.yaml').read_text())
        self.assertEqual(manifest['name'],'Aula de proporção')

    def test_unknown_pattern_in_registered_format(self):
        self.error('UNKNOWN_PATTERN',self.intake,pattern='inexistente')
        self.assertFalse((self.root/'jobs/teste').exists())
    def test_repeated_intake_resumes_without_new_job(self):
        a=self.intake();b=self.intake();self.assertEqual(a['jobs'],b['jobs']);self.assertEqual(b['status'],'resume')
    def test_conflicting_same_id_blocked(self):
        self.intake();self.error('JOB_CONFLICT',self.intake,notes='Outra instrução')
    def test_explicit_new_version(self):
        self.intake();x=self.state.intake({'id':'teste','sources':[str(self.media)],'visual_identity':'IDP01','format':'fixture'},True)
        self.assertEqual(x['jobs'],['teste-v2'])
    def test_sources_preserved_and_accents(self):
        old=sha(self.media);x=self.intake();self.state.resume('teste');self.assertEqual(old,sha(self.media));self.assertTrue((self.root/'jobs/teste/job.yaml').exists())
    def test_missing_source_blocked(self):
        self.error('MISSING_INPUT',self.intake,sources=['/path/not-present.mp4'])
    def test_empty_source_blocked(self):
        self.media.write_bytes(b'');self.error('EMPTY_INPUT',self.intake)
    def test_invalid_count(self):
        for count in (0,True,51,1.2):
            with self.subTest(count=count):self.error('OUTPUT_COUNT',self.intake,expected_outputs=count)
    def test_unknown_fields_not_ignored(self):
        self.error('UNKNOWN_FIELDS',self.intake,unrecognized_setting=True)
    def test_two_outputs_scripts_and_assets_isolated(self):
        b=self.root/'B.txt';b.write_text('B')
        x=self.intake(expected_outputs=2,reference_assignments={'1':str(self.script),'2':str(b)},supporting_assets=[{'path':str(b),'output':2}])
        first=json.loads(self.state.job(x['jobs'][0])['manifest']);second=json.loads(self.state.job(x['jobs'][1])['manifest'])
        self.assertEqual(first['supporting_assets'],[]);self.assertEqual(second['reference_script']['paths'],[str(b.resolve())])
        self.assertFalse(second['script_assignment_pending']);self.assertEqual(self.state.job(x['jobs'][0])['batch'],self.state.job(x['jobs'][1])['batch'])
    def test_one_script_is_assigned_automatically(self):
        self.intake(reference_scripts=[str(self.script)])
        j=json.loads(self.state.job('teste')['manifest']);self.assertTrue(j['reference_script']['enabled'])
    def test_multiple_scripts_not_guessed(self):
        self.intake(expected_outputs=2,reference_scripts=[str(self.script)])
        j=json.loads(self.state.job('teste-v01')['manifest']);self.assertTrue(j['script_assignment_pending'])
        self.error('SCRIPT_ASSIGNMENT_REQUIRED',self.state.checkpoint,'teste-v01','script',note='Cannot skip unknown script',skip=True)
    def test_assign_script_then_continue(self):
        self.intake(expected_outputs=2,reference_scripts=[str(self.script)])
        self.state.assign_script('teste-v01',str(self.script),'User explicitly linked script A')
        self.assertFalse(json.loads(self.state.job('teste-v01')['manifest'])['script_assignment_pending'])
    def test_assigned_reference_cannot_silently_skip(self):
        self.intake(reference_scripts=[str(self.script)])
        self.error('REFERENCE_REQUIRED',self.state.checkpoint,'teste','script',note='Would skip supplied reference',skip=True)
    def test_owner_never_selects_new_job(self):
        m=Memory(self.root);m.init('alpha','Alpha fictícia');m.owner('alpha')
        self.error('FORMAT_REQUIRED',self.state.intake,{'sources':[str(self.media)],'visual_identity':'IDP01'})
        self.assertFalse((self.root/'jobs').exists())
    def test_anonymous_is_blocked_even_with_owner(self):
        m=Memory(self.root);m.init('alpha','Alpha');m.owner('alpha')
        self.error('FORMAT_REQUIRED',self.state.intake,{'sources':[str(self.media)],'visual_identity':'IDP01','anonymous':True})
    def test_single_registered_format_is_not_implicit(self):
        self.error('FORMAT_REQUIRED',self.state.intake,{'sources':[str(self.media)],'visual_identity':'IDP01'})
    def test_missing_format_does_not_read_other_profile(self):
        with patch.object(Memory,'context',side_effect=AssertionError('must not read another format')):
            self.error('FORMAT_REQUIRED',self.state.intake,{'sources':[str(self.media)],'visual_identity':'IDP01'})
    def test_generic_resume_does_not_pick_single_historical_job(self):
        self.intake();self.assertEqual(self.state.resume()['status'],'choose_job')
    def test_legacy_unbound_job_cannot_advance_and_assign_preserves_budget(self):
        self.money();self.reserve()
        before=self.state.budget('teste')
        path=self.root/'jobs/teste/job.yaml'
        job=json.loads(self.state.job('teste')['manifest']);job.update(format=None,client=None)
        atomic_json(path,job)
        with self.state.db(True) as db:
            db.execute('UPDATE jobs SET client=NULL,manifest=? WHERE id=?',(json.dumps(job),'teste'))
        self.error('FORMAT_REQUIRED',self.state.resume,'teste')
        self.error('FORMAT_REQUIRED',self.state.checkpoint,'teste','probe',note='Fixture')
        result=self.state.assign_format('teste','fixture','Synthetic explicit confirmation')
        self.assertTrue(result['budget_preserved'])
        self.assertEqual(self.state.budget('teste'),before)
        self.assertEqual(self.state.resume('teste')['format'],'fixture')
        self.assertEqual(json.loads(path.read_text())['format'],'fixture')
    def test_existing_named_job_cannot_be_reassigned_to_another_format(self):
        self.intake();Memory(self.root).init('other','Other fixture')
        self.error('CLIENT_MISMATCH',self.state.assign_format,'teste','other','Synthetic request')
    def test_explicit_captions_pin_beats_saved_preference(self):
        m=Memory(self.root);m.init('alpha','Alpha')
        m.commit('alpha',[{'kind':'preference','key':'requirements.captions','setting':'requirements.captions','value':True,'scope':'client','scope_id':'alpha','basis':'user_explicit','source':'user_message','quote':'Use legendas nos meus vídeos.','reason':'Synthetic future preference.'}],'test-captions')
        self.intake(format='alpha',captions=False)
        self.assertFalse(json.loads((self.root/'jobs/teste/job.effective.json').read_text())['requirements']['captions'])
    def test_bad_budget_type_is_clear_error(self):
        self.error('INVALID_BUDGET',self.intake,budget=None)
    def test_cross_client_resume_blocked(self):
        m=Memory(self.root);m.init('alpha','Alpha');self.intake(format='alpha')
        self.error('CLIENT_MISMATCH',self.state.resume,'teste','beta')

class ProgressTests(Base):
    def test_stage_order_requires_prior_evidence(self):
        self.intake();self.error('STAGE_ORDER',self.state.checkpoint,'teste','final',[self.evidence('teste','final')],'Fixture')
    def test_cannot_skip_required(self):
        self.intake();self.error('REQUIRED_STAGE',self.state.checkpoint,'teste','assembly',note='Fixture',skip=True)
    def test_must_supply_evidence(self):
        self.intake();self.error('MISSING_EVIDENCE',self.state.checkpoint,'teste','probe',note='Fixture')
    def test_approval_not_inferred(self):
        self.intake();self.error('USER_APPROVAL_REQUIRED',self.state.checkpoint,'teste','approval',note='Fixture')
    def test_scope_pending_cleared_after_real_checkpoint(self):
        self.intake(expected_outputs=2);self.through('teste-v01','scope')
        self.assertFalse(json.loads(self.state.job('teste-v01')['manifest'])['scope_pending'])
        self.assertFalse(json.loads((self.root/'jobs/teste-v01/job.yaml').read_text())['scope_pending'])
    def test_scope_source_verified(self):
        self.intake();self.through('teste','transcript')
        ev=self.evidence('teste','scope',{'job_id':'teste','segments':[{'source':'other.mp4','in':0,'out':1}]})
        self.error('SCOPE_SOURCE',self.state.checkpoint,'teste','scope',[ev],'Fixture')
    def test_scope_duration_verified(self):
        self.intake();self.through('teste','transcript')
        ev=self.evidence('teste','scope',{'job_id':'teste','segments':[{'source':str(self.media),'in':0,'out':99}]})
        with patch.object(State,'media_duration',return_value=10):self.error('SCOPE_RANGE',self.state.checkpoint,'teste','scope',[ev],'Fixture')
    def test_scope_must_be_this_job(self):
        self.intake();self.through('teste','transcript')
        ev=self.evidence('teste','scope',{'job_id':'outro','segments':[]})
        self.error('SCOPE_MISMATCH',self.state.checkpoint,'teste','scope',[ev],'Fixture')
    def test_edl_cannot_escape_child_scope(self):
        self.intake();self.through('teste','scope')
        ev=self.evidence('teste','bad-edl',{'segments':[{'source':str(self.media),'in':0,'out':3}]})
        with patch.object(State,'media_duration',return_value=10):self.error('EDL_OUTSIDE_SCOPE',self.state.validate_edl,'teste',ev)
    def test_edl_within_child_scope_passes(self):
        self.intake();self.through('teste','scope')
        ev=self.evidence('teste','edl',{'segments':[{'source':str(self.media),'in':.2,'out':.8}]})
        with patch.object(State,'media_duration',return_value=10):self.assertTrue(self.state.validate_edl('teste',ev)['scope_checked'])
    def test_overlapping_child_ranges_blocked(self):
        self.intake(expected_outputs=2);self.through('teste-v01','scope');self.through('teste-v02','transcript')
        with self.assertRaises(FactoryError) as e:self.stage('teste-v02','scope')
        self.assertEqual(e.exception.code,'CHILD_SCOPE_OVERLAP')
    def test_selective_asset_change_preserves_transcript(self):
        self.intake();self.through('teste','delivery')
        r=self.state.change('teste','asset','User replaced only an insert')
        self.assertIn('transcript',r['preserved']);self.assertNotIn('captions',r['invalidated']);self.assertIn('approval',r['invalidated'])
    def test_missing_output_invalidates_downstream(self):
        self.intake();self.through('teste','silence');(self.root/'jobs/teste/analysis/assembly.json').unlink()
        r=self.state.resume('teste');self.assertIn('assembly',r['next_stages'])
    def test_changed_input_blocks_until_confirmation(self):
        self.intake();self.through('teste','transcript');self.media.write_bytes(b'an authorized changed source fixture')
        r=self.state.resume('teste');self.assertEqual(r['status'],'inputs_changed');self.assertFalse(r['next_stages'])
        self.state.refresh_inputs('teste','User explicitly confirms new source bytes')
        self.assertEqual(self.state.resume('teste')['next_stages'],['probe'])
    def test_missing_input_cannot_be_reaccepted(self):
        self.intake();self.media.unlink();self.error('MISSING_INPUT',self.state.refresh_inputs,'teste','Fixture')
    def test_other_job_artifact_blocked(self):
        self.intake();self.error('CROSS_JOB_ARTIFACT',self.state.checkpoint,'teste','probe',[str(self.script)],'Fixture')
    def test_ambiguous_resume_lists_jobs(self):
        self.intake(expected_outputs=2);self.assertEqual(self.state.resume()['status'],'choose_job')
    def test_missing_job_export_recovered(self):
        self.intake();(self.root/'jobs/teste/job.yaml').unlink();self.state.resume('teste');self.assertTrue((self.root/'jobs/teste/job.yaml').exists())
    def test_feedback_change_invalidates_then_refreshes(self):
        m=Memory(self.root);m.init('alpha','Alpha');self.intake(format='alpha');self.through('teste','silence')
        m.commit('alpha',[{'kind':'preference','key':'motion.intensity','setting':'motion.intensity','value':'restrained','scope':'client','scope_id':'alpha','basis':'user_explicit','source':'user_message','quote':'Nos próximos vídeos use movimento discreto.','reason':'Synthetic explicit preference.'}],'synthetic-pref')
        self.assertEqual(self.state.resume('teste')['status'],'context_changed')
        self.state.refresh_context('teste','User requests applying saved preference')
        r=self.state.resume('teste');self.assertFalse(r['context_changed']);self.assertIn('assembly',r['next_stages'])
        self.assertTrue((self.root/'jobs/teste/job.effective.json').exists());self.assertTrue((self.root/'jobs/teste/job.effective-v2.json').exists())

class BudgetTests(Base):
    def test_currency_validated(self):
        for x in (-1,float('nan'),float('inf'),True,None,'no'):
            with self.subTest(x=x),self.assertRaises(FactoryError):usd_units(x)
        self.assertEqual(usd_units('.0000001'),1)
    def test_no_consent_no_call(self):
        self.intake();self.error('CONSENT_REQUIRED',self.reserve)
    def test_unknown_billing_no_authorize(self):
        self.intake();self.error('UNKNOWN_BILLING',self.state.authorize,'teste','Fixture')
    def test_zero_budget_blocks(self):
        self.intake(budget={'mode':'usd','limit_usd':0});self.state.authorize('teste','Fixture')
        self.error('BUDGET_EXHAUSTED',self.reserve)
    def test_batch_shared_not_per_child(self):
        self.money(expected_outputs=2);self.reserve('teste-v01',quote='.7')
        self.error('BUDGET_EXHAUSTED',self.reserve,'teste-v02',quote='.4')
    def test_atomic_concurrent_reservations(self):
        self.money(expected_outputs=2)
        def reserve(j):
            try:return State(self.root).reserve(j,'edit','claude','mock','standard',j,'.7',native_cap=True)['status']
            except FactoryError as e:return e.code
        with ThreadPoolExecutor(max_workers=2) as p:r=list(p.map(reserve,['teste-v01','teste-v02']))
        self.assertEqual(r.count('reserved'),1);self.assertIn('BUDGET_EXHAUSTED',r)
    def test_settle_releases_unused_reserve_once(self):
        self.money();c=self.reserve()['call'];self.state.mark_running(c);self.state.settle(c,'.2')
        self.assertEqual(self.state.budget('teste')['remaining_usd'],'0.800000')
        self.error('ALREADY_SETTLED',self.state.settle,c,'.2')
    def test_unknown_usage_keeps_reservation_blocks_next(self):
        self.money();c=self.reserve()['call'];self.state.mark_running(c);self.state.settle(c,success=False)
        self.assertEqual(self.state.budget('teste')['committed_usd'],'0.400000')
        self.error('UNMETERED_COST',self.reserve,key='another')
    def test_manual_settle_preserves_artifact(self):
        self.money();c=self.reserve()['call'];self.state.mark_running(c);self.state.settle(c,result={'path':'fixture'})
        self.state.settle(c,'.2',note='Documented mock usage')
        r=self.reserve();self.assertEqual(r['status'],'reuse');self.assertEqual(r['result'],{'path':'fixture'})
    def test_overrun_freezes_and_retains_real_cost(self):
        self.money();c=self.reserve()['call'];self.state.settle(c,'.6');self.assertTrue(self.state.budget('teste')['frozen'])
        self.error('BATCH_FROZEN',self.reserve,key='q2')
    def test_unfreeze_does_not_zero_ledger(self):
        self.money();c=self.reserve()['call'];self.state.settle(c,'.6');self.state.unfreeze('teste','Budget reviewed')
        self.assertEqual(self.state.budget('teste')['committed_usd'],'0.600000')
    def test_below_committed_limit_rejected(self):
        self.money();self.reserve();self.error('BUDGET_BELOW_COMMITTED',self.state.configure_budget,'teste','usd','.1','native','Fixture')
    def test_resume_does_not_reset_budget(self):
        self.money();self.reserve();self.assertEqual(State(self.root).budget('teste')['remaining_usd'],'0.600000')
    def test_cannot_cancel_running_spend(self):
        self.money();c=self.reserve()['call'];self.state.mark_running(c)
        self.error('CANNOT_CANCEL_SPEND',self.state.cancel_before_launch,c,'Fixture')
    def test_cancel_unlaunched_releases_reserve(self):
        self.money();c=self.reserve()['call'];self.state.cancel_before_launch(c,'Never started')
        self.assertEqual(self.state.budget('teste')['remaining_usd'],'1.000000')
    def test_duplicate_reserved_rejected(self):
        self.money();self.reserve();self.error('UNRESOLVED_CALL',self.reserve)
    def test_premium_approval_required_balanced(self):
        self.money();self.error('PREMIUM_APPROVAL',self.state.reserve,'teste','new-motion','claude','mock','premium','q','.4',native_cap=True)
    def test_no_native_cap_blocks_call(self):
        self.money();self.error('NO_NATIVE_CAP',self.state.reserve,'teste','edit','codex','mock','standard','q','.4')
    def test_estimate_cap_optin(self):
        self.intake(budget={'mode':'usd','limit_usd':'1','cap_mode':'estimate'});self.state.authorize('teste','Explicitly accepts estimates')
        self.assertEqual(self.state.reserve('teste','edit','codex','mock','standard','q','.4')['status'],'reserved')
    def test_subscription_does_not_invent_invoice(self):
        self.intake(budget={'mode':'subscription'});self.state.authorize('teste','Uses subscription')
        c=self.reserve(quote=None)['call'];self.state.settle(c,usage={'input_tokens':12})
        self.assertIsNone(self.state.budget('teste')['committed_usd'])
    def test_failed_retry_must_be_explicit(self):
        self.money();c=self.reserve()['call'];self.state.settle(c,'.1',success=False)
        self.error('RETRY_REQUIRED',self.reserve);self.assertEqual(self.reserve(retry=True)['status'],'reserved')
    def test_attempt_limit_enforced(self):
        self.money();c=self.reserve()['call'];self.state.settle(c,'.1',success=False)
        c=self.reserve(retry=True)['call'];self.state.settle(c,'.1',success=False)
        self.error('ATTEMPT_LIMIT',self.reserve,retry=True)
    def test_parallel_profile_limit(self):
        self.money(profile='economico');self.reserve();self.error('PARALLEL_LIMIT',self.reserve,key='q2')

class SetupTests(Base):
    def test_preview_does_not_install(self):
        r=setup(self.root);self.assertEqual(r['status'],'preview');self.assertFalse((self.root/'.codex/config.toml').exists())
    def test_both_agents_toml_valid(self):
        r=setup(self.root,apply=True);self.assertEqual(r['conflicts'],[])
        for p in (self.root/'.codex/agents').glob('*.toml'):
            d=tomllib.loads(p.read_text());self.assertIn('model',d);self.assertIn('developer_instructions',d)
        self.assertEqual(len(list((self.root/'.codex/agents').glob('*.toml'))),7)
    def test_repeated_setup_idempotent(self):
        setup(self.root,apply=True);r=setup(self.root,apply=True);self.assertEqual(r['status'],'already_configured')
    def test_other_hooks_preserved(self):
        p=self.root/'.claude/settings.json';atomic_json(p,{'custom':'keep','hooks':{'SessionStart':[{'hooks':[{'type':'command','command':'echo user-hook'}]}]}})
        setup(self.root,apply=True);d=json.loads(p.read_text());self.assertEqual(d['custom'],'keep');self.assertIn('user-hook',p.read_text())
    def test_user_toml_settings_preserved(self):
        p=self.root/'.codex/config.toml';p.parent.mkdir();p.write_text('model = "my-main"\n[agents]\nenabled=false\nmax_threads=1\n[other]\nx=2\n')
        setup(self.root,apply=True);d=tomllib.loads(p.read_text());self.assertEqual(d['model'],'my-main');self.assertFalse(d['agents']['enabled']);self.assertEqual(d['other']['x'],2);self.assertEqual(d['agents']['max_concurrent_threads_per_session'],1)
    def test_edited_agent_file_not_overwritten(self):
        p=self.root/'.claude/agents/assembly-editor.md';p.write_text('My custom role')
        r=setup(self.root,apply=True);self.assertIn(str(p.relative_to(self.root)),r['conflicts']);self.assertEqual(p.read_text(),'My custom role')
    def test_setup_backup_and_rollback(self):
        p=self.root/'.claude/settings.json';atomic_json(p,{'custom':'synthetic rollback fixture'});old=p.read_bytes();r=setup(self.root,apply=True);rid=Path(r['receipt']).parent.name
        rollback(self.root,rid,True);self.assertEqual(p.read_bytes(),old);self.assertFalse((self.root/'.codex/config.toml').exists())
        self.assertFalse(setup(self.root,apply=True)['conflicts'])
    def test_rollback_preserves_later_changes(self):
        r=setup(self.root,apply=True);(self.root/'.codex/config.toml').write_text('custom=true\n')
        with self.assertRaises(FactoryError):rollback(self.root,Path(r['receipt']).parent.name,True)
    def test_toml_inline_agents_fails_safely(self):
        with self.assertRaises(FactoryError):toml_agents('agents = {enabled = true}',{'triage':{'model':'m','effort':'low'}},1)
    def test_toml_missing_terminal_newline(self):
        r=toml_agents('[agents]\nenabled = true',{'triage':{'model':'m','effort':'low'}},1);self.assertTrue(tomllib.loads(r)['agents']['enabled'])
    def test_symlink_write_blocked(self):
        dest=Path(self.tmp.name)/'outside';dest.mkdir();(self.root/'unsafe').symlink_to(dest,target_is_directory=True)
        self.error('UNSAFE_PATH',inside,self.root,'unsafe/write.txt')
    def test_no_secret_model_note(self):
        self.error('POSSIBLE_SECRET',bind_model,self.root,'claude','standard','sonnet','medium','senha=superprivate123')
    def test_model_binding_adjusts_native_files(self):
        bind_model(self.root,'codex','triage','user-available','low','Listed in user model picker')
        r=desired_setup(self.root);d=tomllib.loads(r['.codex/agents/transcript-screener.toml'].decode());self.assertEqual(d['model'],'user-available')
    def test_dependencies_no_install_on_preview(self):
        with patch('factory_setup.subprocess.run') as proc:
            r=dependency_plan(self.root,'speech',system='Darwin',machine='arm64');self.assertFalse(proc.called);self.assertIn('mlx-whisper',str(r['commands']))
    def test_dependencies_cpu_fallback(self):
        r=dependency_plan(self.root,'speech',system='Linux',machine='x86_64');self.assertIn('faster-whisper',str(r['commands']))
    def test_upgrade_keeps_custom_and_private(self):
        source=Path(self.tmp.name)/'new';source.mkdir();(source/'VERSION').write_text('1.6.0');(source/'AGENTS.md').write_text('new router');manifest(source)
        custom=self.root/'patterns/custom.yaml';custom.write_text('mine: true')
        old=self.root/'AGENTS.md';old.write_text('user edited router')
        before=sha(self.state.path);r=upgrade(source,self.root,True)
        self.assertEqual(old.read_text(),'user edited router');self.assertIn('AGENTS.md',r['conflicts']);self.assertTrue(custom.exists());self.assertEqual(before,sha(self.state.path));self.assertEqual((self.root/'VERSION').read_text(),'1.6.0')

    def test_upgrade_rollback_restores_manifest(self):
        source=Path(self.tmp.name)/'new';source.mkdir();(source/'VERSION').write_text('next');manifest(source)
        old=(self.root/'PACKAGE_MANIFEST.json').read_bytes();r=upgrade(source,self.root,True)
        rollback(self.root,Path(r['receipt']).parent.name,True)
        self.assertEqual(old,(self.root/'PACKAGE_MANIFEST.json').read_bytes())


class RunnerTests(Base):
    def test_mechanical_task_zero_model(self):
        self.assertEqual(route(self.root,'claude','render')['llm_calls'],0)
    def test_missing_cli_not_fallback(self):
        with patch('factory_runner.shutil.which',return_value=None):self.error('HOST_MISSING',host_check,'claude')
    def test_codex_no_invented_dollar_flag(self):
        self.error('NO_NATIVE_CAP',command_for,'codex','m','low',2,1)
    def test_worker_flags_restrict_tools(self):
        a=command_for('claude','sonnet','medium',2,1);self.assertIn('--restricted',a);self.assertIn('--max-budget-usd',a);self.assertNotIn('--dangerously-skip-permissions',a)
        b=command_for('codex','m','low',2);self.assertIn('--ignore-user-config',b);self.assertIn('agents.enabled=false',b);self.assertNotIn('--yolo',b)
    def test_claude_result_reports_actual_model_and_cost(self):
        r=parse_response('claude',json.dumps({'type':'result','result':'Done','total_cost_usd':'.12','modelUsage':{'actual-id':{}},'usage':{'input_tokens':9}}))
        self.assertEqual(r['observed_models'],['actual-id']);self.assertEqual(r['reported_cost_usd'],'.12')
    def test_codex_usage_not_transformed_to_price(self):
        r=parse_response('codex','\n'.join(json.dumps(x) for x in [{'type':'item.completed','item':{'type':'agent_message','text':'Final'}},{'type':'turn.completed','usage':{'input_tokens':50,'output_tokens':4}}]))
        self.assertEqual(r['text'],'Final');self.assertIsNone(r['reported_cost_usd']);self.assertEqual(r['observed_models'],[])
    def test_no_hidden_reasoning_saved(self):
        r=parse_response('codex','\n'.join(json.dumps(x) for x in [{'type':'item.completed','item':{'type':'reasoning','text':'private'}},{'type':'item.completed','item':{'type':'agent_message','text':'Final'}},{'type':'turn.completed','usage':{}}]))
        self.assertNotIn('private',json.dumps(r))
    def test_run_preview_no_process_or_charge(self):
        self.money()
        with patch('factory_runner.subprocess.Popen') as proc:r=run(self.root,'teste','edit',self.script,quote_usd='.2')
        self.assertFalse(proc.called);self.assertEqual(r['status'],'preview');self.assertEqual(len(self.state.budget('teste')['calls']),0)
    def test_unconfirmed_model_blocks_execute(self):
        self.money();self.error('MODEL_NOT_CONFIRMED',run,self.root,'teste','edit',self.script,'claude','.2',True)
    def test_doctor_does_not_mistake_no_asr_for_speech_ready(self):
        real=subprocess.run
        def fake(args,**kw):
            if '-c' in args:return subprocess.CompletedProcess(args,0,json.dumps({'yaml':True,'faster_whisper':False,'mlx_whisper':False,'playwright':False}), '')
            return real(args,**kw)
        with patch('factory_doctor.subprocess.run',side_effect=fake):r=collect(self.root)
        self.assertFalse(r['capabilities']['speech_editing']['available']);self.assertFalse(r['capabilities']['speech_editing']['end_to_end_tested'])

if __name__=='__main__':unittest.main()
