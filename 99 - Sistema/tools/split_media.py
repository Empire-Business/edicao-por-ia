#!/usr/bin/env python3
import argparse, json, subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("segments_json",help='JSON list: [{"start":0,"end":10,"name":"video-1"}]')
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--copy",action="store_true",help="Stream-copy when possible; may cut on nearby keyframes.")
    a=ap.parse_args()
    segs=json.loads(Path(a.segments_json).read_text())
    if isinstance(segs,dict): segs=segs.get("segments",[])
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    results=[]
    for i,s in enumerate(segs,1):
        start=float(s["start"]); end=float(s["end"]); name=s.get("name") or f"part-{i:02d}"
        p=out/f"{name}.mp4"
        cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(start),"-i",a.input,"-t",str(end-start)]
        if a.copy: cmd += ["-c","copy"]
        else: cmd += ["-c:v","libx264","-crf","18","-c:a","aac","-b:a","192k"]
        cmd.append(str(p)); subprocess.run(cmd,check=True); results.append({"name":name,"path":str(p),"start":start,"end":end})
    print(json.dumps(results,indent=2))
if __name__=="__main__": main()
