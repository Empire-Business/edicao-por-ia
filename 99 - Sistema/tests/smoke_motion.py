#!/usr/bin/env python3
"""Real local JS/browser/FFmpeg integration on synthetic media, not an LLM test.
Usage: python3 tests/smoke_motion.py --workdir /path/to/NEW-directory
"""
from __future__ import annotations
import argparse,copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from render_motion import render,sha
from composite_motion import build_command,probe

def run(cmd):return subprocess.run(cmd,capture_output=True,check=True)
def rgb(path,t):return run(['ffmpeg','-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
def audiohash(p):return run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']).stdout.decode().strip()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workdir',type=Path,required=True);a=ap.parse_args()
    r=a.workdir.resolve();r.mkdir(parents=True,exist_ok=False)
    checks={}
    def check(name,result):
        checks[name]=bool(result)
        if not result:raise AssertionError(name)
    master=r/'clean.mp4'
    run(['ffmpeg','-v','error','-n','-f','lavfi','-i','color=c=0x384255:s=640x360:r=24:d=4','-f','lavfi','-i','sine=frequency=330:sample_rate=48000:duration=4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(master)])
    original_hash=sha(master);edl=r/'edl.json';edl.write_text(json.dumps({'version':'1.0','segments':[{'source':str(master),'in':0,'out':4}]}))
    s=json.loads((ROOT/'motion/examples/keyphrase.json').read_text());s.update(width=640,height=360,fps=24,duration_frames=24,box={'x':.08,'y':.47,'w':.84,'h':.36})
    spec=r/'spec.json';spec.write_text(json.dumps(s));manifest=render(spec,r/'frames')
    from PIL import Image,ImageDraw
    im=Image.open(r/'frames/000012.png');check('transparent_layer_outside_card',im.mode=='RGBA' and im.getpixel((0,0))[3]==0)
    check('complete_frame_count',len(manifest['files'])==24 and manifest['complete'])
    # Non-sequential re-render of an identical frame must be reproducible in this environment.
    preview=render(spec,r/'preview',selected=[12])
    check('deterministic_repeat_frame',sha(r/'preview/000012.png')==sha(r/'frames/000012.png'))
    proof=r/'proof.png';im=Image.new('RGB',(480,200),'#eee9da');d=ImageDraw.Draw(im);d.text((25,35),'SYNTHETIC DEMO / NOT CLIENT EVIDENCE',fill='#182033');im.save(proof)
    p=copy.deepcopy(s);p.update(id='proof-smoke',template='proof-frame',lines=[],label='Exemplo sintético',asset_path='proof.png',box={'x':.08,'y':.2,'w':.84,'h':.62})
    ps=r/'proof-spec.json';ps.write_text(json.dumps(p));pr=render(ps,r/'proof-frames')
    check('raster_asset_hash_tracked',pr['asset_sha256']==sha(proof))
    plan={'timebase':'clean_master_frames','child_id':'demo','base':{'path':'clean.mp4','sha256':sha(master)},'edl':{'path':'edl.json','sha256':sha(edl)},'width':640,'height':360,'fps':24,'layers':[
        {'child_id':'demo','start_frame':12,'speech_cue':'synthetic cue one','reason':'test keyphrase','frames':{'path':'frames/frames.json','sha256':sha(r/'frames/frames.json')}},
        {'child_id':'demo','start_frame':48,'speech_cue':'synthetic cue two','reason':'test proof-frame','frames':{'path':'proof-frames/frames.json','sha256':sha(r/'proof-frames/frames.json')}}]}
    pp=r/'plan.json';pp.write_text(json.dumps(plan));output=r/'composite.mp4';cmd,report=build_command(pp,output);run(cmd)
    md=probe(output);video=next(x for x in md['streams'] if x['codec_type']=='video')
    check('output_96_frames',int(video['nb_frames'])==96)
    check('output_duration_unchanged',abs(float(video['duration'])-4)<1e-5)
    check('output_fps_unchanged',video['avg_frame_rate']=='24/1')
    check('geometry_unchanged',(video['width'],video['height'])==(640,360))
    check('audio_stream_unchanged',audiohash(master)==audiohash(output))
    check('original_not_modified',sha(master)==original_hash)
    # Re-encoding may change RGB values slightly; <=2 mean levels is the baseline tolerance.
    def mean_diff(t):
        aa,bb=rgb(master,t),rgb(output,t)
        return sum(abs(x-y) for x,y in zip(aa,bb))/len(aa)
    check('no_layer_before_start',mean_diff(.25)<=2)
    check('keyphrase_visible_when_scheduled',mean_diff(1)>3)
    check('first_layer_not_held_past_end',mean_diff(1.75)<=2)
    check('proof_visible_when_scheduled',mean_diff(2.5)>3)
    check('second_layer_not_held_past_end',mean_diff(3.5)<=2)
    # Also verify the compositor tolerates a master with no audio stream.
    silent=r/'noaudio.mp4';run(['ffmpeg','-v','error','-n','-i',str(master),'-map','0:v:0','-c','copy',str(silent)])
    p2=copy.deepcopy(plan);p2['base']={'path':'noaudio.mp4','sha256':sha(silent)}
    pp2=r/'noaudio-plan.json';pp2.write_text(json.dumps(p2));cmd,_=build_command(pp2,r/'noaudio-composite.mp4');run(cmd)
    check('no_audio_master_supported',not any(x['codec_type']=='audio' for x in probe(r/'noaudio-composite.mp4')['streams']))
    # Aspect ratio adaptations are separate specs, not stretched exports.
    for name in ['steps','lower-third']:
        s3=json.loads((ROOT/f'motion/examples/{name}.json').read_text());s3.update(width=360,height=640,duration_frames=90)
        path=r/f'{name}.json';path.write_text(json.dumps(s3));render(path,r/f'{name}-preview',selected=[0,30,89])
        check(name+'_portrait_preview',Image.open(r/f'{name}-preview/000030.png').size==(360,640))
    run(['ffmpeg','-v','error','-n','-ss','1','-i',str(output),'-frames:v','1',str(r/'composite-check.png')])
    check('no_network_render',manifest['network_access'] is False)
    results={'test_type':'synthetic real local JS/browser/FFmpeg integration','checks':checks,'passed':sum(checks.values()),'total':len(checks),'browser':manifest['browser'],'ffmpeg':run(['ffmpeg','-version']).stdout.decode().splitlines()[0],
    'limitations':['No Claude API inference or actual customer video tested.','No Remotion installation/render tested.','Human playback/brand approval remains required; structural and sampled-frame checks are not that approval.']}
    (r/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
