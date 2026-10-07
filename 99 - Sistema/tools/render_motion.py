#!/usr/bin/env python3
"""Render trusted bundled JavaScript to transparent PNG frames, offline.
Requires Playwright + an installed Chromium. Never installs or downloads anything.
A frames.json manifest is written only after a complete successful render.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def render(spec_path: Path, outdir: Path, browser_executable: str|None=None, selected: list[int]|None=None) -> dict:
    from playwright.sync_api import sync_playwright
    spec_path=spec_path.resolve(strict=True)
    spec=json.loads(spec_path.read_text(encoding='utf-8'))
    if 'asset_data_uri' in spec: raise ValueError('Use local asset_path, not embedded/unreviewed data in the source spec')
    asset=None
    if spec.get('asset_path'):
        asset=(spec_path.parent/spec['asset_path']).resolve(strict=True)
        from PIL import Image
        if asset.stat().st_size>20*1024*1024: raise ValueError('Image too large; create a smaller working copy')
        with Image.open(asset) as im:
            if im.format not in ('PNG','JPEG','WEBP') or getattr(im,'n_frames',1)!=1: raise ValueError('Use a single PNG/JPEG/WebP image')
            im.verify()
            mime={'PNG':'png','JPEG':'jpeg','WEBP':'webp'}[im.format]
        spec['asset_data_uri']=f'data:image/{mime};base64,'+base64.b64encode(asset.read_bytes()).decode()
    source=ROOT/'motion/browser/motion.js'
    protected={spec_path,source.resolve()}
    if asset:protected.add(asset)
    outdir=outdir.resolve()
    if outdir.exists() or any(p==outdir or p.is_relative_to(outdir) for p in protected):
        raise ValueError('Output directory must be new and cannot contain inputs')
    errors=[]
    with sync_playwright() as pw:
        exe=browser_executable or shutil.which('chromium') or shutil.which('google-chrome')
        browser=pw.chromium.launch(headless=True,**({'executable_path':exe} if exe else {}))
        context=browser.new_context(device_scale_factor=1,locale='pt-BR',timezone_id='UTC',service_workers='block')
        context.route('**/*',lambda route:route.abort())
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:transparent"><main id="stage" style="line-height:0"></main></body></html>')
        page.add_script_tag(path=str(source))
        page.evaluate('(s)=>CVFMotion.validate(s)',spec)
        page.set_viewport_size({'width':spec['width'],'height':spec['height']})
        n=spec['duration_frames']
        frames=list(range(n)) if selected is None else sorted(set(selected))
        if not frames or any(type(i)!=int or not 0<=i<n for i in frames): raise ValueError('Frame outside motion duration')
        outdir.mkdir(parents=True,exist_ok=False)
        records=[]
        for i in frames:
            page.evaluate('''async ({s,i})=>{
                document.querySelector('#stage').innerHTML=CVFMotion.renderFrame(i,s);
                await document.fonts.ready;
                await Promise.all([...document.querySelectorAll('image')].map(el=>new Promise((ok,bad)=>{
                    const img=new Image(); img.onload=ok;img.onerror=()=>bad(Error('Image decode failed'));img.src=el.getAttribute('href');
                })));
            }''',{'s':spec,'i':i})
            p=outdir/f'{i:06d}.png'
            page.screenshot(path=str(p),omit_background=True,animations='disabled')
            records.append({'frame':i,'file':p.name,'sha256':sha(p)})
        if errors:raise RuntimeError('Browser errors: '+'; '.join(errors))
        report={'version':'1.0','engine':'javascript-svg-browser','engine_sha256':sha(source),
                'browser':browser.version,'spec_sha256':sha(spec_path),'asset_sha256':sha(asset) if asset else None,
                'child_id':spec['child_id'],'motion_id':spec['id'],'width':spec['width'],'height':spec['height'],
                'fps':spec['fps'],'duration_frames':n,'complete':selected is None,'mode':spec['mode'],
                'timebase':'local_frames','pattern':'%06d.png','files':records,'network_access':False}
        (outdir/'frames.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        context.close();browser.close()
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('spec',type=Path);ap.add_argument('--outdir',type=Path,required=True)
    ap.add_argument('--browser-executable');ap.add_argument('--frames',help='Comma-separated keyframes; preview only, not compositable')
    a=ap.parse_args()
    try:
        report=render(a.spec,a.outdir,a.browser_executable,[int(x) for x in a.frames.split(',')] if a.frames else None)
        print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
    except Exception as e:
        print(f'Motion render failed: {e}',file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()
