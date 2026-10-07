#!/usr/bin/env python3
"""Real FFmpeg execution with synthetic media and hand-authored transcript; NOT an ASR/LLM test."""
from __future__ import annotations
import argparse
import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(*args, expect=0):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if p.returncode != expect:
        raise RuntimeError(f'Command failed ({p.returncode}): {args}\n{p.stdout[-2000:]}\n{p.stderr[-3000:]}')
    return p


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--report'); a=ap.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print(json.dumps({'ok':False,'skipped':'ffmpeg/ffprobe missing'})); return 2
    with tempfile.TemporaryDirectory(prefix='factory-script-silence-') as td:
        t=Path(td); src=t/'source.mp4'; audio=t/'sound.wav'
        sr=48000; samples=array.array('h')
        for n in range(sr*6):
            sec=n/sr
            hz=440 if 1<=sec<2 else (880 if 4<=sec<5 else 0)
            samples.append(int(8000*math.sin(2*math.pi*hz*sec)) if hz else 0)
        if sys.byteorder!='little': samples.byteswap()
        with wave.open(str(audio),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(samples.tobytes())
        run('ffmpeg','-y','-hide_banner','-loglevel','error','-f','lavfi','-i',
            'testsrc2=size=320x180:rate=30:duration=6','-i',audio,
            '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',src)
        original_hash=digest(src)
        tr=t/'transcript.json'
        tr.write_text(json.dumps({'input':str(src),'language':'pt','synthetic':True,'segments':[
            {'start':1,'end':2,'text':'primeiro trecho','words':[
                {'start':1,'end':1.4,'word':'primeiro'},{'start':1.5,'end':2,'word':'trecho'}]},
            {'start':4,'end':5,'text':'segundo trecho','words':[
                {'start':4,'end':4.4,'word':'segundo'},{'start':4.5,'end':5,'word':'trecho'}]}]}))
        sil=t/'silence.json'
        run(PY,ROOT/'tools/detect_silence.py',src,'--output',sil)
        detected=json.loads(sil.read_text())
        base=t/'assembly.json'
        base.write_text(json.dumps({'version':'1.1','output':{'width':320,'height':180,'fps':30,'crf':28},
                                    'segments':[{'source':str(src),'in':0,'out':6}]}))
        edl=t/'edl.json'; audit=t/'audit.json'
        run(PY,ROOT/'tools/plan_silence_cuts.py','--source',src,'--silence',sil,'--transcript',tr,
            '--base-edl',base,'--mode','natural','--output',edl,'--report',audit)
        planned=json.loads(audit.read_text()); out=t/'draft.mp4'
        run(PY,ROOT/'tools/render_edl.py',edl,'--output',out)
        info=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',out).stdout)
        streams=info['streams'];v=next(s for s in streams if s['codec_type']=='video');au=next(s for s in streams if s['codec_type']=='audio')
        vd,ad=float(v['duration']),float(au['duration'])
        run('ffmpeg','-hide_banner','-loglevel','error','-i',out,'-f','null','-')
        rt=t/'retimed.json';srt=t/'captions.srt'
        run(PY,ROOT/'tools/retime_transcript.py',tr,edl,'--output',rt,'--srt',srt)
        retimed=json.loads(rt.read_text())
        post=t/'post-silence.json'
        run(PY,ROOT/'tools/detect_silence.py',out,'--duration','0.65','--output',post)
        postmap=json.loads(post.read_text())
        # Intentional silence protected in a separately versioned plan.
        protected=t/'protected.json'; protected.write_text(json.dumps({'input':str(src),'ranges':[{'start':2,'end':4,'reason':'intentional_pause'}]}))
        protected_edl=t/'protected-edl.json';protected_audit=t/'protected-audit.json'
        run(PY,ROOT/'tools/plan_silence_cuts.py','--source',src,'--silence',sil,'--transcript',tr,
            '--protected',protected,'--base-edl',base,'--output',protected_edl,'--report',protected_audit)
        pr=json.loads(protected_audit.read_text())
        # Candidate retrieval is explicitly a pending semantic task.
        script=t/'reference.md';script.write_text('Primeiro trecho.\n\nSegundo trecho.',encoding='utf-8')
        packet=t/'comparison.json'
        run(PY,ROOT/'tools/prepare_script_comparison.py','--script',script,'--transcript',tr,'--output',packet)
        comparison=json.loads(packet.read_text())
        # Guard tests use existing output and changed hashes, never overwrite source.
        old=digest(out)
        rerender=subprocess.run([PY,str(ROOT/'tools/render_edl.py'),str(edl),'--output',str(out)],capture_output=True)
        stale=json.loads(sil.read_text());stale['source_sha256']='bad';bad=t/'stale.json';bad.write_text(json.dumps(stale))
        stale_call=subprocess.run([PY,str(ROOT/'tools/plan_silence_cuts.py'),'--source',str(src),
            '--silence',str(bad),'--transcript',str(tr),'--output',str(t/'bad-edl.json'),'--report',str(t/'bad-report.json')],capture_output=True)
        # No audio must be distinguished from an entirely silent recording.
        silent_video=t/'no-audio.mp4'
        run('ffmpeg','-hide_banner','-loglevel','error','-i',src,'-map','0:v:0','-c','copy','-an',silent_video)
        no_audio=t/'no-audio.json';run(PY,ROOT/'tools/detect_silence.py',silent_video,'--output',no_audio)
        sys.path.insert(0,str(ROOT/'tools'))
        from client_memory import Memory
        Memory(t).init('fixture','Synthetic silence test format')
        from design_catalog import register_visual
        register_visual(t,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
        (t/'patterns').mkdir()
        shutil.copy2(ROOT/'patterns/talking-head-clean-v2.yaml',t/'patterns')
        run(PY,ROOT/'tools/make_job.py','--root',t,'--format','fixture','--visual-id','IDP01','--source',src,'--reference-script',script,
            '--id','integration-job','--jobs-dir',t/'jobs','--silence-mode','natural')
        job=json.loads((t/'jobs/integration-job/job.yaml').read_text())
        # The detector's explicitly selected track must be the track rendered, too.
        multi=t/'two-tracks.mp4'
        run('ffmpeg','-hide_banner','-loglevel','error','-i',src,'-f','lavfi','-i',
            'anullsrc=r=48000:cl=mono','-map','0:v:0','-map','1:a:0','-map','0:a:0',
            '-t','6','-c:v','copy','-c:a','aac',multi)
        multi_tr=t/'multi-tr.json';multi_data=json.loads(tr.read_text());multi_data['input']=str(multi);multi_data['audio_stream']=1
        multi_tr.write_text(json.dumps(multi_data))
        multi_sil=t/'multi-sil.json';run(PY,ROOT/'tools/detect_silence.py',multi,'--audio-stream','1','--output',multi_sil)
        multi_base=t/'multi-base.json';multi_base.write_text(json.dumps({'version':'1.1',
            'output':{'width':320,'height':180,'fps':30,'crf':28},'segments':[{'source':str(multi),'in':0,'out':6}]}))
        multi_edl=t/'multi-edl.json';multi_report=t/'multi-report.json'
        run(PY,ROOT/'tools/plan_silence_cuts.py','--source',multi,'--silence',multi_sil,
            '--transcript',multi_tr,'--base-edl',multi_base,'--output',multi_edl,'--report',multi_report)
        multi_out=t/'multi-out.mp4';run(PY,ROOT/'tools/render_edl.py',multi_edl,'--output',multi_out)
        multi_post=t/'multi-post.json';run(PY,ROOT/'tools/detect_silence.py',multi_out,'--duration','0.65','--output',multi_post)
        selected_track_ok=not json.loads(multi_post.read_text())['silences']
        checks={
            'selected_dialogue_track_rendered_not_empty_track':selected_track_ok,
            'three_quiet_regions_detected':len(detected['silences'])==3,
            'automatic_removal_executed':len(planned['cuts'])==3 and planned['removed_seconds']>2,
            'video_audio_streams_present':bool(v and au),
            'duration_matches_edl_within_100ms':abs(float(info['format']['duration'])-planned['after_seconds'])<=0.1,
            'av_duration_drift_within_80ms':abs(vd-ad)<=0.08,
            'no_unmotivated_gap_over_650ms':not postmap['silences'],
            'all_four_synthetic_words_retimed':len(retimed['words'])==4,
            'captions_created':srt.is_file() and srt.stat().st_size>0,
            'protected_pause_not_removed':not any(max(c['start'],2)<min(c['end'],4) for c in pr['cuts']),
            'reference_packet_requires_semantic_review':comparison['comparison_status']=='pending_semantic_editor',
            'script_job_fields_recorded':job['reference_script']['enabled'] and job['reference_script']['mode']=='flexible' and job['silence_removal']['enabled'],
            'source_sha256_unchanged':original_hash==digest(src),
            'existing_render_not_overwritten':rerender.returncode!=0 and digest(out)==old,
            'stale_evidence_blocked':stale_call.returncode!=0 and not (t/'bad-edl.json').exists(),
            'no_audio_reported_not_applicable':json.loads(no_audio.read_text())['status']=='not_applicable_no_audio',
        }
        report={'ok':all(checks.values()),'fixture':'synthetic tones and image; hand-authored synthetic word times',
                'not_tested':['real speech transcription','semantic LLM editing','subjective listening on user media'],
                'checks':checks,'input_seconds':6,'planned_output_seconds':planned['after_seconds'],
                'rendered_video_seconds':vd,'rendered_audio_seconds':ad,
                'removed_seconds':planned['removed_seconds']}
        print(json.dumps(report,ensure_ascii=False,indent=2))
        if a.report:
            Path(a.report).parent.mkdir(parents=True,exist_ok=True)
            Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return 0 if report['ok'] else 1

if __name__=='__main__': raise SystemExit(main())
