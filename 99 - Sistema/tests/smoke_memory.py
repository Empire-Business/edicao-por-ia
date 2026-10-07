#!/usr/bin/env python3
"""End-to-end local synthetic test: hook -> capture -> new job -> changed cuts -> real FFmpeg render.
No live model, real user identity, semantic feedback evaluation, or speech recognition.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
PY=sys.executable


def run(*args,data=None):
    p=subprocess.run([str(x) for x in args],input=json.dumps(data) if data else None,
                     text=True,capture_output=True)
    if p.returncode:
        raise RuntimeError(f'Failed: {args}\n{p.stderr[-2500:]}\n{p.stdout[-1000:]}')
    return p.stdout


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report');a=ap.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print(json.dumps({'ok':False,'skipped':'FFmpeg/ffprobe unavailable'}));return 2
    with tempfile.TemporaryDirectory(prefix='cvf-memory-smoke-') as td:
        root=Path(td);(root/'patterns').mkdir()
        shutil.copy(ROOT/'patterns/talking-head-clean-v2.yaml',root/'patterns/')
        def mem(*args,data=None):return json.loads(run(PY,ROOT/'tools/client_memory.py','--root',root,*args,data=data))
        def hook(event):return json.loads(run(PY,ROOT/'tools/memory_hook.py','--root',root,data=event))
        mem('init','--client','alpha','--name','Synthetic Client Alpha')
        mem('init','--client','beta','--name','Synthetic Client Beta')
        start=hook({'hook_event_name':'SessionStart','session_id':'test-session'})
        submit=hook({'hook_event_name':'UserPromptSubmit','session_id':'test-session','prompt':'synthetic feedback not stored verbatim'})
        token=mem('status','--session','test-session')['turn']
        before=hook({'hook_event_name':'Stop','session_id':'test-session'})
        mem('bind','--session','test-session','--client','alpha')
        item={'kind':'preference','key':'silence_removal.settings.keep_pause_seconds',
              'setting':'silence_removal.settings.keep_pause_seconds','value':0.42,
              'scope':'client','scope_id':'alpha','basis':'user_explicit','source':'user_message',
              'quote':'Synthetic user: keep 0.42 seconds of these pauses in future videos.',
              'reason':'Synthetic explicit feedback fixture, not real client data.'}
        receipt=mem('capture','--session','test-session','--turn',token,data={'items':[item]})
        after=hook({'hook_event_name':'Stop','session_id':'test-session'})
        reread=mem('context','--client','alpha','--json')
        beta=mem('context','--client','beta','--json')
        src=root/'source.mp4'
        run('ffmpeg','-n','-hide_banner','-loglevel','error','-f','lavfi','-i',
            'testsrc2=size=160x90:rate=20:duration=8','-f','lavfi','-i',
            'aevalsrc=if(between(t\\,2\\,4)\\,0\\,0.15*sin(2*PI*330*t)):s=48000:d=8',
            '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',src)
        sha=hashlib.sha256(src.read_bytes()).hexdigest()
        run(PY,ROOT/'tools/make_job.py','--root',root,'--client','alpha','--session','test-session','--source',src,'--id','video-1')
        folder=root/'jobs/video-1';effective=folder/'job.effective.json'
        cfg=json.loads(effective.read_text());settings=folder/'job.effective.silence-settings.json'
        # Hand-authored timing for synthetic tones, NOT recognized speech.
        tr=root/'transcript.json';tr.write_text(json.dumps({'input':str(src),'synthetic':True,'words':[
            {'start':0.1,'end':1.9,'word':'tone-a'},{'start':4.1,'end':7.9,'word':'tone-b'}]}))
        sil=root/'silence.json';sil.write_text(json.dumps({'input':str(src),'source_sha256':sha,
            'duration':8,'silences':[{'start':2,'end':4}]}))
        base=root/'assembly.json';base.write_text(json.dumps({'output':{'width':160,'height':90,'fps':20,'crf':28},
            'segments':[{'source':str(src),'in':0,'out':8}]}))
        def plan(stem,settings_path):
            edl=root/(stem+'.json');report=root/(stem+'-report.json')
            run(PY,ROOT/'tools/plan_silence_cuts.py','--source',src,'--silence',sil,'--transcript',tr,
                '--base-edl',base,'--settings',settings_path,'--output',edl,'--report',report)
            return edl,json.loads(report.read_text())
        first,rep1=plan('first',settings)
        # A later feedback revises the persistent preference, affecting the NEXT resolved edit.
        hook({'hook_event_name':'UserPromptSubmit','session_id':'test-session','prompt':'Synthetic later feedback'})
        token2=mem('status','--session','test-session')['turn']
        item2={**item,'value':0.70,'quote':'Synthetic user: from now on, keep 0.70 seconds.'}
        mem('capture','--session','test-session','--turn',token2,data={'items':[item2]})
        stale=subprocess.run([PY,str(ROOT/'tools/resolve_client_context.py'),'--root',str(root),'--check','--job',str(effective)],capture_output=True,text=True)
        revised=folder/'job.effective-v2.json'
        paths=json.loads(run(PY,ROOT/'tools/resolve_client_context.py','--root',root,'--job',folder/'job.yaml','--output',revised))
        second,rep2=plan('second',Path(paths['silence_settings']))
        out=root/'draft.mp4';run(PY,ROOT/'tools/render_edl.py',second,'--output',out)
        probe=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',out))
        streams=probe['streams'];video=next(x for x in streams if x['codec_type']=='video');audio=next(x for x in streams if x['codec_type']=='audio')
        run('ffmpeg','-v','error','-i',out,'-f','null','-')
        qa=json.loads(run(PY,ROOT/'tools/resolve_client_context.py','--root',root,'--check','--job',revised))
        checks={
            'startup_hook_supplies_memory_route':'CLIENT_MEMORY' in json.dumps(start),
            'prompt_hook_supplies_review_token':token in json.dumps(submit),
            'stop_blocks_missing_review':before.get('decision')=='block',
            'capture_returns_verified_receipt':receipt['status']=='saved',
            'stop_releases_after_review':after=={},
            'new_process_retrieves_saved_preference':'0.42' in reread['text'],
            'second_client_isolated':'0.42' not in beta['text'],
            'new_job_inherits_preference':cfg['silence_removal']['settings']['keep_pause_seconds']==0.42,
            'feedback_changes_real_cut_plan':rep2['after_seconds']>rep1['after_seconds'],
            'plan_delta_equals_saved_pause_change':abs((rep2['after_seconds']-rep1['after_seconds'])-0.28)<1e-6,
            'old_context_snapshot_detected_stale':stale.returncode!=0,
            'updated_snapshot_passes_memory_qa':qa['ok'],
            'real_video_rendered':out.stat().st_size>0,
            'output_has_video_and_audio':bool(video and audio),
            'duration_matches_revised_edl':abs(float(probe['format']['duration'])-rep2['after_seconds'])<=0.15,
            'audio_video_duration_close':abs(float(video['duration'])-float(audio['duration']))<=0.10,
            'original_media_preserved':sha==hashlib.sha256(src.read_bytes()).hexdigest(),
            'earlier_plan_not_overwritten':json.loads((root/'first-report.json').read_text())==rep1,
        }
        result={'ok':all(checks.values()),'checks':checks,'fixture':'Synthetic user turns, tone media and hand-authored timing',
                'first_planned_seconds':rep1['after_seconds'],'revised_planned_seconds':rep2['after_seconds'],
                'rendered_seconds':float(probe['format']['duration']),
                'not_tested':['Live Claude Code hooks','Natural-language feedback interpretation','Real speech transcription','User video quality']}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if a.report:Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
