import copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from composite_motion import build_command
from render_motion import sha

class MotionPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
        self.base=self.r/'base.mp4';self.base.write_bytes(b'probe mocked in unit tests')
        self.edl=self.r/'edl.json';self.edl.write_text('{}')
        files=[]
        for i in range(4):
            p=self.r/f'{i:06d}.png';p.write_bytes(b'png fixture not rendered in unit tests'+str(i).encode());files.append({'frame':i,'file':p.name,'sha256':sha(p)})
        self.m={'complete':True,'child_id':'one','width':640,'height':360,'fps':30,'duration_frames':4,'files':files}
        self.mp=self.r/'frames.json'
        self.plan={'timebase':'clean_master_frames','child_id':'one','width':640,'height':360,'fps':30,'base':{'path':'base.mp4','sha256':sha(self.base)},'edl':{'path':'edl.json','sha256':sha(self.edl)},'layers':[{'child_id':'one','start_frame':3,'speech_cue':'spoken idea','reason':'illustration','frames':{}}]}
        self.pp=self.r/'plan.json'
        self.meta={'streams':[{'codec_type':'video','width':640,'height':360,'avg_frame_rate':'30/1','r_frame_rate':'30/1','nb_frames':'60'}],'format':{'duration':'2'}}
    def tearDown(self):self.tmp.cleanup()
    def run_plan(self):
        self.mp.write_text(json.dumps(self.m));self.plan['layers'][0]['frames']={'path':'frames.json','sha256':sha(self.mp)}
        self.pp.write_text(json.dumps(self.plan))
        with patch('composite_motion.probe',return_value=self.meta):return build_command(self.pp,self.r/'out.mp4')
    def test_valid_audio_preserved(self):
        cmd,r=self.run_plan();self.assertIn('0:a?',cmd);self.assertIn('copy',cmd);self.assertNotIn('-shortest',cmd);self.assertEqual(r['layers'],1)
    def test_wrong_timebase(self):
        self.plan['timebase']='source_seconds'
        with self.assertRaises(ValueError):self.run_plan()
    def test_stale_master(self):
        self.base.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.run_plan()
    def test_stale_edl(self):
        self.edl.write_text('{"changed":true}')
        with self.assertRaises(ValueError):self.run_plan()
    def test_cross_child_layer(self):
        self.plan['layers'][0]['child_id']='two'
        with self.assertRaises(ValueError):self.run_plan()
    def test_cross_child_frames(self):
        self.m['child_id']='two'
        with self.assertRaises(ValueError):self.run_plan()
    def test_keyframe_preview_not_complete(self):
        self.m['complete']=False
        with self.assertRaises(ValueError):self.run_plan()
    def test_modified_png(self):
        (self.r/'000001.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.run_plan()
    def test_missing_png(self):
        (self.r/'000003.png').unlink()
        with self.assertRaises(ValueError):self.run_plan()
    def test_frame_path_traversal(self):
        self.m['files'][1]['file']='../private.png'
        with self.assertRaises(ValueError):self.run_plan()
    def test_duration_overflow(self):
        self.plan['layers'][0]['start_frame']=58
        with self.assertRaises(ValueError):self.run_plan()
    def test_fractional_start(self):
        self.plan['layers'][0]['start_frame']=1.5
        with self.assertRaises(ValueError):self.run_plan()
    def test_no_overwrite(self):
        (self.r/'out.mp4').write_bytes(b'existing')
        with self.assertRaises(ValueError):self.run_plan()
    def test_geometry_mismatch(self):
        self.m['width']=1080
        with self.assertRaises(ValueError):self.run_plan()
    def test_fps_mismatch(self):
        self.m['fps']=24
        with self.assertRaises(ValueError):self.run_plan()
    def test_missing_semantic_anchor(self):
        self.plan['layers'][0]['speech_cue']=''
        with self.assertRaises(ValueError):self.run_plan()
if __name__=='__main__':unittest.main()
