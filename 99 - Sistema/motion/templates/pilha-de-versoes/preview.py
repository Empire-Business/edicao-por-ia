#!/usr/bin/env python3
"""Prévia rápida de quadros (sem render): servidor local na porta 8799 + Chromium (playwright) + hf-seek.
Uso: preview.py <comp-dir-name> <saida-dir> t1 t2 ...   (ex.: preview.py comp tmp/prev 0.5 1.8 8.0)"""
import asyncio, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

J = Path(__file__).resolve().parents[1]
comp, out, ts = sys.argv[1], J / sys.argv[2], [float(x) for x in sys.argv[3:]]
out.mkdir(parents=True, exist_ok=True)
SRV = ('import http.server,functools\nclass S(http.server.ThreadingHTTPServer):\n    request_queue_size=256\n    daemon_threads=True\n'
       'S(("127.0.0.1",8799),functools.partial(http.server.SimpleHTTPRequestHandler,directory=".")).serve_forever()')
srv = subprocess.Popen([sys.executable, '-c', SRV], cwd=J, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
JS = """async (t)=>{ const tl=window.__timelines.main; tl.seek(t,false);
  document.querySelectorAll('video.clip').forEach(v=>{ const s=parseFloat(v.dataset.start), d=parseFloat(v.dataset.duration); v.currentTime=Math.max(0,Math.min(d-0.04,t-s)); });
  const ps=[]; window.dispatchEvent(new CustomEvent('hf-seek',{detail:{time:t,waitUntil:(p)=>ps.push(p)}})); await Promise.all(ps);
  await Promise.all([...document.querySelectorAll('video.clip')].map(v=>new Promise(r=>{ if(v.readyState>=2&&!v.seeking) r(); else v.addEventListener('seeked',()=>r(),{once:true}); setTimeout(r,1500); })));
  window.dispatchEvent(new CustomEvent('hf-seek',{detail:{time:t,waitUntil:(p)=>ps.push(p)}})); return true; }"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        msgs = []
        pg.on('console', lambda m: msgs.append(m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: msgs.append('PAGEERROR ' + str(e)))
        await pg.goto(f'http://127.0.0.1:8799/{comp}/index.html')
        for _ in range(120):
            if await pg.evaluate('!!(window.__timelines && window.__timelines.main)'): break
            await pg.wait_for_timeout(250)
        else:
            print('timeline não registrada'); print(msgs[:10]); return
        for t in ts:
            await pg.evaluate(JS, t)
            await pg.wait_for_timeout(120)
            await pg.screenshot(path=str(out / f't{t:06.2f}.png'), timeout=180000)
        await b.close()
        for m in msgs[:12]:
            print('console:', m[:300])


try:
    asyncio.run(main())
finally:
    srv.terminate()
