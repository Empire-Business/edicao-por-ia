#!/usr/bin/env python3
import argparse, json, platform, sys
from pathlib import Path

def normalize_segments(raw_segments):
    out=[]
    for s in raw_segments:
        if isinstance(s, dict):
            words=s.get("words") or []
            out.append({"start":float(s.get("start",0)),"end":float(s.get("end",0)),"text":s.get("text","").strip(),"words":[{"word":w.get("word","").strip(),"start":float(w.get("start",0)),"end":float(w.get("end",0)),"probability":w.get("probability")} for w in words if w.get("start") is not None and w.get("end") is not None]})
        else:
            words=[]
            for w in (getattr(s,"words",None) or []):
                words.append({"word":w.word.strip(),"start":float(w.start),"end":float(w.end),"probability":getattr(w,"probability",None)})
            out.append({"start":float(s.start),"end":float(s.end),"text":s.text.strip(),"words":words})
    return out

def run_mlx(path, model, language):
    import mlx_whisper
    kw={"path_or_hf_repo":model,"word_timestamps":True,"verbose":False}
    if language != "auto": kw["language"] = language
    r=mlx_whisper.transcribe(path, **kw)
    return {"backend":"mlx-whisper","model":model,"language":r.get("language"),"text":r.get("text","").strip(),"segments":normalize_segments(r.get("segments",[]))}

def run_faster(path, model, language):
    from faster_whisper import WhisperModel
    device=__import__('os').environ.get("CVF_WHISPER_DEVICE") or ("cuda" if __import__('shutil').which("nvidia-smi") else "cpu")
    compute="float16" if device=="cuda" else "int8"
    m=WhisperModel(model,device=device,compute_type=compute)
    segs,info=m.transcribe(path,word_timestamps=True,vad_filter=True,language=None if language=="auto" else language)
    segs=list(segs)
    return {"backend":"faster-whisper","model":model,"device":device,"language":getattr(info,"language",None),"text":" ".join(s.text.strip() for s in segs).strip(),"segments":normalize_segments(segs)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output",required=True)
    ap.add_argument("--backend",choices=["auto","mlx","faster"],default="auto")
    ap.add_argument("--language",default="auto")
    ap.add_argument("--model")
    a=ap.parse_args()
    backend=a.backend
    is_apple=platform.system()=="Darwin" and platform.machine() in ("arm64","aarch64")
    errors=[]
    result=None
    if backend in ("auto","mlx") and is_apple:
        try:
            result=run_mlx(a.input,a.model or "mlx-community/whisper-large-v3-turbo",a.language)
        except Exception as e:
            errors.append(f"mlx-whisper: {e}")
            if backend=="mlx": raise
    if result is None and backend in ("auto","faster"):
        try:
            model=a.model or ("large-v3-turbo" if __import__('shutil').which("nvidia-smi") else "medium")
            result=run_faster(a.input,model,a.language)
        except Exception as e:
            errors.append(f"faster-whisper: {e}")
            if backend=="faster": raise
    if result is None:
        raise SystemExit("No transcription backend succeeded. Install mlx-whisper on Apple Silicon or faster-whisper. Details: "+" | ".join(errors))
    result["input"]=str(Path(a.input).resolve())
    if errors: result["fallback_notes"]=errors
    o=Path(a.output); o.parent.mkdir(parents=True,exist_ok=True); o.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(o),"backend":result["backend"],"language":result.get("language"),"segments":len(result.get("segments",[]))},indent=2,ensure_ascii=False))
if __name__=="__main__": main()
