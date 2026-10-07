"""Memory mechanics + synthetic host protocol. No live Claude/Codex calls."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from design_catalog import register_visual
from client_memory import Memory, validate_setting
from resolve_client_context import resolve, check, write_resolution
from memory_hook import handle
from install_memory_hooks import merge, install


def pref(key='motion.intensity',value='restrained',**kw):
    return {'kind':'preference','key':key,'value':value,'setting':key,'scope':'format',
            'scope_id':'alpha','basis':'user_explicit','source':'user_message',
            'quote':'Nos próximos vídeos, use movimentos mais discretos.',
            'reason':'Explicit future-scoped instruction in this synthetic test.',**kw}


def job(**kw):
    return {'id':'video-1','client':'alpha','project':'campaign-a','pattern':'talking-head-clean-v2',
            'explicit_fields':[],'motion':{'intensity':'balanced'},
            'silence_removal':{'enabled':True,'mode':'pattern_default'},
            'reference_script':{'enabled':False,'paths':[],'mode':'flexible'},**kw}


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        register_visual(self.root,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
        self.m=Memory(self.root);self.m.init('alpha','Synthetic Alpha');self.m.init('beta','Synthetic Beta')
        self.n=0
    def tearDown(self):self.tmp.cleanup()

    def save(self,item=None,client='alpha',token=None):
        self.n+=1
        return self.m.commit(client,[item or pref()],token or 'fixture-'+str(self.n))

    def test_01_explicit_preference_without_metrics(self):
        rec=self.save();self.assertEqual(rec['changes'][0]['status'],'active')
        self.assertEqual(self.m.context('alpha')['active'][0]['payload']['value'],'restrained')

    def test_02_reopen_store_persists(self):
        self.save();self.assertEqual(Memory(self.root).context('alpha')['active'][0]['key'],'motion.intensity')

    def test_03_cross_client_retrieval_is_empty(self):
        self.save();self.assertEqual(self.m.context('beta')['active'],[])

    def test_04_safe_path_components(self):
        for bad in ['../beta','Alpha','/tmp/client','a/b','_template','x'*81]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.m.init(bad,'test')

    def test_05_client_id_collision_not_silently_merged(self):
        with self.assertRaises(ValueError):self.m.init('alpha','Someone else')

    def test_06_missing_client_not_auto_created(self):
        with self.assertRaises(ValueError):self.m.context('absent')
        self.assertFalse((self.root/'context/clients/absent').exists())

    def test_07_cross_client_write_denied(self):
        with self.assertRaises(ValueError):self.save(pref(scope_id='beta'))

    def test_08_inference_is_not_an_active_rule(self):
        self.save(pref(basis='inferred'));c=self.m.context('alpha')
        self.assertEqual(c['active'],[]);self.assertEqual(c['candidate_count'],1)

    def test_09_document_instructions_are_not_user_preferences(self):
        self.save(pref(source='authorized_document'));self.assertEqual(self.m.context('alpha')['active'],[])

    def test_10_simulation_stays_candidate(self):
        self.save(pref(basis='simulated',source='simulation'));self.assertEqual(self.m.context('alpha')['active'],[])

    def test_11_fact_can_be_saved_without_setting(self):
        p=pref(kind='fact',key='brand.primary_color',value='blue');p.pop('setting')
        self.save(p);self.assertEqual(self.m.context('alpha')['active'][0]['key'],'brand.primary_color')

    def test_12_vague_feedback_not_invented_as_rule(self):
        p=pref(kind='observation',key='feedback.reaction',value='Não gostei.',basis='inferred');p.pop('setting')
        self.save(p);self.assertFalse(self.m.context('alpha')['active'])

    def test_13_unknown_target_approval_is_candidate(self):
        p=pref(kind='approval',key='reference.current',value='Gostei.');p.pop('setting')
        self.save(p);self.assertEqual(self.m.context('alpha')['candidate_count'],1)

    def test_14_approval_is_reference_not_winner(self):
        p=pref(kind='approval',key='reference.title',value='Use this title version',artifact={'id':'title','version':'v2'});p.pop('setting')
        self.save(p);c=self.m.context('alpha')
        self.assertFalse(c['active']);self.assertEqual(c['references'][0]['status'],'reference')

    def test_15_later_rejection_removes_positive_reference(self):
        p=pref(kind='approval',key='reference.title',value='approved',artifact={'id':'title','version':'v2'});p.pop('setting')
        self.save(p);self.save({**p,'kind':'rejection','value':'rejected'})
        refs=self.m.context('alpha')['references'];self.assertEqual(len(refs),1);self.assertEqual(refs[0]['status'],'rejected')

    def test_16_artifact_versions_not_confused(self):
        p=pref(kind='approval',key='reference.title',value='approved',artifact={'id':'title','version':'v2'});p.pop('setting')
        self.save(p);self.save({**p,'kind':'rejection','artifact':{'id':'title','version':'v1'},'value':'rejected'})
        self.assertEqual(len(self.m.context('alpha')['references']),2)

    def test_17_performance_needs_metrics(self):
        p=pref(kind='result',key='results.retention',value='great');p.pop('setting')
        with self.assertRaises(ValueError):self.save(p)

    def test_18_observed_result_no_causal_promotion(self):
        p=pref(kind='result',key='results.retention',value=0.6,basis='observed',source='metric_file',
               metrics={'metric':'retention','value':0.6,'period':'2026-09-01 to 2026-09-07',
                        'source_ref':'synthetic supplied report','comparison':None,'limitations':'Uncontrolled observation.'});p.pop('setting')
        self.save(p);rs=self.m.records('alpha');self.assertEqual(rs[0]['status'],'observed');self.assertFalse(self.m.context('alpha')['active'])

    def test_19_job_exception_does_not_leak(self):
        self.save(pref(scope='job',scope_id='video-1'))
        self.assertEqual(len(self.m.context('alpha',job='video-1')['active']),1)
        self.assertFalse(self.m.context('alpha',job='video-2')['active'])

    def test_20_project_isolation(self):
        self.save(pref(scope='project',scope_id='campaign-a'))
        self.assertEqual(len(self.m.context('alpha',project='campaign-a')['active']),1)
        self.assertFalse(self.m.context('alpha',project='campaign-b')['active'])

    def test_21_pattern_specific_preferences(self):
        self.save(pref(scope='pattern',scope_id='reels-dynamic-v2'))
        self.assertFalse(self.m.context('alpha',pattern='talking-head-clean-v2')['active'])
        self.assertEqual(len(self.m.context('alpha',pattern='reels-dynamic-v2')['active']),1)

    def test_22_scope_precedence(self):
        self.save(pref(value='energetic'));self.save(pref(value='balanced',scope='project',scope_id='campaign-a'))
        self.save(pref(value='restrained',scope='job',scope_id='video-1'))
        self.assertEqual(self.m.context('alpha',project='campaign-a',job='video-1')['active'][0]['payload']['value'],'restrained')
        self.assertEqual(self.m.context('alpha',project='campaign-a',job='video-2')['active'][0]['payload']['value'],'balanced')

    def test_23_same_scope_supersedes_history(self):
        self.save();self.save(pref(value='energetic'));rs=self.m.show('alpha',key='motion.intensity')
        self.assertEqual([r['status'] for r in rs],['superseded','active'])

    def test_24_revoke_does_not_resurrect_old_rule(self):
        self.save();rec=self.save(pref(value='energetic'));self.m.revoke('alpha',rec['changes'][0]['id'],'Withdrawn by synthetic user')
        self.assertFalse(self.m.context('alpha')['active'])

    def test_25_restore_creates_new_version(self):
        a=self.save();self.save(pref(value='energetic'));self.m.restore('alpha',a['changes'][0]['id'],'User requested the earlier restrained motion')
        self.assertEqual(self.m.context('alpha')['active'][0]['payload']['value'],'restrained')
        self.assertEqual(len(self.m.show('alpha',key='motion.intensity')),3)

    def test_26_forget_removes_all_versions(self):
        self.save();self.save(pref(value='energetic'))
        self.assertEqual(self.m.forget('alpha','motion.intensity',True)['removed'],2)
        self.assertEqual(self.m.show('alpha',key='motion.intensity'),[])

    def test_27_forget_needs_confirmation(self):
        self.save()
        with self.assertRaises(ValueError):self.m.forget('alpha','motion.intensity')
        self.assertEqual(len(self.m.context('alpha')['active']),1)

    def test_28_expired_preference_not_retrieved(self):
        self.save(pref(expires_at=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()))
        self.assertFalse(self.m.context('alpha')['active'])

    def test_29_idempotent_batch(self):
        first=self.save(token='same');second=self.save(token='same')
        self.assertEqual(first,second);self.assertEqual(len(self.m.show('alpha',key='motion.intensity')),1)

    def test_30_changed_payload_same_token_is_error(self):
        self.save(token='same')
        with self.assertRaises(ValueError):self.save(pref(value='energetic'),token='same')

    def test_31_repeated_same_value_no_inflation(self):
        self.save();r=self.save();self.assertEqual(r['changes'][0]['status'],'unchanged')
        self.assertEqual(len(self.m.show('alpha',key='motion.intensity')),1)

    def test_32_batch_failure_is_atomic(self):
        with self.assertRaises(ValueError):self.m.commit('alpha',[pref(),pref(value='bogus')],'bad')
        self.assertFalse(self.m.context('alpha')['active'])

    def test_33_contradictory_same_turn_rejected(self):
        with self.assertRaises(ValueError):self.m.commit('alpha',[pref(),pref(value='energetic')],'conflict')
        self.assertFalse(self.m.context('alpha')['active'])

    def test_34_credentials_rejected(self):
        with self.assertRaises(ValueError):self.save(pref(quote='api_key=abcdefghi987654321'))

    def test_35_setting_allowlist(self):
        with self.assertRaises(ValueError):self.save(pref(key='permissions.allow',value=['Bash(*)']))

    def test_36_invalid_numeric_values_rejected(self):
        for value in [True,float('nan'),float('inf'),-1,31,'0.2']:
            with self.subTest(value=value),self.assertRaises(ValueError):validate_setting('silence_removal.settings.keep_pause_seconds',value)

    def test_37_numeric_zero_minimum_rejected(self):
        with self.assertRaises(ValueError):validate_setting('silence_removal.settings.minimum_cut_seconds',0)

    def test_38_symlinked_storage_rejected(self):
        outside=self.root/'outside';outside.mkdir();(self.root/'context/clients/link').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):self.m.init('link','No')

    def test_39_no_implicit_owner(self):
        self.assertIsNone(self.m.owner());self.m.owner('alpha');self.assertEqual(self.m.owner(),'alpha');self.assertIsNone(self.m.owner(clear=True))

    def test_40_session_isolation(self):
        self.m.bind('one','alpha');self.m.bind('two','beta')
        t=self.m.begin('one')['turn'];self.m.capture('one',t,[pref()])
        self.assertFalse(self.m.context('beta')['active']);self.assertEqual(self.m.session('two')['client'],'beta')

    def test_41_unbound_capture_refused(self):
        turn=self.m.begin('session')['turn']
        with self.assertRaises(ValueError):self.m.capture('session',turn,[pref()])

    def test_42_stale_turn_refused(self):
        self.m.bind('session','alpha');a=self.m.begin('session')['turn'];self.m.begin('session')
        with self.assertRaises(ValueError):self.m.capture('session',a,[pref()])

    def test_43_bound_job_mismatch_refused(self):
        self.m.bind('session','alpha',job='video-1');t=self.m.begin('session')['turn']
        with self.assertRaises(ValueError):self.m.capture('session',t,[pref(scope='job',scope_id='video-2')])

    def test_44_capture_receipt_releases_stop(self):
        self.m.bind('session','alpha');handle(self.m,{'hook_event_name':'UserPromptSubmit','session_id':'session'})
        self.assertEqual(handle(self.m,{'hook_event_name':'Stop','session_id':'session'})['decision'],'block')
        self.m.capture('session',self.m.session('session')['turn'],[pref()])
        self.assertEqual(handle(self.m,{'hook_event_name':'Stop','session_id':'session'}),{})

    def test_45_skip_releases_stop_without_claiming_saved(self):
        turn=self.m.begin('s')['turn'];r=self.m.skip('s',turn,'No relevant new information')
        self.assertEqual(r['status'],'reviewed_no_save');self.assertEqual(handle(self.m,{'hook_event_name':'Stop','session_id':'s'}),{})

    def test_46_stop_hook_has_loop_guard(self):
        self.m.begin('s');r=handle(self.m,{'hook_event_name':'Stop','session_id':'s','stop_hook_active':True})
        self.assertNotIn('decision',r);self.assertIn('pending',r['systemMessage'])

    def test_47_prompt_not_stored(self):
        sensitive='unique-raw-prompt-not-for-storage-API-secret-999'
        handle(self.m,{'hook_event_name':'UserPromptSubmit','session_id':'s','prompt':sensitive,'transcript_path':'/no/access'})
        self.assertNotIn(sensitive.encode(),self.m.state_path().read_bytes())

    def test_48_new_session_does_not_get_other_client_profile(self):
        self.save();r=handle(self.m,{'hook_event_name':'SessionStart','session_id':'new'})
        self.assertNotIn('Synthetic Alpha',json.dumps(r));self.assertIn('No format',json.dumps(r))

    def test_48a_session_start_never_promotes_or_names_old_format(self):
        self.m.bind('old-session','alpha')
        response=handle(self.m,{'hook_event_name':'SessionStart','session_id':'old-session'})
        self.assertNotIn('alpha',json.dumps(response))
        self.assertIn('no owner/session fallback',json.dumps(response))

    def test_49_subagent_does_not_start_competing_turn(self):
        self.assertEqual(handle(self.m,{'hook_event_name':'UserPromptSubmit','session_id':'s','agent_id':'worker'}),{})
        self.assertIsNone(self.m.session('s'))

    def test_50_interrupted_turn_disclosed(self):
        self.m.begin('s');r=handle(self.m,{'hook_event_name':'UserPromptSubmit','session_id':'s'})
        self.assertIn('not reviewed',json.dumps(r))

    def test_51_context_omissions_explicit(self):
        for i in range(8):
            p=pref(kind='fact',key='brand.note'+str(i),value='a'*500);p.pop('setting');self.save(p)
        c=self.m.context('alpha',max_chars=1100)
        self.assertTrue(c['omitted_ids']);self.assertLessEqual(len(c['text']),1100)

    def test_52_show_requires_selective_query(self):
        with self.assertRaises(ValueError):self.m.show('alpha')

    def test_53_concurrent_writes_preserve_records(self):
        def work(i):
            p=pref(kind='fact',key='brand.fact'+str(i),value='synthetic-'+str(i));p.pop('setting')
            return Memory(self.root).commit('alpha',[p],'parallel-'+str(i))
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(work,range(12)))
        self.assertEqual(len(self.m.context('alpha',max_chars=20000)['active']),12)

    def test_54_moving_client_folder_preserves_memory(self):
        self.save();copyroot=self.root/'moved';copyroot.mkdir()
        shutil.copytree(self.root/'context/clients',copyroot/'context/clients')
        self.assertEqual(Memory(copyroot).context('alpha')['fingerprint'],self.m.context('alpha')['fingerprint'])

    def test_55_write_failure_cannot_report_saved(self):
        with patch('client_memory.sqlite3.connect',side_effect=sqlite3.OperationalError('readonly')):
            with self.assertRaises(sqlite3.OperationalError):self.save()

    def test_56_resolver_applies_preference(self):
        self.save();out,ctx=resolve(self.m,job());self.assertEqual(out['motion']['intensity'],'restrained');self.assertEqual(len(out['_memory']['applied']),1)

    def test_57_explicit_current_override_wins(self):
        self.save();out,_=resolve(self.m,job(explicit_fields=['motion.intensity']))
        self.assertEqual(out['motion']['intensity'],'balanced');self.assertFalse(out['_memory']['applied']);self.assertTrue(out['_memory']['overridden'])

    def test_58_parent_override_pins_children(self):
        self.save();out,_=resolve(self.m,job(explicit_fields=['motion']))
        self.assertEqual(out['motion']['intensity'],'balanced')

    def test_59_legacy_job_settings_preserved(self):
        self.save();j=job();j.pop('explicit_fields');out,_=resolve(self.m,j)
        self.assertEqual(out['motion']['intensity'],'balanced');self.assertTrue(out['_memory']['legacy_pinning'])

    def test_60_resolver_does_not_mutate_source_object(self):
        self.save();j=job();old=copy.deepcopy(j);resolve(self.m,j);self.assertEqual(j,old)

    def test_61_qa_detects_stale_memory(self):
        self.save();out,_=resolve(self.m,job());self.assertTrue(check(self.m,out)['ok'])
        self.save(pref(value='energetic'));self.assertFalse(check(self.m,out)['ok'])

    def test_62_qa_detects_tampered_setting(self):
        self.save();out,_=resolve(self.m,job());out['motion']['intensity']='energetic';self.assertFalse(check(self.m,out)['ok'])

    def test_63_no_script_no_reference_preference_application(self):
        self.save(pref(key='reference_script.mode',value='strict'))
        out,_=resolve(self.m,job());self.assertEqual(out['reference_script']['mode'],'flexible');self.assertTrue(out['_memory']['review'])

    def test_64_unknown_pin_refused(self):
        with self.assertRaises(ValueError):resolve(self.m,job(explicit_fields=['motion.missing']))

    def test_65_silence_off_normalized(self):
        self.save(pref(key='silence_removal.mode',value='off'));out,_=resolve(self.m,job())
        self.assertFalse(out['silence_removal']['enabled']);self.assertTrue(check(self.m,out)['ok'])

    def test_66_explicit_enabled_beats_inherited_off(self):
        self.save(pref(key='silence_removal.mode',value='off'));out,_=resolve(self.m,job(explicit_fields=['silence_removal.enabled']))
        self.assertTrue(out['silence_removal']['enabled']);self.assertEqual(out['silence_removal']['mode'],'pattern_default');self.assertTrue(check(self.m,out)['ok'])

    def test_67_conflicting_explicit_silence_switches_refused(self):
        with self.assertRaises(ValueError):resolve(self.m,job(silence_removal={'enabled':True,'mode':'off'},explicit_fields=['silence_removal.enabled','silence_removal.mode']))

    def test_68_saved_context_file_and_silence_settings(self):
        self.save(pref(key='silence_removal.settings.keep_pause_seconds',value=0.42))
        (self.root/'patterns').mkdir();shutil.copy(ROOT/'patterns/talking-head-clean-v2.yaml',self.root/'patterns/')
        raw=self.root/'job.yaml';raw.write_text(json.dumps(job()));before=raw.read_bytes()
        out=self.root/'job.effective.json';paths=write_resolution(self.m,raw,out)
        self.assertEqual(raw.read_bytes(),before)
        settings=json.loads(Path(paths['silence_settings']).read_text());self.assertEqual(settings['keep_pause_seconds'],0.42)
        self.assertTrue(Path(paths['context']).read_text().startswith('# Format memory: alpha'))
        with self.assertRaises(ValueError):write_resolution(self.m,raw,out)

    def test_69_missing_pattern_not_silently_faked(self):
        raw=self.root/'job.yaml';raw.write_text(json.dumps(job()))
        with self.assertRaises(ValueError):write_resolution(self.m,raw,self.root/'effective.json')
        self.assertFalse((self.root/'effective.json').exists())

    def test_70_hook_installer_preserves_settings(self):
        old={'permissions':{'deny':['Read(.env)']},'env':{'SOME_NON_SECRET':'x'},'hooks':{'Stop':[{'hooks':[{'type':'command','command':'echo existing'}]}]}}
        new=merge(old,'python3 tools/memory_hook.py')
        self.assertEqual(new['permissions'],old['permissions']);self.assertEqual(new['env'],old['env'])
        self.assertIn('echo existing',json.dumps(new));self.assertEqual(merge(new,'python3 tools/memory_hook.py'),new)

    def test_71_hook_installer_dry_run_and_backup(self):
        p=self.root/'.claude/settings.json';p.parent.mkdir();p.write_text('{"permissions":{"deny":["Read(.env)"]}}')
        old=p.read_bytes();install(self.root,False);self.assertEqual(p.read_bytes(),old)
        result=install(self.root,True);self.assertEqual(Path(result['backup']).read_bytes(),old)
        self.assertEqual(install(self.root,True)['status'],'already_installed')

    def test_72_capture_cli_across_processes(self):
        def cli(*args,data=None):
            p=subprocess.run([sys.executable,str(ROOT/'tools/client_memory.py'),'--root',str(self.root),*args],
                             input=json.dumps(data) if data else None,text=True,capture_output=True,check=True)
            return json.loads(p.stdout)
        cli('bind','--session','cli','--client','alpha');t=cli('begin','--session','cli')['turn']
        r=cli('capture','--session','cli','--turn',t,data={'items':[pref()]});self.assertEqual(r['status'],'saved')
        self.assertIn('restrained',cli('context','--client','alpha','--json')['text'])
        self.assertEqual(cli('status','--session','cli')['reviewed'],1)

    def test_72a_new_format_cli_and_legacy_client_alias(self):
        def cli(*args):
            p=subprocess.run([sys.executable,str(ROOT/'tools/format_memory.py'),'--root',str(self.root),*args],
                             text=True,capture_output=True,check=True)
            return json.loads(p.stdout)
        created=cli('init','--format','shorts','--name','Shorts format','--example-url','https://example.com/shorts')
        self.assertEqual(created['format'],'shorts')
        self.assertEqual(cli('context','--format','shorts','--json')['format'],'shorts')
        legacy=cli('init','--client','longform','--name','Longform format','--example-url','https://example.com/longform')
        self.assertEqual(legacy['format'],'longform')

    def test_72b_format_scope_and_format_only_job(self):
        item=pref(scope='format',scope_id='alpha')
        self.save(item)
        format_only={'id':'video-format-only','format':'alpha','project':'campaign-a',
                     'pattern':'talking-head-clean-v2','explicit_fields':[],
                     'motion':{'intensity':'balanced'},
                     'silence_removal':{'enabled':True,'mode':'pattern_default'},
                     'reference_script':{'enabled':False,'paths':[],'mode':'flexible'}}
        resolved,_=resolve(self.m,format_only)
        self.assertEqual(resolved['format'],'alpha')
        self.assertEqual(resolved['client'],'alpha')

    def test_73_make_job_inherits_client_without_mutating_pattern(self):
        self.save(pref(key='silence_removal.mode',value='relaxed'));self.save(pref(key='defaults.pattern',value='reels-dynamic-v2'))
        (self.root/'patterns').mkdir()
        for name in ['reels-dynamic-v2.yaml','talking-head-clean-v2.yaml']:shutil.copy(ROOT/'patterns'/name,self.root/'patterns'/name)
        source=self.root/'sample.mp4';source.write_bytes(b'synthetic-placeholder-not-a-render-test')
        pattern_before=(self.root/'patterns/reels-dynamic-v2.yaml').read_bytes()
        subprocess.run([sys.executable,str(ROOT/'tools/make_job.py'),'--visual-id','IDP01','--root',str(self.root),'--client','alpha','--source',str(source),'--id','my-video'],capture_output=True,text=True,check=True)
        j=json.loads((self.root/'jobs/my-video/job.effective.json').read_text())
        self.assertEqual(j['client'],'alpha');self.assertEqual(j['pattern'],'reels-dynamic-v2');self.assertEqual(j['silence_removal']['mode'],'relaxed')
        self.assertEqual((self.root/'patterns/reels-dynamic-v2.yaml').read_bytes(),pattern_before)

    def test_74_new_job_explicit_override_beats_client(self):
        self.save(pref(key='silence_removal.mode',value='relaxed'));(self.root/'patterns').mkdir();shutil.copy(ROOT/'patterns/talking-head-clean-v2.yaml',self.root/'patterns/')
        src=self.root/'s.mp4';src.write_bytes(b'fixture')
        subprocess.run([sys.executable,str(ROOT/'tools/make_job.py'),'--visual-id','IDP01','--root',str(self.root),'--client','alpha','--source',str(src),'--id','j','--silence-mode','tight'],check=True,capture_output=True,text=True)
        out=json.loads((self.root/'jobs/j/job.effective.json').read_text());self.assertEqual(out['silence_removal']['mode'],'tight')

    def test_75_new_job_needs_explicit_format_even_with_owner_or_session(self):
        (self.root/'patterns').mkdir();shutil.copy(ROOT/'patterns/talking-head-clean-v2.yaml',self.root/'patterns/')
        self.m.owner('alpha');self.m.bind('old-session','alpha');src=self.root/'s.mp4';src.write_bytes(b'fixture')
        for extra in ([],['--anonymous'],['--session','old-session']):
            result=subprocess.run([sys.executable,str(ROOT/'tools/make_job.py'),'--visual-id','IDP01','--root',str(self.root),
                '--source',str(src),'--id','missing-format',*extra],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Qual formato',result.stderr)
            self.assertFalse((self.root/'jobs/missing-format').exists())

    def test_76_schema_example_is_simulation(self):
        example=json.loads((ROOT/'memory/CAPTURE_EXAMPLE.json').read_text())['items'][0]
        self.assertEqual(example['basis'],'simulated')
        try:import jsonschema
        except ImportError:self.skipTest('optional jsonschema unavailable')
        jsonschema.validate(example,json.loads((ROOT/'memory/RECORD_SCHEMA.json').read_text()))

    def test_77_past_job_examples_retrievable_not_client_rules(self):
        p=pref(kind='approval',key='reference.title',value='approved',topic='motion',scope='job',scope_id='old-video',artifact={'id':'jobs/old/title.json','version':'v2'});p.pop('setting')
        self.save(p)
        self.assertFalse(self.m.context('alpha',job='new-video')['active'])
        self.assertEqual(len(self.m.history('alpha','examples','motion')['records']),1)
        self.assertEqual(self.m.history('beta','examples','motion')['records'],[])

    def test_78_history_excludes_stale_positive_after_rejection(self):
        p=pref(kind='approval',key='reference.title',value='approved',artifact={'id':'title','version':'v2'});p.pop('setting')
        self.save(p);self.save({**p,'kind':'rejection','value':'rejected'})
        rows=self.m.history('alpha','examples')['records']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['status'],'rejected')

    def test_79_candidate_shelf_inspectable_and_bounded(self):
        for i in range(5):
            p=pref(kind='observation',key='feedback.item'+str(i),value='unclear reaction',basis='inferred',topic='motion');p.pop('setting');self.save(p)
        rows=self.m.history('alpha','candidates','motion',3)['records']
        self.assertEqual(len(rows),3);self.assertEqual(rows[0]['key'],'feedback.item4')
        self.assertEqual(self.m.history('alpha','candidates','captions')['records'],[])

    def test_80_simulation_source_never_observed_performance(self):
        p=pref(kind='result',key='results.views',value=100,basis='observed',source='simulation');p.pop('setting')
        self.save(p)
        self.assertEqual(self.m.records('alpha',include_candidates=True)[0]['status'],'candidate')

    def test_81_revoking_latest_reference_does_not_revive_earlier_approval(self):
        p=pref(kind='approval',key='reference.title',value='approved',artifact={'id':'title','version':'v2'});p.pop('setting')
        self.save(p);rejection=self.save({**p,'kind':'rejection','value':'rejected'})
        self.m.revoke('alpha',rejection['changes'][0]['id'],'Explicit withdrawal')
        self.assertEqual(self.m.context('alpha')['references'],[])
        self.assertEqual(self.m.history('alpha','examples')['records'],[])

if __name__=='__main__':unittest.main(verbosity=2)
