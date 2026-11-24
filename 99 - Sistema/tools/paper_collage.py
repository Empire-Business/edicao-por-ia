#!/usr/bin/env python3
"""F22 Colagem de Papel: recortes, peças, render em stop-motion, efeitos e mixagem.

Renderizador por tempo (seek em t): cada quadro é calculado só a partir de t, com os elementos
tremendo a 12 qps. Uma cena por frase da narração; faixas de texto entram na palavra dita.

  paper_collage.py cutouts <fotos> <recortes> <cutouts.json>   recorta pessoas/fotos com borda de papel
  paper_collage.py props <recortes>                            folha de caderno, placa e relógio
  paper_collage.py render <cenas.py> <saida.mp4>               vídeo mudo + <saida>.events.json
  paper_collage.py frames <cenas.py> <pasta> t1,t2,...         quadros-chave para revisão
  paper_collage.py sfx <events.json> <sfx.wav>                 pop, papel e whoosh nas entradas
  paper_collage.py mix <mudo.mp4> <voz.wav> <sfx.wav> <saida.mp4> [--music trilha]

O arquivo de cenas é Python e define ACCENT (cor principal da ID), CUT_DIR, WORDS (json de palavras
com "w" e "s"), SCENE_DUR (segundos por cena), SCENES e, opcional, TAIL. Ver
examples/reference-library/F22/colagem-de-papel/cenas.example.py.
"""
import argparse, functools, hashlib, json, math, random, runpy, subprocess, unicodedata, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from scipy import ndimage

ENGINE = Path(__file__).resolve().parents[1]
FONTS = ENGINE / 'assets' / 'fonts' / 'portable'
MODNET_URL = 'https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx'
MODNET_SHA256 = '07c308cf0fc7e6e8b2065a12ed7fc07e1de8febb7dc7839d7b7f15dd66584df9'

W, H, FPS, STOP = 1080, 1920, 30, 12
FONT = str(FONTS / 'anton-regular.ttf')
MARKER = str(FONTS / 'permanent-marker-regular.ttf')
CREAM, INK, PAPER_W = (236, 228, 210), (24, 23, 22), (246, 243, 236)
BGW, BGH = 1140, 2026


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if c.isalnum() and unicodedata.category(c) != 'Mn')


def step(t):
    return math.floor(t * STOP) / STOP


# ---------- fundos ----------
def _noise(shape, sigma, seed):
    n = ndimage.gaussian_filter(np.random.default_rng(seed).standard_normal(shape), sigma)
    return n / (np.abs(n).max() + 1e-6)


def bg_paper(base, seed, crumple=0.0, fibers=True):
    sh = (BGH, BGW)
    a = np.empty(sh + (3,), np.float32); a[:] = base
    blot = _noise(sh, 120, seed) * 10 + _noise(sh, 30, seed + 1) * 4
    a += blot[..., None]
    if crumple:
        h = sum(np.abs(_noise(sh, s, seed + 10 + i)) * w for i, (s, w) in enumerate([(70, 1), (25, .6), (9, .3)]))
        gy, gx = np.gradient(h); sh_ = (gx * 0.7 - gy) * 900 * crumple
        a += sh_[..., None]
    a += np.random.default_rng(seed + 3).normal(0, 5, sh)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if fibers:
        d = ImageDraw.Draw(img, 'RGBA'); r = random.Random(seed)
        for _ in range(260):
            x, y = r.uniform(0, BGW), r.uniform(0, BGH); ang = r.uniform(0, 6.28); L = r.uniform(6, 26)
            d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(90, 70, 50, r.randint(15, 40)), width=1)
    return img


def bg_black(seed):
    img = bg_paper((30, 29, 28), seed, 0, False)
    a = np.asarray(img, np.float32)
    chalk = np.clip(_noise((BGH, BGW), 40, seed + 5), 0, 1) * 22 + np.clip(_noise((BGH, BGW), 6, seed + 6), .55, 1) * 30 - 16
    a += np.clip(chalk, 0, None)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(img, 'RGBA'); r = random.Random(seed)
    for _ in range(70):
        x, y = r.uniform(0, BGW), r.uniform(0, BGH); s = r.uniform(3, 9)
        if r.random() < .5: d.line([(x - s, y - s), (x + s, y + s)], fill=(230, 230, 225, 70), width=2); d.line([(x - s, y + s), (x + s, y - s)], fill=(230, 230, 225, 70), width=2)
        else: d.ellipse([x - s, y - s, x + s, y + s], outline=(230, 230, 225, 60), width=2)
    return img


def bg_burst(accent, seed, cx=.5, cy=.55, rays=22):
    img = Image.new('RGB', (BGW, BGH), accent); d = ImageDraw.Draw(img)
    X, Y = cx * BGW, cy * BGH; R = 3000; dark = (33, 30, 28)
    for i in range(rays):
        a0 = i * 2 * math.pi / rays; a1 = a0 + math.pi / rays
        d.polygon([(X, Y), (X + R * math.cos(a0), Y + R * math.sin(a0)), (X + R * math.cos(a1), Y + R * math.sin(a1))], fill=dark)
    a = np.asarray(img, np.float32)
    yy, xx = np.mgrid[0:BGH, 0:BGW]; v = 1 - .35 * np.clip(np.hypot((xx - X) / BGW, (yy - Y) / BGH) * 1.3, 0, 1)
    a = a * v[..., None] + np.random.default_rng(seed).normal(0, 7, (BGH, BGW))[..., None] + _noise((BGH, BGW), 60, seed)[..., None] * 10
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


@functools.lru_cache(None)
def background(kind, accent, seed, cx=.5, cy=.55):
    if kind == 'cream': return bg_paper(CREAM, seed, .25)
    if kind == 'kraft': return bg_paper((172, 132, 88), seed, 1.0)
    if kind == 'black': return bg_black(seed)
    if kind == 'burst': return bg_burst(accent, seed, cx, cy)
    raise ValueError(kind)


# ---------- peças ----------
def shadowed(im, off=(7, 10), blur=7, alpha=95):
    m = 30; out = Image.new('RGBA', (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 255)); sh.putalpha(im.getchannel('A').point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (m + off[0], m + off[1])); out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (m, m)); return out


@functools.lru_cache(None)
def font(path, size): return ImageFont.truetype(path, size)


@functools.lru_cache(None)
def strip_img(text, size, style, accent, seed):
    f = font(FONT, size); l, t, r, b = f.getbbox(text)
    px, py = int(size * .26), int(size * .16); w, h = r - l + 2 * px, b - t + 2 * py
    bgc, fg = {'w': (PAPER_W, INK), 'k': (INK, PAPER_W), 'a': (accent, INK)}[style]
    im = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rr = random.Random(seed)
    j = lambda: rr.uniform(-3, 3)
    d.polygon([(4 + j(), 4 + j()), (w + 4 + j(), 4 + j()), (w + 4 + j(), h + 4 + j()), (4 + j(), h + 4 + j())], fill=bgc + (255,))
    a = np.asarray(im, np.float32).copy(); a[..., :3] += np.random.default_rng(seed).normal(0, 5, a.shape[:2])[..., None]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(im)
    d.text((4 + px - l, 4 + py - t), text, font=f, fill=fg)
    return shadowed(im, (5, 7), 5, 80)


@functools.lru_cache(None)
def load_img(path, w, sil=False):
    im = Image.open(path).convert('RGBA'); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    if sil:  # silhueta preta mantendo a borda de papel
        a = np.asarray(im).copy(); m = a[..., 3] > 0
        inner = ndimage.binary_erosion(m, iterations=14)
        a[inner, :3] = (20, 19, 18); im = Image.fromarray(a, 'RGBA')
    return shadowed(im)


def transformed(base, scale, rot):
    im = base
    if abs(scale - 1) > .01: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(rot) > .05: im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def paste(canvas, im, px, py):
    x0, y0 = max(0, -px), max(0, -py); x1, y1 = min(im.width, canvas.width - px), min(im.height, canvas.height - py)
    if x1 > x0 and y1 > y0: canvas.alpha_composite(im.crop((x0, y0, x1, y1)) if (x0 or y0 or x1 < im.width or y1 < im.height) else im, (px + x0, py + y0))


# ---------- rabiscos ----------
def wobble(pts, amp, seed):
    r = random.Random(seed); return [(x + r.uniform(-amp, amp), y + r.uniform(-amp, amp)) for x, y in pts]


def doodle_paths(kind, p, seed):
    """devolve lista de polilinhas (em coordenadas da tela)."""
    r = random.Random(seed); P = []
    x, y = p.get('x', 540), p.get('y', 960); s = p.get('s', 100)
    if kind == 'circle':
        rx, ry = p.get('rx', s), p.get('ry', s * .6); n = 60
        P.append(wobble([(x + rx * math.cos(a) * (1 + .04 * i / n), y + ry * math.sin(a)) for i, a in enumerate(np.linspace(-.3, 2 * math.pi + .35, n))], 3, seed))
    elif kind == 'stars':
        for i in range(p.get('n', 4)):
            cx, cy = x + r.uniform(-s, s) * 2, y + r.uniform(-s, s); k = r.uniform(14, 26)
            P += [[(cx - k, cy), (cx + k, cy)], [(cx, cy - k * 1.3), (cx, cy + k * 1.3)]]
    elif kind == 'rays':
        for i in range(p.get('n', 9)):
            a = p.get('a0', 0) + i * p.get('spread', 2 * math.pi) / p.get('n', 9); r0, r1 = s, s * 1.45 + r.uniform(-8, 8)
            P.append([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))])
    elif kind == 'arrow':
        x1, y1 = p['x1'], p['y1']; mx, my = (x + x1) / 2 + p.get('bend', 60), (y + y1) / 2 - p.get('bend', 60) * .5
        pts = [((1 - t) ** 2 * x + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) ** 2 * y + 2 * (1 - t) * t * my + t * t * y1) for t in np.linspace(0, 1, 30)]
        P.append(wobble(pts, 1.5, seed)); ang = math.atan2(y1 - pts[-4][1], x1 - pts[-4][0])
        P.append([(x1 - 34 * math.cos(ang - .5), y1 - 34 * math.sin(ang - .5)), (x1, y1), (x1 - 34 * math.cos(ang + .5), y1 - 34 * math.sin(ang + .5))])
    elif kind == 'waves':
        for k in range(p.get('n', 3)):
            yy = y + k * 46; P.append(wobble([(x - s + i * 2 * s / 40, yy + 14 * math.sin(i * .8 + k)) for i in range(41)], 1.5, seed + k))
    elif kind == 'wind':
        for k in range(3):
            yy = y + (k - 1) * 60; L = s * (1 - .2 * k)
            pts = [(x - L + i * L / 20, yy) for i in range(21)] + [(x + 22 * math.cos(a) , yy - 22 + 22 * math.sin(a)) for a in np.linspace(math.pi / 2, -math.pi, 14)]
            P.append(wobble(pts, 1.5, seed + k))
    elif kind == 'crown':
        w2 = s; pts = [(x - w2, y + s * .5), (x - w2, y - s * .3), (x - w2 * .5, y + s * .1), (x, y - s * .55), (x + w2 * .5, y + s * .1), (x + w2, y - s * .3), (x + w2, y + s * .5), (x - w2, y + s * .5)]
        P.append(wobble(pts, 2, seed))
    elif kind == 'eyex':
        P.append(wobble([(x - s + 2 * s * t, y - s * .55 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 20)], 1.5, seed))
        P.append(wobble([(x - s + 2 * s * t, y + s * .55 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 20)], 1.5, seed + 1))
        P.append([(x + s * .3 * math.cos(a), y + s * .3 * math.sin(a)) for a in np.linspace(0, 6.4, 20)])
        P += [[(x - s * 1.1, y - s * .9), (x + s * 1.1, y + s * .9)], [(x + s * 1.1, y - s * .9), (x - s * 1.1, y + s * .9)]]
    elif kind == 'globe':
        P.append([(x + s * math.cos(a), y + s * math.sin(a)) for a in np.linspace(0, 6.35, 50)])
        for f in (.35, .75): P.append([(x + s * f * math.cos(a), y + s * math.sin(a)) for a in np.linspace(-math.pi / 2, 3 * math.pi / 2, 40)])
        for yy in (-.5, 0, .5): hw = s * math.sqrt(1 - yy * yy); P.append([(x - hw, y + yy * s), (x + hw, y + yy * s)])
    elif kind == 'medal':
        P.append([(x - s * .4, y - s * 2.1), (x - s * .15, y - s * .9)]); P.append([(x + s * .4, y - s * 2.1), (x + s * .15, y - s * .9)])
        P.append([(x + s * math.cos(a), y + s * math.sin(a)) for a in np.linspace(0, 6.35, 50)])
        P.append([(x - s * .2, y - s * .3), (x + s * .05, y - s * .5), (x + s * .05, y + s * .55)])
    elif kind == 'crowd':
        for i in range(p.get('n', 9)):
            cx = x - s + i * 2 * s / (p.get('n', 9) - 1) + r.uniform(-8, 8); cy = y + r.uniform(-10, 10); k = r.uniform(20, 26)
            P.append([(cx + k * math.cos(a), cy + k * math.sin(a)) for a in np.linspace(0, 6.35, 18)])
            P.append([(cx - k * 1.6 + 3.2 * k * t, cy + k * 2.6 - k * 1.3 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 14)])
    elif kind == 'octagon':
        P.append(wobble([(x + s * math.cos(a + math.pi / 8), y + s * .75 * math.sin(a + math.pi / 8)) for a in np.linspace(0, 2 * math.pi, 9)], 2, seed))
        P.append(wobble([(x + s * .9 * math.cos(a + math.pi / 8), y + s * .68 * math.sin(a + math.pi / 8)) for a in np.linspace(0, 2 * math.pi, 9)], 2, seed + 1))
    elif kind == 'underline':
        P.append(wobble([(x - s + 2 * s * t, y + 6 * math.sin(t * 7)) for t in np.linspace(0, 1, 20)], 1.5, seed))
    elif kind == 'line':
        P.append(wobble([(p['x'], p['y']), (p['x1'], p['y1'])], 1, seed))
    return P


def draw_doodle(canvas, e, prog, color):
    d = ImageDraw.Draw(canvas); paths = e['_paths']; width = e.get('width', 8)
    tot = sum(len(pp) for pp in paths); show = prog * tot; acc = 0
    for pp in paths:
        n = len(pp); k = int(min(n, max(0, show - acc))); acc += n
        if k >= 2: d.line(pp[:k], fill=color, width=width, joint='curve')
    if e['kind'] in ('question', 'mark') and prog >= 1:
        f = font(MARKER, e.get('s', 200)); d.text((e['x'], e['y']), e.get('text', '?'), font=f, fill=color, anchor='mm')


# ---------- motor ----------
class Engine:
    def __init__(self, spec_path):
        g = runpy.run_path(spec_path); self.g = g
        self.accent = tuple(g['ACCENT']); self.cut = g['CUT_DIR']
        words = json.load(open(g['WORDS'])); dur = g['SCENE_DUR']
        self.starts = np.concatenate([[0], np.cumsum(dur)]); self.T = float(self.starts[-1]) + g.get('TAIL', .4)
        self.scenes = []; self.events = []
        for i, sc in enumerate(g['SCENES']):
            s0, s1 = self.starts[i], self.starts[i + 1] if i + 1 < len(dur) else self.T
            ws = [w for w in words if s0 - .4 <= w['s'] < s1 - .1]
            sc = dict(sc); sc['t0'], sc['t1'] = float(s0), float(s1); sc['_words'] = ws; cur = [0]
            def when(key, sc=sc, cur=cur, advance=True):
                if isinstance(key, (int, float)): return sc['t0'] + key
                if key.startswith('@'): return sc['t0'] + float(key[1:])
                k = norm(key)
                for j in range(cur[0] if advance else 0, len(sc['_words'])):
                    t = norm(sc['_words'][j]['w'])
                    if t and (t == k or t.startswith(k) or (len(t) >= 2 and k.startswith(t))):
                        if advance: cur[0] = j + 1
                        return max(sc['t0'], sc['_words'][j]['s'])
                raise ValueError(f"cena {i+1}: palavra '{key}' não dita ({[w['w'] for w in sc['_words']]})")
            els = []
            for n, e in enumerate(sc['els']):
                e = dict(e); e['_seed'] = i * 100 + n
                if e['t'] == 'strip':
                    toks = e['text'].split(' '); keys = e.get('keys')
                    if keys is None: keys = [None] * len(toks)
                    e['_times'] = []
                    for tk, kk in zip(toks, keys):
                        if kk == '=': e['_times'].append(e['_times'][-1] if e['_times'] else when(0)); continue
                        e['_times'].append(when(kk if kk is not None else tk))
                    e['_toks'] = toks; e['_in'] = e['_times'][0]
                    self.events.append(('paper', e['_in']))
                else:
                    e['_in'] = when(e.get('at', 0), advance=False)
                    if e['t'] == 'img': self.events.append(('pop', e['_in']))
                    if e['t'] == 'doodle':
                        e['_paths'] = doodle_paths(e['kind'], e, e['_seed'])
                e['_out'] = when(e['until'], advance=False) if 'until' in e else 1e9
                els.append(e)
            sc['els'] = els; self.scenes.append(sc)
            if sc.get('wipe_in'): self.events.append(('whoosh', sc['t0'] - .12))
        rng = np.random.default_rng(7); self.grain = [rng.normal(0, 6, (H, W)).astype(np.int16) for _ in range(6)]

    def scene_at(self, t):
        i = int(np.searchsorted(self.starts, t, 'right') - 1); return min(max(i, 0), len(self.scenes) - 1)

    def jitter(self, e, t):
        r = random.Random(e['_seed'] * 7919 + int(t * STOP)); a = e.get('jit', 1.0)
        return r.uniform(-2.5, 2.5) * a, r.uniform(-2.5, 2.5) * a, r.uniform(-.5, .5) * a

    def render_scene(self, sc, t):
        bgk = sc['bg']; bg = background(bgk, self.accent, sc.get('seed', 1), *sc.get('center', (.5, .55)))
        z = 1 + .035 * (t - sc['t0']) / max(.5, sc['t1'] - sc['t0']); cw, ch = W / z, H / z
        ox, oy = (BGW - cw) / 2, (BGH - ch) / 2
        canvas = bg.crop((int(ox), int(oy), int(ox + cw), int(oy + ch))).resize((W, H), Image.BILINEAR).convert('RGBA')
        ink = (245, 242, 234) if bgk in ('black', 'burst') else INK
        st = step(t)
        for e in sc['els']:
            if st < step(e['_in']) - 1e-6 or t >= e['_out']: continue
            age = st - step(e['_in']); dx, dy, dr = self.jitter(e, t)
            if e['t'] == 'doodle':
                prog = min(1, (age + 1 / STOP) / e.get('draw', .33)); col = self.accent if e.get('color') == 'a' else (INK if e.get('color') == 'k' else ink)
                draw_doodle(canvas, e, prog, col); continue
            if e['t'] == 'strip':
                n = sum(1 for tt in e['_times'] if step(tt) <= st + 1e-6)
                base = strip_img(' '.join(e['_toks'][:n]), e.get('size', 90), e.get('style', 'w'), self.accent, e['_seed'])
                full = strip_img(e['text'], e.get('size', 90), e.get('style', 'w'), self.accent, e['_seed'])
            else:
                base = load_img(f"{self.cut}/{e['src']}.png", e['w'], e.get('sil', False)); full = base
            anim = e.get('anim', 'pop'); p = min(1, (age + 1 / STOP) / .25); sc_ = 1; ox_ = oy_ = 0
            if anim == 'pop': sc_ = .55 + .45 * p + .16 * math.sin(math.pi * p) if p < 1 else 1
            elif anim.startswith('slide'):
                dist = (1 - p) ** 2 * 420; ox_, oy_ = {'slide_l': (-dist, 0), 'slide_r': (dist, 0), 'slide_up': (0, dist), 'slide_down': (0, -dist)}[anim]
            im = transformed(base, sc_, e.get('rot', 0) + dr)
            x, y = e['x'] + dx + ox_, e['y'] + dy + oy_
            if e['t'] == 'strip' and e.get('anchor', 'c') == 'c':  # cresce a partir da esquerda da faixa completa
                left = x - full.width * sc_ / 2; px, py = int(left), int(y - im.height / 2)
            elif e['t'] == 'strip':
                px, py = int(x), int(y - im.height / 2)
            else:
                px, py = int(x - im.width / 2), int(y - im.height / 2)
            paste(canvas, im, px, py)
        return canvas

    def frame(self, t):
        i = self.scene_at(t); img = self.render_scene(self.scenes[i], t)
        # folha de papel deslizando na troca (paper wipe)
        for j, sc in enumerate(self.scenes):
            if sc.get('wipe_in') and abs(t - sc['t0']) < .2:
                q = (step(t) - (sc['t0'] - .2)) / .4; x = int(W * (1 - 2.1 * q))
                paste(img, wipe_sheet(), x - 60, 0)
        a = np.asarray(img.convert('RGB'), np.int16) + self.grain[int(t * STOP) % 6][..., None]
        return a.clip(0, 255).astype(np.uint8)


@functools.lru_cache(None)
def wipe_sheet():
    w = W + 120; im = bg_paper((240, 235, 222), 99, .15, True).resize((w, H)).convert('RGBA')
    a = np.full((H, w), 255, np.uint8); r = random.Random(3)
    edge = [int(18 + 14 * math.sin(y / 31) + r.uniform(-6, 6)) for y in range(H)]
    for y in range(H): a[y, :edge[y]] = 0; a[y, w - edge[H - 1 - y]:] = 0
    im.putalpha(Image.fromarray(a)); return shadowed(im, (-10, 0), 12, 110).crop((30, 30, 30 + w, 30 + H))


# ---------- recortes ----------
def matte_model():
    """MODNet (Apache-2.0) baixado uma vez para .factory/models e conferido pelo hash."""
    path = ENGINE / '.factory' / 'models' / 'modnet.onnx'
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == MODNET_SHA256: return path
    path.parent.mkdir(parents=True, exist_ok=True); tmp = path.with_suffix('.part')
    subprocess.run(['curl', '--fail', '--silent', '--location', '--max-time', '600', '-o', str(tmp), MODNET_URL], check=True)
    if hashlib.sha256(tmp.read_bytes()).hexdigest() != MODNET_SHA256:
        tmp.unlink(); raise SystemExit('Modelo de recorte baixado não confere com o hash esperado.')
    tmp.replace(path); return path


_s = None


def matte(im):
    import onnxruntime as ort
    global _s
    _s = _s or ort.InferenceSession(str(matte_model()), providers=['CPUExecutionProvider'])
    w, h = im.size; r = 512 / max(w, h); W, H = max(32, int(w*r)//32*32), max(32, int(h*r)//32*32)
    x = np.asarray(im.convert('RGB').resize((W, H), Image.BICUBIC), np.float32) / 127.5 - 1
    m = _s.run(None, {'input': x.transpose(2, 0, 1)[None]})[0][0, 0]
    return Image.fromarray((m*255).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)


def rough(a, px, seed):
    """borda de papel: dilata o alfa com contorno irregular."""
    rng = np.random.default_rng(seed); m = np.asarray(a) > 128
    d = ndimage.distance_transform_edt(~m)
    noise = ndimage.gaussian_filter(rng.standard_normal(m.shape), 9); noise = noise/np.abs(noise).max()
    return (d <= px*(1 + .45*noise)) | m


def grade(im, bw, k=1.35):
    im = im.convert('RGB')
    if bw:
        g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1 if k > 1.2 else .2)
        g = ImageEnhance.Contrast(g).enhance(k); im = g.convert('RGB')
    a = np.asarray(im, np.float32); a += np.random.default_rng(1).normal(0, 9, a.shape[:2])[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def cutout(raw, sp, k):
    """spec: out, src, crop [x0,y0,x1,y1] em frações, mode person|print|white, neck (fração y), border px, bw, width px."""
    im = Image.open(f"{raw}/{sp['src']}").convert('RGB'); w, h = im.size
    c = sp.get('crop', [0, 0, 1, 1]); im = im.crop((int(c[0]*w), int(c[1]*h), int(c[2]*w), int(c[3]*h)))
    tw = sp.get('width', 700); im = im.resize((tw, int(im.height*tw/im.width)), Image.LANCZOS)
    w, h = im.size; mode = sp.get('mode', 'print'); B = sp.get('border', 14)
    if mode == 'print':
        pad = B; out = Image.new('RGBA', (w+2*pad, h+2*pad), (246, 243, 236, 255))
        out.paste(grade(im, sp.get('bw', True), 1.05), (pad, pad)); return out
    if mode == 'person': a = matte(im)
    else:  # fundo branco
        g = np.asarray(ImageOps.grayscale(im)); a = Image.fromarray(((g < 235)*255).astype(np.uint8))
        a = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    a = np.asarray(a).copy()
    if sp.get('neck'):  # corte no pescoço, levemente torto
        y = int(sp['neck']*h); xs = np.arange(w); cut = y + (np.sin(xs/37.)*6 + (xs-w/2)*.04).astype(int)
        a[np.arange(h)[:, None] > cut[None, :]] = 0
    a = (ndimage.gaussian_filter(a.astype(np.float32), 1.2)).clip(0, 255)
    pad = B*3; A = np.pad(a, pad); img = ImageOps.expand(grade(im, sp.get('bw', True)), pad, fill='white')
    paper = rough(Image.fromarray(A.astype(np.uint8)), B, k)
    paper = ndimage.gaussian_filter(paper.astype(np.float32), .8)
    rgb = np.asarray(img, np.float32); bg = np.full_like(rgb, 246); bg[..., 2] = 238
    al = (A/255.)[..., None]; rgb = rgb*al + bg*(1-al)
    out = np.dstack([rgb, (paper*255).clip(0, 255)]).astype(np.uint8)
    o = Image.fromarray(out, 'RGBA'); return o.crop(o.getbbox())


def bordered(im, B=14, seed=0):
    a = im.getchannel('A'); pad = B * 3; big = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); big.alpha_composite(im, (pad, pad))
    A = np.pad(np.asarray(a), pad); m = rough(Image.fromarray(A), B, seed)
    paper = Image.new('RGBA', big.size, (246, 243, 236, 0)); pa = np.asarray(paper).copy(); pa[..., 3] = m * 255
    paper = Image.fromarray(pa, 'RGBA'); paper.alpha_composite(big); return paper.crop(paper.getbbox())


def props(cut):
    """Peças desenhadas: folha de caderno com fita, placa de proibido estacionar, relógio de pulso."""
    # folha de caderno com fita
    w, h = 760, 900; im = Image.new('RGBA', (w, h), (250, 249, 244, 255)); d = ImageDraw.Draw(im)
    for y in range(110, h, 46): d.line([(0, y), (w, y)], fill=(150, 185, 215, 255), width=2)
    d.line([(90, 0), (90, h)], fill=(220, 120, 120, 255), width=3)
    a = np.asarray(im).copy(); r = np.random.default_rng(2)
    top = (14 + 8 * np.sin(np.arange(w) / 9) + r.uniform(-4, 4, w)).astype(int)
    for x in range(w): a[:top[x], x, 3] = 0
    a[..., :3] = (a[..., :3] + r.normal(0, 3, a.shape[:2])[..., None]).clip(0, 255)
    im = Image.fromarray(a.astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(im, 'RGBA')
    d.polygon([(w / 2 - 120, 0), (w / 2 + 120, 8), (w / 2 + 116, 58), (w / 2 - 124, 50)], fill=(235, 225, 190, 170))
    im.save(f'{cut}/sheet.png')
    # placa de estacionamento (E cortado)
    s = 360; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=(200, 30, 35, 255)); d.ellipse([34, 34, s - 35, s - 35], fill=(245, 242, 234, 255))
    f = font(FONT, 200); d.text((s / 2, s / 2 + 6), 'E', font=f, fill=(25, 25, 25), anchor='mm')
    d.line([(s * .2, s * .2), (s * .8, s * .8)], fill=(200, 30, 35, 255), width=30)
    bordered(im, 12, 4).save(f'{cut}/sign_e.png')
    # relógio de pulso
    im = Image.new('RGBA', (360, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([110, 0, 250, 760], 30, fill=(92, 62, 40, 255))
    for y in (520, 570, 620): d.ellipse([170, y, 190, y + 20], fill=(40, 28, 20, 255))
    d.rectangle([60, 220, 300, 520], fill=(200, 170, 90, 255)); d.rectangle([84, 244, 276, 496], fill=(246, 243, 232, 255))
    cx, cy = 180, 370
    for k in range(12):
        a2 = k * math.pi / 6; d.line([(cx + 80 * math.cos(a2), cy + 100 * math.sin(a2)), (cx + 92 * math.cos(a2), cy + 112 * math.sin(a2))], fill=(30, 30, 30), width=5)
    d.line([(cx, cy), (cx + 50, cy - 40)], fill=(25, 25, 25), width=8); d.line([(cx, cy), (cx - 10, cy - 90)], fill=(25, 25, 25), width=6)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(25, 25, 25))
    bordered(im, 12, 5).save(f'{cut}/watch.png')


# ---------- efeitos e mixagem ----------
SR = 48000


def _env(n, a=.002, d=.06): t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)


def _bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))


def sfx_track(events_path, out_path):
    ev = json.load(open(events_path)); T = ev['duration']; out = np.zeros(int(T * SR) + SR, np.float32)
    rng = np.random.default_rng(5)

    def pop():
        n = int(.09 * SR); t = np.arange(n) / SR; f = 520 * np.exp(-t * 18) + 140
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .001, .03) * .6 + _bp(rng.standard_normal(n), 1500, 6000) * _env(n, .0005, .008) * .25

    def paper():
        n = int(.12 * SR); return _bp(rng.standard_normal(n), 2000, 9000) * _env(n, .003, .035) * .35

    def whoosh():
        n = int(.4 * SR); t = np.arange(n) / SR; e = np.sin(np.pi * t / t[-1]) ** 2
        return _bp(rng.standard_normal(n), 400, 4000) * e * .3

    last = {}
    for kind, t in ev['events']:
        t = max(0, t)
        if kind in last and t - last[kind] < .12: continue  # evita metralhadora de sons
        last[kind] = t; s = {'pop': pop, 'paper': paper, 'whoosh': whoosh}[kind]() * rng.uniform(.75, 1.0)
        i = int(t * SR); out[i:i + len(s)] += s[:len(out) - i]
    out = out[:int(T * SR)]; out /= max(1e-6, np.abs(out).max()); out *= .5
    with wave.open(str(out_path), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    return len(ev['events'])


def mix(video, voice, sfx, out, music=None):
    """Voz + efeitos (+ trilha abaixada pela voz), −16 LUFS / −1,5 dBTP."""
    T = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video], capture_output=True, text=True, check=True).stdout)
    inputs = ['-i', video, '-i', voice, '-i', sfx]
    graph = f'[1:a]aresample=48000,apad,atrim=0:{T},asplit=2[voz][sc];[2:a]aresample=48000,volume=0.35[fx];'
    if music:
        inputs += ['-i', music]
        graph += (f'[3:a]aresample=48000,atrim=0:{T},afade=t=in:d=0.4,afade=t=out:st={max(0, T - 1.6)}:d=1.6,volume=0.22[mus];'
                  '[mus][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[musd];[voz][musd][fx]amix=inputs=3:normalize=0')
    else:
        graph += '[sc]anullsink;[voz][fx]amix=inputs=2:normalize=0'
    graph += ',loudnorm=I=-16:TP=-1.5:LRA=9,afade=t=in:d=0.005[a]'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', graph, '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], check=True)


# ---------- linha de comando ----------
def render(spec, out):
    eng = Engine(spec); n = int(round(eng.T * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '2', out], stdin=subprocess.PIPE)
    for k in range(n):
        ff.stdin.write(eng.frame(k / FPS).tobytes())
        if k % 150 == 0: print(f'{k}/{n}', flush=True)
    ff.stdin.close(); ff.wait()
    json.dump({'duration': eng.T, 'events': eng.events, 'scenes': [[s['t0'], s['t1']] for s in eng.scenes]}, open(out + '.events.json', 'w'))
    return eng.T


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('cutouts'); c.add_argument('raw'); c.add_argument('cut'); c.add_argument('specs'); c.add_argument('only', nargs='*')
    c = sub.add_parser('props'); c.add_argument('cut')
    c = sub.add_parser('render'); c.add_argument('spec'); c.add_argument('out')
    c = sub.add_parser('frames'); c.add_argument('spec'); c.add_argument('dir'); c.add_argument('times')
    c = sub.add_parser('sfx'); c.add_argument('events'); c.add_argument('out')
    c = sub.add_parser('mix'); c.add_argument('video'); c.add_argument('voice'); c.add_argument('sfx'); c.add_argument('out'); c.add_argument('--music')
    a = ap.parse_args()
    if a.cmd == 'cutouts':
        Path(a.cut).mkdir(parents=True, exist_ok=True)
        for k, sp in enumerate(json.load(open(a.specs))):
            if a.only and sp['out'] not in a.only: continue
            o = cutout(a.raw, sp, k); o.save(f"{a.cut}/{sp['out']}.png"); print(sp['out'], o.size, flush=True)
    elif a.cmd == 'props': Path(a.cut).mkdir(parents=True, exist_ok=True); props(a.cut); print('ok')
    elif a.cmd == 'render': print('ok', a.out, render(a.spec, a.out))
    elif a.cmd == 'frames':
        eng = Engine(a.spec); Path(a.dir).mkdir(parents=True, exist_ok=True)
        for t in (float(x) for x in a.times.split(',')): Image.fromarray(eng.frame(t)).save(f'{a.dir}/f_{t:06.2f}.jpg', quality=88)
    elif a.cmd == 'sfx': print('ok', sfx_track(a.events, a.out))
    else: mix(a.video, a.voice, a.sfx, a.out, a.music); print('ok', a.out)


if __name__ == '__main__': main()
