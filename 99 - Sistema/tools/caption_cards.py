"""Render one transparent PNG caption card per cue (local, Pillow).

Usage: caption_cards.py STYLE.json CUES.json OUTDIR
CUES.json: {"cues":[{"id":"0001","start":0.0,"end":1.0,"text":"linha 1\\nlinha 2"}]}
Also writes OUTDIR/overlay.ffconcat (blank card between cues) for an ffmpeg overlay track.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def hex_rgb(s):
    s = s.lstrip('#'); return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def main():
    style = json.load(open(sys.argv[1])); cues = json.load(open(sys.argv[2]))['cues']; out = sys.argv[3]
    os.makedirs(out, exist_ok=True)
    W = style['canvas']['width']; H = style['band']['height']
    f = style['font']; path = os.path.expanduser(f['file'])
    font = ImageFont.truetype(path, f['size'])
    sw = style['stroke']['width_px']; sc = hex_rgb(style['stroke']['color']); fill = hex_rgb(style['fill'])
    sh = style['shadow']; lh = int(f['size'] * f.get('line_spacing', 1.0))
    for c in cues:
        lines = c['text'].split('\n')
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        total = lh * len(lines); y0 = (H - total) // 2
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shadow)
        d = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            y = y0 + i * lh
            sd.text((W // 2, y + sh['offset_y']), line, font=font, anchor='ma', fill=hex_rgb(sh['color']) + (int(255 * sh['alpha']),), stroke_width=sw, stroke_fill=hex_rgb(sh['color']) + (int(255 * sh['alpha']),))
        shadow = shadow.filter(ImageFilter.GaussianBlur(sh['blur'] / 2))
        img = Image.alpha_composite(shadow, img); d = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            d.text((W // 2, y0 + i * lh), line, font=font, anchor='ma', fill=fill + (255,), stroke_width=sw, stroke_fill=sc + (255,))
        img.save(os.path.join(out, f"cue_{c['id']}.png"))
    Image.new('RGBA', (W, H), (0, 0, 0, 0)).save(os.path.join(out, 'blank.png'))
    # ffconcat timeline: blank between cues, exact durations
    lines = ['ffconcat version 1.0']; t = 0.0
    for c in cues:
        if c['start'] > t + 1e-3:
            lines += ['file blank.png', f"duration {c['start'] - t:.3f}"]
        lines += [f"file cue_{c['id']}.png", f"duration {c['end'] - c['start']:.3f}"]; t = c['end']
    lines += ['file blank.png', 'duration 1.000', 'file blank.png']
    open(os.path.join(out, 'overlay.ffconcat'), 'w').write('\n'.join(lines) + '\n')
    print(json.dumps({'cards': len(cues), 'font': os.path.basename(path)}))


if __name__ == '__main__':
    main()
