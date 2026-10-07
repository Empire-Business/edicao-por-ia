"""Bundle overlay.src.html + layout.json + studio assets into index.html/spec.json for tools/studio_render.py."""
import hashlib, json, os
V = os.path.dirname(os.path.abspath(__file__)); J = os.path.dirname(V)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
lay = json.load(open(os.path.join(V, 'layout.json'), encoding='utf-8'))
src = open(os.path.join(V, 'overlay.src.html'), encoding='utf-8').read()
adir = os.path.join(J, 'assets', 'studio')
ids = [f[:-4] for f in sorted(os.listdir(adir)) if f.split('-')[0] in ('p', 'c', 'l', 'h1') and f.endswith(('.jpg', '.png'))]
html = src.replace('/*LAYOUT*/null', json.dumps(lay, ensure_ascii=False)).replace('/*IMGS*/[]', json.dumps(ids))
open(os.path.join(V, 'index.html'), 'w', encoding='utf-8').write(html)
assets = []
for i in ids:
    fn = next(f for f in os.listdir(adir) if f.startswith(i + '.'))
    p = os.path.join(adir, fn)
    assets.append({'id': i, 'path': os.path.relpath(p, V).replace('\\', '/'), 'sha256': sha(p), 'mime': 'image/png' if fn.endswith('.png') else 'image/jpeg'})
n = round(lay['duration'] * lay['fps'])
spec = {'schema_version': 1, 'id': 'empire-ikea-overlay', 'child_id': 'video-26afc23b9c24', 'width': 1080, 'height': 1920, 'fps': lay['fps'],
        'duration_frames': n, 'mode': 'overlay', 'entry': {'path': 'index.html', 'sha256': sha(os.path.join(V, 'index.html'))}, 'assets': assets}
json.dump(spec, open(os.path.join(V, 'spec.json'), 'w', encoding='utf-8'), indent=1)
print(n, 'frames', len(assets), 'assets')

