#!/usr/bin/env python3
import argparse, json, subprocess
from pathlib import Path
from edit_support import check_output, number, read_data

def audio_count(path):
    p=subprocess.run(["ffprobe","-v","error","-select_streams","a","-show_entries","stream=index","-of","json",path],capture_output=True,text=True,check=True)
    return len(json.loads(p.stdout).get("streams", []))

def main():
    ap=argparse.ArgumentParser(description="Render a simple cut-based EDL with FFmpeg.")
    ap.add_argument("edl")
    ap.add_argument("--output",required=True)
    ap.add_argument("--crf",type=int)
    a=ap.parse_args()
    edl=read_data(a.edl)
    segs=edl.get("segments",[])
    if not segs: raise SystemExit("EDL has no segments")
    for s in segs:
        if float(s["out"]) <= float(s["in"]): raise SystemExit(f"Invalid segment: {s}")
        if not Path(s["source"]).exists(): raise SystemExit(f"Missing source: {s['source']}")
    check_output(a.output, [a.edl] + [s["source"] for s in segs])
    for s in segs:
        number(s["in"], "segment in")
        number(s["out"], "segment out")
    unique=[]
    for s in segs:
        if s["source"] not in unique: unique.append(s["source"])
    idx={p:i for i,p in enumerate(unique)}
    cmd=["ffmpeg","-n","-hide_banner"]
    for p in unique: cmd += ["-i",p]
    outcfg=edl.get("output",{})
    W=int(outcfg.get("width",1080)); H=int(outcfg.get("height",1920)); fps=float(outcfg.get("fps",30)); fit=outcfg.get("fit","cover")
    fade_ms=float(outcfg.get("edge_audio_fade_ms",5)); fade=max(0,fade_ms/1000)
    filters=[]; concat_inputs=[]
    audio_flags={p:audio_count(p) for p in unique}
    for n,s in enumerate(segs):
        i=idx[s["source"]]; start=float(s["in"]); end=float(s["out"]); dur=end-start
        if fit=="contain":
            vf=f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        else:
            vf=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
        zoom=float(s.get("zoom",1.0))
        if not 1.0 <= zoom <= 1.25: raise SystemExit("Invalid EDL segment zoom (1.0-1.25)")
        if zoom>1.0:
            # Optional punch-in: scale up, crop back to W:H, horizontally centered, vertical anchor 0..1.
            ay=float(s.get("zoom_anchor_y",0.5)); zw=int(round(W*zoom/2))*2; zh=int(round(H*zoom/2))*2
            vf += f",scale={zw}:{zh},crop={W}:{H}:{(zw-W)//2}:{int((zh-H)*ay)},setsar=1"
        filters.append(f"[{i}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,{vf},fps={fps}[v{n}]")
        if audio_flags[s["source"]]:
            track=s.get("audio_stream",0)
            if not isinstance(track,int) or isinstance(track,bool) or not 0 <= track < audio_flags[s["source"]]:
                raise SystemExit("Invalid EDL audio stream")
            af=f"atrim=start={start}:end={end},asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
            if fade>0 and dur>2*fade:
                af += f",afade=t=in:st=0:d={fade},afade=t=out:st={max(0,dur-fade)}:d={fade}"
            filters.append(f"[{i}:a:{track}]{af}[a{n}]")
        else:
            filters.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={dur},asetpts=PTS-STARTPTS[a{n}]")
        concat_inputs += [f"[v{n}]",f"[a{n}]"]
    filters.append("".join(concat_inputs)+f"concat=n={len(segs)}:v=1:a=1[vout][aout]")
    cmd += ["-filter_complex",";".join(filters),"-map","[vout]","-map","[aout]","-c:v",outcfg.get("video_codec","libx264"),"-crf",str(a.crf if a.crf is not None else outcfg.get("crf",18)),"-pix_fmt","yuv420p","-c:a",outcfg.get("audio_codec","aac"),"-b:a",outcfg.get("audio_bitrate","192k"),"-movflags","+faststart",a.output]
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(cmd,check=True)
    print(json.dumps({"output":str(Path(a.output).resolve()),"segments":len(segs)},indent=2))
if __name__=="__main__": main()
