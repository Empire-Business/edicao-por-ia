#!/usr/bin/env python3
"""Real local studio integration using synthetic media. No provider calls/art approval."""
import argparse, copy, json, subprocess, sys, wave
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from factory_common import sha
from studio_render import inspect, render, determinism
from studio_review import sheets, validate_plan, validate_review, register_review, briefs, GATES, VISUAL
from studio_audio import synth, analyze
from composite_motion import build_command, probe

def run(cmd):return subprocess.run([str(x) for x in cmd],capture_output=True,check=True)
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8');return p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--outdir',type=Path,required=True);a=ap.parse_args();r=a.outdir.resolve();r.mkdir(parents=True,exist_ok=False)
 checks={}
 def check(name,ok):
  checks[name]=bool(ok)
  if not ok:raise AssertionError(name)
 def rejected(name,fn):
  try:fn()
  except Exception:check(name,True)
  else:check(name,False)
 source=ROOT/'studio/examples/decision-flow.json';s=json.loads(source.read_text());s['entry']['path']=str(ROOT/'studio/examples/decision-flow.html');s['child_id']='studio-test'
 spec=save(r/'spec.json',s);approval=inspect(spec)[3]['bundle_sha256']
 # The test author inspected the bundled source; this approval is not permission for arbitrary code.
 d=determinism(spec,approval);save(r/'determinism.json',d)
 check('rgba_determinism_repeat_reverse_fresh',d['ok'] and len(d['checks'])==12)
 rejected('wrong_bundle_approval_rejected',lambda:render(spec,r/'wrong',approval='incorrect',selected=[0]))
 rejected('frame_sample_budget_enforced',lambda:render(spec,r/'overbudget',approval,frame_budget=10))
 full=render(spec,r/'frames',approval)
 check('complete_144_frames',full['complete'] and len(full['files'])==144)
 check('no_network_in_render',full['network_access'] is False)
 check('all_png_integrities',all(sha(r/'frames'/f['file'])==f['sha256'] for f in full['files']))
 sparse=render(spec,r/'sparse',approval,selected=[0,72,108])
 check('sparse_not_complete',sparse['complete'] is False)
 rejected('no_overwrite_frames',lambda:render(spec,r/'frames',approval))
 blur=render(spec,r/'blur',approval,selected=[71,72,73],subframes=4)
 check('subframe_render_count',blur['sample_count']==12)
 for name,w,h in [('portrait',360,640),('square',360,360)]:
  variant=copy.deepcopy(s);variant.update(width=w,height=h)
  sp=save(r/(name+'.json'),variant);apv=inspect(sp)[3]['bundle_sha256'];render(sp,r/(name+'-frames'),apv,selected=[0,72,108])
  check(name+'_reflow_dimensions',Image.open(r/(name+'-frames')/'000108.png').size==(w,h))
  check(name+'_separate_bundle',apv!=approval)
 # Decode/encode actual PNGs and composite them on a locked audiovisual master.
 standalone=r/'motion.mp4'
 run(['ffmpeg','-v','error','-n','-framerate','24','-i',r/'frames/%06d.png','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',standalone])
 base=r/'clean.mp4';run(['ffmpeg','-v','error','-n','-f','lavfi','-i','testsrc2=size=640x360:rate=24:duration=8','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=8','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',base])
 before=sha(base);edl=save(r/'edl.json',{'synthetic_test':True,'duration_frames':192});transcript=save(r/'retimed.json',{'synthetic_test':True,'text':'Synthetic timeline cue, not transcribed speech.'})
 pp=save(r/'composition.json',{'timebase':'clean_master_frames','child_id':'studio-test','width':640,'height':360,'fps':24,'base':{'path':base.name,'sha256':sha(base)},'edl':{'path':edl.name,'sha256':sha(edl)},'layers':[{'child_id':'studio-test','start_frame':24,'speech_cue':'Synthetic cue; not speech recognition.','reason':'Six-second conceptual animation over test media','frames':{'path':'frames/frames.json','sha256':sha(r/'frames/frames.json')}}]})
 cmd,report=build_command(pp,r/'composite.mp4');run(cmd);master=r/'composite.mp4';p=probe(master);v=next(x for x in p['streams'] if x['codec_type']=='video')
 check('compositor_accepts_seek_manifest',report['layers']==1)
 check('preserves_192_frames',int(v['nb_frames'])==192)
 check('preserves_duration',abs(float(v['duration'])-8)<1e-5)
 check('preserves_fps',v['avg_frame_rate']=='24/1')
 def audiohash(path):return run(['ffmpeg','-v','error','-i',path,'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']).stdout
 check('preserves_audio_bitstream',audiohash(base)==audiohash(master))
 check('source_unchanged',sha(base)==before)
 bad=json.loads(pp.read_text());bad['layers'][0]['frames']={'path':'sparse/frames.json','sha256':sha(r/'sparse/frames.json')};bp=save(r/'bad-composition.json',bad)
 rejected('compositor_rejects_sparse_frames',lambda:build_command(bp,r/'bad.mp4'))
 evidence=sheets(master,r/'evidence',max_samples=8,columns=3,rows=2,strip_at=3.2)
 check('paginated_evidence',len(evidence['pages'])>1)
 check('samples_cover_end',max(x['t'] for x in evidence['frames'])>=7.9)
 check('phone_360_pixels',Image.open(r/'evidence'/evidence['frames'][0]['path']).width==360)
 check('evidence_not_auto_approved',evidence['actual_visual_review']=='PENDING')
 check('sampling_thinning_disclosed',evidence['uniform_sampling_thinned'])
 # Local raster asset route: no web server or external file access needed.
 im=r/'asset.png';Image.new('RGB',(64,64),(32,128,64)).save(im)
 html=r/'asset.html';html.write_text('''<canvas width="64" height="64"></canvas><img id="im" src="/assets/a" crossorigin="anonymous" hidden><script>window.seek=(t)=>document.querySelector('canvas').getContext('2d').drawImage(document.getElementById('im'),0,0);</script>''')
 als=copy.deepcopy(s);als.update(width=64,height=64,duration_frames=2,entry={'path':html.name,'sha256':sha(html)},assets=[{'id':'a','path':im.name,'sha256':sha(im),'mime':'image/png'}])
 asp=save(r/'asset-spec.json',als);afr=render(asp,r/'asset-frames',inspect(asp)[3]['bundle_sha256'])
 check('approved_raster_asset_loaded',Image.open(r/'asset-frames/000000.png').getpixel((30,30))[:3]==(32,128,64))
 # Deliberately flawed but harmless scripts must not receive determinism approval.
 state=r/'state.html';state.write_text('''<canvas width="64" height="64"></canvas><script>let n=0;window.seek=(t)=>{const g=document.querySelector('canvas').getContext('2d');g.fillStyle='rgb('+ (++n*10)+',0,0)';g.fillRect(0,0,64,64)};</script>''')
 st=copy.deepcopy(als);st['assets']=[];st['entry']={'path':state.name,'sha256':sha(state)};stp=save(r/'state-spec.json',st)
 check('stateful_renderer_detected',not determinism(stp,inspect(stp)[3]['bundle_sha256'])['ok'])
 random=r/'random.html';random.write_text('<canvas width="64" height="64"></canvas><script>window.seek=(t)=>Math.random();</script>')
 st['entry']={'path':random.name,'sha256':sha(random)};rp=save(r/'random-spec.json',st)
 rejected('unseeded_random_rejected',lambda:render(rp,r/'random-frames',inspect(rp)[3]['bundle_sha256']))
 # Real synthesized audio and local beat analysis. Not music composition/listening.
 cues=save(r/'cues.json',{'duration_s':8,'cues':[{'id':f'c{i}','type':'click','t':.25+i*.5,'gain':.6} for i in range(16)]})
 sx=synth(cues,r/'clicks.wav');sy=synth(cues,r/'clicks-again.wav')
 check('sfx_repeatable',sx['sha256']==sy['sha256'])
 beats=analyze(r/'clicks.wav',r/'beats.json')
 check('measured_click_tempo_near_120',beats['estimated_bpm'] and abs(beats['estimated_bpm']-120)<5)
 check('downbeat_not_guessed',beats['downbeats']==[])
 check('audio_master_offset_pending',beats['sync_to_master'].startswith('UNMAPPED'))
 silence=save(r/'silent-cues.json',{'duration_s':2,'cues':[]});synth(silence,r/'silent.wav');b0=analyze(r/'silent.wav',r/'silent-beats.json')
 check('silent_audio_no_beats',b0['estimated_bpm']==0 and b0['beats']==[])
 # Simulate review declarations ONLY to test state rules; not an art/vision evaluation.
 plan=json.loads((ROOT/'studio/templates/PLAN_TEMPLATE.json').read_text());plan['child_id']='studio-test';plan['new_style']=True
 planpath=save(r/'studio-plan.json',plan);briefs(planpath,r/'briefs')
 check('per_shot_briefs_created',len(list((r/'briefs').glob('*.md')))==2)
 review={'child_id':'studio-test','plan_sha256':sha(planpath),'review_type':'agent_declared','reviewer':'SYNTHETIC INTEGRATION DECLARATIONS — NOT REAL VISION','artifacts':[{'id':'im','path':'frames/000108.png','sha256':sha(r/'frames/000108.png'),'kind':'image','viewed':True},{'id':'v','path':standalone.name,'sha256':sha(standalone),'kind':'video','viewed':True}],
 'gates':{k:{'status':'not_applicable' if k in ('audio_sync','loop_seam') else 'pass','observation':'Simulated gate for mechanics only; no artistic judgment.','evidence_ids':['im'] if k in VISUAL else ['v']} for k in GATES},'issues':[]}
 rv=save(r/'simulated-review.json',review);receipt=register_review(planpath,rv)
 check('new_style_requires_user_approval',receipt['action']=='ready_for_user_approval')
 check('silence_never_approval',receipt['approved_by_silence'] is False)
 rejected('duplicate_review_not_new_round',lambda:register_review(planpath,rv))
 plan['visual_goal']='Changed meaning';save(planpath,plan)
 rejected('stale_review_rejected',lambda:validate_review(planpath,rv))
 results={'checks':checks,'passed':sum(checks.values()),'total':len(checks),'ok':all(checks.values()),'determinism_subchecks':d['checks'],'browser':d['browser'],'test_type':'Executed local synthetic media integration',
 'limitations':['No Codex/Claude session, paid call, ASR, scene understanding, real client video, Remotion or HyperFrames execution.','Review records explicitly simulate declarations; not a real independent visual, listening or artistic approval.','Sampled browser repeatability is not a cross-device or all-frame guarantee.']}
 save(r/'results.json',results);print(json.dumps(results,indent=2))
if __name__=='__main__':main()
