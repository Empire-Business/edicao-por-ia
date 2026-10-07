#!/usr/bin/env python3
import argparse, hashlib, json, subprocess
from pathlib import Path

def sha256(path, chunk=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()

def probe(path):
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(p.stdout)
    out = {
        "path": str(Path(path).resolve()),
        "sha256": sha256(path),
        "format": data.get("format", {}),
        "streams": data.get("streams", []),
    }
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output")
    args = ap.parse_args()
    data = probe(args.input)
    s = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        p = Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s+"\n", encoding="utf-8")
    else:
        print(s)
if __name__ == "__main__": main()
