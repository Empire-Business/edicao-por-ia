#!/usr/bin/env python3
"""F21 Mural de investigação — renderizador determinístico seek(t) a partir de um roteiro de cenas.

Cada quadro 1080x1920 é desenhado a partir do tempo t (sem relógio simulado): cortiça gerada,
evidências que entram uma por vez, fios só onde a fala liga os itens, legenda karaokê das
palavras realmente ditas e barra de progresso. Cores vêm da ID visual escolhida.

  python tools/mural_board.py SPEC.json --identity context/visual-identities/ID09/identity-v1.json --keyframes 3,40
  python tools/mural_board.py SPEC.json --identity ... --render OUT.mp4 --workers 6

O roteiro (SPEC) fica no trabalho; caminhos relativos são resolvidos a partir dele.
"""
import argparse, json, math, random, subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

ENGINE = Path(__file__).resolve().parents[1]
FONTS = ENGINE / 'assets/fonts/portable'
W, H, FPS = 1080, 1920, 30

# Papéis de cor usados pelo mural; a ID escolhida preenche os que tiver.
C = dict(background='#0E0C08', surface='#5E4B30', text='#FFFFFF', muted='#8C8C8C', primary='#F2C230',
         alert='#D92B2B', pin_blue='#3A6FD8', card='#F1EEE6', card_ink='#1A1A1A', sticky='#F5E27A',
         string='#C8242A')
SPEC, BASE = {}, Path('.')


def rgb(h, a=255):
    h = C.get(h, h).lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


# ---------------------------------------------------------------- fontes
@lru_cache(None)
def font(kind, size):
    files = {'inter': ('inter-800-latin.woff2', None), 'inter7': ('inter-700-latin.woff2', None),
             'mono': ('jetbrains-mono-variable.ttf', 'ExtraBold'), 'monob': ('jetbrains-mono-variable.ttf', 'Bold'),
             'serif': ('libre-baskerville-variable.ttf', 'Bold'), 'serifr': ('libre-baskerville-variable.ttf', 'Regular')}
    name, var = files[kind]
    f = ImageFont.truetype(str(FONTS / name), size)
    if var:
        f.set_variation_by_name(var)
    return f


def text_img(text, fnt, fill, italic=0.0, spacing=0):
    """Texto em RGBA justo; italic = cisalhamento (itálico simulado, a Libre Baskerville local não tem itálico)."""
    widths = [fnt.getlength(ch) + spacing for ch in text] if spacing else None
    tw = int(sum(widths)) + 4 if spacing else int(fnt.getlength(text)) + 4
    asc, desc = fnt.getmetrics()
    th = asc + desc + 4
    pad = int(th * abs(italic)) + 4
    im = Image.new('RGBA', (tw + pad, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if spacing:
        x = 2
        for ch, w in zip(text, widths):
            d.text((x, 2), ch, font=fnt, fill=fill)
            x += w
    else:
        d.text((2, 2), text, font=fnt, fill=fill)
    if italic:
        im = im.transform(im.size, Image.AFFINE, (1, italic, -italic * th, 0, 1, 0), Image.BICUBIC)
        bb = im.getbbox()
        if bb:
            im = im.crop((bb[0], 0, bb[2], im.height))
    return im


def wrap(text, fnt, maxw):
    lines, cur = [], ''
    for word in text.split():
        t = (cur + ' ' + word).strip()
        if fnt.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- fundo de cortiça (gerado)
def make_background():
    rng = np.random.default_rng(7)

    def noise(scale):
        small = rng.random((H // scale + 2, W // scale + 2)).astype(np.float32)
        return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255.0

    n = 0.45 * noise(3) + 0.3 * noise(7) + 0.25 * noise(19)
    granules = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(granules)
    for _ in range(26000):
        x, y = rng.integers(0, W), rng.integers(0, H)
        r = rng.integers(2, 7)
        gd.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=int(rng.integers(60, 255)))
    g = np.asarray(granules.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0
    tex = np.clip(0.55 * n + 0.45 * g, 0, 1)
    col = np.array(rgb('surface')[:3], np.float32)[None, None, :] * (0.7 + 0.95 * tex[..., None])
    # vinheta forte: centro alto mais claro, bordas e terço inferior quase pretos (área da legenda)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.36) / (H * 0.6)) ** 2)
    v = np.clip(1.25 - d, 0, 1) ** 1.25 * (1 - 0.85 * np.clip((yy - H * 0.55) / (H * 0.35), 0, 1))
    dark = np.array(rgb('background')[:3], np.float32)
    return Image.fromarray(np.clip(dark + (col - dark) * v[..., None], 0, 255).astype(np.uint8)).convert('RGBA')


# ---------------------------------------------------------------- fotos e pictogramas
@lru_cache(None)
def real_photo(kind):
    """Foto real do trabalho (licença registrada), recortada pelo roteiro e em preto e branco."""
    v = SPEC['photos'][kind]
    im = Image.open(BASE / v['file']).convert('RGB')
    w, h = im.size
    b = v['box']
    im = im.crop((int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)))
    im = ImageOps.fit(im, tuple(v.get('size', (300, 290))), Image.LANCZOS, centering=tuple(v.get('center', (0.5, 0.5))))
    g = ImageOps.autocontrast(im.convert('L'), cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.08).point(lambda x, gm=v.get('gamma', 0.85): int(255 * (x / 255) ** gm))
    return g.convert('RGBA')


def photo(kind):
    """Foto real quando o roteiro a fornece; senão um pictograma claramente ilustrativo (nunca rosto inventado)."""
    if kind in SPEC.get('photos', {}):
        return real_photo(kind)
    S = 2
    pw, ph = 300 * S, 290 * S
    im = Image.new('L', (pw, ph), 70)
    d = ImageDraw.Draw(im)
    for y in range(ph):
        d.line((0, y, pw, y), fill=int(95 - 55 * y / ph))
    if kind == 'flower':  # vítima/pessoa que não deve ser exposta
        d.rectangle((0, 0, pw, ph), fill=28)
        cx, cy = pw * 0.52, ph * 0.42
        d.line((cx, cy, cx - 40 * S, ph), fill=120, width=8 * S)
        for k in range(6):
            pet = Image.new('L', (pw, ph), 0)
            ImageDraw.Draw(pet).ellipse((cx - 30 * S, cy - 105 * S, cx + 30 * S, cy), fill=235)
            im.paste(225, (0, 0), pet.rotate(math.degrees(k * math.pi / 3 + 0.3), center=(cx, cy), resample=Image.BICUBIC))
        d.ellipse((cx - 16 * S, cy - 16 * S, cx + 16 * S, cy + 16 * S), fill=150)
        for k in range(6):
            a = k * math.pi / 3
            d.line((cx, cy, cx + 40 * S * math.cos(a), cy + 40 * S * math.sin(a)), fill=110, width=3 * S)
    elif kind in ('person', 'unknown'):  # identidade não fornecida
        d.rectangle((0, 0, pw, ph), fill=38)
        cx = pw / 2
        d.ellipse((cx - 62 * S, ph * 0.18, cx + 62 * S, ph * 0.18 + 124 * S), fill=12)
        d.ellipse((cx - 135 * S, ph * 0.66, cx + 135 * S, ph * 1.4), fill=12)
        if kind == 'unknown':
            d.text((cx, ph * 0.18 + 62 * S), '?', font=font('inter', 70 * S), fill=150, anchor='mm')
    elif kind == 'city':
        rnd = random.Random(3)
        x = 10 * S
        while x < pw:
            bw, bh = rnd.randint(18, 40) * S, rnd.randint(20, 70) * S
            d.rectangle((x, ph * 0.62 - bh, x + bw, ph * 0.62), fill=rnd.randint(45, 70))
            x += bw + 4 * S
    arr = np.asarray(im, np.float32) + np.random.default_rng(len(kind)).normal(0, 9, (ph, pw))
    yy, xx = np.mgrid[0:ph, 0:pw]
    v = 1 - 0.35 * (((xx - pw / 2) / (pw / 2)) ** 2 + ((yy - ph / 2) / (ph / 2)) ** 2)
    arr = np.clip(arr * np.clip(v, 0.4, 1), 0, 255).astype(np.uint8)
    return Image.fromarray(arr).resize((pw // S, ph // S), Image.LANCZOS).convert('RGBA')


# ---------------------------------------------------------------- componentes do mural
def with_shadow(im, pin=None, blur=12, off=(8, 14), op=150):
    pad = 46
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 255))
    sh.putalpha(im.split()[3].point(lambda v: v * op // 255))
    layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
    layer.paste(sh, (pad + off[0], pad + off[1]))
    out.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (pad, pad))
    if pin:
        draw_pin(out, out.width // 2, pad + 6, pin)
    return out


def draw_pin(im, x, y, color):
    d = ImageDraw.Draw(im)
    d.ellipse((x - 8, y - 5, x + 18, y + 21), fill=(0, 0, 0, 110))
    d.ellipse((x - 15, y - 15, x + 15, y + 15), fill=rgb(color))
    d.ellipse((x - 8, y - 10, x + 1, y - 2), fill=(255, 255, 255, 140))


def polaroid(kind, label, scale=1.0, label_style='hand', pin='string'):
    pic = photo(kind)
    pw, ph = pic.size
    m, bottom = 18, 92 if label_style == 'hand' else 120
    card = Image.new('RGBA', (pw + 2 * m, ph + m + bottom), rgb('#F4F2EC'))
    card.alpha_composite(pic, (m, m))
    if label_style == 'hand':
        t = text_img(label, font('serifr', 30), rgb('#2A2A2A'), italic=-0.25)
        card.alpha_composite(t, ((card.width - t.width) // 2, ph + m + (bottom - t.height) // 2))
    else:  # rótulo de status jurídico em mono vermelho
        y = ph + m + 14
        for ln in label.split('\n'):
            t = text_img(ln, font('mono', 22), rgb('alert'))
            card.alpha_composite(t, ((card.width - t.width) // 2, y))
            y += 30
    credit = SPEC.get('photos', {}).get(kind, {}).get('credit')
    if credit:  # crédito exigido pela licença da foto
        cr = text_img('Foto: ' + credit, font('monob', 13), rgb('#8A8780'))
        card.alpha_composite(cr, (card.width - cr.width - 10, card.height - cr.height - 4))
    if scale != 1.0:
        card = card.resize((int(card.width * scale), int(card.height * scale)), Image.LANCZOS)
    return with_shadow(card, pin=pin)


def index_card(title, body='', stripe='alert', width=430, title_size=46):
    fb = font('monob', 24)
    lines = wrap(body.upper(), fb, width - 50) if body else []
    hgt = 30 + 64 + 34 * len(lines) + 26
    card = Image.new('RGBA', (width, hgt), rgb('card'))
    d = ImageDraw.Draw(card)
    for y in range(76, hgt, 34):
        d.line((0, y, width, y), fill=rgb('#B9C9E6', 120), width=2)
    d.rectangle((0, 0, width, 9), fill=rgb(stripe))
    card.alpha_composite(text_img(title, font('mono', title_size), rgb('alert' if stripe == 'alert' else 'card_ink')), (24, 22))
    y = 82
    for ln in lines:
        card.alpha_composite(text_img(ln, fb, rgb('#2C2C2C')), (24, y))
        y += 34
    return with_shadow(card, pin='string' if stripe == 'alert' else 'pin_blue')


def sticky(text, width=560, size=40, color='sticky'):
    f = font('inter', size)
    lines = wrap(text.upper(), f, width - 70)
    lh = int(size * 1.12)
    note = Image.new('RGBA', (width, 56 + lh * len(lines) + 40), rgb(color))
    ImageDraw.Draw(note).rectangle((0, 0, width, 24), fill=(0, 0, 0, 18))
    y = 50
    for ln in lines:
        t = text_img(ln, f, rgb('#2B2510'), italic=-0.12)
        note.alpha_composite(t, ((width - t.width) // 2, y))
        y += lh
    return with_shadow(note, pin='pin_blue')


def act_tag(n, title):
    f = font('mono', 38)
    a = text_img(f'ATO {n}', f, rgb('#FFFFFF'), spacing=2)
    b = text_img(title, f, rgb('#FFFFFF'), spacing=2)
    h = 64
    im = Image.new('RGBA', (a.width + b.width + 64, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, a.width + 28, h), fill=rgb('alert'))
    d.rectangle((a.width + 28, 0, im.width, h), fill=rgb('#141210'))
    im.alpha_composite(a, (14, (h - a.height) // 2))
    im.alpha_composite(b, (a.width + 42, (h - b.height) // 2))
    return with_shadow(im, blur=8, off=(4, 6))


def case_tag(text):
    t = text_img(text, font('mono', 24), rgb('#FFFFFF'), spacing=1)
    im = Image.new('RGBA', (t.width + 40, 46), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, 45), 8, fill=rgb('#141210', 235), outline=rgb('alert'), width=3)
    im.alpha_composite(t, (20, (46 - t.height) // 2))
    return im


def counter(n, total=4, label='ACUSAÇÃO'):
    f = font('mono', 36)
    a = text_img(label, f, rgb('#FFFFFF'), spacing=3)
    num = text_img(str(n), f, rgb('#FFFFFF'))
    b = text_img(f'DE {total}', f, rgb('#FFFFFF'), spacing=3)
    h = 60
    im = Image.new('RGBA', (a.width + num.width + b.width + 80, h), (0, 0, 0, 0))
    im.alpha_composite(a, (0, (h - a.height) // 2))
    x = a.width + 16
    ImageDraw.Draw(im).rectangle((x, 4, x + num.width + 22, h - 4), fill=rgb('alert'))
    im.alpha_composite(num, (x + 11, (h - num.height) // 2))
    im.alpha_composite(b, (x + num.width + 40, (h - b.height) // 2))
    return with_shadow(im, blur=8, off=(3, 5), op=180)


def stamp(text, color='alert', size=96):
    t = text_img(text, font('inter', size), rgb(color))
    im = Image.new('RGBA', (t.width + 60, t.height + 36), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((4, 4, im.width - 5, im.height - 5), 10, outline=rgb(color), width=9)
    im.alpha_composite(t, (30, 16))
    a = np.asarray(im.split()[3], np.float32)  # tinta de carimbo irregular
    a *= np.clip(np.random.default_rng(11).normal(0.92, 0.18, a.shape), 0.25, 1)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def outline_box(text, size=84):
    ts = [text_img(l, font('inter', size), rgb('#FFFFFF')) for l in text.split('\n')]
    w, h = max(t.width for t in ts) + 70, sum(t.height for t in ts) + 50
    im = Image.new('RGBA', (w, h), (0, 0, 0, 120))
    ImageDraw.Draw(im).rectangle((3, 3, w - 4, h - 4), outline=rgb('#FFFFFF'), width=6)
    y = 25
    for t in ts:
        im.alpha_composite(t, ((w - t.width) // 2, y))
        y += t.height
    return im


def banner(parts, size=50):
    """Faixa clara com trechos coloridos: [[texto, cor]]."""
    ts = [text_img(t, font('inter', size), rgb(c)) for t, c in parts]
    w, h = sum(t.width for t in ts) + 50, max(t.height for t in ts) + 26
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), 10, fill=rgb('#F4F2EC'))
    x = 25
    for t in ts:
        im.alpha_composite(t, (x, (h - t.height) // 2))
        x += t.width
    return with_shadow(im, blur=8, off=(4, 6))


def lines_block(lines, size=58):
    """Linhas centralizadas com contorno escuro; cada linha = [[texto, cor]]."""
    rows = [[text_img(t, font('inter', size), rgb(c)) for t, c in parts] for parts in lines]
    lh = int(size * 1.08)
    im = Image.new('RGBA', (max(sum(t.width for t in r) for r in rows) + 10, lh * len(rows) + 16), (0, 0, 0, 0))
    y = 4
    for r in rows:
        x = (im.width - sum(t.width for t in r)) // 2
        for t in r:
            im.alpha_composite(t, (x, y))
            x += t.width
        y += lh
    blk = Image.new('RGBA', im.size, (0, 0, 0, 255))
    blk.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: min(255, v * 2)))
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.alpha_composite(blk)
    out.alpha_composite(im)
    return out


def quote_card(lines, label):
    lab = text_img(label, font('mono', 20), rgb('#FFFFFF'), spacing=1)
    ts = [[text_img(t, font('inter', 38), rgb(c)) for t, c in parts] for parts in lines]
    w = max(max(sum(t.width for t in r) for r in ts), lab.width) + 70
    h = 70 + 46 * len(ts) + 30
    im = Image.new('RGBA', (w, h), rgb('#141210', 240))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 9, h), fill=rgb('alert'))
    d.ellipse((30, 26, 42, 38), fill=rgb('alert'))
    im.alpha_composite(lab, (52, 20))
    y = 66
    for r in ts:
        x = 34
        for t in r:
            im.alpha_composite(t, (x, y))
            x += t.width
        y += 46
    return with_shadow(im, blur=10, off=(5, 8))


def pill(text, fill='alert', ink='#FFFFFF', size=36):
    t = text_img(text, font('inter', size), rgb(ink))
    im = Image.new('RGBA', (t.width + 70, t.height + 30), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=rgb(fill))
    im.alpha_composite(t, (35, 15))
    return with_shadow(im, blur=8, off=(3, 6))


def small_label(text, fill='primary', ink='#1A1A1A', size=20):
    t = text_img(text, font('mono', size), rgb(ink), spacing=1)
    im = Image.new('RGBA', (t.width + 24, t.height + 10), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 6, fill=rgb(fill))
    im.alpha_composite(t, (12, 5))
    return im


def bracket(text, width):
    t = text_img(text, font('mono', 30), rgb('primary'), spacing=1)
    im = Image.new('RGBA', (max(width, t.width) + 20, t.height + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1, y = (im.width - width) // 2, (im.width + width) // 2, t.height + 18
    for seg in ((x0, y, x1, y), (x0, y - 14, x0, y + 14), (x1, y - 14, x1, y + 14)):
        d.line(seg, fill=rgb('primary'), width=5)
    im.alpha_composite(t, ((im.width - t.width) // 2, 0))
    return im


COMPONENTS = {f.__name__: f for f in (case_tag, polaroid, index_card, sticky, act_tag, counter, stamp, outline_box,
                                       banner, lines_block, quote_card, pill, small_label, bracket)}


# ---------------------------------------------------------------- linha do tempo
class El:
    def __init__(self, item):
        self.id, self.kind = item['id'], item['type']
        self.args = {k: v for k, v in item.items() if k not in ('id', 'type', 'x', 'y', 't_in', 't_out', 'rot', 'enter')}
        self.x, self.y, self.t_in = item['x'], item['y'], item['t_in']
        self.t_out = item.get('t_out', SPEC['duration'] + 1)
        self.rot, self.enter = item.get('rot', 0.0), item.get('enter', 'drop')
        self._raw, self._sprite = None, None

    @property
    def raw(self):
        if self._raw is None:
            self._raw = COMPONENTS[self.kind](**self.args)
        return self._raw

    @property
    def sprite(self):
        if self._sprite is None:
            self._sprite = self.raw.rotate(self.rot, Image.BICUBIC, expand=True) if self.rot else self.raw
        return self._sprite

    def pin_point(self):
        dy = -(self.raw.height / 2) + 52
        a = math.radians(self.rot)  # PIL gira no sentido anti-horário para ângulos positivos
        return self.x + dy * math.sin(a), self.y + dy * math.cos(a)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


ENTER, EXIT = 0.38, 0.22


def state(e, t):
    """(alpha, dx, dy, scale) do elemento no instante t, ou None se fora de cena."""
    if t < e.t_in or t >= e.t_out:
        return None
    p, q = (t - e.t_in) / ENTER, (e.t_out - t) / EXIT
    a = ease(p) * (ease(q) if q < 1 else 1.0)
    if e.enter == 'drop':
        return a, 0, -36 * (1 - ease(p)), 1.06 - 0.06 * ease(p)
    if e.enter == 'stamp':
        return a, 0, 0, 1.35 - 0.35 * ease(p * 1.6)
    if e.enter == 'slide':
        return a, -60 * (1 - ease(p)), 0, 1.0
    return a, 0, 0, 1.0


def paste(frame, im, cx, cy, alpha, scale):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v, a=alpha: int(v * a)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    sx, sy, ex, ey = max(0, -x), max(0, -y), min(im.width, W - x), min(im.height, H - y)
    if ex <= sx or ey <= sy:
        return
    if sx or sy or ex < im.width or ey < im.height:
        im = im.crop((sx, sy, ex, ey))
    frame.alpha_composite(im, (x + sx, y + sy))


def draw_string(frame, a, b, t0, t1, t):
    """Fio vermelho entre pinos, atrás das evidências; só onde a fala sustenta a ligação."""
    if t < t0 or t >= t1:
        return
    p, fade = ease((t - t0) / 0.45), min(1.0, (t1 - t) / EXIT)
    (x0, y0), (x1, y1) = a.pin_point(), b.pin_point()
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + 40 + 0.08 * math.hypot(x1 - x0, y1 - y0)
    pts = []
    for i in range(41):
        u = i / 40 * p
        pts.append(((1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u ** 2 * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u ** 2 * y1))
    d = ImageDraw.Draw(frame)
    d.line([(x + 4, y + 7) for x, y in pts], fill=(0, 0, 0, int(90 * fade)), width=5)
    d.line(pts, fill=rgb('string', int(255 * fade)), width=5)


def draw_circle(frame, e, t0, t1, t):
    if t < t0 or t >= t1:
        return
    p = ease((t - t0) / 0.6)
    rx, ry = e.raw.width / 2 - 40, e.raw.height / 2 - 34
    pts = [(e.x + rx * 1.05 * math.cos(math.radians(-100 + 380 * i / 90)), e.y + 6 + ry * 1.08 * math.sin(math.radians(-100 + 380 * i / 90)))
           for i in range(int(90 * p) + 1)]
    if len(pts) > 1:
        ImageDraw.Draw(frame).line(pts, fill=rgb('string'), width=8, joint='curve')


# ---------------------------------------------------------------- legenda karaokê (palavras realmente ditas)
def chunk_words(words, breaks):
    chunks, cur = [], []
    for w in words:
        if cur:
            crossed = any((cur[-1][1] < b) != (w[1] < b) for b in breaks)  # troca de quem fala
            gap = w[1] - cur[-1][2]
            chars = sum(len(x[0]) for x in cur) + len(w[0])
            if crossed or len(cur) >= 3 or gap > 0.35 or chars > 20 or cur[-1][0][-1:] in '.,?!:':
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1][0][1] if i + 1 < len(chunks) else SPEC['duration']
        out.append((c, c[0][1] - 0.04, min(nxt - 0.02, c[-1][2] + 0.7)))
    return out


@lru_cache(None)
def word_img(word, spoken, key):
    clean = word.strip('.,?!:;“”"')
    if key:  # palavra-chave em serifa itálica na cor principal da ID
        return text_img(clean, font('serif', 58), rgb('primary') if spoken else rgb('primary', 110), italic=-0.22)
    return text_img(clean, font('inter7', 60), rgb('#FFFFFF') if spoken else rgb('muted', 150))


def draw_caption(frame, chunks, keys, t):
    for c, a, b in chunks:
        if a <= t < b:
            imgs = [word_img(w, t >= s, w.strip('.,?!:;“”"').lower() in keys) for w, s, e in c]
            x = (W - (sum(i.width for i in imgs) + 16 * (len(imgs) - 1))) // 2
            for im in imgs:
                frame.alpha_composite(im, (int(x), 1420 - im.height // 2 + (4 if im.height < 70 else 0)))
                x += im.width + 16
            return


# ---------------------------------------------------------------- forma de onda real (áudio de arquivo)
def load_envelope(audio):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a, hop = np.frombuffer(raw, np.float32), 8000 // 60
    env = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    return env / (env.max() + 1e-9)


def draw_wave(frame, env, wave, t):
    t0, t1, l0, l1 = wave['t0'], wave['t1'], wave['live_t0'], wave['live_t1']
    if not (t0 <= t < t1):
        return
    alpha = ease((t - t0) / 0.4) * (1 - ease((t - (t1 - 0.25)) / 0.25))
    d = ImageDraw.Draw(frame)
    n, bw, gap, yc = 44, 10, 8, wave.get('y', 1010)
    x0 = (W - n * (bw + gap)) // 2
    for k in range(n):
        tt = t - (n - k) * 0.03
        idx = int(tt * 60)
        live = l0 <= tt <= l1
        v = env[idx] if 0 <= idx < len(env) else 0
        hgt = 8 + (v * 120 if live else 4)
        col = rgb('primary', int(255 * alpha)) if live else rgb('muted', int(160 * alpha))
        cx = x0 + k * (bw + gap)
        d.rounded_rectangle((cx, yc - hgt / 2, cx + bw, yc + hgt / 2), 4, fill=col)


# ---------------------------------------------------------------- composição
STATE = {}


def init(spec_path, identity_path):
    global SPEC, BASE
    if STATE:
        return
    BASE = Path(spec_path).resolve().parent
    SPEC = json.loads(Path(spec_path).read_text(encoding='utf-8'))
    if identity_path:
        palette = json.loads(Path(identity_path).read_text(encoding='utf-8'))['palette']
        C.update({k: v for k, v in palette.items() if k in C})
    els = [El(item) for item in SPEC['elements']]
    by_id = {e.id: e for e in els}
    words = json.loads((BASE / SPEC['captions']['words']).read_text(encoding='utf-8'))
    STATE.update(
        els=els,
        strings=[(by_id[a], by_id[b], t0, t1) for a, b, t0, t1 in SPEC.get('strings', [])],
        circles=[(by_id[a], t0, t1) for a, t0, t1 in SPEC.get('circles', [])],
        chunks=chunk_words([tuple(w) for w in words], SPEC['captions'].get('speaker_breaks', [])),
        keys={k.lower() for k in SPEC['captions'].get('keywords', [])},
        env=load_envelope(BASE / SPEC['audio']) if SPEC.get('wave') else None,
        bg=make_background())


def frame_at(t):
    fr = STATE['bg'].copy()
    for a, b, t0, t1 in STATE['strings']:
        draw_string(fr, a, b, t0, t1, t)
    for e in STATE['els']:
        st = state(e, t)
        if st:
            a, dx, dy, sc = st
            paste(fr, e.sprite, e.x + dx, e.y + dy, a, sc)
    for e, t0, t1 in STATE['circles']:
        draw_circle(fr, e, t0, t1, t)
    if SPEC.get('wave'):
        draw_wave(fr, STATE['env'], SPEC['wave'], t)
    draw_caption(fr, STATE['chunks'], STATE['keys'], t)
    ImageDraw.Draw(fr).rectangle((0, 0, int(W * t / SPEC['duration']), 7), fill=rgb('alert'))
    return fr.convert('RGB')


def render_range(args):
    spec, identity, i0, i1, out = args
    init(spec, identity)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec')
    ap.add_argument('--identity', help='identity-v1.json da ID escolhida (paleta)')
    ap.add_argument('--keyframes', help='tempos separados por vírgula; PNGs ao lado do roteiro em keyframes/')
    ap.add_argument('--render', help='MP4 de saída (novo caminho; nunca sobrescreve originais)')
    ap.add_argument('--workers', type=int, default=6)
    a = ap.parse_args()
    init(a.spec, a.identity)
    if a.keyframes:
        outd = BASE / 'keyframes'
        outd.mkdir(exist_ok=True)
        for t in a.keyframes.split(','):
            frame_at(float(t)).save(outd / f'k{float(t):07.2f}.png')
    if a.render:
        from multiprocessing import Pool
        dur = SPEC['duration']
        n, tmp = int(round(dur * FPS)), BASE / 'tmp'
        tmp.mkdir(exist_ok=True)
        step = math.ceil(n / a.workers)
        parts = [(a.spec, a.identity, k * step, min(n, (k + 1) * step), str(tmp / f'part{k}.mp4')) for k in range(a.workers)]
        with Pool(a.workers) as pool:
            pool.map(render_range, parts)
        lst = tmp / 'parts.txt'
        lst.write_text(''.join(f"file '{Path(p[-1]).as_posix()}'\n" for p in parts), encoding='utf-8')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst),
                        '-i', str(BASE / SPEC['audio']), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-af', f'atrim=0:{dur},afade=t=in:d=0.005,afade=t=out:st={dur - 0.3}:d=0.3,'
                               'loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000',
                        '-c:a', 'aac', '-b:a', '192k', '-t', str(dur), '-movflags', '+faststart', a.render], check=True)
        print(a.render)


if __name__ == '__main__':
    main()
