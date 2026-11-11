#!/usr/bin/env python3
"""Ad-motion pipeline (format "Anúncio com Motion"): job.json -> plan -> alpha motion overlay -> base video -> audio mix -> final.

AI-operated. Deterministic and local: Playwright renders the GSAP composition frame by frame (seek(t)), FFmpeg assembles.
Usage (from the engine root):
  python studio/ad-motion/kit/ad_motion.py --job jobs/<job> plan|track|frames T...|overlay [N]|base|audio|final|qa
The job folder must contain job.json (see studio/ad-motion/example/job.example.json) and analysis/transcript-*.json
produced by tools/transcribe.py (word timestamps). Sources are copies inside the factory (originals stay immutable).
"""
from __future__ import annotations
import argparse, json, math, re, shutil, subprocess, sys, wave
from pathlib import Path

KIT = Path(__file__).resolve().parent
ENGINE = KIT.parents[2]


def ff(*args, cwd=None):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, args)], check=True, cwd=cwd)


class Job:
    def __init__(self, path: Path):
        self.dir = path.resolve()
        self.cfg = json.loads((self.dir / 'job.json').read_text(encoding='utf-8'))
        self.W, self.H, self.FPS = self.cfg.get('canvas', [1080, 1920, 30])
        for sub in ('analysis', 'edit', 'motion/assets', 'renders', 'tmp', 'qa/frames', 'audio'):
            (self.dir / sub).mkdir(parents=True, exist_ok=True)

    def src(self, key):
        p = Path(self.cfg['sources'][key]['path'])
        return p if p.is_absolute() else (self.dir / p).resolve()

    def rotate(self, key):
        return self.cfg['sources'][key].get('rotate')   # 'ccw' when a vertical camera stored the clip landscape

    def j(self, rel, default=None):
        p = self.dir / rel
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default


# ---------------- plan: EDL + caption words ----------------
def fix_word(w, fixes):
    core = re.sub(r'[^\wÀ-ÿ]', '', w.strip(), flags=re.U).lower()
    if core in fixes:
        lead = re.match(r'^\W*', w.strip()).group(0); trail = re.search(r'\W*$', w.strip()).group(0)
        return lead + fixes[core] + trail
    return w.strip()


def _n(w):
    import unicodedata
    w = unicodedata.normalize('NFKD', w.lower()); return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if not unicodedata.combining(c)))


def apply_phrase_fixes(words, fixes):
    """Replace misheard multi-word phrases (e.g. 'a gente de A' -> 'agente de IA'), keeping timings."""
    for src, dst in fixes:
        frm = [_n(x) for x in src.split()]; to = dst.split(); i = 0
        while i <= len(words) - len(frm):
            if [_n(w['w']) for w in words[i:i + len(frm)]] == frm:
                trail = re.search(r'[.,?!:;]*$', words[i + len(frm) - 1]['w'].strip()).group(0)
                seg = words[i:i + len(frm)]; end = seg[-1]['e']
                new = [dict(seg[min(k, len(seg) - 1)], w=t) for k, t in enumerate(to)]
                new[-1]['w'] += trail; new[-1]['e'] = end
                words[i:i + len(frm)] = new; i += len(new)
            else: i += 1
    return words


def plan(job: Job):
    tr = {k: [w for s in job.j(v)['segments'] for w in s['words']] for k, v in job.cfg['transcripts'].items()}
    fixes = {k.lower(): v for k, v in job.cfg.get('word_fixes', {}).items()}
    manual = job.cfg.get('manual_words', {})
    segs, words, t = [], [], 0.0
    used = set()   # each source word goes into the captions once (a word can straddle two parts of a take)
    for seg in job.cfg['segments']:
        a, b = seg['in'], seg['out']; dur = b - a
        if segs and segs[-1]['id'] == seg['id']:
            segs[-1]['end'] = round(t + dur, 3); segs[-1]['parts'].append([seg.get('src'), a, b, round(t, 3)])
        else:
            segs.append({'id': seg['id'], 'scene': seg['scene'], 'type': seg['type'], 'props': seg.get('props', {}),
                         'start': round(t, 3), 'end': round(t + dur, 3), 'parts': [[seg.get('src'), a, b, round(t, 3)]]})
        if seg['type'] != 'text':
            pool = tr[seg['src']]; man = manual.get(seg['id'])
            covered = None
            if man and a <= man['window'][0] < b:     # words a transcriber skipped (e.g. a retake): spread over the speech window
                w0, w1 = man['window']; toks = man['text'].split(); L = sum(len(x) for x in toks); acc = w0
                for x in toks:
                    d = (w1 - w0) * len(x) / L; words.append({'w': x, 's': round(t + acc - a, 3), 'e': round(t + acc + d - a, 3)}); acc += d
                covered = w1
            for w in pool:
                if not (w['e'] > a + .08 and w['s'] < b - .05) or (covered and w['s'] < covered): continue
                key = (seg['src'], w['s'], w['e'], w['w'])
                if key in used: continue
                used.add(key)
                s, e = w['s'], w['e']
                if e - s > 1.0: s = e - .45                   # stretched word swallowed a pause/retake
                s = max(s, a); e = min(max(e, s + .12), b)
                txt = fix_word(w['w'], fixes)
                if not txt or txt.lower() in job.cfg.get('drop_words', []): continue
                if any(d['src'] == seg['src'] and abs(d['t'] - w['s']) < .02 and d.get('w', w['w']).strip().lower() == w['w'].strip().lower() for d in job.cfg.get('drop_at', [])): continue   # misheard filler at a known source time
                words.append({'w': txt, 's': round(t + s - a, 3), 'e': round(t + e - a, 3)})
        t += dur
    words.sort(key=lambda w: w['s'])
    words = apply_phrase_fixes(words, job.cfg.get('phrase_fixes', []))
    seg_of = lambda x: next((s for s in segs if s['start'] <= x < s['end'] + .01), None)
    for i, w in enumerate(words):
        nxt = words[i + 1] if i + 1 < len(words) else None
        w['segEnd'] = bool(nxt is None or seg_of(w['s']) is not seg_of(nxt['s']))
    P = {'fps': job.FPS, 'duration': round(t, 3), 'segs': segs, 'words': words,
         'panel': job.cfg.get('panel'), 'still': 'assets/still.jpg', 'thumbs': sorted(p.name for p in (job.dir / 'motion/assets/thumbs').glob('*.jpg'))}
    (job.dir / 'motion/plan.json').write_text(json.dumps(P, ensure_ascii=False, indent=1), encoding='utf-8')
    (job.dir / 'edit/edl.json').write_text(json.dumps({'segments': job.cfg['segments'], 'timeline': segs, 'duration': P['duration'],
        'format': job.cfg.get('format'), 'identity': job.cfg.get('identity'), 'canvas': [job.W, job.H, job.FPS]}, ensure_ascii=False, indent=1), encoding='utf-8')
    stage_assets(job)
    print('plan ok · duration', P['duration'], '· segments', len(segs), '· words', len(words))
    return P


def stage_assets(job: Job):
    """Copy composition + fonts + GSAP into the job so it is portable and reproducible."""
    a = job.dir / 'motion/assets'
    shutil.copy2(KIT / 'composition.html', job.dir / 'motion/composition.html')
    for f in ('manrope-variable.ttf', 'jetbrains-mono-variable.ttf', 'libre-baskerville-variable.ttf'):
        shutil.copy2(ENGINE / 'assets/fonts/portable' / f, a / f)
    shutil.copy2(ENGINE / 'studio/product-motion/kit/vendor/gsap.min.js', a / 'gsap.min.js')
    ident = job.cfg.get('identity_tokens')
    (job.dir / 'motion/identity.css').write_text(':root{' + ''.join(f'--{k}:{v};' for k, v in (ident or {}).items()) + '}\n', encoding='utf-8')


# ---------------- face framing (virtual camera) ----------------
def src_dims(job, key):
    o = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json',
                                   str(job.src(key))], capture_output=True, text=True, check=True).stdout)['streams'][0]
    w, h = o['width'], o['height']
    return (h, w) if job.rotate(key) else (w, h)


def track(job: Job, step=0.2):
    """Sample the face every `step` s per face segment and smooth it (Haar cascade; big faces only)."""
    import cv2, numpy as np
    from concurrent.futures import ThreadPoolExecutor
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    P = job.j('motion/plan.json'); out = {}
    for sg in P['segs']:
        if sg['type'] != 'face': continue
        key, a, b, _ = sg['parts'][0]; rot = 'transpose=2,' if job.rotate(key) == 'ccw' else ''
        def sample(t):
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(job.src(key)), '-vf', f'{rot}scale=540:960', '-frames:v', '1',
                                  '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
            img = np.frombuffer(raw, np.uint8).reshape(960, 540)
            f = list(casc.detectMultiScale(img, 1.1, 6, minSize=(110, 110)))
            if not f: return None
            x, y, w, h = max(f, key=lambda r: r[2] * r[3]); return ((x + w / 2) / 540, (y + h / 2) / 960)
        ts = list(np.arange(0, b - a + 1e-6, step))
        with ThreadPoolExecutor(8) as ex: pts = list(ex.map(lambda r: sample(a + r), ts))
        cx = np.array([p[0] if p else np.nan for p in pts]); cy = np.array([p[1] if p else np.nan for p in pts])
        if np.isnan(cx).all(): continue
        for arr in (cx, cy):
            idx = np.where(~np.isnan(arr))[0]; arr[:] = np.interp(np.arange(len(arr)), idx, arr[idx])
        k = np.array([1, 3, 1], float); k /= k.sum(); sm = lambda v: np.convolve(np.pad(v, 1, mode='edge'), k, mode='valid')
        out[sg['id']] = [[round(float(t), 2), round(float(x), 4), round(float(y), 4)] for t, x, y in zip(ts, sm(cx), sm(cy))]
    (job.dir / 'analysis/face_track.json').write_text(json.dumps(out), encoding='utf-8'); print('track ok', list(out))


def track_safe(job: Job):
    """Face measurement is an optimisation: without OpenCV (or on failure) faces stay center-framed."""
    try: track(job)
    except Exception as e: print('track ignorado (enquadramento central):', type(e).__name__, str(e)[:120])


def face_vf(job, key, zoom, trackpts=None, punch=False):
    sw, sh = src_dims(job, key); rot = 'transpose=2,' if job.rotate(key) == 'ccw' else ''
    cxs = [p[1] for p in trackpts] if trackpts else [.5]; cy = sorted(p[2] for p in trackpts)[len(trackpts) // 2] if trackpts else .35
    need = 1 / (2 * max(min(min(cxs), 1 - max(cxs)), .30)) + .01
    zoom = max(zoom, min(need, 1.7)); ar = job.W / job.H
    ch = int(min(sh, sw / ar) / zoom) // 2 * 2; cw = int(ch * ar) // 2 * 2
    if trackpts:
        xs = [min(max(p[1] * sw - cw / 2, 0), sw - cw) for p in trackpts]; ts = [p[0] for p in trackpts]
        expr = f'{xs[-1]:.1f}'
        for i in range(len(ts) - 2, -1, -1):
            expr = f'if(lt(t,{ts[i+1]:.2f}),{xs[i]:.1f}+({xs[i+1]-xs[i]:.1f})*(t-{ts[i]:.2f})/{ts[i+1]-ts[i]:.2f},{expr})'
        x = f"'{expr}'"
    else:
        x = str(int((sw - cw) / 2))
    y = int(min(max(cy * sh - .40 * ch, 0), sh - ch))
    vf = f'{rot}crop={cw}:{ch}:{x}:{y},scale={job.W}:{job.H}:flags=lanczos,setsar=1'
    if punch: vf += f",scale=w='trunc({job.W}*(1+0.10*max(0,1-t/0.5))/2)*2':h=-2:eval=frame:flags=bicubic,crop={job.W}:{job.H}"
    return vf


def base(job: Job):
    P = job.j('motion/plan.json'); TR = job.j('analysis/face_track.json', {}); parts = []; k = 0
    bg = job.cfg.get('background', '#0D0419').replace('#', '0x'); first_face = True
    for sg in P['segs']:
        for key, a, b, t0 in sg['parts']:
            f = job.dir / 'tmp' / f'base_{k:02d}.mp4'
            vid = next((x.get('video') for x in job.cfg['segments'] if x['id'] == sg['id'] and x.get('video')), None)
            if vid:   # real footage as the picture (e.g. an approved edit shown as an example); audio still comes from the EDL
                off = t0 - sg['start']   # offset of this part inside the segment
                ff('-ss', f"{vid['in'] + off:.3f}", '-i', job.src(vid['src']), '-t', f'{b-a:.3f}', '-an', '-vf',
                   f'scale={job.W}:{job.H}:force_original_aspect_ratio=increase,crop={job.W}:{job.H},fps={job.FPS},format=yuv420p',
                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', f)
            elif sg['type'] == 'face':
                tr = TR.get(sg['id'])
                if tr and job.cfg.get('framing', 'static') == 'static':   # median face position, no panning
                    xs = sorted(p[1] for p in tr); ys = sorted(p[2] for p in tr); tr = [[0, xs[len(xs) // 2], ys[len(ys) // 2]], [b - a, xs[len(xs) // 2], ys[len(ys) // 2]]]
                vf = face_vf(job, key, 1.30 if k % 2 == 0 else 1.40, tr, punch=first_face and job.cfg.get('punch_in_first_face', True))
                first_face = False
                ff('-ss', f'{a:.3f}', '-i', job.src(key), '-t', f'{b-a:.3f}', '-an', '-vf', vf + f',fps={job.FPS},eq=contrast=1.04:saturation=1.06,format=yuv420p',
                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', f)
            else:
                ff('-f', 'lavfi', '-i', f'color=c={bg}:s={job.W}x{job.H}:r={job.FPS}:d={b-a:.3f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', f)
            parts.append(f); k += 1
    lst = job.dir / 'tmp/base.txt'; lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
    ff('-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', job.dir / 'renders/base.mp4'); print('base ok')


def still_and_thumbs(job: Job):
    """Preview still (approved, natural frame) + gallery thumbnails from the raw recording."""
    c = job.cfg.get('stills', {}); a = job.dir / 'motion/assets'; (a / 'thumbs').mkdir(exist_ok=True)
    if 'preview' in c:
        key, t = c['preview']['src'], c['preview']['t']
        ff('-ss', t, '-i', job.src(key), '-vf', face_vf(job, key, 1.25), '-frames:v', 1, '-q:v', 3, a / 'still.jpg')
    (a / 'roll').mkdir(exist_ok=True)
    for i, r in enumerate(c.get('roll', [])):   # camera-roll squares: vary source (outfits), time and crop (close/medium/wide)
        sw, sh = src_dims(job, r['src']); side = {'close': .44, 'medium': .70, 'wide': 1.0}[r.get('crop', 'medium')] * sw
        x = (sw - side) / 2 * (1.1 if r.get('crop') == 'close' else 1); y = sh * {'close': .21, 'medium': .18, 'wide': .13}[r.get('crop', 'medium')]
        rot = 'transpose=2,' if job.rotate(r['src']) == 'ccw' else ''
        ff('-ss', r['t'], '-i', job.src(r['src']), '-vf', f'{rot}crop={int(side)}:{int(side)}:{int(x)}:{int(y)},scale=300:300', '-frames:v', 1, '-q:v', 4, a / 'roll' / f'r{i+1:02d}.jpg')
    for i, t in enumerate(c.get('thumbs', {}).get('times', [])):
        key = c['thumbs']['src']
        ff('-ss', t, '-i', job.src(key), '-vf', face_vf(job, key, 1.3) + ',scale=240:426', '-frames:v', 1, '-q:v', 4, a / 'thumbs' / f't{i+1:02d}.jpg')
    print('stills ok')


# ---------------- motion overlay (parallel browsers) ----------------
def _browser(job_dir):
    from playwright.sync_api import sync_playwright
    job = Job(Path(job_dir)); P = job.j('motion/plan.json')
    pw = sync_playwright().start()
    b = pw.chromium.launch(args=['--allow-file-access-from-files', '--disable-gpu', '--use-angle=swiftshader', '--disable-dev-shm-usage'])
    pg = b.new_page(viewport={'width': job.W, 'height': job.H}, device_scale_factor=1)
    pg.add_init_script('window.PLAN=' + json.dumps(P, ensure_ascii=False) + ';')
    pg.goto((job.dir / 'motion/composition.html').as_uri()); pg.evaluate('window.READY'); pg.wait_for_timeout(300)
    return pw, b, pg, P, job


def _shot(pg, t):
    for tries in range(6):          # software compositor can transiently fail on heavy 3D/filter frames
        try:
            pg.evaluate(f'seek({t})'); return pg.screenshot(omit_background=True, type='png', timeout=20000)
        except Exception:
            if tries == 5: raise
            pg.wait_for_timeout(300 * (tries + 1))


def _chunk(args):
    job_dir, i0, i1, k = args
    pw, b, pg, P, job = _browser(job_dir); out = job.dir / 'tmp' / f'ov_{k:02d}.mov'
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(job.FPS), '-c:v', 'png', '-i', '-',
                          '-c:v', 'qtrle', '-pix_fmt', 'argb', str(out)], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(_shot(pg, i / job.FPS))
    p.stdin.close(); p.wait()
    if k == 0: (job.dir / 'motion/sfx.json').write_text(json.dumps(pg.evaluate('window.SFX')))
    b.close(); pw.stop(); return str(out)


def overlay(job: Job, workers=5):
    from concurrent.futures import ProcessPoolExecutor
    P = job.j('motion/plan.json'); n = int(math.ceil(P['duration'] * job.FPS)); step = math.ceil(n / workers)
    jobs = [(str(job.dir), i, min(n, i + step), k) for k, i in enumerate(range(0, n, step))]
    with ProcessPoolExecutor(workers) as ex: outs = list(ex.map(_chunk, jobs))
    lst = job.dir / 'tmp/ov.txt'; lst.write_text(''.join("file '" + Path(o).as_posix() + "'\n" for o in outs))
    ff('-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', job.dir / 'renders/overlay.mov'); print('overlay ok', n, 'frames')


def frames(job: Job, times):
    pw, b, pg, P, _ = _browser(job.dir)
    for t in times: (job.dir / 'qa/frames' / f'ov_{t:06.2f}.png').write_bytes(_shot(pg, t))
    (job.dir / 'motion/sfx.json').write_text(json.dumps(pg.evaluate('window.SFX'))); b.close(); pw.stop(); print('frames ok')


# ---------------- audio (local cleanup + sparse SFX + music bed) ----------------
LIGHT = 'highpass=f=75,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150:makeup=2,loudnorm=I=-16:TP=-2:LRA=7'


def deepfilter():
    """Local DeepFilterNet runtime prepared by setup (.factory/runtimes/deepfilter) or on PATH."""
    p = ENGINE / '.factory/runtimes/deepfilter' / ('deep-filter.exe' if sys.platform == 'win32' else 'deep-filter')
    return str(p) if p.is_file() else shutil.which('deep-filter')

def audio(job: Job):
    import numpy as np
    SR = 48000; P = job.j('motion/plan.json'); DUR = P['duration']; N = int(DUR * SR) + SR; A = job.dir / 'audio'
    models = A / 'models'; models.mkdir(exist_ok=True)
    rn = job.cfg.get('rnnoise_model')       # optional local RNNoise model file (e.g. cb.rnnn); ffmpeg runs from its folder
    if rn: shutil.copy2(Path(rn) if Path(rn).is_absolute() else job.dir / rn, models / 'model.rnnn')
    chain = 'highpass=f=80,lowpass=f=14000,' + ('arnndn=m=model.rnnn:mix=0.9,' if rn else '') + 'afftdn=nf=-40,' \
            'equalizer=f=220:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,loudnorm=I=-16:TP=-2:LRA=7'
    out = np.zeros(N, np.float32); fade = int(.025 * SR); clean = {}   # 25 ms edge fades: no clicks
    for sg in P['segs']:
        for key, a, b, t0 in sg['parts']:
            if not key: continue
            if key not in clean:
                lo = min(p[1] for s in P['segs'] for p in s['parts'] if p[0] == key) - 1; hi = max(p[2] for s in P['segs'] for p in s['parts'] if p[0] == key) + 1
                lo = max(lo, 0); dur = hi - lo; df = deepfilter()
                if df:   # local DeepFilterNet: -6 dB headroom avoids clipping, pad then trim back to the exact duration (sync)
                    w = job.dir / 'tmp' / f'{key}_win.wav'; o = job.dir / 'tmp' / 'df'; o.mkdir(exist_ok=True)
                    ff('-ss', lo, '-t', dur, '-i', job.src(key), '-vn', '-ac', 1, '-ar', SR, '-af', 'volume=-6dB,apad=pad_dur=0.25', '-c:a', 'pcm_s16le', w)
                    subprocess.run([df, '-D', '-o', str(o), str(w)], check=True, capture_output=True)
                    ff('-i', o / w.name, '-af', f'apad,atrim=duration={dur:.3f},' + LIGHT, '-ar', SR, '-ac', 1, A / f'{key}_clean.wav')
                else:
                    ff('-ss', lo, '-t', dur, '-i', job.src(key), '-ac', 1, '-ar', SR, '-af', chain, A / f'{key}_clean.wav', cwd=models)
                with wave.open(str(A / f'{key}_clean.wav')) as w: clean[key] = (np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, lo)
            x, off = clean[key]; seg = x[int((a - off) * SR):int((b - off) * SR)].copy()
            r = np.linspace(0, 1, fade); seg[:fade] *= r; seg[-fade:] *= r[::-1]; i = int(t0 * SR); out[i:i + len(seg)] += seg
    _write(A / 'voice.wav', out, SR)
    _write(A / 'sfx.wav', _sfx(job, N, SR), SR)
    music = job.cfg.get('music')
    vol = job.cfg.get('music_volume', .42)
    inputs = ['-i', A / 'voice.wav', '-i', A / 'sfx.wav']
    if music:
        inputs += ['-stream_loop', '-1', '-i', job.dir / music]   # loop when the ad is longer than the track
        fc = (f'[2:a]aresample={SR},aformat=channel_layouts=stereo,volume={vol},afade=t=out:st={DUR-2.2:.2f}:d=2.2[m];'
              '[0:a]asplit=2[v][sc];[m][sc]sidechaincompress=threshold=0.025:ratio=6:attack=25:release=350[md];'
              '[v]aformat=channel_layouts=stereo[vs];[1:a]aformat=channel_layouts=stereo[ss];[vs][ss][md]amix=inputs=3:normalize=0:weights=1 0.8 1[mx];')
    else:
        fc = '[0:a]aformat=channel_layouts=stereo[vs];[1:a]aformat=channel_layouts=stereo[ss];[vs][ss]amix=inputs=2:normalize=0[mx];'
    ff(*inputs, '-filter_complex', fc + f'[mx]loudnorm=I=-14:TP=-1.2:LRA=9,atrim=0:{DUR:.3f}', '-ar', SR, '-ac', 2, A / 'mix.wav'); print('audio ok')


def _write(p, x, SR):
    import numpy as np
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(p), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())


def _sfx(job, N, SR):
    """Sparse, synthesized cues only at key moments (whoosh on big scene changes, pop/ding/click), never on every title."""
    import numpy as np
    rng = np.random.default_rng(5); out = np.zeros(N, np.float32)
    env = lambda n, a, d: np.minimum(1, (np.arange(n) / SR) / a) * np.exp(-(np.arange(n) / SR) / d)
    def lp(x, k):
        y = np.empty_like(x); acc = 0.0
        for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
        return y
    def whoosh(d=.55):
        n = int(d * SR); x = rng.standard_normal(n).astype(np.float32); t = np.arange(n) / n
        lo, hi = lp(x, .015), lp(x, .12); return ((lo + (hi - lo) * np.sin(np.pi * t) ** 2) * np.sin(np.pi * t) ** 1.5 * .28).astype(np.float32)
    def tone(f0, f1, d, dec, g):
        n = int(d * SR); t = np.arange(n) / SR; f = f0 * np.exp(-t * 18) + f1
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, dec) * g).astype(np.float32)
    def ding():
        n = int(.7 * SR); t = np.arange(n) / SR
        return ((np.sin(2 * np.pi * 1318.5 * t) * .6 + np.sin(2 * np.pi * 1975.5 * t) * .25) * env(n, .002, .18) * .07).astype(np.float32)
    def tick():
        n = int(.03 * SR); return (lp((rng.standard_normal(n) * env(n, .0003, .004)).astype(np.float32), .5) * .06).astype(np.float32)
    bank = {'whoosh': whoosh(), 'pop': tone(520, 260, .12, .03, .11), 'click': tone(1800, 0, .05, .008, .1), 'ding': ding()}
    gap = {'whoosh': 3.0, 'pop': 2.0, 'click': 1.0, 'ding': 3.0}; last = {}
    for e in sorted(json.loads((job.dir / 'motion/sfx.json').read_text()), key=lambda e: e['t']):
        ty, t = e['type'], e['t']
        if ty == 'type':
            k = t
            while k < t + e.get('dur', 1):
                s = tick(); i = int(k * SR); out[i:i + len(s)] += s[:max(0, N - i)]; k += .055 + rng.random() * .05
            continue
        if ty not in bank or t - last.get(ty, -9) < gap[ty]: continue
        last[ty] = t; s = bank[ty]; i = int(max(0, t - (.18 if ty == 'whoosh' else 0)) * SR); out[i:i + len(s)] += s[:max(0, N - i)]
    return out


def final(job: Job, out=None):
    out = Path(out) if out else job.dir / 'renders/final.mp4'
    ff('-i', job.dir / 'renders/base.mp4', '-i', job.dir / 'renders/overlay.mov', '-i', job.dir / 'audio/mix.wav', '-filter_complex',
       '[0:v][1:v]overlay=format=auto:shortest=1,format=yuv420p[v]', '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', 17,
       '-profile:v', 'high', '-r', job.FPS, '-c:a', 'aac', '-b:a', '256k', '-ac', 2, '-movflags', '+faststart', '-shortest', out)
    print('final ok', out)


def qa(job: Job, video=None):
    """Mechanical QA: frozen stretches (look like a stalled player), loudness, full decode."""
    v = Path(video) if video else job.dir / 'renders/final.mp4'
    fr = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(v), '-vf', 'freezedetect=n=0.0005:d=0.4', '-map', '0:v', '-f', 'null', '-'],
                        capture_output=True, text=True).stderr.count('freeze_start')
    lufs = re.findall(r'I:\s+(-?[\d.]+) LUFS', subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(v), '-af', 'ebur128', '-f', 'null', '-'],
                                                            capture_output=True, text=True).stderr)
    dec = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(v), '-f', 'null', '-'], capture_output=True, text=True).stderr.strip()
    rep = {'video': v.name, 'frozen_stretches_over_0_4s': fr, 'integrated_lufs': float(lufs[-1]) if lufs else None, 'decode_errors': dec[:300]}
    (job.dir / 'qa/qa.json').write_text(json.dumps(rep, indent=1)); print(rep)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--job', required=True); ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    a = ap.parse_args(); job = Job(Path(a.job))
    {'plan': lambda: plan(job), 'stills': lambda: still_and_thumbs(job), 'track': lambda: track_safe(job), 'base': lambda: base(job),
     'overlay': lambda: overlay(job, int(a.args[0]) if a.args else 5), 'frames': lambda: frames(job, [float(x) for x in a.args]),
     'audio': lambda: audio(job), 'final': lambda: final(job, a.args[0] if a.args else None), 'qa': lambda: qa(job, a.args[0] if a.args else None)}[a.cmd]()
