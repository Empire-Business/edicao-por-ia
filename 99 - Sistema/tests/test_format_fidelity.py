"""Real file provenance, stale renders and completeness gates; no artistic-score fiction."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from factory_common import sha,fingerprint
from format_fidelity import snapshot,validate,validate_locks

class Fidelity(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  for folder in ['config','patterns','references','jobs/demo/analysis','jobs/demo/qa','jobs/demo/frames','jobs/demo/renders']:(self.root/folder).mkdir(parents=True)
  self.reference=self.root/'references/example.mp4';self.reference.write_bytes(b'approved synthetic reference bytes')
  self.frame=self.root/'jobs/demo/frames/reference.png';self.frame.write_bytes(b'\x89PNG\r\n\x1a\n' + b'synthetic fixture')
  self.outframe=self.root/'jobs/demo/frames/output.png';self.outframe.write_bytes(b'\x89PNG\r\n\x1a\n' + b'output fixture')
  self.render=self.root/'jobs/demo/renders/final.mp4';self.render.write_bytes(b'final fixture')
  (self.root/'patterns/fixture-v1.yaml').write_text('id: fixture-v1\n')
  self.entry={'code':'FP01','uid':'personal.fixture','name':'Example','pattern':'fixture-v1','mechanism_details':{'mechanism':'Fixture mechanism','inputs':'Real input','steps':['Observed scene change'],'avoid':'No branding'},'reference_materials':[{'path':'references/example.mp4','sha256':sha(self.reference)}]}
  self.contract=snapshot(self.root,self.entry);self.job=self.root/'jobs/demo'
  self.manifest={'id':'demo','format_code':'FP01','format_uid':'personal.fixture','pattern':'fixture-v1','format_contract':self.contract}
 def report(self,phase='plan'):
  evidence={'path':'references/example.mp4','sha256':sha(self.reference),'at_seconds':0,'frame_path':'jobs/demo/frames/reference.png','frame_sha256':sha(self.frame)}
  report={'job_id':'demo','contract_sha256':self.contract['sha256'],'comparisons':[{'criterion':x['id'],'reference':copy.deepcopy(evidence),'decision':'Applied observed mechanism','status':'matched','output':{'frame_path':'jobs/demo/frames/output.png','frame_sha256':sha(self.outframe)}} for x in self.contract['criteria']]}
  if phase=='review':report.update(status='pass',render={'path':'jobs/demo/renders/final.mp4','sha256':sha(self.render)})
  path=self.job/('analysis/format-plan.json' if phase=='plan' else 'qa/format-fidelity.json');path.write_text(json.dumps(report));return path,report
 def test_plan_and_review_validate_actual_pinned_files(self):
  self.report();self.report('review');self.assertTrue(validate(self.root,self.job,self.manifest,'plan')['ok']);self.assertTrue(validate(self.root,self.job,self.manifest,'review')['ok'])
 def test_missing_comparison_blocks_assembly(self):
  with self.assertRaises(ValueError):validate(self.root,self.job,self.manifest,'plan')
 def test_controller_pins_reference_and_blocks_assembly_without_comparison(self):
  import shutil
  from client_memory import Memory
  from design_catalog import save,register_visual
  from factory_state import State
  from factory_common import FactoryError
  shutil.copytree(ROOT/'config',self.root/'config',dirs_exist_ok=True)
  entry={**self.entry,'memory_store':'fixture','description':'Fixture mechanism'}
  Memory(self.root).init('fixture','Fixture')
  save(self.root,{'version':2,'formats':[entry],'visual_identities':[]})
  identity=register_visual(self.root,'Private',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Test','body':'Test','labels':'Test'})
  source=self.root/'source.mp4';source.write_bytes(b'synthetic source fixture')
  state=State(self.root);state.intake({'id':'integration','format':'FP01','visual_identity':identity['code'],'sources':[str(source)]})
  manifest=json.loads((self.root/'jobs/integration/job.yaml').read_text())
  self.assertEqual(manifest['format_uid'],'personal.fixture');self.assertTrue(manifest['format_contract']['required'])
  evidence=self.root/'jobs/integration/analysis/edl.json';evidence.write_text('{"segments":[]}')
  with self.assertRaises(FactoryError) as result:state.checkpoint('integration','assembly',[str(evidence)],'Synthetic integration test')
  self.assertEqual(result.exception.code,'FORMAT_FIDELITY_REQUIRED')
 def test_reference_corruption_is_not_accepted(self):
  self.report();self.reference.write_bytes(b'changed reference')
  with self.assertRaises(ValueError):validate(self.root,self.job,self.manifest,'plan')
 def test_changed_render_or_pending_review_is_not_a_pass(self):
  self.report('review');self.render.write_bytes(b'new revision')
  with self.assertRaises(ValueError):validate(self.root,self.job,self.manifest,'review')
 def test_other_job_frame_and_missing_criterion_are_rejected(self):
  path,report=self.report();report['comparisons'].pop();path.write_text(json.dumps(report))
  with self.assertRaises(ValueError):validate(self.root,self.job,self.manifest,'plan')
  path,report=self.report();outside=self.root/'references/wrong.png';outside.write_bytes(self.frame.read_bytes());report['comparisons'][0]['reference']['frame_path']='references/wrong.png';path.write_text(json.dumps(report))
  with self.assertRaises(ValueError):validate(self.root,self.job,self.manifest,'plan')
 def test_reused_f_alias_cannot_inherit_old_generation_reference(self):
  entry={**self.entry,'code':'F02','uid':'official.new'};entry.pop('reference_materials')
  (self.root/'config/reference-library.json').write_text(json.dumps({'formats':{'F02':{'uid':'factory.old','references':self.entry['reference_materials']}},'files':{}}))
  self.assertIsNone(snapshot(self.root,entry))
 def test_published_primary_reference_is_selected_and_hash_checked(self):
  alternative=self.root/'references/published.mp4';alternative.write_bytes(b'published fixture')
  ref={'path':'references/published.mp4','sha256':sha(alternative)}
  entry={k:v for k,v in self.entry.items() if k!='reference_materials'}
  refs=[*self.entry['reference_materials'],ref]
  (self.root/'config/reference-library.json').write_text(json.dumps({'formats':{'FP01':{'uid':entry['uid'],'references':refs}},'files':{r['path']:r['sha256'] for r in refs}}))
  (self.root/'config/format-reference-selection.json').write_text(json.dumps({'formats':{entry['uid']:{'primary_reference':ref}}}))
  self.assertEqual(snapshot(self.root,entry)['primary_reference']['path'],ref['path'])
  alternative.write_bytes(b'changed publication')
  with self.assertRaises(ValueError):snapshot(self.root,entry)
 def test_reference_recipe_conflict_requires_current_job_instruction(self):
  self.contract['reference_conflicts']=[{'field':'visual.presenter_on_camera','recipe_value':'opening_only','reference_observation':'Presenter remains in body scenes'}]
  self.contract['sha256']=fingerprint({k:v for k,v in self.contract.items() if k!='sha256'})
  self.report()
  with self.assertRaisesRegex(ValueError,'divergência'):validate(self.root,self.job,self.manifest,'plan')
  self.manifest['format_deviations']={'pace-and-composition':'Use a slower pace'}
  with self.assertRaisesRegex(ValueError,'divergência'):validate(self.root,self.job,self.manifest,'plan')
  self.manifest['format_deviations']['recipe-specific-rules']='For this job, retain the presenter in the body as shown in the example.'
  self.assertTrue(validate(self.root,self.job,self.manifest,'plan')['ok'])
 def test_consolidated_recipe_and_name_locks_detect_changes(self):
  (self.root/'config/design-defaults.json').write_text(json.dumps({'formats':[self.entry]}))
  locks={'formats':{'personal.fixture':{'code':'FP01','definition_sha256':fingerprint(self.entry),'pattern_sha256':sha(self.root/'patterns/fixture-v1.yaml')}}}
  (self.root/'config/format-locks.json').write_text(json.dumps(locks));self.assertTrue(validate_locks(self.root)['ok'])
  entry={**self.entry,'name':'Unauthorized rename'};(self.root/'config/design-defaults.json').write_text(json.dumps({'formats':[entry]}))
  with self.assertRaises(ValueError):validate_locks(self.root)

if __name__=='__main__':unittest.main()
