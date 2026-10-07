#!/usr/bin/env python3
"""Real local preparation -> specs -> JavaScript frames -> composition on SYNTHETIC media.
The scene rectangles and semantic decisions are fixtures. No perception/LLM/generator test.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from visual_direction import prepare, inspect, export, sha, ref
from render_motion import render
from composite_motion import build_command, probe

def run(cmd):return subprocess.run(cmd,check=True,capture_output=True)
def audiohash(p):return run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']).stdout

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workdir',type=Path,required=True);a=ap.parse_args()
    r=a.workdir.resolve();r.mkdir(parents=True,exist_ok=False);checks={}
    def check(name,ok):
        checks[name]=bool(ok)
        if not ok:raise AssertionError(name)
    master=r/'clean.mp4'
    run(['ffmpeg','-v','error','-n','-f','lavfi','-i','color=c=0x343D48:s=640x360:r=24:d=6',
         '-f','lavfi','-i','sine=frequency=330:sample_rate=48000:duration=6',
         '-vf','drawbox=x=30:y=50:w=190:h=220:color=0x526F8A:t=fill',
         '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(master)])
    original=sha(master)
    edl=r/'edl.json';edl.write_text(json.dumps({'segments':[{'source':str(master),'in':0,'out':3},{'source':str(master),'in':3,'out':6}]}))
    tr=r/'retimed.json';tr.write_text(json.dumps({'timebase':'clean_master_seconds','base_sha256':sha(master),'words':[
        {'word':'Processo','start':.2,'end':.6},{'word':'visual.','start':.65,'end':2.5},
        {'word':'Três','start':3.3,'end':3.7},{'word':'etapas.','start':3.75,'end':5.35},
        {'word':'Preservar.','start':5.6,'end':5.95}]}))
    context=r/'visual/context.json'
    packet=prepare(master,edl,tr,r/'visual','fixture','one',True)
    check('two_edl_shots_prepared',len(packet['shots'])==2)
    check('six_actual_frames_extracted',len(packet['frames'])==6)
    check('three_timestamped_units',len(packet['utterances'])==3)
    extra=prepare(master,edl,tr,r/'visual-extra-cut','fixture','one',True,extra_cuts=[36])
    check('observed_extra_cut_splits_map_without_editing_speech',len(extra['shots'])==3)
    try:
        prepare(master,edl,tr,r/'visual-budget','fixture','one',True,max_frames=2)
        budget_blocked=False
    except ValueError:
        budget_blocked=True
    check('frame_budget_refuses_silent_scene_omission',budget_blocked)
    check('no_perception_claim',packet['semantic_analysis_performed'] is False)
    initial=json.loads((r/'visual/scene-map.json').read_text())
    check('initial_scene_unreviewed',all(s['reviewed'] is False for s in initial['shots']))
    scene=copy.deepcopy(initial);scene['global_forbidden']=[{'role':'captions','box':[.02,.87,.96,.1]}]
    for s in scene['shots']:
        s.update(reviewed=True,inspected_frames=s['sample_frames'],
                 observations={'source':'SYNTHETIC FIXTURE, manually specified rectangles; no perception test', 'background':'flat test canvas'},
                 forbidden=[{'role':'synthetic protected rectangle, NOT detected person','box':[.02,.08,.34,.7]}])
    sp=r/'scene-reviewed.json';sp.write_text(json.dumps(scene))
    p={'version':'1.0','client_id':'fixture','child_id':'one','timebase':'clean_master_frames','context_sha256':sha(context),'caption_pipeline':'after_visuals',
       'style':{'direction':'Synthetic mechanical layout test only','colors':{'foreground':'#FFFFFF','background':'#152035','accent':'#A5C6DA'}},
       'beats':[{'id':'title','utterance_ids':['u-0001'],'shot_id':'shot-0001','start_frame':8,'end_frame':56,
                 'meaning':'demonstrate local visual sequence','purpose':'test title placement','mode':'overlay','engine':'js_svg',
                 'component':'keyphrase','box':[.44,.1,.52,.62],'evidence':'concept','props':{'lines':['TESTE VISUAL']}},
                {'id':'steps','utterance_ids':['u-0002'],'shot_id':'shot-0002','start_frame':80,'end_frame':128,
                 'meaning':'three stages','purpose':'test frame-driven sequence','mode':'overlay','engine':'js_svg',
                 'component':'steps','box':[.44,.1,.52,.62],'evidence':'concept','props':{'lines':['ETAPAS'],'steps':['Ler','Dirigir','Revisar']}},
                {'id':'keep','utterance_ids':['u-0003'],'start_frame':134,'end_frame':144,'meaning':'leave frame unchanged','purpose':'preserve source','mode':'keep','engine':'none'}]}
    pp=r/'plan.json';pp.write_text(json.dumps(p))
    review=inspect(context,sp,pp)
    check('storyboard_structurally_valid',review['structural_ok'])
    check('no_false_render_approval',review['render_approval'] is False)
    exp=export(context,sp,pp,r/'production')
    check('two_supported_specs_exported',len(exp['items'])==2 and all('spec' in i for i in exp['items']))
    check('brief_is_not_a_render',exp['rendered'] is False)
    layers=[]
    from PIL import Image
    for item in exp['items']:
        spec=r/'production'/item['spec'];frames=r/'frames'/item['id']
        f=render(spec,frames)
        check(item['id']+'_complete_pngs',f['complete'] and len(f['files'])==48)
        with Image.open(frames/'000024.png') as im:
            check(item['id']+'_protected_area_transparent',im.getpixel((80,130))[3]==0)
            check(item['id']+'_caption_area_transparent',im.getpixel((300,330))[3]==0)
            check(item['id']+'_visible_in_right_region',im.getpixel((350,160))[3]>0)
        layers.append({'child_id':'one','start_frame':item['start_frame'],'frames':ref(frames/'frames.json',r),
                       'speech_cue':'Synthetic timed fixture','reason':'Mechanical pipeline check, not artistic approval'})
    mp={'timebase':'clean_master_frames','child_id':'one','width':640,'height':360,'fps':24,
        'base':ref(master,r),'edl':ref(edl,r),'layers':layers}
    mpp=r/'motion-plan.json';mpp.write_text(json.dumps(mp));out=r/'composited.mp4'
    cmd,meta=build_command(mpp,out);run(cmd)
    v=next(s for s in probe(out)['streams'] if s['codec_type']=='video')
    check('duration_frames_unchanged',int(v['nb_frames'])==144)
    check('audio_packets_preserved',audiohash(master)==audiohash(out))
    check('master_immutable',sha(master)==original)
    changed=copy.deepcopy(p);changed['beats'][0]['box']=[.1,.1,.5,.6];pp.write_text(json.dumps(changed))
    check('collision_is_blocked',not inspect(context,sp,pp)['structural_ok'])
    pp.write_text(json.dumps(p));changed=copy.deepcopy(p);changed['client_id']='other';pp.write_text(json.dumps(changed))
    check('client_mix_blocked',not inspect(context,sp,pp)['structural_ok'])
    pp.write_text(json.dumps(p));edl.write_text(edl.read_text()+'\n')
    check('changed_edit_invalidates_plan',not inspect(context,sp,pp)['structural_ok'])
    result={'test':'synthetic visual integration','checks':checks,'passed':all(checks.values()),
            'scope':'Real extraction/JS rendering/composition with hand-authored synthetic scene and transcript. No semantic perception, ASR, external generation, segmentation, tracking, client footage or artistic evaluation.'}
    (r/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
