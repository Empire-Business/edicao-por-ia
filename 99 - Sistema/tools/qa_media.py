#!/usr/bin/env python3
import argparse, json, re, subprocess
from pathlib import Path

def probe(path):
    p=subprocess.run(["ffprobe","-v","error","-print_format","json","-show_format","-show_streams",path],capture_output=True,text=True)
    return p.returncode, json.loads(p.stdout or '{}'), p.stderr

def run_filter(path, vf=None, af=None):
    cmd=["ffmpeg","-hide_banner","-nostats","-i",path]
    if vf: cmd += ["-vf",vf]
    if af: cmd += ["-af",af]
    cmd += ["-f","null","-"]
    return subprocess.run(cmd,capture_output=True,text=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--output"); ap.add_argument("--black-duration",type=float,default=.5); ap.add_argument("--silence-duration",type=float,default=2.5); a=ap.parse_args()
    rc,data,err=probe(a.input)
    report={"input":str(Path(a.input).resolve()),"decodable":rc==0,"probe_error":err.strip() or None,"format":data.get("format",{}),"streams":data.get("streams",[]),"black_segments":[],"long_silences":[],"volume":{}}
    if rc==0:
        bp=run_filter(a.input,vf=f"blackdetect=d={a.black_duration}:pix_th=0.10")
        for m in re.finditer(r"black_start:([0-9.]+) black_end:([0-9.]+) black_duration:([0-9.]+)",bp.stderr):
            report["black_segments"].append({"start":float(m.group(1)),"end":float(m.group(2)),"duration":float(m.group(3))})
        sp=run_filter(a.input,af=f"silencedetect=n=-45dB:d={a.silence_duration}")
        starts=[]
        for line in sp.stderr.splitlines():
            m=re.search(r"silence_start:\s*([0-9.]+)",line)
            if m: starts.append(float(m.group(1)))
            m=re.search(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)",line)
            if m:
                end=float(m.group(1)); dur=float(m.group(2)); start=starts.pop(0) if starts else max(0,end-dur)
                report["long_silences"].append({"start":start,"end":end,"duration":dur})
        vp=run_filter(a.input,af="volumedetect")
        for k in ("mean_volume","max_volume"):
            m=re.search(rf"{k}:\s*([^\s]+ dB)",vp.stderr)
            if m: report["volume"][k]=m.group(1)
    s=json.dumps(report,indent=2,ensure_ascii=False)
    if a.output:
        o=Path(a.output); o.parent.mkdir(parents=True,exist_ok=True); o.write_text(s+"\n")
    else: print(s)
    raise SystemExit(0 if report["decodable"] else 1)
if __name__=="__main__": main()
