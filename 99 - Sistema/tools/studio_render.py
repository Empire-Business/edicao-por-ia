#!/usr/bin/env python3
"""Offline renderer for reviewed HTML/Canvas using window.seek(seconds).
No installation, model call or real HTTP server. All resources are explicitly hashed.
Not a sandbox for hostile JavaScript. Review the bundle before approving its hash.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, math, shutil, sys
from pathlib import Path
from PIL import Image
from factory_common import ROOT, read_json, fingerprint, sha, atomic_json
ORIGIN='https://cvf-studio.invalid'

def integer(v,name,lo=0,hi=18000):
    if type(v)!=int or not lo<=v<=hi: raise ValueError(f'{name}: integer {lo}..{hi} required')
    return v

def check_file(r,parent):
    try:p=(parent/r['path']).resolve(strict=True)
    except OSError as e:raise ValueError('Missing input: '+str(r.get('path'))) from e
    if not p.is_file() or sha(p)!=r.get('sha256'): raise ValueError('Missing/stale input: '+str(p))
    if p.name.startswith('.env') or p.suffix in ('.pem','.key') or any(x in p.parts for x in ('.ssh','.aws')):
        raise ValueError('Secrets are not studio assets')
    return p

def inspect(spec_path):
    path=Path(spec_path).resolve(strict=True); spec=read_json(path)
    if spec.get('schema_version')!=1: raise ValueError('schema_version must be 1')
    for key in ('id','child_id'):
        if not isinstance(spec.get(key),str) or not spec[key].strip(): raise ValueError(key+' required')
    w=integer(spec['width'],'width',64,3840); h=integer(spec['height'],'height',64,3840)
    fps=integer(spec['fps'],'fps',1,120); n=integer(spec['duration_frames'],'duration_frames',1,18000)
    if w*h>8_400_000: raise ValueError('Oversized render; split the job')
    if spec.get('mode') not in ('overlay','full_frame'):raise ValueError('mode: overlay or full_frame')
    entry=check_file(spec['entry'],path.parent)
    if entry.suffix.lower() not in ('.html','.htm') or entry.stat().st_size>2_000_000:raise ValueError('Use reviewed HTML up to 2MB')
    resources={ORIGIN+'/index.html':('text/html',entry.read_bytes())}
    protect=[path,entry,ROOT/'studio/lib/motion.js']; assets=[]; ids=set()
    for a in spec.get('assets',[]):
        aid=a['id']
        if not isinstance(aid,str) or not aid or any(x not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. ' for x in aid) or ' ' in aid or aid in ids:raise ValueError('Unique simple asset id required')
        ids.add(aid); p=check_file(a,path.parent)
        mime=a['mime']
        allowed={'image/png','image/jpeg','image/webp','font/woff2','font/woff'}
        if mime not in allowed or p.stat().st_size>25_000_000:raise ValueError('Use local raster images/fonts up to 25MB; no active SVG, script, or video assets')
        protect.append(p); assets.append({'id':aid,'sha256':sha(p),'mime':mime})
        resources[ORIGIN+'/assets/'+aid]=(mime,p.read_bytes())
    cuts=spec.get('cut_frames',[])
    if any(type(c)!=int or not 0<c<n for c in cuts) or cuts!=sorted(set(cuts)):raise ValueError('cut_frames must increase within duration')
    code_sha=fingerprint({'spec':spec,'core_sha256':sha(ROOT/'studio/lib/motion.js'),'assets':assets})
    return spec,resources,protect,{'bundle_sha256':code_sha,'width':w,'height':h,'fps':fps,'duration_frames':n,'assets':assets,'network_access':False}

def sample_times(frame,fps,n,cuts,subframes=1,shutter=.5):
    integer(frame,'frame',0,n-1); integer(subframes,'subframes',1,8)
    if not isinstance(shutter,(int,float)) or isinstance(shutter,bool) or not math.isfinite(shutter) or not 0<=shutter<=1:raise ValueError('shutter must be 0..1')
    if subframes==1:return [frame/fps]
    low=max([0]+[c for c in cuts if c<=frame])/fps
    high=min([n]+[c for c in cuts if c>frame])/fps
    return [max(low,min(high-1e-9,(frame+((j+.5)/subframes-.5)*shutter)/fps)) for j in range(subframes)]

def blend(images):
    if len(images)==1:return images[0]
    # Premultiplied alpha average in sRGB, not physically correct linear-light exposure.
    import numpy as np
    arr=np.stack([np.asarray(im.convert('RGBA'),dtype=np.float32)/255 for im in images])
    alpha=arr[...,3:4]; a=alpha.mean(axis=0); rgb=(arr[...,:3]*alpha).mean(axis=0)
    rgb=np.divide(rgb,a,out=np.zeros_like(rgb),where=a>1e-8)
    return Image.fromarray(np.rint(np.clip(np.concatenate([rgb,a],axis=-1),0,1)*255).astype('uint8'),'RGBA')

def rawhash(image):return hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()

class BrowserSession:
    def __init__(self,spec,resources,browser_executable=None):
        self.spec=spec;self.resources=resources;self.exe=browser_executable;self.blocked=[];self.errors=[]
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.pw=sync_playwright().start(); self.browser=None; self.context=None
        try:
            exe=self.exe or shutil.which('chromium') or shutil.which('google-chrome')
            self.browser=self.pw.chromium.launch(headless=True,**({'executable_path':exe} if exe else {}))
            s=self.spec
            self.context=self.browser.new_context(viewport={'width':s['width'],'height':s['height']},device_scale_factor=1,locale='pt-BR',timezone_id='UTC',service_workers='block',accept_downloads=False)
            def resource(route):
                if route.request.url in self.resources:
                    mime,body=self.resources[route.request.url];route.fulfill(status=200,content_type=mime,body=body,headers={'access-control-allow-origin':'*'})
                else:self.blocked.append(route.request.url);route.abort()
            self.context.route('**/*',resource)
            spec_js=json.dumps({k:s[k] for k in ('width','height','fps','duration_frames','mode')})
            guard="""
                window.__STUDIO_RENDER__=true;
                for(const k of ['setTimeout','setInterval','requestAnimationFrame'])window[k]=()=>{throw Error(k+' forbidden in seek render');};
                Math.random=()=>{throw Error('Use per-scene seeded noise, not Math.random');};
                Date.now=()=>{throw Error('Use timeline time, not Date.now');};
            """
            asset_data={url.split('/assets/',1)[1]:'data:'+mime+';base64,'+base64.b64encode(body).decode() for url,(mime,body) in self.resources.items() if '/assets/' in url}
            asset_js='window.__STUDIO_ASSETS__=Object.freeze('+json.dumps(asset_data)+');window.studioAsset=(id)=>{const a=__STUDIO_ASSETS__[id];if(!a)throw Error("Unknown declared asset: "+id);return a;};'
            self.context.add_init_script(script=guard+'\nwindow.__STUDIO_SPEC__=Object.freeze('+spec_js+');\n'+asset_js+'\n'+(ROOT/'studio/lib/motion.js').read_text())
            self.page=self.context.new_page();self.page.set_default_timeout(15000)
            self.page.on('pageerror',lambda e:self.errors.append(str(e)))
            self.page.goto('about:blank')
            html=self.resources[ORIGIN+'/index.html'][1].decode('utf-8')
            # No navigation to a real/synthetic external host. Asset URLs are intercepted.
            self.page.set_content('<base href="'+ORIGIN+'/index.html">'+html,wait_until='load')
            self.page.evaluate('''async()=>{await document.fonts.ready;
              await Promise.all([...document.images].map(im=>im.decode()));
              if(window.__STUDIO_READY__)await window.__STUDIO_READY__;
              if(typeof window.seek!=='function')throw Error('window.seek(t) missing');
              if(document.getAnimations().length)throw Error('CSS/Web Animations active; use seek time');
            }''')
            self.check();return self
        except BaseException:
            self.__exit__(None,None,None);raise
    def check(self):
        if self.errors or self.blocked:raise ValueError('Browser failure or unapproved resource: '+repr(self.errors+self.blocked))
    def frame(self,t):
        value=self.page.evaluate('''async(t)=>{
            await window.seek(t);
            if(document.getAnimations().length)throw Error('Uncontrolled animation');
            const c=document.querySelector('canvas');
            if(c && (c.width!==__STUDIO_SPEC__.width || c.height!==__STUDIO_SPEC__.height))throw Error('Canvas geometry differs from spec');
            return c?c.toDataURL('image/png'):null;
        }''',float(t))
        self.check()
        # Canvas captures pixels, independent of screenshot timing. DOM fallback uses viewport.
        data=base64.b64decode(value.split(',',1)[1]) if value else self.page.screenshot(omit_background=True)
        image=Image.open(io.BytesIO(data)).convert('RGBA');image.load();return image
    def __exit__(self,*args):
        if self.context:self.context.close()
        if self.browser:self.browser.close()
        self.pw.stop()

def determinism(spec_path,approval,browser_executable=None):
    spec,resources,protect,report=inspect(spec_path)
    if approval!=report['bundle_sha256']:raise ValueError('Review and approve current bundle SHA-256 first')
    n=spec['duration_frames']; points=sorted(set([0,n//3,n//2,n-1]))
    expected={};checks={}
    with BrowserSession(spec,resources,browser_executable) as b:
        for i in points:expected[i]=rawhash(b.frame(i/spec['fps']))
        for i in reversed(points):checks['reverse_'+str(i)]=rawhash(b.frame(i/spec['fps']))==expected[i]
        for i in points:checks['repeat_'+str(i)]=rawhash(b.frame(i/spec['fps']))==expected[i]
        browser=b.browser.version
    with BrowserSession(spec,resources,browser_executable) as b:
        for i in points:checks['fresh_context_'+str(i)]=rawhash(b.frame(i/spec['fps']))==expected[i]
    return {**report,'checks':checks,'ok':all(checks.values()),'browser':browser,'hash_basis':'decoded RGBA pixels, not MP4 container',
      'limits':'Sampled repeatability on this browser/OS. Not proof for every frame or across machines; not a loop-continuity test.'}

def render(spec_path,outdir,approval,selected=None,subframes=1,shutter=.5,frame_budget=1800,browser_executable=None):
    spec,resources,protect,report=inspect(spec_path)
    if approval!=report['bundle_sha256']:raise ValueError('Review and approve current bundle SHA-256 first')
    n=spec['duration_frames'];frames=list(range(n)) if selected is None else sorted(set(selected))
    if not frames:raise ValueError('No frames selected')
    for i in frames:integer(i,'selected frame',0,n-1)
    integer(frame_budget,'frame_budget',1,144000);integer(subframes,'subframes',1,8)
    if len(frames)*subframes>frame_budget:raise ValueError('Render exceeds authorized frame sample budget; preview/split or explicitly raise budget')
    outdir=Path(outdir).resolve()
    if outdir.exists() or any(p.resolve().is_relative_to(outdir) for p in protect):raise ValueError('Output must be a NEW directory outside inputs')
    outdir.mkdir(parents=True,exist_ok=False);records=[]
    with BrowserSession(spec,resources,browser_executable) as b:
        for i in frames:
            times=sample_times(i,spec['fps'],n,spec.get('cut_frames',[]),subframes,shutter)
            image=blend([b.frame(t) for t in times]);p=outdir/f'{i:06d}.png';image.save(p)
            records.append({'frame':i,'file':p.name,'sha256':sha(p),'rgba_sha256':rawhash(image)})
        b.check()
        manifest={**report,'version':'1.0','engine':'html-canvas-seek','browser':b.browser.version,
            'spec_sha256':sha(spec_path),'motion_id':spec['id'],'child_id':spec['child_id'],'mode':spec['mode'],
            'timebase':'local_frames','complete':selected is None,'pattern':'%06d.png','files':records,
            'subframes':subframes,'shutter':shutter,'sample_count':len(frames)*subframes}
        atomic_json(outdir/'frames.json',manifest)
    return manifest

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec',type=Path)
    p.add_argument('--outdir',type=Path);p.add_argument('--approve-bundle');p.add_argument('--inspect',action='store_true');p.add_argument('--check-determinism',action='store_true')
    p.add_argument('--frames');p.add_argument('--subframes',type=int,default=1);p.add_argument('--shutter',type=float,default=.5);p.add_argument('--frame-budget',type=int,default=1800);p.add_argument('--browser-executable')
    a=p.parse_args(argv)
    try:
        if a.inspect:out=inspect(a.spec)[3]
        elif a.check_determinism:out=determinism(a.spec,a.approve_bundle,a.browser_executable)
        else:
            if a.outdir is None:raise ValueError('--outdir required')
            out=render(a.spec,a.outdir,a.approve_bundle,[int(x) for x in a.frames.split(',')] if a.frames else None,a.subframes,a.shutter,a.frame_budget,a.browser_executable)
        print(json.dumps({k:v for k,v in out.items() if k!='files'},ensure_ascii=False,indent=2));return 0 if out.get('ok',True) else 1
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
