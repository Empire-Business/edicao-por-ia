#!/usr/bin/env python3
import argparse, json, math, subprocess
from pathlib import Path

def duration(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",path],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())

def frame(input_path, t, out, width):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",f"{t:.3f}","-i",input_path,"-frames:v","1","-vf",f"scale={width}:-2",str(out)],check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--times",help="JSON file containing a list of seconds")
    ap.add_argument("--interval",type=float,default=20.0)
    ap.add_argument("--width",type=int,default=640)
    a=ap.parse_args()
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    if a.times:
        times=json.loads(Path(a.times).read_text())
        if isinstance(times,dict): times=times.get("times",[])
    else:
        d=duration(a.input); times=[min(d-0.001, i*a.interval) for i in range(max(1,math.ceil(d/a.interval))) if i*a.interval < d]
    manifest=[]
    for i,t in enumerate(times):
        p=out/f"frame_{i:04d}_{float(t):010.3f}.jpg"
        frame(a.input,float(t),p,a.width)
        manifest.append({"time":float(t),"file":str(p)})
    (out/"frames.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"count":len(manifest),"manifest":str(out/'frames.json')},indent=2))
if __name__=="__main__": main()
