#!/usr/bin/env python3
import argparse, json
from pathlib import Path

def fmt_srt(t):
    ms=round(t*1000); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; ms%=1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("edl")
    ap.add_argument("--output",required=True)
    ap.add_argument("--srt")
    a=ap.parse_args()
    tr=json.loads(Path(a.transcript).read_text()); edl=json.loads(Path(a.edl).read_text())
    words=[]
    for seg in tr.get("segments",[]): words.extend(seg.get("words",[]))
    mapped=[]; out_cursor=0.0
    for clip in edl.get("segments",[]):
        start=float(clip["in"]); end=float(clip["out"])
        for w in words:
            ws=w.get("start"); we=w.get("end")
            if ws is None or we is None: continue
            if ws >= start and we <= end:
                mapped.append({**w,"source_start":ws,"source_end":we,"start":out_cursor+(ws-start),"end":out_cursor+(we-start)})
        out_cursor += end-start
    result={"language":tr.get("language"),"duration":out_cursor,"words":mapped}
    o=Path(a.output); o.parent.mkdir(parents=True,exist_ok=True); o.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    if a.srt:
        # Simple phrase grouping: <= 8 words, <= ~3.2 sec, split on strong punctuation.
        cues=[]; buf=[]
        for w in mapped:
            buf.append(w)
            text=" ".join(x.get("word","") for x in buf).strip()
            dur=buf[-1]["end"]-buf[0]["start"]
            if len(buf)>=8 or dur>=3.2 or text.endswith((".","?","!")):
                cues.append(buf); buf=[]
        if buf: cues.append(buf)
        lines=[]
        for i,c in enumerate(cues,1):
            lines += [str(i),f"{fmt_srt(c[0]['start'])} --> {fmt_srt(c[-1]['end'])}"," ".join(x.get('word','') for x in c).strip(),""]
        sp=Path(a.srt); sp.parent.mkdir(parents=True,exist_ok=True); sp.write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"words":len(mapped),"duration":out_cursor,"output":str(o)},indent=2))
if __name__=="__main__": main()
