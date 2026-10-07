#!/usr/bin/env python3
"""Local music analysis and deterministic sound-effect synthesis. No music downloads/APIs.
Beat events are estimates, not downbeat labels. Does not change or time-stretch speech.
"""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, sys, wave
from pathlib import Path
from factory_common import read_json, sha, atomic_json

def grid_document(bpm,beats,hits,duration,source,method,first_downbeat_index=None,beats_per_bar=None):
    def valid_time(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<duration
    if not math.isfinite(duration) or duration<=0:raise ValueError('Invalid duration')
    if bpm is not None and (not math.isfinite(bpm) or bpm<0):raise ValueError('Invalid BPM')
    if any(not valid_time(x) for x in beats+hits) or beats!=sorted(set(beats)):raise ValueError('Invalid beat timestamps')
    down=[]
    if first_downbeat_index is not None or beats_per_bar is not None:
        if type(first_downbeat_index)!=int or not 0<=first_downbeat_index<len(beats) or type(beats_per_bar)!=int or not 1<=beats_per_bar<=16:raise ValueError('Confirm downbeat index AND meter explicitly')
        down=beats[first_downbeat_index::beats_per_bar]
    return {'schema_version':1,'source':source,'duration_s':duration,'estimated_bpm':bpm,'beats':beats,'hits':hits,'downbeats':down,
      'downbeat_status':'user_phase_and_meter_declared' if down else 'unknown_not_inferred','beats_per_bar':beats_per_bar,
      'method':method,'timebase':'audio_file_seconds','sync_to_master':'UNMAPPED — record trim/offset before use',
      'limits':'No confidence of musical bar phase from every fourth beat; tempo may vary. Verify against the track. Never shorten speech to land on a beat.'}

def analyze(path,out,first_downbeat_index=None,beats_per_bar=None):
    import numpy as np, librosa
    path=Path(path).resolve(strict=True);out=Path(out).resolve()
    if out.exists() or out==path:raise ValueError('New output path required')
    sr=22050
    meta=json.loads(subprocess.run(['ffprobe','-v','error','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True).stdout)
    duration=float(meta['format']['duration'])
    if not 0<duration<=600:raise ValueError('Analyze separate music sections of at most 600 seconds')
    b=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-vn','-ar',str(sr),'-ac','1','-f','f32le','-'],capture_output=True,check=True).stdout
    y=np.frombuffer(b,dtype='<f4').copy()
    if not len(y) or not np.all(np.isfinite(y)):raise ValueError('Empty or invalid audio')
    duration=len(y)/sr
    if np.max(np.abs(y))<1e-6:tempo=0.;beats=[];hits=[]
    else:
        onset=librosa.onset.onset_strength(y=y,sr=sr,hop_length=512)
        tempo,beat_frames=librosa.beat.beat_track(onset_envelope=onset,sr=sr,hop_length=512)
        tempo=float(np.atleast_1d(tempo)[0])
        hit_frames=librosa.onset.onset_detect(onset_envelope=onset,sr=sr,hop_length=512)
        beats=sorted(set(float(round(x,6)) for x in librosa.frames_to_time(beat_frames,sr=sr,hop_length=512) if 0<=x<duration))
        hits=sorted(set(float(round(x,6)) for x in librosa.frames_to_time(hit_frames,sr=sr,hop_length=512) if 0<=x<duration))
    doc=grid_document(tempo,beats,hits,duration,{'path':str(path),'sha256':sha(path)},'librosa.beat.beat_track '+librosa.__version__,first_downbeat_index,beats_per_bar)
    atomic_json(out,doc);return doc

def synth(spec_path,out):
    import numpy as np
    spec_path=Path(spec_path).resolve(strict=True);p=read_json(spec_path);out=Path(out).resolve()
    if out.exists() or out==spec_path or out.suffix.lower()!='.wav':raise ValueError('New WAV path required')
    duration=p['duration_s'];sr=p.get('sample_rate',48000)
    if not isinstance(duration,(int,float)) or isinstance(duration,bool) or not math.isfinite(duration) or not 0<duration<=600:raise ValueError('duration_s: 0..600')
    if type(sr)!=int or sr not in (24000,44100,48000):raise ValueError('Unsupported sample rate')
    cues=p.get('cues',[])
    if not isinstance(cues,list) or len(cues)>1000:raise ValueError('At most 1000 cues')
    outbuf=np.zeros(round(duration*sr),np.float64);ids=set()
    voices={'click':(.045,1800,1800),'pop':(.12,700,180),'thump':(.35,110,55),'whoosh':(.3,0,0)}
    for c in cues:
        cid=c.get('id');typ=c.get('type');t=c.get('t');gain=c.get('gain',.25)
        if not isinstance(cid,str) or not cid or cid in ids:raise ValueError('Unique cue id required')
        ids.add(cid)
        if typ not in voices:raise ValueError('Unsupported SFX')
        if not isinstance(t,(int,float)) or isinstance(t,bool) or not math.isfinite(t) or not 0<=t<duration:raise ValueError('Cue outside timeline')
        if not isinstance(gain,(int,float)) or isinstance(gain,bool) or not math.isfinite(gain) or not 0<=gain<=1:raise ValueError('gain: 0..1')
        length,f0,f1=voices[typ];count=min(round(length*sr),len(outbuf)-round(t*sr));time=np.arange(count)/sr
        env=np.sin(np.pi*np.minimum(1,time/length))**2
        if typ=='whoosh':
            seed=int.from_bytes(hashlib.sha256(cid.encode()).digest()[:8],'big');signal=np.random.default_rng(seed).uniform(-1,1,count)
        else:signal=np.sin(2*np.pi*(f0*time+.5*(f1-f0)/length*time**2))
        pos=round(t*sr);outbuf[pos:pos+count]+=gain*signal*env
    peak=float(np.max(np.abs(outbuf)));scale=min(1.,.8/peak) if peak else 1.
    pcm=np.rint(outbuf*scale*32767).astype('<i2')
    out.parent.mkdir(parents=True,exist_ok=True)
    # O_EXCL avoids overwriting an existing file even during concurrent invocations.
    with out.open('xb') as f:
        with wave.open(f,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())
    return {'ok':True,'path':str(out),'sha256':sha(out),'source_spec_sha256':sha(spec_path),'samples':len(pcm),'sample_rate':sr,'peak_before_headroom':peak,'headroom_scale':scale,
      'speech_modified':False,'music_composition':False,'note':'SFX stem only, not a soundtrack or final loudness master. Listen and mix below the voice.'}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='cmd',required=True)
    s=sp.add_parser('beats');s.add_argument('input',type=Path);s.add_argument('--output',required=True,type=Path);s.add_argument('--first-downbeat-index',type=int);s.add_argument('--beats-per-bar',type=int)
    s=sp.add_parser('sfx');s.add_argument('input',type=Path);s.add_argument('--output',required=True,type=Path)
    a=p.parse_args(argv)
    try:
        out=analyze(a.input,a.output,a.first_downbeat_index,a.beats_per_bar) if a.cmd=='beats' else synth(a.input,a.output)
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
