"""Final compositor: presenter base (renders/base-1440.mp4) + real B-roll + overlay PNGs -> 1080x1920 30 fps.
Adapted from video-4cb9c29dec82 (v3 fixed face centre). New: per-video source crop, 'cover' = blurred fill + sharp band.
usage: composite.py OVERLAY_DIR OUT.mp4 [--frames 1,2,3 --stills DIR] [--audio WAV]"""
import json, os, subprocess, argparse
import numpy as np, cv2
import facefix
V = os.path.dirname(os.path.abspath(__file__)); J = os.path.dirname(V)
lay = json.load(open(os.path.join(V, 'layout.json'), encoding='utf-8'))
FPS = lay['fps']; N = round(lay['duration'] * FPS); W, H, SEAM = 1080, 1920, 960
BW, BH = 1440, 2560
FIX = tuple(json.load(open(os.path.join(V, 'face_track.json')))['median'])   # ONE fixed centre (client 20k feedback)

ap = argparse.ArgumentParser(); ap.add_argument('overlay'); ap.add_argument('out'); ap.add_argument('--frames'); ap.add_argument('--stills')
ap.add_argument('--facefix', action='store_true'); ap.add_argument('--look', default='graded'); ap.add_argument('--audio', default=os.path.join(J, 'audio', 'mix-master.wav'))
a = ap.parse_args()
frames = [int(x) for x in a.frames.split(',')] if a.frames else list(range(N))
fset = set(frames)

def shot_at(t):
    for s in lay['shots']:
        if s['t0'] - 1e-6 <= t < s['t1'] - 1e-6: return s
    return lay['shots'][-1]

def decode(v, n):
    cx, cy, cw, ch = v['crop']
    vf = f'fps=30,crop={cw}:{ch}:{cx}:{cy}'
    cmd = ['ffmpeg', '-v', 'error', '-ss', f"{v['src']:.3f}", '-i', os.path.join(J, v['file']), '-frames:v', str(n), '-vf', vf,
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8); k = len(arr) // (cw * ch * 3)
    return arr[:k * cw * ch * 3].reshape(k, ch, cw, 3)

def cover_fit(fr, w, h, zoom=1.0, fx=0.5):
    sh, sw = fr.shape[:2]; s = max(w / sw, h / sh) * zoom
    r = cv2.resize(fr, (int(round(sw * s)), int(round(sh * s))), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    y = (r.shape[0] - h) // 2; x = int(min(max(0, fx * r.shape[1] - w / 2), r.shape[1] - w))   # v12: horizontal focus
    return r[y:y + h, x:x + w]

def band(fr, prog):
    """Full-screen media: blurred, darkened fill + sharp width-fitted band slightly above centre, slow push."""
    bg = cv2.GaussianBlur(cover_fit(fr, W // 4, H // 4), (0, 0), 6)
    bg = (cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.42).astype(np.uint8)
    z = 1.0 + 0.05 * prog; sh, sw = fr.shape[:2]
    bw = int(W * z); bh = int(bw * sh / sw)
    b = cv2.resize(fr, (bw, bh), interpolation=cv2.INTER_CUBIC)
    x0 = (bw - W) // 2; b = b[:, x0:x0 + W]
    y = int(H * 0.40 - bh / 2); bg[max(0, y):y + bh] = b[max(0, -y):max(0, -y) + min(bh, H - max(0, y))]
    return bg

# v9 'card' (user ref. image 2): fixed black frame, horizontal media plays inside a rounded near-square card (no blurred self-fill)
CX, CY, CW, CH, CR = 60, 486, 960, 948, 52
_m = np.zeros((CH * 4, CW * 4), np.uint8); r4 = CR * 4
cv2.rectangle(_m, (r4, 0), (CW * 4 - r4, CH * 4), 255, -1); cv2.rectangle(_m, (0, r4), (CW * 4, CH * 4 - r4), 255, -1)
for cx_, cy_ in ((r4, r4), (CW * 4 - r4, r4), (r4, CH * 4 - r4), (CW * 4 - r4, CH * 4 - r4)): cv2.circle(_m, (cx_, cy_), r4, 255, -1)
CMASK = (cv2.resize(_m, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0)[..., None]

def card(fr, prog):
    out = np.zeros((H, W, 3), np.uint8)
    v = cover_fit(fr, CW, CH, 1.0 + 0.05 * prog).astype(np.float32)
    out[CY:CY + CH, CX:CX + CW] = (v * CMASK).astype(np.uint8)
    return out

broll = {}
for idx, s in enumerate(lay['shots']):
    if 'video' in s:
        broll[idx] = decode(s['video'], round((s['t1'] - s['t0']) * FPS) + 2)

# v7 multicam: per-camera fixed face centre + framing. B (side angle) is already ~1.45x closer than A.
CAM = {'A': dict(face=FIX, zdiv=1.0, full_y=0.30, split_w=1180, split_y=0.30),   # v11: higher in the split + slightly less zoom (user ref.)
       'B': dict(face=tuple(json.load(open(os.path.join(V, 'face_track_cam2.json')))['median']), zdiv=1.45, full_y=0.36, split_w=1440, split_y=0.32)}
CAMS = lay.get('cams', [[0.0, 'A']])
def cam_at(t):
    c = CAMS[0][1]
    for t0, cc in CAMS:
        if t >= t0 - 1e-6: c = cc
    return c

def crop_full(fr, z, prog, c='A'):
    P = CAM[c]; z = max(1.0, z / P['zdiv']) * (1 + 0.035 * prog)
    cw = BW / z; ch = cw * 16 / 9
    x = P['face'][0] * BW - cw / 2; y = P['face'][1] * BH - P['full_y'] * ch
    x = min(max(0, x), BW - cw); y = min(max(0, y), BH - ch)
    return cv2.resize(fr[int(y):int(y + ch), int(x):int(x + cw)], (W, H), interpolation=cv2.INTER_AREA)

# v2 soft split (user reference): media fills 0..TOP_H, presenter fills P0..H and fades in over the media (no hard seam)
TOP_H, P0, FADE = 1100, 640, 140   # v11: presenter area starts at 640 (was 820)   # v3: fade ends at 960, head kept below it (media never over the presenter)
_r = np.clip((np.arange(H - P0) / FADE), 0, 1); _r = _r * _r * (3 - 2 * _r)
PALPHA = _r.astype(np.float32)[:, None, None]
# v10 depth split (user): keep the diffuse seam, but the media now runs BETWEEN the presenter and the room behind him:
# media fills 0..TOPM, fades out 900->1300 over the room only; the person (rembg u2net_human_seg mask) stays in front.
TOPM, D0, D1 = 1150, 700, 1150   # v11
_d = np.clip((np.arange(P0, H) - D0) / (D1 - D0), 0, 1); _d = 1 - _d * _d * (3 - 2 * _d)
DFADE = _d.astype(np.float32)[:, None]
MASKDIR = os.path.join(V, '_pmask'); os.makedirs(MASKDIR, exist_ok=True)
_seg = None
def person_mask(i, img):
    """Person alpha (float 0..1) for the presenter area, cached per output frame."""
    global _seg
    p = os.path.join(MASKDIR, f'{i:06d}.png')
    if os.path.exists(p):
        m = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_GRAYSCALE)
    else:
        if _seg is None:
            from rembg import new_session; _seg = new_session('u2net_human_seg')
        from rembg import remove; from PIL import Image
        m = np.array(remove(Image.fromarray(img), session=_seg, only_mask=True))
        cv2.imencode('.png', m)[1].tofile(p)
    return cv2.GaussianBlur(m, (0, 0), 2.0).astype(np.float32) / 255.0

def crop_split(fr, prog, c='A'):
    P = CAM[c]; cw = P['split_w'] * (1 - 0.03 * prog); ch = cw * (H - P0) / 1080
    x = P['face'][0] * BW - cw / 2; y = P['face'][1] * BH - P['split_y'] * ch   # v3: presenter lower, hair clears the fade
    x = min(max(0, x), BW - cw); y = min(max(0, y), BH - ch)
    return cv2.resize(fr[int(y):int(y + ch), int(x):int(x + cw)], (W, H - P0), interpolation=cv2.INTER_AREA)

# v4: presenter base is color graded (edit/grade.txt) like the user's reference
base = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', os.path.join(J, 'renders', f'base-1440-{a.look}.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                        stdout=subprocess.PIPE, bufsize=BW * BH * 3 * 2)
base2 = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', os.path.join(J, 'renders', f'base-cam2-{a.look}.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE, bufsize=BW * BH * 3 * 2)   # v7: camera 2, frame-aligned to the same EDL
enc = None
if not a.stills:
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', a.audio, '-map', '0:v', '-map', '1:a',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                            '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
else:
    os.makedirs(a.stills, exist_ok=True)
prev_raw = prev_raw2 = None
for i in range(max(frames) + 1):
    raw = base.stdout.read(BW * BH * 3); raw2 = base2.stdout.read(BW * BH * 3)
    if len(raw) < BW * BH * 3: raw = prev_raw
    if len(raw2) < BW * BH * 3: raw2 = prev_raw2
    prev_raw, prev_raw2 = raw, raw2
    if i not in fset: continue
    t = i / FPS; cam = cam_at(t)
    fr = np.frombuffer(raw if cam == 'A' else raw2, np.uint8).reshape(BH, BW, 3)
    if a.facefix: fr = facefix.relight(fr, cam)   # v13 test: brighten/soften the face only
    s = shot_at(t); si = lay['shots'].index(s); prog = (t - s['t0']) / max(1e-3, s['t1'] - s['t0'])
    k = None
    if si in broll: b = broll[si]; k = b[min(len(b) - 1, round((t - s['t0']) * FPS))]
    if s['mode'] == 'gfx':
        out = np.zeros((H, W, 3), np.uint8)
    elif s['mode'] == 'full':
        out = crop_full(fr, s.get('zoom', 1.3), prog, cam)
    elif s['mode'] == 'split':
        out = np.zeros((H, W, 3), np.uint8)
        if k is not None: out[:TOPM] = cover_fit(k, W, TOPM, 1.0 + 0.04 * prog, s['video'].get('fx', 0.5))
        prc = crop_split(fr, prog, cam); pr = prc.astype(np.float32)
        pm = person_mask(i, prc)
        ma = (DFADE * (1 - pm))[..., None] if k is not None else np.zeros_like(pm)[..., None]
        out[P0:] = (pr * (1 - ma) + out[P0:].astype(np.float32) * ma).astype(np.uint8)
    elif s['mode'] == 'card':
        out = card(k, prog)
    else:
        out = band(k, prog)
    op = os.path.join(a.overlay, f'{i:06d}.png')
    if os.path.exists(op):
        ov = cv2.imdecode(np.fromfile(op, np.uint8), cv2.IMREAD_UNCHANGED)
        al = ov[..., 3:4].astype(np.float32) / 255.0
        if s['mode'] == 'split': al[P0:TOPM] *= (1 - pm[:TOPM - P0])[..., None]   # v11: only the panel band; captions (y 1690) never go behind him   # v10: overlay panel (headline) also passes behind the person
        out = (out.astype(np.float32) * (1 - al) + ov[..., 2::-1].astype(np.float32) * al).astype(np.uint8)
    if a.stills:
        cv2.imencode('.jpg', out[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])[1].tofile(os.path.join(a.stills, f'{i:06d}.jpg'))
    else:
        enc.stdin.write(out.tobytes())
    if i % 300 == 0: print(i, flush=True)
if a.stills: base.kill(); base2.kill()
base.stdout.close(); base.wait(); base2.stdout.close(); base2.wait()
if enc: enc.stdin.close(); enc.wait()
print('done')
