import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from visual_direction import inspect, export, phrases, rectangle, intersects, shot_intervals, prepare, sha

class VisualDirectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.r=Path(self.tmp.name)
        self.cp=self.r/'context.json';self.sp=self.r/'scene.json';self.pp=self.r/'plan.json'
        for n in ('base.mp4','edl.json','tr.json','frame.png'):(self.r/n).write_text('synthetic fixture, not media')
        self.c={'client_id':'a','child_id':'one','timebase':'clean_master_frames','fps':24,'width':640,'height':360,'duration_frames':96,
                'base':self.ref('base.mp4'),'edl':self.ref('edl.json'),'transcript':self.ref('tr.json'),
                'frames':[dict(self.ref('frame.png'), frame=0,width=640,height=360)],
                'shots':[{'id':'s1','start_frame':0,'end_frame':96,'sample_frames':[0]}],
                'utterances':[{'id':'u1','text':'Teste.','start_frame':0,'end_frame':48}, {'id':'u2','text':'Preservar.','start_frame':48,'end_frame':96}]}
        self.cp.write_text(json.dumps(self.c))
        self.s={'client_id':'a','child_id':'one','coordinate_space':'normalized_clean_master','context_sha256':sha(self.cp),
                'global_forbidden':[{'role':'caption','box':[.05,.86,.9,.1]}],
                'shots':[{'id':'s1','start_frame':0,'end_frame':96,'sample_frames':[0],'inspected_frames':[0],'reviewed':True,
                          'observations':{'background':'fixture'},'forbidden':[{'role':'face','box':[.02,.1,.30,.7]}], 'candidates':[]}]}
        self.p={'version':'1.0','client_id':'a','child_id':'one','context_sha256':sha(self.cp),'timebase':'clean_master_frames','caption_pipeline':'after_visuals',
                'style':{'direction':'Editorial vector fixture','colors':{'foreground':'#FFFFFF','background':'#182033','accent':'#A5C6DA'}},
                'beats':[{'id':'b1','utterance_ids':['u1'],'shot_id':'s1','start_frame':0,'end_frame':48,'meaning':'example','purpose':'illustrate',
                          'mode':'overlay','engine':'js_svg','component':'keyphrase','box':[.50,.2,.4,.5],'evidence':'concept','props':{'lines':['Example']}},
                         {'id':'b2','utterance_ids':['u2'],'start_frame':48,'end_frame':96,'meaning':'pause','purpose':'face visible','mode':'keep','engine':'none'}]}
    def tearDown(self):self.tmp.cleanup()
    def ref(self,n):return {'path':n,'sha256':sha(self.r/n)}
    def files(self):self.sp.write_text(json.dumps(self.s));self.pp.write_text(json.dumps(self.p))
    def runcheck(self):self.files();return inspect(self.cp,self.sp,self.pp)
    def bad(self):self.assertFalse(self.runcheck()['structural_ok'])
    def test_valid(self):self.assertTrue(self.runcheck()['structural_ok'])
    def test_no_render_approval(self):self.assertIs(self.runcheck()['render_approval'],False)
    def test_collision_face(self):self.p['beats'][0]['box']=[.1,.2,.4,.5];self.bad()
    def test_collision_captions(self):self.p['beats'][0]['box']=[.5,.5,.4,.4];self.bad()
    def test_all_covered(self):self.p['beats'].pop();self.bad()
    def test_repeated_coverage(self):self.p['beats'][1]['utterance_ids']=['u1'];self.bad()
    def test_unknown_anchor(self):self.p['beats'][1]['utterance_ids']=['missing'];self.bad()
    def test_negative_frame(self):self.p['beats'][0]['start_frame']=-1;self.bad()
    def test_boolean_frame(self):self.p['beats'][0]['start_frame']=True;self.bad()
    def test_outside_master(self):self.p['beats'][1]['end_frame']=100;self.bad()
    def test_unsafe_identifier(self):self.p['beats'][0]['id']='../../oops';self.bad()
    def test_wrong_child(self):self.p['child_id']='two';self.bad()
    def test_wrong_client(self):self.s['client_id']='b';self.bad()
    def test_timebase(self):self.p['timebase']='source_seconds';self.bad()
    def test_coordinates(self):self.s['coordinate_space']='pixels';self.bad()
    def test_unknown_inspection(self):self.s['shots'][0]['inspected_frames']=[9];self.bad()
    def test_unreviewed_pending(self):
        self.s['shots'][0]['reviewed']=False;r=self.runcheck();self.assertTrue(r['structural_ok']);self.assertTrue(r['pending'])
    def test_unreviewed_cannot_export_spec(self):
        self.s['shots'][0]['reviewed']=False;self.files();r=export(self.cp,self.sp,self.pp,self.r/'out');self.assertEqual(r['items'][0]['status'],'brief_only')
    def test_nonexistent_shot(self):self.p['beats'][0]['shot_id']='missing';self.bad()
    def test_modified_shot(self):self.s['shots'][0]['end_frame']=97;self.bad()
    def test_changed_base(self):(self.r/'base.mp4').write_text('changed');self.bad()
    def test_changed_edl(self):(self.r/'edl.json').write_text('changed');self.bad()
    def test_changed_frame(self):(self.r/'frame.png').write_text('changed');self.bad()
    def test_changed_context(self):self.c['fps']=30;self.cp.write_text(json.dumps(self.c));self.bad()
    def test_simulation_needs_label(self):self.p['beats'][0]['evidence']='simulation';self.bad()
    def test_fake_proof(self):
        self.p['beats'][0].update(engine='image_generator',evidence='provided_media');self.bad()
    def test_real_case_needs_disclosure(self):self.p['beats'][0]['represents_real_case']=True;self.bad()
    def test_behind_subject_pending(self):
        self.p['beats'][0]['mode']='behind_subject';r=self.runcheck();self.assertTrue(r['structural_ok']);self.assertTrue(any('mask/track' in x for x in r['pending']))
    def test_behind_subject_no_simple_spec(self):
        self.p['beats'][0]['mode']='behind_subject';self.files();r=export(self.cp,self.sp,self.pp,self.r/'out');self.assertEqual(r['items'][0]['status'],'brief_only')
    def test_cutaway_caption_order(self):self.p['beats'][0]['mode']='cutaway';self.p['caption_pipeline']='burned';self.bad()
    def test_unknown_component_pending(self):
        self.p['beats'][0]['component']='custom-3d';self.assertTrue(self.runcheck()['pending'])
    def test_empty_props_fail(self):self.p['beats'][0]['props']={};self.bad()
    def test_nans_rejected(self):self.p['beats'][0]['box'][0]=float('nan');self.bad()
    def test_outside_box(self):self.p['beats'][0]['box'][0]=.9;self.bad()
    def test_missing_style(self):self.p['style']={};self.bad()
    def test_keep_no_engine(self):self.p['beats'][1]['engine']='image_generator';self.bad()
    def test_export_spec_and_brief(self):
        self.files();r=export(self.cp,self.sp,self.pp,self.r/'out');self.assertEqual(len(r['items']),1);self.assertFalse(r['rendered']);self.assertTrue((self.r/'out/b1-spec.json').is_file())
    def test_motion_envelope_reserved(self):
        self.files();export(self.cp,self.sp,self.pp,self.r/'out');s=json.loads((self.r/'out/b1-spec.json').read_text());self.assertLess(s['box']['h']+.012,self.p['beats'][0]['box'][3])
    def test_no_overwrite(self):
        self.files();out=self.r/'out';out.mkdir()
        with self.assertRaises(ValueError):export(self.cp,self.sp,self.pp,out)
    def test_generation_brief_not_image(self):
        self.p['beats'][0].update(engine='image_generator', generation_brief={k:'specified' for k in ['subject','relationship','composition','motion','avoid']})
        self.files();r=export(self.cp,self.sp,self.pp,self.r/'out');self.assertEqual(r['items'][0]['status'],'brief_only');self.assertFalse(r['rendered'])
    def test_prepare_requires_final_time_confirmation(self):
        with self.assertRaises(ValueError):prepare(self.r/'base.mp4',self.r/'edl.json',self.r/'tr.json',self.r/'out','a','one',False)
    def test_group_phrases(self):
        words=[{'word':'Não','start':0,'end':.2},{'word':'corte.','start':.25,'end':.5},{'word':'Aqui.','start':1,'end':1.3}]
        r=phrases(words,24,96,self.c['shots']);self.assertEqual([u['text'] for u in r],['Não corte.','Aqui.'])
    def test_transcript_overlap(self):
        with self.assertRaises(ValueError):phrases([{'word':'a','start':0,'end':1},{'word':'b','start':.2,'end':.5}],24,96,self.c['shots'])
    def test_no_transcript(self):
        with self.assertRaises(ValueError):phrases([],24,96,self.c['shots'])
    def test_edl_duration_mismatch(self):
        with self.assertRaises(ValueError):shot_intervals({'segments':[{'in':0,'out':99}]},24,96)
    def test_geometry(self):
        self.assertTrue(intersects([0,0,.5,.5],[.1,.1,.2,.2]));self.assertFalse(intersects([0,0,.1,.1],[.8,.8,.1,.1]))

if __name__=='__main__':unittest.main()
