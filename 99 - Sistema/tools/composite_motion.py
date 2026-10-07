#!/usr/bin/env python3
"""Composite complete PNG motion layers onto a locked clean master.
Timeline: integer clean-master frames; end is exclusive. Preserve the base audio.
Reject stale base/EDL hashes, cross-child assets, mismatched frame geometry and overwrites.
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys
from fractions import Fraction
from pathlib import Path
from render_motion import sha

def probe(path: Path) -> dict:
    return json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True).stdout)

def checked_file(record:dict,parent:Path)->Path:
    p=(parent/record['path']).resolve(strict=True)
    if not p.is_file() or sha(p)!=record['sha256']:raise ValueError('Stale or invalid file hash: '+str(p))
    return p

def build_command(plan_path:Path,output:Path)->tuple[list[str],dict]:
    plan_path=plan_path.resolve(strict=True);parent=plan_path.parent
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    if plan.get('timebase')!='clean_master_frames':raise ValueError('Expected clean_master_frames, not source seconds')
    child=plan.get('child_id')
    if not isinstance(child,str) or not child:raise ValueError('child_id required')
    base=checked_file(plan['base'],parent);edl=checked_file(plan['edl'],parent)
    meta=probe(base);video=next(s for s in meta['streams'] if s['codec_type']=='video')
    fps=float(Fraction(video['avg_frame_rate']))
    r_fps=float(Fraction(video['r_frame_rate']))
    if abs(fps-r_fps)>1e-5:raise ValueError('Normalize variable-rate media to a locked CFR master first')
    width,height=video['width'],video['height']
    if width%2 or height%2:raise ValueError('Use even dimensions for H.264 output')
    if (plan['width'],plan['height'])!=(width,height) or not math.isclose(plan['fps'],fps,abs_tol=1e-6):raise ValueError('Plan/master geometry mismatch')
    count=int(video.get('nb_frames') or round(float(video.get('duration') or meta['format']['duration'])*fps))
    layers=plan.get('layers',[])
    if not layers or len(layers)>24:raise ValueError('Provide 1..24 motion layers; batch large projects')
    output=output.resolve()
    if output.suffix.lower()!='.mp4':raise ValueError('Output must be a new .mp4')
    inputs={base,edl,plan_path};cmd=['ffmpeg','-n','-hide_banner','-loglevel','error','-i',str(base)]
    filters=['[0:v]setpts=PTS-STARTPTS,format=yuv420p[base0]'];last='base0'
    for index,layer in enumerate(layers,1):
        if layer.get('child_id')!=child:raise ValueError('Cross-child motion layer rejected')
        start=layer['start_frame']
        if type(start)!=int or start<0:raise ValueError('start_frame must be a nonnegative integer')
        if not layer.get('reason') or not layer.get('speech_cue'):raise ValueError('Placement needs a reason and speech cue')
        mp=checked_file(layer['frames'],parent);inputs.add(mp)
        manifest=json.loads(mp.read_text())
        if manifest.get('complete') is not True:raise ValueError('Keyframe-only preview is not a complete animation')
        if manifest.get('child_id')!=child:raise ValueError('Frames belong to a different child')
        n=manifest['duration_frames']
        if type(n)!=int or n<=0 or start+n>count:raise ValueError('Motion extends beyond the clean master')
        if (manifest['width'],manifest['height'])!=(width,height) or not math.isclose(manifest['fps'],fps,abs_tol=1e-6):raise ValueError('Motion/master dimensions or fps differ')
        files=manifest.get('files',[])
        if len(files)!=n:raise ValueError('Missing motion frames')
        for i,f in enumerate(files):
            if f.get('frame')!=i or f.get('file')!=f'{i:06d}.png':raise ValueError('Invalid frame numbering/path')
            fp=mp.parent/f['file'];inputs.add(fp.resolve())
            if not fp.is_file() or sha(fp)!=f['sha256']:raise ValueError('Missing/modified PNG frame')
        cmd+=['-framerate',str(fps),'-start_number','0','-i',str(mp.parent/'%06d.png')]
        filters.append(f'[{index}:v]setpts=PTS-STARTPTS+{start}/{fps}/TB,format=rgba[m{index}]')
        filters.append(f'[{last}][m{index}]overlay=eof_action=pass:repeatlast=0:format=yuv420:enable=\'gte(n,{start})*lt(n,{start+n})\'[v{index}]')
        last=f'v{index}'
    if output.exists() or output in inputs:raise ValueError('Output exists or aliases an input; use a new path')
    # No shortest flag: a short layer must not truncate the master. Audio stays from base.
    cmd+=['-filter_complex',';'.join(filters),'-map',f'[{last}]','-map','0:a?','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r',str(fps),'-fps_mode','cfr','-c:a','copy','-movflags','+faststart',str(output)]
    return cmd,{'base':str(base),'base_sha256':sha(base),'edl_sha256':sha(edl),'layers':len(layers),'fps':fps,'expected_frames':count,'output':str(output)}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('plan',type=Path)
    ap.add_argument('--output',required=True,type=Path);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
    try:
        cmd,report=build_command(a.plan,a.output)
        if a.dry_run:print(json.dumps({'command':cmd,'validation':report},indent=2));return
        a.output.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(cmd,check=True)
        print(json.dumps(report,indent=2))
    except Exception as e:print(f'Motion composition failed: {e}',file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()
