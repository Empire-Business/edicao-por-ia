#!/usr/bin/env python3
"""Paste the presenter's ORIGINAL head back over an outfit-swap generation (sharp, real face; generated clothes).

Why (author, 20/10/2026): "achei que a minha imagem de roupa social ficou com baixa qualidade" / "o MEU VÍDEO está com
baixíssima qualidade". The video-edit model returns ~704×1248 and redraws the face (smoother, slightly different
expression); it also draws the person a few % larger while the background stays aligned. This tool keeps the generated
frame (clothes, hands, background) and pastes the original head at full resolution on top:
1. tracking at low resolution: the head is followed in the original (normalised cross-correlation from the first-frame
   position you give), then matched in the generated frame to find scale + offset; motion is smoothed (Savitzky–Golay);
2. compositing at full resolution: feathered ellipse around the head, plus a low-frequency colour correction near the
   edge so the original skin meets the generated neck without a seam. Audio comes from the original clip.
Both inputs must be the SAME range at the SAME size (gen_video_edit.py `run` already conforms its output to the clip
it was given). Inspect a face close-up and the neck before delivery; a low `ncc_min` in the report usually means a
hand passed in front of the face — check that frame.

Usage:
  python3 tools/composite_original_head.py --original <orig.mov> --generated <gen.mp4> --out <result.mov> \
      --head X,Y --head-size W,H [--report report.json]
  X,Y = centre of the head (hair top to chin) in the FIRST frame, in pixels of the clip; W,H = head width/height.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv
from scipy.ndimage import zoom
from scipy.signal import savgol_filter


def probe(path: Path) -> tuple[int, int, str]:
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                        '-of', 'json', str(path)], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)['streams'][0]
    return int(s['width']), int(s['height']), s['r_frame_rate']


def frames(path: Path, w: int, h: int, gray: bool = False):
    fmt, c = ('gray', 1) if gray else ('rgb24', 3)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(path), '-vf', f'scale={w}:{h}:flags=area', '-f', 'rawvideo',
                          '-pix_fmt', fmt, '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = w * h * c
    try:
        while True:
            b = p.stdout.read(n)
            if len(b) < n:
                break
            a = np.frombuffer(b, np.uint8)
            yield a.reshape(h, w) if gray else a.reshape(h, w, 3)
    finally:
        p.stdout.close(); p.wait()


def ncc_best(img: np.ndarray, tpl: np.ndarray, cx: float, cy: float, r: int) -> tuple[float, float, float]:
    """Best centre of tpl inside img around (cx, cy) ± r (normalised cross-correlation)."""
    th, tw = tpl.shape
    x0 = max(0, min(img.shape[1] - tw - 2 * r - 1, int(round(cx - tw / 2 - r))))
    y0 = max(0, min(img.shape[0] - th - 2 * r - 1, int(round(cy - th / 2 - r))))
    V = swv(img[y0:y0 + th + 2 * r, x0:x0 + tw + 2 * r], (th, tw))
    t = (tpl - tpl.mean()) / (tpl.std() + 1e-6)
    m = V.mean((-1, -2), keepdims=True); s = V.std((-1, -2), keepdims=True) + 1e-6
    score = (((V - m) / s) * t).mean((-1, -2))
    iy, ix = np.unravel_index(score.argmax(), score.shape)
    return x0 + ix + tw / 2, y0 + iy + th / 2, float(score.max())


def patch(img: np.ndarray, cx: float, cy: float, w: int, h: int) -> np.ndarray:
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    return img[y0:y0 + h, x0:x0 + w].astype(np.float32)


def track(orig: Path, gen: Path, W: int, H: int, head: tuple[float, float], head_size: tuple[float, float], low_w: int = 360) -> dict:
    K = W / low_w; LW, LH = low_w, int(round(H / K))
    PW, PH = max(24, int(head_size[0] * 0.55 / K)), max(24, int(head_size[1] * 0.55 / K))   # face+hair patch
    O = np.stack(list(frames(orig, LW, LH, True))).astype(np.float32)
    G = np.stack(list(frames(gen, LW, LH, True))).astype(np.float32)
    n = min(len(O), len(G)); O, G = O[:n], G[:n]
    cx, cy = head[0] / K, head[1] / K
    t0 = patch(O[0], cx, cy, PW, PH); tpl = t0.copy(); co = []
    r = max(6, int(PW * 0.12))
    for i in range(n):
        cx, cy, _ = ncc_best(O[i], 0.5 * t0 + 0.5 * tpl, cx, cy, r)
        co.append((cx, cy)); tpl = patch(O[i], cx, cy, PW, PH)
    co = np.array(co)
    samples = []
    for i in range(0, n, max(1, n // 8)):
        p = patch(O[i], *co[i], PW, PH)
        cand = [(ncc_best(G[i], zoom(p, s, order=1), *co[i], r + 4)[2], s) for s in np.arange(0.94, 1.141, 0.02)]
        samples.append(round(float(max(cand)[1]), 2))
    s = float(np.median(samples))
    cg, scores = [], []
    for i in range(n):
        prev = cg[-1] if cg else tuple(co[0])
        dx, dy = (prev[0] - co[i - 1][0], prev[1] - co[i - 1][1]) if i else (0.0, 0.0)
        gx, gy, sc = ncc_best(G[i], zoom(patch(O[i], *co[i], PW, PH), s, order=1), co[i][0] + dx, co[i][1] + dy, r)
        cg.append((gx, gy)); scores.append(sc)
    cg = np.array(cg); win = min(9, max(3, (n // 2) * 2 - 1))
    co_s = savgol_filter(co, win, 2, axis=0) if n >= 5 else co
    cg_s = savgol_filter(cg, win, 2, axis=0) if n >= 5 else cg
    return {'frames': n, 'scale': s, 'scale_samples': samples, 'ncc_min': round(min(scores), 3),
            'ncc_median': round(float(np.median(scores)), 3), 'co': (co_s * K).tolist(), 'cg': (cg_s * K).tolist()}


def composite(orig: Path, gen: Path, out: Path, W: int, H: int, fps: str, tr: dict, head_size: tuple[float, float]) -> None:
    import torch
    dev = torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')
    AX, AY, FE = head_size[0] * 0.52, head_size[1] * 0.53, max(24.0, head_size[0] * 0.13)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', fps, '-i', '-',
                            '-i', str(orig), '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-crf', '13', '-preset', 'medium',
                            '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', '-shortest', str(out)], stdin=subprocess.PIPE)
    s = tr['scale']
    bw, bh = int(AX * s + FE) + 4, int(AY * s + FE) + 4
    yy, xx = torch.meshgrid(torch.arange(-bh, bh, device=dev, dtype=torch.float32),
                            torch.arange(-bw, bw, device=dev, dtype=torch.float32), indexing='ij')
    rr = torch.sqrt((xx / (AX * s)) ** 2 + (yy / (AY * s)) ** 2)
    edge = FE / (AX * s)
    m = torch.clamp((1 + edge - rr) / edge, 0, 1); m = (m * m * (3 - 2 * m))[None]   # smoothstep
    pool = lambda t: torch.nn.functional.avg_pool2d(torch.nn.functional.avg_pool2d(t[None], 61, 1, 30, count_include_pad=False),
                                                    61, 1, 30, count_include_pad=False)[0]
    for i, (o, g) in enumerate(zip(frames(orig, W, H), frames(gen, W, H))):
        if i >= tr['frames']:
            break
        (ox, oy), (gx, gy) = tr['co'][i], tr['cg'][i]
        G = torch.from_numpy(g.copy()).to(dev).permute(2, 0, 1).float()
        Ot = torch.from_numpy(o.copy()).to(dev).permute(2, 0, 1).float()[None]
        cx, cy = int(round(gx)), int(round(gy))
        x0, x1, y0, y1 = max(0, cx - bw), min(W, cx + bw), max(0, cy - bh), min(H, cy + bh)
        sl = (slice(y0 - cy + bh, y1 - cy + bh), slice(x0 - cx + bw, x1 - cx + bw))
        px, py = xx[sl] + cx, yy[sl] + cy
        qx, qy = ox + (px - gx) / s, oy + (py - gy) / s          # generated pixel ← original pixel
        grid = torch.stack([qx / (W - 1) * 2 - 1, qy / (H - 1) * 2 - 1], -1)[None]
        src = torch.nn.functional.grid_sample(Ot, grid, mode='bicubic', padding_mode='border', align_corners=True)[0]
        mm = m[:, sl[0], sl[1]]
        ring = ((mm > 0.05) & (mm < 0.95)).float()
        D = pool((G[:, y0:y1, x0:x1] - src) * ring) / (pool(ring) + 1e-3)
        src = src + D * (1 - mm) ** 0.7                         # only low-frequency colour, near the edge
        G[:, y0:y1, x0:x1] = mm * src + (1 - mm) * G[:, y0:y1, x0:x1]
        enc.stdin.write(G.clamp(0, 255).round().byte().permute(1, 2, 0).cpu().numpy().tobytes())
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise SystemExit('ffmpeg failed while encoding the composite')


def pair(v: str) -> tuple[float, float]:
    a, b = v.split(',')
    return float(a), float(b)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--original', required=True); ap.add_argument('--generated', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--head', required=True, type=pair, help='centro da cabeça no 1º quadro, px do clipe (x,y)')
    ap.add_argument('--head-size', required=True, type=pair, help='largura,altura da cabeça (cabelo→queixo) em px')
    ap.add_argument('--report')
    a = ap.parse_args(argv)
    orig, gen, out = Path(a.original), Path(a.generated), Path(a.out)
    if out.resolve() in (orig.resolve(), gen.resolve()):
        raise SystemExit('Never overwrite an input; choose another output.')
    W, H, fps = probe(orig)
    if probe(gen)[:2] != (W, H):
        raise SystemExit('Original and generated clips must have the same size (conform the generation first).')
    tr = track(orig, gen, W, H, a.head, a.head_size)
    composite(orig, gen, out, W, H, fps, tr, a.head_size)
    rep = {k: v for k, v in tr.items() if k not in ('co', 'cg')}
    rep.update({'original': str(orig), 'generated': str(gen), 'output': str(out)})
    if a.report:
        Path(a.report).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
