#!/usr/bin/env python3
"""Generate paginated visual evidence and register bounded, artifact-bound reviews.
A receipt records the reviewer's declaration. It cannot prove a human/model actually looked.
No external calls. No inferred aesthetic scores. A missing review never becomes approval.
"""
from __future__ import annotations
import argparse, hashlib, io, json, math, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from factory_common import ROOT, read_json, sha, atomic_json, fingerprint
from studio_render import integer, check_file

GATES={'opening','visual_semantics','phone_readability','composition','motion_playback','brand_assets','audio_sync','loop_seam'}
VISUAL={'opening','visual_semantics','phone_readability','composition','brand_assets'}

def validate_plan(path):
    path=Path(path).resolve(strict=True);p=read_json(path)
    if p.get('schema_version')!=1:raise ValueError('Plan schema_version must be 1')
    for key in ('id','child_id','visual_goal'):
        if not isinstance(p.get(key),str) or not p[key].strip():raise ValueError(key+' required')
    n=integer(p['duration_frames'],'duration_frames',1,18000);fps=integer(p['fps'],'fps',1,120)
    if p.get('mode') not in ('speech_led','music_led'):raise ValueError('Choose speech_led or music_led')
    if p.get('audio_mode') not in ('none','speech','supplied_music','synth_sfx','mixed'):raise ValueError('Unknown audio_mode')
    profiles=read_json(ROOT/'config/studio-profiles.json')
    if p.get('profile') not in profiles:raise ValueError('Unknown studio profile')
    deps=p.get('dependencies',{})
    if p['mode']=='speech_led' and not {'master','edl','retimed_transcript'}.issubset(deps):raise ValueError('Speech-led plans need locked master, EDL and retimed transcript dependencies')
    for dep in deps.values():check_file(dep,path.parent)
    refs=p.get('references',[])
    for r in refs:
        check_file(r,path.parent)
        if not r.get('take') or not r.get('avoid'):raise ValueError('Reference needs what to take and what not to copy')
    proportions=p.get('proportions')
    legacy_formats=p.get('formats')
    if proportions is not None and legacy_formats is not None and proportions!=legacy_formats:
        raise ValueError('proportions and legacy formats fields disagree')
    proportions=proportions if proportions is not None else legacy_formats
    seen=set()
    if not isinstance(proportions,list) or not 1<=len(proportions)<=3:
        raise ValueError('Plan 1..3 requested proportions, not exports by default')
    for proportion in proportions:
        if proportion['id'] in seen:raise ValueError('Repeated proportion id')
        seen.add(proportion['id']);w=integer(proportion['width'],'width',64,3840);h=integer(proportion['height'],'height',64,3840)
        if w%2 or h%2:raise ValueError('Delivery geometry must be even')
        if not proportion.get('layout_note'):raise ValueError('Each proportion needs a reflow note, not a blind crop')
    assets=p.get('assets',[]);aids=set()
    for asset in assets:
        if asset['id'] in aids:raise ValueError('Duplicate asset id')
        aids.add(asset['id']);check_file(asset,path.parent)
        if asset.get('child_id',p['child_id'])!=p['child_id']:raise ValueError('Cross-child asset')
        if asset.get('origin') not in ('user_supplied','authorized_capture','original_code','labeled_simulation'):raise ValueError('Asset origin required')
        if asset.get('origin')=='labeled_simulation' and not asset.get('visible_label'):raise ValueError('Simulation needs a visible label')
        if asset.get('kind')=='product_ui' and asset['origin'] not in ('user_supplied','authorized_capture'):raise ValueError('Real product UI cannot be invented')
    shots=p.get('shots',[]);end=0;sids=set()
    if not shots or len(shots)>120:raise ValueError('Plan requires 1..120 shots')
    for s in shots:
        if s['id'] in sids:raise ValueError('Duplicate shot id')
        sids.add(s['id']);a=integer(s['start_frame'],'shot start',0,n-1);b=integer(s['end_frame'],'shot end',1,n)
        if a!=end or b<=a:raise ValueError('Shots must cover the timeline without overlap/gaps')
        end=b
        for k in ('purpose','visual_action','why_not_generic'):
            if not s.get(k):raise ValueError('Shot needs '+k)
        if s.get('treatment') not in ('keep','diagram','real_asset','kinetic_type','illustration','ui_morph','scene'):raise ValueError('Invalid treatment')
        if p['mode']=='speech_led' and not s.get('speech_cue'):raise ValueError('Speech-led shots must describe their retained spoken cue')
        if p['mode']=='speech_led' and s.get('moves_speech_to_beat',False):raise ValueError('Never shift/cut words to satisfy music beats')
        if any(x not in aids for x in s.get('asset_ids',[])):raise ValueError('Unknown shot asset')
        states=s.get('states',[]);previous=a-1
        if not states:raise ValueError('List the visible states, not only the vibe')
        for state in states:
            at=integer(state['frame'],'state frame',a,b-1)
            if at<=previous or not state.get('visible_result'):raise ValueError('State times must increase with a visible result')
            previous=at
    if end!=n:raise ValueError('Last shot does not cover timeline end')
    return p,{'ok':True,'plan_sha256':sha(path),'shots':len(shots),'duration_s':n/fps,'profile':p['profile'],
        'references_examined_by_tool':False,'semantics_evaluated_by_tool':False}

def sample_grid(duration,interval=.5,max_samples=120):
    if not math.isfinite(duration) or duration<=0 or not math.isfinite(interval) or interval<=0:raise ValueError('Positive duration/interval required')
    integer(max_samples,'max_samples',2,600)
    # Keep requested sampling when it fits; otherwise distribute the sample cap.
    last=max(0,duration-1/1000)
    count=math.floor(last/interval)+1
    if count+1>max_samples:
        return [round(last*i/(max_samples-1),6) for i in range(max_samples)]
    return sorted(set([round(i*interval,6) for i in range(count)]+[round(last,6)]))

def sheets(video,outdir,interval=.5,max_samples=120,columns=5,rows=3,phone_width=360,strip_at=None):
    video=Path(video).resolve(strict=True);outdir=Path(outdir).resolve()
    if outdir.exists() or video.is_relative_to(outdir):raise ValueError('Use a new evidence directory outside the source')
    integer(columns,'columns',1,8);integer(rows,'rows',1,8);integer(phone_width,'phone_width',120,720)
    meta=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,check=True).stdout)
    v=next(s for s in meta['streams'] if s['codec_type']=='video');duration=float(v.get('duration') or meta['format']['duration'])
    from fractions import Fraction
    fps=float(Fraction(v['avg_frame_rate']));times=sample_grid(duration,interval,max_samples)
    if strip_at is not None:
        if not math.isfinite(strip_at) or not 0<=strip_at<duration:raise ValueError('Strip timestamp outside video')
        times=sorted(set(times+[max(0,min(duration-1/fps,strip_at+(i-6)/fps)) for i in range(12)]))
    outdir.mkdir(parents=True,exist_ok=False);thumbs=[];records=[]
    height=max(1,round(phone_width*v['height']/v['width']))
    if height>2560:raise ValueError('Extreme aspect ratio: use targeted inspection, not a distorted phone sheet')
    for index,t in enumerate(times):
        # Final seek must be inside the last frame for ordinary CFR/VFR sources.
        actual=min(t,max(0,duration-1/fps))
        cmd=['ffmpeg','-v','error','-ss',str(actual),'-i',str(video),'-frames:v','1','-vf',f'scale={phone_width}:{height}', '-f','image2pipe','-vcodec','png','-']
        data=subprocess.run(cmd,capture_output=True,check=True).stdout
        im=Image.open(io.BytesIO(data)).convert('RGB');f=outdir/f'frame-{index:04d}.png';im.save(f)
        thumbs.append(im);records.append({'id':f'f{index:04d}','t':actual,'path':f.name,'sha256':sha(f)})
    pages=[];page_size=columns*rows;label=30
    for start in range(0,len(thumbs),page_size):
        group=thumbs[start:start+page_size];nr=math.ceil(len(group)/columns)
        sheet=Image.new('RGB',(columns*phone_width,nr*(height+label)),(235,235,235));d=ImageDraw.Draw(sheet)
        for j,im in enumerate(group):
            x=(j%columns)*phone_width;y=(j//columns)*(height+label)
            sheet.paste(im,(x,y));r=records[start+j];d.text((x+8,y+height+8),f"{r['id']} | {r['t']:.3f}s",fill=(15,15,15))
        f=outdir/f'contact-{len(pages)+1:03d}.png';sheet.save(f);pages.append({'path':f.name,'sha256':sha(f),'frame_ids':[r['id'] for r in records[start:start+page_size]]})
    report={'source':{'path':str(video),'sha256':sha(video)},'duration_s':duration,'sample_count':len(records),'requested_interval_s':interval,
      'uniform_sampling_thinned':math.floor(max(0,duration-.001)/interval)+2>max_samples,'phone_width_px':phone_width,'pages':pages,'frames':records,
      'actual_visual_review':'PENDING','limits':'Sparse stills cannot prove motion, audio sync, full-video comprehension or absence of flicker. Review playback separately.'}
    atomic_json(outdir/'evidence.json',report);return report

def validate_review(plan_path,review_path):
    p,plan_report=validate_plan(plan_path);review_path=Path(review_path).resolve(strict=True);r=read_json(review_path)
    if r.get('plan_sha256')!=plan_report['plan_sha256'] or r.get('child_id')!=p['child_id']:raise ValueError('Stale plan or wrong child in review')
    if not r.get('reviewer') or r.get('review_type') not in ('agent_declared','human_declared'):raise ValueError('Identify the reviewer and declared scope')
    evidence={}
    for a in r.get('artifacts',[]):
        path=check_file(a,review_path.parent)
        if a['id'] in evidence:raise ValueError('Repeated evidence id')
        if a.get('kind') not in ('image','video','audio','report'):raise ValueError('Invalid evidence kind')
        if a.get('kind')=='image':
            with Image.open(path) as image:image.verify()
        if a.get('kind')=='video' and path.suffix.lower() not in ('.mp4','.mov','.webm','.mkv'):raise ValueError('Use an actual video artifact')
        if a.get('kind')=='audio' and path.suffix.lower() not in ('.wav','.mp3','.m4a','.flac','.aac','.ogg'):raise ValueError('Use an actual audio artifact')
        if a.get('kind') in ('video','audio'):
            probe=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type','-of','json',str(path)],capture_output=True,text=True,check=True)
            kinds={x.get('codec_type') for x in json.loads(probe.stdout).get('streams',[])}
            if a['kind'] not in kinds:raise ValueError('Evidence has no '+a['kind']+' stream')
            if a.get('audio_listened') is True and 'audio' not in kinds:raise ValueError('No audio stream exists to listen to')
        evidence[a['id']]=a
    gates=r.get('gates',{})
    if set(gates)!=GATES:raise ValueError('Every named quality gate must have its own status; scores alone do not approve')
    failures=[];pending=[]
    for name,g in gates.items():
        status=g.get('status')
        if status not in ('pass','fail','pending','not_applicable'):raise ValueError('Invalid gate status')
        if not isinstance(g.get('observation'),str) or len(g['observation'].strip())<6:raise ValueError('A concrete observation/reason is required for '+name)
        optional=(name=='audio_sync' and p['audio_mode']=='none') or (name=='loop_seam' and not p.get('loop',False))
        if status=='not_applicable' and not optional:raise ValueError('Required gate cannot be N/A: '+name)
        ids=g.get('evidence_ids',[])
        if any(i not in evidence for i in ids):raise ValueError('Unknown evidence id')
        if status=='pass':
            items=[evidence[i] for i in ids]
            required='image' if name in VISUAL else ('video' if name in ('motion_playback','loop_seam') else 'audio')
            if not any(x.get('viewed') is True and (x['kind']==required or (required=='audio' and x['kind']=='video' and x.get('audio_listened') is True)) for x in items):raise ValueError('Gate needs actually declared matching evidence: '+name)
        if status=='fail':failures.append(name)
        if status=='pending':pending.append(name)
    issues=r.get('issues',[])
    if failures and not issues:raise ValueError('Failed gates need timestamped issues and fixes')
    for i in issues:
        if i.get('gate') not in GATES or i.get('shot_id') not in {s['id'] for s in p['shots']} or not i.get('fix'):raise ValueError('Issue needs gate, shot and actionable fix')
        start=integer(i['start_frame'],'issue start',0,p['duration_frames']-1);end=integer(i['end_frame'],'issue end',1,p['duration_frames'])
        if end<=start:raise ValueError('Invalid issue range')
    # An unresolved issue also blocks passage, even if a reviewer labels every gate pass.
    unresolved=[x for x in issues if x.get('resolved') is not True]
    return p,r,{'ok':True,'all_required_gates_pass':not failures and not pending and not unresolved,
      'failed_gates':failures,'pending_gates':pending,'top_fixes':sorted(unresolved,key=lambda x:0 if x.get('severity')=='blocking' else 1)[:3],
      'evidence_scope':'Reviewer declaration and file integrity verified; viewing itself and artistic quality are not mechanically proven.'}

def register_review(plan_path,review_path):
    plan_path=Path(plan_path).resolve(strict=True);p,r,result=validate_review(plan_path,review_path)
    history=plan_path.parent/'studio-review-history.json';lock=history.with_suffix('.lock')
    limits=read_json(ROOT/'config/studio-profiles.json')[p['profile']]
    try:fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise ValueError('Review registration already running; inspect stale lock before retrying')
    os.close(fd)
    try:
        h=read_json(history) if history.exists() else {'child_id':p['child_id'],'entries':[]}
        if h['child_id']!=p['child_id']:raise ValueError('Do not mix child histories')
        review_sha=sha(review_path)
        if any(x['review_sha256']==review_sha for x in h['entries']):raise ValueError('This review was already registered')
        round_no=len(h['entries'])+1
        if round_no>limits['max_review_rounds']:raise ValueError('Review budget exhausted. Keep draft; ask before a new authorization. Do not erase history.')
        if result['all_required_gates_pass']:action='ready_for_user_approval' if p.get('new_style',True) else 'ready_for_final_checks'
        elif round_no>=limits['max_review_rounds']:action='stop_not_approved'
        elif result['pending_gates']:action='obtain_missing_evidence'
        else:action='fix_top_issues_and_review_changed_shots'
        receipt={**result,'round':round_no,'action':action,'plan_sha256':sha(plan_path),'review_sha256':review_sha,'profile':p['profile'],
            'budget_resets_on_plan_revision':False,'approved_by_silence':False}
        h['entries'].append(receipt);atomic_json(history,h);return receipt
    finally:lock.unlink(missing_ok=True)

def briefs(plan_path,outdir):
    p,r=validate_plan(plan_path);outdir=Path(outdir).resolve()
    if outdir.exists():raise ValueError('Use a new briefs directory')
    outdir.mkdir(parents=True)
    for idx,s in enumerate(p['shots'],1):
        states='\n'.join(f"- frame {x['frame']}: {x['visible_result']}" for x in s['states'])
        text=f"# Shot {s['id']}\n\nPurpose: {s['purpose']}\nSpoken cue: {s.get('speech_cue','N/A — music-led')}\nTreatment: {s['treatment']}\nAction: {s['visual_action']}\nDistinctive choice: {s['why_not_generic']}\nFrames: [{s['start_frame']}, {s['end_frame']}) at {p['fps']} fps\n\n## Visible states\n{states}\n\nReference/asset IDs: {', '.join(s.get('asset_ids',[])) or 'none'}\n\nKeep the active style guide and approved frames. Do not rewrite the speech. Code is a pure function of time. Review code before execution; run local previews before paid revisions. No silent style, provider or budget changes.\n"
        (outdir/f'{idx:03d}.md').write_text(text,encoding='utf-8')
    atomic_json(outdir/'manifest.json',r);return {**r,'brief_directory':str(outdir)}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='cmd',required=True)
    s=sp.add_parser('plan-check');s.add_argument('plan',type=Path)
    s=sp.add_parser('briefs');s.add_argument('plan',type=Path);s.add_argument('--outdir',type=Path,required=True)
    s=sp.add_parser('review');s.add_argument('plan',type=Path);s.add_argument('review',type=Path);s.add_argument('--register',action='store_true')
    s=sp.add_parser('sheets');s.add_argument('video',type=Path);s.add_argument('--outdir',type=Path,required=True);s.add_argument('--interval',type=float,default=.5);s.add_argument('--max-samples',type=int,default=120);s.add_argument('--strip-at',type=float)
    a=p.parse_args(argv)
    try:
        if a.cmd=='plan-check':out=validate_plan(a.plan)[1]
        elif a.cmd=='briefs':out=briefs(a.plan,a.outdir)
        elif a.cmd=='review':out=register_review(a.plan,a.review) if a.register else validate_review(a.plan,a.review)[2]
        else:out=sheets(a.video,a.outdir,a.interval,a.max_samples,strip_at=a.strip_at)
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
