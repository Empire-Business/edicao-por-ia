#!/usr/bin/env python3
"""Diagnostic default now requires speech readiness. --task cuts requests only cutting."""
import argparse, json
from factory_doctor import collect
from factory_common import ROOT
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(ROOT));p.add_argument('--task',choices=['cuts','speech','motion'],default='speech');p.add_argument('--smoke',action='store_true');a=p.parse_args()
    r=collect(a.root,a.smoke);cap={'cuts':'cuts','speech':'speech_editing','motion':'javascript_motion'}[a.task]
    r['required_ok']=r['capabilities'][cap]['available'];r['requested_task']=a.task
    r['transcription_backend_available']=bool(r['modules']['mlx_whisper'] or r['modules']['faster_whisper'])
    print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['required_ok'] else 1)
