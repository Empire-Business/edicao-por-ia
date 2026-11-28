#!/usr/bin/env python3
"""Prévia de quadros da composição no navegador (playwright + servidor local na porta 8781, exclusiva deste trabalho).
Uso: ../../../.venv/bin/python src/preview.py [--comp comp-cta-comment] 0 1.2 3.4 ...  → tmp/prev/f_<t>.png (1080x1920) e tmp/prev/sheet.jpg"""
import sys, http.server, threading, functools
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
J = Path(__file__).resolve().parents[1]
OUT = J / 'tmp/prev'; OUT.mkdir(parents=True, exist_ok=True)
args = sys.argv[1:]; comp = 'comp'
if args and args[0] == '--comp':
    comp = args[1]; args = args[2:]
class QH(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class Q(http.server.ThreadingHTTPServer): allow_reuse_address = True
srv = Q(('127.0.0.1', 8781), functools.partial(QH, directory=str(J / comp))); threading.Thread(target=srv.serve_forever, daemon=True).start()
ts = [float(x) for x in args] or [0.0]
files = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--ignore-gpu-blocklist', '--enable-webgl'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    logs = []
    pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: logs.append(f'pageerror: {e}'))
    pg.goto('http://127.0.0.1:8781/index.html')
    for _ in range(120):
        if pg.evaluate('window.__mod===true && !!(window.__timelines && window.__timelines.main)'): break
        pg.wait_for_timeout(500)
    else:
        print('\n'.join(logs[:20])); raise SystemExit('falhou: módulo não carregou')
    for t in ts:
        pg.evaluate("""async (t)=>{ window.__timelines.main.seek(t); const ps=[]; window.dispatchEvent(new CustomEvent('hf-seek',{detail:{time:t, waitUntil:(q)=>ps.push(q)}})); await Promise.all(ps); }""", t)
        f = OUT / f'f_{t:06.2f}.png'; pg.screenshot(path=str(f)); files.append(f)
    b.close()
srv.shutdown()
for l in logs[:20]: print(l)
cols = min(len(files), 6); rows = -(-len(files) // cols)
sheet = Image.new('RGB', (cols * 270, rows * 480), (0, 0, 0))
for i, f in enumerate(files):
    sheet.paste(Image.open(f).convert('RGB').resize((270, 480), Image.LANCZOS), ((i % cols) * 270, (i // cols) * 480))
sheet.save(OUT / 'sheet.jpg', quality=88)
print('ok', len(files))
