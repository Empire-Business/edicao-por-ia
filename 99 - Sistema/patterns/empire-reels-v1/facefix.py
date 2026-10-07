"""v13 test: lift + soften ONLY the presenter's face (user: face too dark, expression lines too marked; clothes/background OK).
Per frame: Haar face box (smoothed per camera) -> soft ellipse x soft skin mask (YCrCb) -> shadow lift (gamma) on luma,
slight local-contrast reduction (edge-preserving blend) inside the mask. Applied to the graded 1440x2560 presenter frame."""
import os, shutil, tempfile
import numpy as np, cv2
_x = os.path.join(tempfile.gettempdir(), 'cvf_haar_face.xml')
shutil.copy(os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml'), _x)
CASC = cv2.CascadeClassifier(_x)
_p = os.path.join(tempfile.gettempdir(), 'cvf_haar_profile.xml')
shutil.copy(os.path.join(cv2.data.haarcascades, 'haarcascade_profileface.xml'), _p)
PROF = cv2.CascadeClassifier(_p)   # camera 2 is a side angle: frontal Haar misses it
GAMMA, SOFT, FLAT = 0.78, 0.40, 0.10       # shadow lift, edge-preserving smoothing amount, contrast flattening toward local mean
_state = {}
MINW = {'A': 300, 'B': 440}
LUT = (np.power(np.arange(256) / 255.0, GAMMA) * 255).astype(np.float32)

def _box(fr, cam):
    sm = cv2.cvtColor(cv2.resize(fr, (360, 640), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    f = CASC.detectMultiScale(sm, 1.1, 5, minSize=(72, 72))
    if not len(f):
        f = PROF.detectMultiScale(sm, 1.1, 4, minSize=(72, 72))
        if not len(f):
            g = PROF.detectMultiScale(cv2.flip(sm, 1), 1.1, 4, minSize=(72, 72))
            f = [(360 - x - w, y, w, h) for x, y, w, h in g]
    prev = _state.get(cam)
    f = [r for r in f if r[2] * 4 >= MINW[cam]]          # drop hands/partial hits: camera 2 face is ~1.45x larger
    if len(f):
        b = np.array(max(f, key=lambda r: r[2] * r[3]), np.float32) * 4.0
        if prev is not None and np.abs(b[:2] - prev[:2]).max() < 160: b = prev * 0.75 + b * 0.25   # smooth jitter
        _state[cam] = b
    if cam not in _state and cam == 'B':                  # never seen yet: fall back to the measured fixed centre of camera 2
        import json; c = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_track_cam2.json')))['median']
        _state[cam] = np.array([c[0] * 1440 - 280, c[1] * 2560 - 300, 560, 560], np.float32)
    return _state.get(cam)

def relight(fr, cam):
    b = _box(fr, cam)
    if b is None: return fr
    x, y, w, h = b; cx, cy = x + w / 2, y + h * 0.55
    ax, ay = w * 0.78, h * 0.95                                  # ellipse covers face + forehead/chin + ears
    H, W = fr.shape[:2]
    x0, x1 = int(max(0, cx - ax * 1.3)), int(min(W, cx + ax * 1.3)); y0, y1 = int(max(0, cy - ay * 1.3)), int(min(H, cy + ay * 1.3))
    roi = fr[y0:y1, x0:x1]
    if roi.size == 0: return fr
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = ((xx - cx) / ax) ** 2 + ((yy - cy) / ay) ** 2
    ell = np.clip(1.25 - d, 0, 1) ** 1.2
    ycc = cv2.cvtColor(roi, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    skin = np.clip((ycc[..., 1] - 133) / 12, 0, 1) * np.clip((ycc[..., 1] - 182) / -10, 0, 1) * np.clip((ycc[..., 2] - 78) / 8, 0, 1) * np.clip((ycc[..., 2] - 132) / -8, 0, 1)
    m = cv2.GaussianBlur(skin * ell, (0, 0), 9)[..., None]
    r = roi.astype(np.float32)
    sm = cv2.bilateralFilter(roi, 9, 28, 9).astype(np.float32)               # softens fine lines, keeps edges (glasses, eyes)
    loc = cv2.GaussianBlur(r, (0, 0), 25)
    o = r * (1 - SOFT * m) + sm * SOFT * m
    o = o * (1 - FLAT * m) + loc * FLAT * m
    ly = 0.299 * o[..., 0] + 0.587 * o[..., 1] + 0.114 * o[..., 2]
    gain = (LUT[np.clip(ly, 0, 255).astype(np.uint8)] + 1) / (ly + 1)
    o = o * (1 + (gain[..., None] - 1) * m)
    out = fr.copy(); out[y0:y1, x0:x1] = np.clip(o, 0, 255).astype(np.uint8)
    return out
