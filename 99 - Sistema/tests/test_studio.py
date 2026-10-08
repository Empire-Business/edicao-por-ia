"""New mechanics only. Artistic judgment / provider vision not simulated as real approval."""
import copy, json, sys, tempfile, unittest, wave, subprocess, shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from studio_render import inspect, sample_times, blend, rawhash
from studio_review import validate_plan, validate_review, register_review, sample_grid, GATES, VISUAL, briefs
from studio_audio import grid_document, synth
from factory_common import sha
from factory_runner import route
from factory_setup import dependency_plan

class Studio(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.media_temp=tempfile.TemporaryDirectory();cls.synthetic_video=Path(cls.media_temp.name)/'synthetic-motion-demo.mp4'
  if shutil.which('ffmpeg'):
   subprocess.run(['ffmpeg','-v','error','-n','-f','lavfi','-i','testsrc2=size=64x64:rate=10:duration=0.5','-c:v','libx264','-pix_fmt','yuv420p',str(cls.synthetic_video)],check=True)
 @classmethod
 def tearDownClass(cls):cls.media_temp.cleanup()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
  self.plan=json.loads((ROOT/'studio/templates/PLAN_TEMPLATE.json').read_text())
  self.plan['new_style']=False
  self.pp=self.r/'plan.json';self.save_plan()
 def tearDown(self):self.tmp.cleanup()
 def save_plan(self):self.pp.write_text(json.dumps(self.plan))
 def invalid_plan(self):self.save_plan();self.assertRaises(ValueError,validate_plan,self.pp)
 def test_valid_plan(self):self.assertTrue(validate_plan(self.pp)[1]['ok'])
 def test_gap(self):self.plan['shots'][1]['start_frame']=73;self.invalid_plan()
 def test_overlap(self):self.plan['shots'][1]['start_frame']=71;self.invalid_plan()
 def test_incomplete(self):self.plan['shots'][-1]['end_frame']=143;self.invalid_plan()
 def test_repeat_shot(self):self.plan['shots'][1]['id']='s01';self.invalid_plan()
 def test_missing_state(self):self.plan['shots'][0]['states']=[];self.invalid_plan()
 def test_state_order(self):self.plan['shots'][0]['states'].reverse();self.invalid_plan()
 def test_state_outside(self):self.plan['shots'][0]['states'][0]['frame']=75;self.invalid_plan()
 def test_reject_vibe_only(self):del self.plan['shots'][0]['visual_action'];self.invalid_plan()
 def test_requires_proportion_layout(self):del self.plan['proportions'][0]['layout_note'];self.invalid_plan()
 def test_accepts_legacy_formats_field(self):
  self.plan['formats']=self.plan.pop('proportions');self.save_plan();self.assertTrue(validate_plan(self.pp)[1]['ok'])
 def test_rejects_conflicting_proportion_aliases(self):
  self.plan['formats']=[{'id':'vertical','width':360,'height':640,'layout_note':'Reflow vertically.'}];self.invalid_plan()
 def test_fractional_fps_explicitly_rejected(self):self.plan['fps']=29.97;self.invalid_plan()
 def test_invented_profile(self):self.plan['profile']='cheap';self.invalid_plan()
 def test_speech_needs_master(self):self.plan['mode']='speech_led';self.invalid_plan()
 def test_missing_dependency(self):self.plan['dependencies']={'master':{'path':'missing.mp4','sha256':'x'}};self.invalid_plan()
 def test_stale_dependency(self):p=self.r/'data.txt';p.write_text('a');self.plan['dependencies']={'source':{'path':p.name,'sha256':sha(p)}};p.write_text('b');self.invalid_plan()
 def test_unknown_asset(self):self.plan['shots'][0]['asset_ids']=['invented'];self.invalid_plan()
 def asset(self,**kw):
  p=self.r/'asset.png';Image.new('RGB',(50,50)).save(p)
  a={'id':'asset','path':p.name,'sha256':sha(p),'origin':'user_supplied'};a.update(kw);self.plan['assets']=[a]
 def test_real_asset(self):self.asset();self.save_plan();self.assertTrue(validate_plan(self.pp)[1]['ok'])
 def test_fake_product_ui(self):self.asset(origin='original_code',kind='product_ui');self.invalid_plan()
 def test_wrong_child(self):self.asset(child_id='other');self.invalid_plan()
 def test_unlabeled_mock(self):self.asset(origin='labeled_simulation');self.invalid_plan()
 def test_labeled_mock(self):self.asset(origin='labeled_simulation',visible_label='Simulação');self.save_plan();self.assertTrue(validate_plan(self.pp)[1]['ok'])
 def test_reference_needs_what_not_copy(self):
  self.asset();a=self.plan['assets'][0].copy();a['take']='palette';self.plan['references']=[a];self.invalid_plan()
 def test_briefs(self):out=self.r/'briefs';briefs(self.pp,out);self.assertEqual(len(list(out.glob('*.md'))),2);self.assertRaises(ValueError,briefs,self.pp,out)
 def review(self):
  image=self.r/'frame.png';Image.new('RGB',(50,50)).save(image)
  # Real synthetic media as schema fixture; view/approval declarations remain simulated.
  if not self.synthetic_video.is_file():self.skipTest('FFmpeg is required for the synthetic video fixture')
  video=self.r/'synthetic-fixture.mp4';video.write_bytes(self.synthetic_video.read_bytes())
  artifacts=[{'id':'im','path':image.name,'sha256':sha(image),'kind':'image','viewed':True},{'id':'vid','path':video.name,'sha256':sha(video),'kind':'video','viewed':True,'audio_listened':False}]
  r={'plan_sha256':sha(self.pp),'child_id':self.plan['child_id'],'reviewer':'synthetic-unit-fixture','review_type':'agent_declared','artifacts':artifacts,'issues':[],
  'gates':{k:{'status':'not_applicable' if k in ('audio_sync','loop_seam') else 'pass','observation':'Schema fixture, not artistic evaluation.','evidence_ids':['im'] if k in VISUAL else ['vid']} for k in GATES}}
  return r
 def save_review(self,r,name='review.json'):p=self.r/name;p.write_text(json.dumps(r));return p
 def test_valid_declared_review(self):r=self.review();self.assertTrue(validate_review(self.pp,self.save_review(r))[2]['all_required_gates_pass'])
 def test_review_stale_plan(self):r=self.review();self.plan['visual_goal']='Changed';self.save_plan();self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_review_missing_gate(self):r=self.review();del r['gates']['opening'];self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_score_not_gate(self):r=self.review();r['gates']={'score':10};self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_no_view_declaration(self):r=self.review();r['artifacts'][0]['viewed']=False;self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_still_cannot_prove_motion(self):r=self.review();r['gates']['motion_playback']['evidence_ids']=['im'];self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_real_audio_gate_required(self):self.plan['audio_mode']='speech';self.save_plan();r=self.review();self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_loop_required(self):self.plan['loop']=True;self.save_plan();r=self.review();self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_gate_cannot_hide_as_optional(self):r=self.review();r['gates']['opening']['status']='not_applicable';self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_missing_matching_file(self):r=self.review();(self.r/'frame.png').unlink();self.assertRaises((ValueError,FileNotFoundError),validate_review,self.pp,self.save_review(r))
 def test_changed_file(self):r=self.review();Image.new('RGB',(50,50),'red').save(self.r/'frame.png');self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_failed_gate_needs_action(self):r=self.review();r['gates']['opening']['status']='fail';self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def failed_review(self):
  r=self.review();r['gates']['composition']['status']='fail';r['issues']=[{'gate':'composition','shot_id':'s01','start_frame':1,'end_frame':3,'fix':'Move the crossing line behind the node.','severity':'blocking'}];return r
 def test_failed_gate_requests_fix(self):r=self.failed_review();p=self.save_review(r);self.assertEqual(register_review(self.pp,p)['action'],'fix_top_issues_and_review_changed_shots')
 def editorial_context(self):
  context=json.loads((ROOT/'visual/EDITORIAL_REASONING_TEMPLATE.json').read_text())['issue_context']
  context.update(beat_id='fixture-beat',problem='Synthetic crossing-line issue.',
                 expected_result='Move the line without changing the existing gates or timeline.')
  return context
 def test_editorial_issue_context_preserves_legacy_blocker(self):
  r=self.failed_review();before=validate_review(self.pp,self.save_review(r,'before.json'))[2]
  r['issues'][0]['editorial_context']=self.editorial_context()
  after=validate_review(self.pp,self.save_review(r,'after.json'))[2]
  for field in ('all_required_gates_pass','failed_gates','pending_gates','evidence_scope'):
   self.assertEqual(before[field],after[field])
  self.assertEqual(after['top_fixes'][0]['fix'],before['top_fixes'][0]['fix'])
  self.assertFalse(after['all_required_gates_pass'])
 def test_editorial_context_cannot_resolve_open_issue_or_pending_gate(self):
  r=self.failed_review();r['gates']['composition']['status']='pass'
  r['issues'][0]['editorial_context']={**self.editorial_context(),'resolved':True}
  result=validate_review(self.pp,self.save_review(r))[2]
  self.assertFalse(result['all_required_gates_pass']);self.assertEqual(len(result['top_fixes']),1)
  r['issues'][0]['resolved']=True;r['gates']['motion_playback']['status']='pending'
  result=validate_review(self.pp,self.save_review(r,'pending.json'))[2]
  self.assertFalse(result['all_required_gates_pass']);self.assertIn('motion_playback',result['pending_gates'])
 def test_editorial_context_cannot_bypass_stale_review(self):
  r=self.failed_review();r['issues'][0]['editorial_context']=self.editorial_context()
  self.plan['visual_goal']='Changed after review';self.save_plan()
  self.assertRaises(ValueError,validate_review,self.pp,self.save_review(r))
 def test_no_infinite_loop(self):
  for i in range(3):
   r=self.failed_review();r['reviewer']=f'fixture-{i}';result=register_review(self.pp,self.save_review(r,f'r{i}.json'))
  self.assertEqual(result['action'],'stop_not_approved');r=self.failed_review();r['reviewer']='fixture-4';self.assertRaises(ValueError,register_review,self.pp,self.save_review(r,'r4.json'))
 def test_revision_does_not_reset(self):
  r=self.failed_review();register_review(self.pp,self.save_review(r));self.plan['visual_goal']='New wording';self.save_plan();r=self.failed_review();self.assertEqual(register_review(self.pp,self.save_review(r,'r2.json'))['round'],2)
 def test_duplicate_review_rejected(self):r=self.failed_review();p=self.save_review(r);register_review(self.pp,p);self.assertRaises(ValueError,register_review,self.pp,p)
 def test_new_style_needs_user(self):self.plan['new_style']=True;self.save_plan();r=self.review();self.assertEqual(register_review(self.pp,self.save_review(r))['action'],'ready_for_user_approval')
 def test_first_good_pass_stops(self):r=self.review();x=register_review(self.pp,self.save_review(r));self.assertEqual(x['action'],'ready_for_final_checks');self.assertFalse(x['approved_by_silence'])
 def test_hidden_open_issue_blocks(self):r=self.failed_review();r['gates']['composition']['status']='pass';self.assertFalse(validate_review(self.pp,self.save_review(r))[2]['all_required_gates_pass'])
 def test_uniform_sheet_whole_film(self):x=sample_grid(120,.5,30);self.assertEqual(len(x),30);self.assertAlmostEqual(x[-1],119.999);self.assertEqual(x[0],0)
 def test_regular_sampling_when_fits(self):x=sample_grid(3,.5,30);self.assertEqual(x[:4],[0,.5,1,1.5]);self.assertAlmostEqual(x[-1],2.999)
 def test_invalid_sheet_duration(self):self.assertRaises(ValueError,sample_grid,float('nan'))
 def test_subframes_stay_inside_cut(self):self.assertTrue(all(1<=x<2 for x in sample_times(24,24,72,[24,48],4)))
 def test_no_subframes_timing_change(self):self.assertEqual(sample_times(3,24,72,[],1),[.125])
 def test_premultiplied_alpha_no_black_fringe(self):
  a=Image.new('RGBA',(1,1),(255,0,0,255));b=Image.new('RGBA',(1,1),(0,0,0,0));p=blend([a,b]).getpixel((0,0));self.assertEqual(p[:3],(255,0,0));self.assertEqual(p[3],128)
 def test_sample_negative_rejected(self):self.assertRaises(ValueError,sample_times,-1,24,72,[])
 def test_spec_invalid_source_hash(self):
  spec=json.loads((ROOT/'studio/examples/decision-flow.json').read_text());spec['entry']={'path':str(ROOT/'studio/examples/decision-flow.html'),'sha256':'bad'};p=self.r/'spec.json';p.write_text(json.dumps(spec));self.assertRaises(ValueError,inspect,p)
 def test_spec_changed_geometry_changes_bundle(self):
  spec=json.loads((ROOT/'studio/examples/decision-flow.json').read_text());spec['entry']['path']=str(ROOT/'studio/examples/decision-flow.html');p=self.r/'spec.json';p.write_text(json.dumps(spec));a=inspect(p)[3]['bundle_sha256'];spec['width']=360;spec['height']=640;p.write_text(json.dumps(spec));self.assertNotEqual(inspect(p)[3]['bundle_sha256'],a)
 def test_beats_no_guessed_downbeat(self):d=grid_document(120,[0.,.5,1.],[0.],2,{},'fixture');self.assertEqual(d['downbeats'],[]);self.assertEqual(d['downbeat_status'],'unknown_not_inferred')
 def test_meter_without_phase_rejected(self):self.assertRaises(ValueError,grid_document,120,[0.,.5],[0.],2,{},'fixture',None,4)
 def test_phase_confirmed(self):d=grid_document(120,[0.,.5,1.,1.5],[0.],2,{},'fixture',1,2);self.assertEqual(d['downbeats'],[.5,1.5])
 def test_silent_beats_valid(self):self.assertEqual(grid_document(0,[],[],2,{},'silence')['estimated_bpm'],0)
 def sfx(self,cues):p=self.r/'cues.json';p.write_text(json.dumps({'duration_s':1,'cues':cues}));return p
 def test_empty_sfx(self):s=synth(self.sfx([]),self.r/'out.wav');self.assertEqual(s['samples'],48000);self.assertEqual(s['peak_before_headroom'],0)
 def test_invalid_cue(self):self.assertRaises(ValueError,synth,self.sfx([{'id':'a','type':'click','t':2}]),self.r/'out.wav')
 def test_sfx_deterministic(self):p=self.sfx([{'id':'a','type':'whoosh','t':.2}]);a=synth(p,self.r/'a.wav');b=synth(p,self.r/'b.wav');self.assertEqual(a['sha256'],b['sha256'])
 def test_sfx_protect_output(self):p=self.sfx([]);synth(p,self.r/'a.wav');self.assertRaises(ValueError,synth,p,self.r/'a.wav')
 def test_sfx_headroom(self):p=self.sfx([{'id':str(i),'type':'click','t':.2,'gain':1} for i in range(10)]);a=synth(p,self.r/'a.wav');self.assertLess(a['headroom_scale'],1)
 def test_local_routes(self):
  for host in ('claude','codex'):
   for name in ('studio-render','studio-sheets','studio-beats','studio-sfx','studio-plan-check'):self.assertEqual(route(ROOT,host,name)['llm_calls'],0)
 def test_motion_dependencies_include_pillow(self):self.assertIn('Pillow',str(dependency_plan(ROOT,'motion')['commands']))
 def test_audio_dependencies_opt_in(self):self.assertIn('librosa',str(dependency_plan(ROOT,'studio-audio')['commands']));self.assertNotIn('librosa',str(dependency_plan(ROOT,'speech')['commands']))
if __name__=='__main__':unittest.main()
