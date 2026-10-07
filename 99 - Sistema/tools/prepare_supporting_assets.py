#!/usr/bin/env python3
"""Prepare supporting insertion assets for the edit pipeline.
- For images: create a simple MP4 hold clip so the renderer can use it as a timeline source.
- For videos: optionally just report metadata.
This tool is intentionally conservative and local-only.
"""
import argparse, json, subprocess
from pathlib import Path

IMG_EXT={'.png','.jpg','.jpeg','.webp','.bmp'}
VID_EXT={'.mp4','.mov','.m4v','.mkv','.avi','.webm'}

def ffprobe_json(path):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True)
    return json.loads(p.stdout)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('assets', nargs='+')
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--duration', type=float, default=3.0, help='default duration for image-derived clips')
    args=ap.parse_args()
    outdir=Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    results=[]
    for raw in args.assets:
        p=Path(raw)
        if not p.exists():
            results.append({'path':str(p), 'status':'missing'})
            continue
        ext=p.suffix.lower()
        if ext in IMG_EXT:
            out=outdir / f'{p.stem}.mp4'
            cmd=['ffmpeg','-y','-loop','1','-i',str(p),'-t',str(args.duration),'-vf','scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1','-r','30','-pix_fmt','yuv420p','-c:v','libx264','-an',str(out)]
            subprocess.run(cmd,check=True,capture_output=True,text=True)
            results.append({'path':str(p), 'prepared_path':str(out), 'kind':'image', 'status':'prepared', 'duration_s':args.duration})
        elif ext in VID_EXT:
            meta=ffprobe_json(p)
            results.append({'path':str(p), 'prepared_path':str(p), 'kind':'video', 'status':'ready', 'metadata':meta})
        else:
            results.append({'path':str(p), 'status':'unsupported'})
    print(json.dumps({'assets':results}, indent=2))

if __name__=='__main__':
    main()
