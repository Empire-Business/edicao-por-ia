#!/usr/bin/env python3
"""QA visual: folha de quadros (1 por segundo, com o tempo) e quadros em resolução cheia de momentos-chave. Uso: qa_sheet.py <video> <saida.jpg> [t1 t2 ...]"""
import io, subprocess, sys
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
ts = [float(x) for x in sys.argv[3:]] or [i + 0.5 for i in range(int(dur))]
ims = []
for t in ts:
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', '-vf', 'scale=216:384', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    im = Image.open(io.BytesIO(r)).convert('RGB'); d = ImageDraw.Draw(im); d.rectangle([0, 0, 52, 16], fill='black'); d.text((3, 2), f'{t:.1f}', fill='yellow'); ims.append(im)
cols = 10; rows = -(-len(ims) // cols); g = Image.new('RGB', (216 * cols, 384 * rows), 'white')
for i, im in enumerate(ims): g.paste(im, ((i % cols) * 216, (i // cols) * 384))
g.save(out, quality=85)
