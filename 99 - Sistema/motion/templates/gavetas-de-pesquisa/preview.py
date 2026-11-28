#!/usr/bin/env python3
"""Prévia de quadros da composição no navegador (playwright + servidor local na porta 8792, exclusiva deste trabalho).
Uso: ../../../.venv/bin/python src/preview.py 0 1.2 3.4 ...   → tmp/prev/f_<t>.png (1080x1920) e tmp/prev/sheet.jpg"""
import subprocess, sys, time, http.server, threading, functools
from pathlib import Path
from playwright.sync_api import sync_playwright
J = Path(__file__).resolve().parents[1]
OUT = J / 'tmp/prev'; OUT.mkdir(parents=True, exist_ok=True)
class QH(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(QH, directory=str(J / 'comp'))
class Q(http.server.ThreadingHTTPServer): allow_reuse_address = True
srv = Q(('127.0.0.1', 8792), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
ts = [float(x) for x in sys.argv[1:]] or [0.0]
files = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--ignore-gpu-blocklist', '--enable-webgl'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    logs = []
    pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: logs.append(f'pageerror: {e}'))
    pg.goto('http://127.0.0.1:8792/index.html')
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
if len(files) > 1:
    n = len(files); cols = min(n, 6)
    args = sum([['-i', str(f)] for f in files], [])
    fl = ''.join(f'[{i}:v]scale=270:480[v{i}];' for i in range(n))
    rows = []
    for r in range(0, n, cols):
        ids = list(range(r, min(n, r + cols)))
        while len(ids) < cols: ids.append(None)
        rows.append(ids)
    parts = []
    for ri, ids in enumerate(rows):
        ins = ''.join(f'[v{i}]' if i is not None else '' for i in ids)
        cnt = sum(1 for i in ids if i is not None)
        parts.append(f'{ins}hstack=inputs={cnt}[r{ri}]' if cnt > 1 else f'{ins}null[r{ri}]')
    if len(rows) > 1:
        # pad last row
        last = [i for i in rows[-1] if i is not None]
        if len(last) < cols:
            parts[-1] = ''.join(f'[v{i}]' for i in last) + f'hstack=inputs={len(last)}[rr]' if len(last) > 1 else f'[v{last[0]}]null[rr]'
            parts[-1] += f';[rr]pad={cols*270}:480[r{len(rows)-1}]'
        parts.append(''.join(f'[r{i}]' for i in range(len(rows))) + f'vstack=inputs={len(rows)}[o]')
    else:
        parts[-1] = parts[-1].replace('[r0]', '[o]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args, '-filter_complex', fl + ';'.join(parts), '-map', '[o]', '-q:v', '3', str(OUT / 'sheet.jpg')], check=True)
print('ok', len(files))
