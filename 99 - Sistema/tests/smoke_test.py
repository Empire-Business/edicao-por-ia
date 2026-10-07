#!/usr/bin/env python3
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY=sys.executable

def run(*args, capture=False):
    return subprocess.run(list(args), check=True, text=True, capture_output=capture)

def main():
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print(json.dumps({'ok':False,'skipped':'ffmpeg/ffprobe missing'},indent=2)); return 2
    with tempfile.TemporaryDirectory(prefix='video-factory-smoke-') as td:
        t=Path(td); src=t/'source.mp4'
        run('ffmpeg','-y','-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc2=size=640x360:rate=30:duration=6','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=6','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(src))
        before=hashlib.sha256(src.read_bytes()).hexdigest()
        probe=t/'probe.json'; run(PY,str(ROOT/'tools/probe_media.py'),str(src),'--output',str(probe))
        edl=t/'edl.json'; edl.write_text(json.dumps({'version':'1.0','output':{'width':360,'height':640,'fps':30,'fit':'cover','crf':28},'segments':[{'source':str(src),'in':0.5,'out':2.0},{'source':str(src),'in':3.0,'out':5.5}]}))
        render=t/'render.mp4'; run(PY,str(ROOT/'tools/render_edl.py'),str(edl),'--output',str(render), capture=True)
        tr=t/'tr.json'; tr.write_text(json.dumps({'language':'pt','segments':[{'start':0.5,'end':1.5,'text':'ola mundo','words':[{'word':'ola','start':0.5,'end':0.9},{'word':'mundo','start':1.0,'end':1.5}]},{'start':3.0,'end':4.2,'text':'segundo trecho','words':[{'word':'segundo','start':3.0,'end':3.6},{'word':'trecho','start':3.7,'end':4.2}]}]}))
        rt=t/'rt.json'; srt=t/'c.srt'; run(PY,str(ROOT/'tools/retime_transcript.py'),str(tr),str(edl),'--output',str(rt),'--srt',str(srt), capture=True)
        qa=t/'qa.json'; run(PY,str(ROOT/'tools/qa_media.py'),str(render),'--output',str(qa), capture=True)
        after=hashlib.sha256(src.read_bytes()).hexdigest()
        q=json.loads(qa.read_text()); r=json.loads(rt.read_text())
        vp=run('ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,sample_aspect_ratio','-of','json',str(render),capture=True)
        v=json.loads(vp.stdout)['streams'][0]
        checks={
            'source_unchanged': before==after,
            'render_decodable': q.get('decodable') is True,
            'resolution_ok': (v.get('width'),v.get('height'))==(360,640),
            'sar_ok': v.get('sample_aspect_ratio')=='1:1',
            'retime_ok': len(r.get('words',[]))==4 and abs(r.get('duration',0)-4.0)<0.05,
            'srt_created': srt.exists() and srt.stat().st_size>0,
        }
        print(json.dumps({'ok':all(checks.values()),'checks':checks},indent=2))
        return 0 if all(checks.values()) else 1

if __name__=='__main__': raise SystemExit(main())
