#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da voz final, das palavras alinhadas e de src/index.tpl.html.
ID04 Dourado + legenda L03 (uma palavra por vez; palavras curtas de função vão junto com a seguinte). Ideia: a IA é uma íris dourada
(mecanismo de diafragma 3D, lâminas reais em 3D) que "respira" com a própria voz; em "é melhor você ouvir quem já usa" a íris ABRE e revela
o Convidado (cliente, trecho real da live). Volta a IA: a íris fecha em parte, o ponteiro do aro marca "2 dias", o arco de "100%" acende.
CTA=comment gera a variante "Comente CORTEZ" em comp-cta-comment. Grava analysis/scene_plan.json, motion_plan.json e caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cta import snippets

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3), 'sp': w['speaker'], 'b': w['block']}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
SEGS = EDL['segments']
BLK = {}
for s in SEGS:
    b = BLK.setdefault(s['take'], {'start': s['start'], 'end': 0})
    b['end'] = round(s['start'] + (s['out'] - s['in']), 3)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9%]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0, end=False):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['e'] if end else x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


T = {'cortez': W('cortez'), 'uma': W('uma'), 's2': W('eu', 3.0), 'bom': W('bom'), 's3': W('mas'), 'quem': W('quem', 6.5), 'usa': W('usa'),
     'j1': BLK['j1']['start'], 'j1e': BLK['j1']['end'], 'caramba': W('caramba'), 'j2': BLK['j2']['start'], 'j2e': BLK['j2']['end'],
     'postei': W('postei'), 'editado': W('editado', 18.0), 'pct': W('100%'), 'd6b': BLK['d6b']['start'], 'tec': W('tecnológica'),
     'em': W('em', 24.0), 'dois': W('dois', 24.0), 'dias': W('dias', 24.0), 'editado2': W('editado', 26.0), 'cem': W('cem'), 'mim': W('mim'),
     'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['open0'] = round(T['quem'] - 0.25, 3); T['open1'] = round(T['j1'] + 0.15, 3)          # a íris abre em "quem já usa" → Convidado
T['cards0'] = round(T['s2'] - 0.05, 3); T['cardsOut'] = round(T['s3'] + 0.2, 3)
T['close0'] = round(T['d6b'] - 0.05, 3); T['close1'] = round(T['d6b'] + 0.75, 3)       # volta a IA: fecha em parte
T['reopen0'] = round(T['editado2'] - 0.1, 3); T['reopen1'] = round(T['editado2'] + 0.8, 3)
T['arc0'] = round(T['editado'] - 0.05, 3); T['arc1'] = round(T['pct'] + 0.45, 3)
T['rA0'] = round(W('já', 18.9) - 0.12, 3); T['rA1'] = round(T['d6b'] - 0.02, 3)     # Reel do Convidado: "Já tem um vídeo lá editado…"
T['rB0'] = round(T['em'] - 0.08, 3); T['rB1'] = round(T['editado2'] - 0.06, 3)       # Reel do Convidado: "Em dois dias, ele já tinha vídeo postado"
T['tap'] = round(SPEECH + 2.75, 3)

GL = '<em>'
HEADS = [
    ('h1', 0, T['s2'] - 0.08, 'Inteligência artificial', [('Eu sou o', 0), ('<em>Cortez.</em>', 0)]),
    ('h2', T['s2'], T['s3'] - 0.08, 'Editados pelo Cortez', [('Eu poderia dizer', T['s2'] + 0.02), ('<em>que sou bom…</em>', W('dizendo') - 0.1)]),
    ('h3', T['s3'], T['j1'] - 0.1, 'Prova real', [('Melhor ouvir', T['s3'] + 0.02), ('<em>quem já usa.</em>', T['quem'] - 0.12)]),
    ('h4', T['caramba'] - 0.08, T['j2'] - 0.12, 'Convidado · cliente', [('“Isso daqui é <em>sinistro</em>.”', T['caramba'] - 0.05)]),
    ('h5', T['editado'] - 0.1, T['j2e'] + 0.25, 'Convidado · cliente', [('“Editado <em>100%</em> pela ferramenta.”', T['editado'] - 0.08)]),
    ('h6', T['d6b'] + 0.05, T['em'] - 0.1, 'Cortez · IA', [('Ele não é', T['d6b'] + 0.1), ('<em>técnico.</em>', W('tecnológica') - 0.2)]),
    ('h7', T['em'], T['cta0'] - 0.05, 'Em dois dias', [('<em>2 dias.</em>', T['dois'] - 0.1), ('Vídeo postado.', W('postado') - 0.15)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.7, en - 0.34 - at)), 3)} for tx, at in lines_]})

# ---------- legenda L03: uma palavra por vez; palavra curta (≤ 2 letras ou < 0,16 s) vai junto com a seguinte ----------
KEY = {'cortez', 'bom', 'usa', 'sinistro', 'apresentador', '100%', 'ferramenta', 'tecnologica', 'dois', 'dias', 'cem', 'cento', 'mim', 'inteligencia', 'artificial',
       'quem', 'postei', 'editado', 'funcionamento', 'pratica', 'caramba', 'dinheiro', 'papo'}
groups, g = [], []
for i, w in enumerate(WORDS):
    g.append(w)
    nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    short = (len(norm(w['w'])) <= 2 or (w['e'] - w['s']) < 0.16) and not w['w'][-1] in '.,:?!'
    if nxt is None or nxt['b'] != w['b'] or not short or len(g) >= 3 or (nxt['s'] - w['e']) > 0.35:
        groups.append(g); g = []
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s'] - 0.03
    nx = groups[i + 1][0]['s'] - 0.03 if i + 1 < len(groups) else SPEECH
    e = min(nx, gw[-1]['e'] + 0.45) if (i + 1 < len(groups) and groups[i + 1][0]['b'] == gw[0]['b']) else gw[-1]['e'] + 0.22
    e = max(e, s + 0.12)
    sp = gw[0]['sp']
    parts = []
    for x in gw:
        cls = 'k' if norm(x['w']) in KEY else ''
        parts.append(f'<span class="{cls}">{html.escape(x["w"])}</span>')
    caps_html.append(f'<div class="cap {sp}" id="cg{i}"><span class="bx">{" ".join(parts)}</span></div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'sp': sp, 'text': ' '.join(x['w'] for x in gw)})

# a voz da IA move a íris: envelope por quadro (só onde a IA fala), suavizado
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(J / 'renders/voice.wav'), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(r, np.float32)
fr = np.array_split(x, int(round(len(x) / 16000 * 30)))
env = np.array([np.sqrt((s_ ** 2).mean() + 1e-12) for s_ in fr]); env = np.clip(env / np.percentile(env, 97), 0, 1)
k = np.array([.25, .5, .25]); env = np.convolve(env, k, mode='same')

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'env': [round(float(v), 3) for v in env],
        'blocks': BLK, 'jpre': [round(T['open0'] - 0.6, 3)], 'cards': ['c0', 'c1', 'c2', 'c3', 'c4', 'c5']}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}'))
CTA_MODE, _cta = snippets()
for k_, v in _cta.items():
    out = out.replace('{{' + k_ + '}}', v)
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if CTA_MODE != 'saiba':
    O = J / f'comp-cta-{CTA_MODE}'
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir(): d.mkdir(parents=True, exist_ok=True)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            if d.exists(): d.unlink()
            os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': CTA_MODE, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes += [{'id': 'hook', 'start': 0, 'end': T['s2'], 'label': 'macro das lâminas douradas da íris → recua e mostra o diafragma inteiro; a íris pulsa com a voz da IA'},
           {'id': 'cards', 'start': T['cards0'], 'end': T['cardsOut'] + 1.2, 'label': '6 entregas reais do Cortez orbitam a íris ("dizendo que sou bom") e recuam'},
           {'id': 'reveal', 'start': T['open0'], 'end': T['open1'], 'label': 'a íris abre e revela o Convidado (live real)'},
           {'id': 'convidado', 'start': T['j1'], 'end': T['j2e'], 'label': 'Convidado, cliente, trecho real da live — janela da íris aberta'},
           {'id': 'arc100', 'start': T['arc0'], 'end': T['arc1'], 'label': 'arco dourado do aro enche até 100% em "editado 100%"'},
           {'id': 'ai_back', 'start': T['d6b'], 'end': SPEECH, 'label': 'IA volta: íris fecha em parte; ponteiro do aro vai a "2 dias"; reabre em "editado cem por cento por mim"'},
           {'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': f'CTA escrito ({CTA_MODE})', 'title': 'Não acredite em mim. / Ouça quem usa. / Você grava. O Cortez edita. Você aprova.'}]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Bokeh + UnrealBloom + Output, stencil) via hf-seek',
    'identity': 'ID04', 'caption_style': 'L03', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['diafragma (íris) com 9 lâminas 3D extrudadas, máscara por stencil no círculo do alojamento, abertura poligonal que gira ao abrir',
                 'aro dourado extrudado com bisel, marcas gravadas (instanced), legendas gravadas em arco', 'janela do Convidado atrás das lâminas',
                 'arco de progresso 100% (tubo emissivo)', 'ponteiro "2 dias"', '6 cartões de prova orbitando', 'mostrador de fundo e brilho quente'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'T': {k_: T[k_] for k_ in ('s2', 's3', 'quem', 'j1', 'j2', 'd6b', 'dois', 'editado2', 'pct')}}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['sp'], c['text'])
