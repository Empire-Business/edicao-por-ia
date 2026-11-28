#!/usr/bin/env python3
"""EXEMPLO_1 V3 — gera comp/index.html (HyperFrames + GSAP + three.js) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
IDP02 Black Alto Valor + legenda L04. Tempos = palavras realmente faladas na voz final (segundos do master limpo).
O texto das legendas segue a transcrição com contexto da fonte quando a voz cortada confunde o Whisper ("a hotéis" ≠ "ao Téz").
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, re, unicodedata
from pathlib import Path
import os, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cta_variant import snippets

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
# texto conferido na transcrição contínua da fonte (tempo aproximado, palavra ouvida → palavra dita)
FIXES = [(14.5, 'ao', 'a'), (14.9, 'Téz', 'hotéis'), (15.2, 'Barato.', 'baratos.'), (19.2, 'do', 'de'), (19.4, 'Téz,', 'hotéis,'),
         (14.9, 'Hotéis', 'hotéis'), (15.2, 'Baratos.', 'baratos.')]
for w in WORDS:
    for t, a, b in FIXES:
        if w['w'] == a and abs(w['s'] - t) < 0.45:
            w['w'] = b


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


wipes, cur = [], EDL['segments'][0]['speaker']
for s in EDL['segments']:
    if s['speaker'] != cur:
        wipes.append({'t': s['start'], 'to': s['speaker']})
        cur = s['speaker']
F = [w['t'] for w in wipes]
T = {'flip1': F[0], 'flip2': F[1], 'flip3': F[2], 'flip4': F[3], 'res0': W('resultado') - 0.3, 'hoteis': W('hotéis'),
     'cortez0': W('quem', 15) - 0.1, 'toda': W('toda'), 'cortezW': W('cortez', 16), 'items0': W('pegou'), 'imagens': W('imagens'),
     'cortes': W('cortes', 19), 'efeitos': W('efeitos'), 'holly0': W('então', 21.5), 'holly1': W('hollywood'), 'nunca0': W('nunca') - 0.05,
     'anim0': W('animação', 31), 'marav': W('maravilhado'), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['phoneA0'] = T['cortez0']; T['phoneA1'] = T['holly0']; T['phoneB0'] = round(SPEECH + 0.15, 3)
T['cine0'] = round(T['holly0'] + 0.78, 3)                 # depois que o cartão volta do modo celular
T['cine1'] = round(W('quando', 25.5) + 0.55, 3)
T['fs0'] = T['flip4']; T['fs1'] = W('quando', 33); T['fs2'] = round(W('pô', 36.5) - 0.1, 3)
T['tap'] = round(SPEECH + 2.7, 3)
wipes[3]['hidden'] = True                                 # 4ª troca acontece com o cartão escondido (animações em destaque)
PUNCH = [('convidado', 0, 1.0), ('convidado', W('galera') - 0.45, 1.12), ('apresentador', T['flip1'], 1.0), ('apresentador', W('contratava') - 0.32, 1.13),
         ('convidado', T['flip2'], 1.0), ('convidado', W('ficava') - 0.05, 1.12), ('convidado', T['res0'], 1.0), ('convidado', W('vídeo', 12.5) - 0.25, 1.12),
         ('convidado', T['phoneA0'] - 0.2, 1.0), ('apresentador', T['flip3'], 1.0), ('apresentador', W('que', 29.9), 1.13), ('convidado', T['cine1'] + 0.6, 1.12),
         ('convidado', T['fs2'] - 0.1, 1.08)]
punches = [{'who': w, 't': round(t, 3), 's': sc} for w, t, sc in PUNCH]

HEADS = [
    ('h1', 0, T['flip1'], 'Depoimento · cliente do Cortez', [('Ele pagava editor.', 0), ('<em>Agora usa o Cortez.</em>', W('cortez') - 0.05)]),
    ('h2', T['flip1'] + 0.1, T['flip2'], 'A pergunta do Apresentador', [('Era do mesmo', T['flip1'] + 0.2), ('<em>nível?</em>', T['flip1'] + 0.5)]),
    ('h3', T['flip2'] + 0.1, T['res0'], 'A resposta', [('“Ficava', W('ficava') - 0.15), ('<em>parecido.”</em>', W('parecido') - 0.15)]),
    ('h4', T['res0'] + 0.05, T['cortez0'] - 0.05, 'O resultado favorito dele', [('Um vídeo sobre', T['res0'] + 0.15), ('<em>hotéis baratos.</em>', W('postei') - 0.1)]),
    ('h5', T['cortez0'] + 0.05, T['holly0'], 'Quem editou', [('Toda a edição:', W('toda') - 0.1), ('<em>o próprio Cortez.</em>', W('cortez', 16) - 0.25)]),
    ('h7', T['nunca0'] + 0.05, T['flip3'] + 0.25, 'Nas palavras dele', [('“Nunca fiz uma', T['nunca0']), ('edição <em>assim.”</em>', W('edição', 27) - 0.1)]),
    ('h8', T['flip3'] + 0.35, T['flip4'], 'A pergunta do Apresentador', [('O que mais', T['flip3'] + 0.45), ('<em>chamou atenção?</em>', W('chamou') - 0.2)]),
    ('h9', T['flip4'] + 0.1, T['marav'] - 0.05, 'A resposta', [('<em>A animação.</em>', W('animação', 31) - 0.1)]),
    ('h10', T['marav'] - 0.05, SPEECH + 0.05, 'Nas palavras dele', [('“Fiquei', T['marav'] - 0.15), ('<em>maravilhado.”</em>', T['marav'] + 0.15)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    # cada linha termina de entrar antes de o título sair (sem tweens sobrepostos)
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.7, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legendas L04: frases por pausa/pontuação/troca de quem fala; blocos de até ~40 caracteres em 2 linhas
spk_at = lambda t: next(s['speaker'] for s in reversed(EDL['segments']) if s['start'] <= t + 1e-6)
mid = lambda x: (x['s'] + x['e']) / 2
HIDE_FROM = T['holly1'] - 0.12            # "de Hollywood." já está escrito grande no título
units, g = [], []
for w in WORDS:
    if w['s'] >= HIDE_FROM - 0.05 and w['e'] <= T['holly1'] + 0.6:
        if g:
            units.append(g); g = []
        continue
    if g:
        prev = g[-1]
        if w['s'] - prev['e'] > 0.32 or prev['w'][-1] in '.?!' or spk_at(mid(w)) != spk_at(mid(prev)):
            units.append(g); g = []
    g.append(w)
if g:
    units.append(g)
groups = []
for u in units:
    n = len(' '.join(x['w'] for x in u))
    k = max(1, -(-n // 40))
    if k == 1:
        groups.append(u); continue
    target, cur_, acc = n / k, [], 0
    for x in u:
        cur_.append(x); acc += len(x['w']) + 1
        if len(cur_) > 1 and acc >= target - 3:
            groups.append(cur_); cur_, acc = [], 0
    if cur_:
        if len(' '.join(x['w'] for x in cur_)) < 10 and groups:
            groups[-1] = groups[-1] + cur_
        else:
            groups.append(cur_)


def lines(ws):
    if len(' '.join(x['w'] for x in ws)) <= 24:
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
    s = gw[0]['s']
    e = groups[i + 1][0]['s'] if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.5 else gw[-1]['e'] + 0.25
    e = min(e, SPEECH)
    ls, j, spans = lines(gw), 0, []
    for ln in ls:
        parts = []
        for x in ln:
            parts.append(f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>')
            j += 1
        spans.append(f'<span class="cl">{" ".join(parts)}</span>')
    top = 1160 if len(ls) == 2 else 1192
    caps_html.append(f'<div class="cap" id="cg{i}" style="top:{top}px">{"".join(spans)}</div>')
    ww = [x for ln in ls for x in ln]
    caps_data.append({'s': round(s, 3), 'e': round(e, 3),
                      'w': [{'s': x['s'], 'e': round(min(x['e'] + 0.05, ww[k + 1]['s']) if k + 1 < len(ww) else x['e'] + 0.15, 3)} for k, x in enumerate(ww)],
                      'text': ' / '.join(' '.join(x['w'] for x in ln) for ln in ls)})

SCREENS = [f'assets/tile{i:02d}.jpg' for i in (3, 7, 5, 9, 6, 4, 10, 1, 8, 2)]
seqA = len(list((C / 'assets/seqA').glob('*.jpg'))); seqB = len(list((C / 'assets/seqB').glob('*.jpg')))
data = {'T': T, 'wipes': wipes, 'heads': heads_data, 'caps': caps_data, 'punches': punches, 'seqA': seqA, 'seqB': seqB, 'fspillB': 388}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH + 1.0:.3f}')
       .replace('{{FSA_START}}', f"{T['fs0'] - 0.05:.3f}").replace('{{FSB_START}}', f"{T['fs1']:.3f}").replace('{{FSPILL_TOP}}', '460'))
CTA_MODE, _cta = snippets(J / 'src', top=1176, acc='#f6c6c3', dark='#131211', light_rgb='240,237,228', muted='#b6b3ac', font='"Schibsted Grotesk", sans-serif', typed_weight=700)
for k, v in _cta.items():
    out = out.replace('{{' + k + '}}', v)
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if CTA_MODE != 'saiba' or os.environ.get('COMP_OUT'):
    # variante de CTA (ou conferência): comp separada com os mesmos materiais (hard links), sem reescrever as análises aprovadas
    O = Path(os.environ.get('COMP_OUT') or (J / f'comp-cta-{CTA_MODE}'))
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir(): d.mkdir(parents=True, exist_ok=True)
        elif not d.exists(): d.parent.mkdir(parents=True, exist_ok=True); os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': CTA_MODE, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Edição profissional, sem editor. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V3', 'engine': 'HyperFrames 0.8.92 (GSAP paused timeline) + three.js r160 via hf-seek',
    'identity': 'IDP02', 'caption_style': 'L04', 'determinism': 'função do tempo do quadro; PRNG de semente fixa; sem timers',
    'three_js': 'celular 3D (corpo metálico, ambiente de estúdio PMREM, sombra de contato) tocando, quadro a quadro, trechos reais de vídeos editados pelo Cortez',
    'v3_additions': ['zoom de corte no ritmo da fala', 'modo cinema em tela larga no de Hollywood', 'animações reais em destaque com o Convidado em miniatura', 'prova em movimento no celular'],
    'removed_after_v1_feedback': ['partículas', 'holofotes', 'texto 3D HOLLYWOOD', 'mural voando', 'brilho neon', 'giro de moeda do cartão'],
    'T': T, 'wipes': wipes, 'punches': punches, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
