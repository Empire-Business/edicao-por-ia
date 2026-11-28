#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da voz final, da transcrição alinhada e de src/index.tpl.html.
ID05 Roxo + legenda L04 (bloco visível, palavra falada muda de cor). Tempos = palavras da narração ElevenLabs deslocadas pelos respiros.
CTA=comment gera a variante "Comente CORTEZ" numa comp separada (comp-cta-comment) com os mesmos materiais.
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
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
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0, end=False):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['e'] if end else x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


T = {'s2': W('essa'), 'c0': W('e', 3.0), 'tbn': W('também'), 'd0': W('eu', 5.8), 'cortez': W('cortez'), 's5': W('eu', 9.0), 'esc': W('escolhi'),
     'cenas': W('cenas'), 'cut': W('cortei'), 'leg': W('legendei'), 'anim': W('animei'), 'tudo': W('tudo'), 'soz': W('sozinho'),
     's6': W('e', 13.8), 'deixar': W('deixar'), 'cara': W('cara'), 's7': W('agora'), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['wire0'] = round(T['c0'] + 0.05, 3); T['wire1'] = round(T['wire0'] + 0.95, 3)
T['sweep0'] = round(T['d0'] - 0.15, 3); T['sweep1'] = round(T['sweep0'] + 1.25, 3)
T['lock'] = round(T['cenas'] - 0.02, 3); T['pick'] = round(T['lock'] + 0.45, 3)
T['cutMid'] = round(T['cut'] + 0.11, 3)
T['hero'] = round(T['deixar'] - 0.05, 3); T['heroOut'] = round(T['s7'] + 0.1, 3)
T['lite0'] = round(T['s7'] - 0.02, 3); T['slot0'] = round(T['s7'] + 0.5, 3)
T['tap'] = round(SPEECH + 2.75, 3)
assert T['pick'] < T['cut'] - 0.02, (T['pick'], T['cut'])

HEADS = [
    ('h1', 0, T['s2'] - 0.05, 'Uma confissão', [('Uma coisa sobre', 0), ('<em>este vídeo.</em>', 0)], False),
    ('h2', T['s2'], T['c0'] - 0.05, 'A voz', [('Não é', W('não', 1.9) - 0.1), ('<em>humana.</em>', W('pessoa') - 0.15)], False),
    ('h3', T['c0'], T['d0'] - 0.1, 'A edição', [('<em>Também não.</em>', T['tbn'] - 0.1)], False),
    ('h4', T['d0'], T['s5'] - 0.1, 'Inteligência artificial', [('Eu sou', T['d0'] + 0.05), ('<em>o Cortez.</em>', T['cortez'] - 0.15)], False),
    ('h5', T['s5'] - 0.1, T['s6'] - 0.2, 'O que eu fiz', [], False),
    ('h6', T['s6'], T['heroOut'], 'Vídeo editado pelo Cortez', [('Sem cara de <em>IA.</em>', T['s6'] + 0.1)], False),
    ('h7', T['s7'], T['cta0'] - 0.05, 'Agora', [('Imagina isso', W('imagina') - 0.1), ('<em>nos seus vídeos.</em>', W('seus') - 0.25)], True),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_, lite in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd{" lite" if lite else ""}" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.7, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legendas L04: uma ideia por bloco (frases da narração; quebras extras nas vírgulas longas), até 2 linhas
BREAK = {W('uma', 6.5), W('cortei'), W('tudo'), W('de', 14.5), W('com', 15.0)}
groups, g = [], []
for w in WORDS:
    if g and (g[-1]['w'][-1] in '.?!' or w['s'] in BREAK):
        groups.append(g); g = []
    g.append(w)
if g: groups.append(g)


def lines(ws):
    if len(' '.join(x['w'] for x in ws)) <= 26:
        return [ws]
    best, bi = 1e9, 1
    for k in range(1, len(ws)):
        a = len(' '.join(x['w'] for x in ws[:k])); b = len(' '.join(x['w'] for x in ws[k:]))
        score = max(a, b) - (4 if ws[k - 1]['w'][-1] in ',;' else 0)
        if score < best:
            best, bi = score, k
    return [ws[:bi], ws[bi:]]


caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = 0.0 if i == 0 else gw[0]['s'] - 0.04
    e = groups[i + 1][0]['s'] - 0.04 if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.5 else gw[-1]['e'] + 0.3
    e = min(e, SPEECH)
    ls, j, spans = lines(gw), 0, []
    for ln in ls:
        parts = []
        for x in ln:
            parts.append(f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>')
            j += 1
        spans.append(f'<span class="cl">{" ".join(parts)}</span>')
    lite = s >= T['lite0'] - 0.05
    hero = s < T['heroOut'] and e > T['s6'] - 0.1
    top = 1466 if hero else 1330 - (64 if len(ls) == 2 else 0)
    caps_html.append(f'<div class="cap{" lite" if lite else ""}" id="cg{i}" style="top:{top}px"><span class="bx">{"".join(spans)}</span></div>')
    ww = [x for ln in ls for x in ln]
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'lite': lite,
                      'w': [{'s': x['s'], 'e': round(min(x['e'] + 0.05, ww[k + 1]['s']) if k + 1 < len(ww) else x['e'] + 0.15, 3)} for k, x in enumerate(ww)],
                      'text': ' / '.join(' '.join(x['w'] for x in ln) for ln in ls)})

# a voz real como escultura: 180 barras = envelope RMS da narração; envelope por quadro para o pulso da cabeça de leitura
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(J / 'renders/voice.wav'), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(r, np.float32)
NB = 180
sl = np.array_split(x, NB)
bars = np.array([np.sqrt((s_ ** 2).mean() + 1e-12) for s_ in sl]); bars = (bars / bars.max()) ** 0.7
fr = np.array_split(x, int(len(x) / 16000 * 30))
env = np.array([np.sqrt((s_ ** 2).mean() + 1e-12) for s_ in fr]); env = np.clip(env / np.percentile(env, 98), 0, 1)

SCN = ['agenda', 'reuniao', 'escritorio', 'callcenter', 'relogio', 'crm']
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'scenes': SCN, 'pickIndex': SCN.index('callcenter'),
        'bars': [round(float(v), 4) for v in bars], 'env': [round(float(v), 3) for v in env]}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{HERO_START}}', f'{T["anim"]:.3f}').replace('{{HERO_DUR}}', f'{min(6.3, DUR - T["anim"]):.3f}'))
CTA_MODE, _cta = snippets()
for k, v in _cta.items():
    out = out.replace('{{' + k + '}}', v)
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
scenes += [{'id': 'backstage', 'start': T['wire0'], 'end': T['sweep1'], 'label': 'bastidores: o cenário deste vídeo vira wireframe e volta renderizado'},
           {'id': 'demos', 'start': T['s5'], 'end': T['s6'], 'label': 'cenas (escolha) → corte (lâmina) → legenda (destaque) → animação (curva) em entregas reais'},
           {'id': 'hero', 'start': T['hero'], 'end': T['heroOut'], 'label': 'entrega real do Cortez em tela cheia (EXEMPLO_2)'},
           {'id': 'slot', 'start': T['slot0'], 'end': SPEECH, 'label': '"seu vídeo aqui" no cenário claro'},
           {'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': f'CTA escrito ({CTA_MODE})', 'title': 'Feito por IA. / Sem cara de IA. / Você grava. O Cortez edita. Você aprova.'}]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Bokeh no gancho + UnrealBloom + Output) via hf-seek',
    'identity': 'ID05', 'caption_style': 'L04', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['anel de 180 barras = envelope real da narração (a voz desenha o anel)', 'monólito 9:16 = a tela deste vídeo',
                 'varredura com planos de recorte: sólido ↔ wireframe (bastidores)', 'gizmo da câmera virtual', 'cenas candidatas + seleção', 'lâmina do corte',
                 'destaque da legenda', 'editor de curva (bezier) com quadros-chave', 'transição escuro → claro'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'T': {k: T[k] for k in ('s2', 'c0', 'd0', 's5', 'cut', 'anim', 's6', 'hero', 's7')}}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
