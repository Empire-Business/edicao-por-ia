#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL e de src/index.tpl.html.
F22 Corte de Live 3D + ID04 Dourado + legenda L01 (clássica em duas linhas, blocos de até 6 palavras, troca por bloco).
Tempos das palavras: transcrição contínua da live (texto conferido; a transcrição da voz cortada confunde "né, o Cortez" com
"cortei e paguei") projetada pelo EDL no relógio do vídeo. Conceito visual: "a conta não fecha" — de um lado a etiqueta de preço
dourada "De graça." pendurada sobre a impressora do Cortez, que imprime o recibo do que ele entrega; do outro, a pilha de notas do
editor por fora (cada edição, depois os maços "mês 1" e "mês 2"). Sem preços nem números inventados: só o que é dito.
CTA=comment gera a variante "Comente CORTEZ" (comp-cta-comment/), sem reescrever as análises da versão principal.
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cta_variant import snippets

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
SH = J.parent / 'material-compartilhado'
EDL = json.loads((J / 'edit/edl.json').read_text())
SRCW = {k: [w for s in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s['words']] for k in ('ig',)}
SPEECH = EDL['duration']
CTA = 4.8
DUR = round(SPEECH + CTA, 3)

# palavras do vídeo = palavras da fonte dentro de cada pedaço do EDL, no relógio de saída
WORDS = []
for s in EDL['segments']:
    a, b = s['in'], s['in'] + s['frames'] / 30
    for w in SRCW[s['src']]:
        mid = (w['start'] + w['end']) / 2
        if a - 0.02 <= mid < b:
            WORDS.append({'w': w['word'].strip(), 's': round(s['start'] + max(0.0, w['start'] - a), 3),
                          'e': round(s['start'] + min(b, w['end']) - a, 3), 'who': s['speaker']})
FIX = {'Cortez': 'Cortez'}


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


seg0 = {s['take']: s['start'] for s in reversed(EDL['segments'])}
T = {'graca': W('graça'), 'pelo': W('pelo'), 'entrega': W('entrega'), 'negocio': W('negócio'), 'so': W('só'), 'se': W('se', W('só')),
     'edicoes': W('edições'), 'faco': W('faço'), 'cortez': W('cortez'), 'pagar': W('pagar'), 'fora': W('fora'), 'muito': W('muito'),
     'oferta2': W('oferta', W('muito')), 'apresentador': seg0['t02'], 'um': W('um', seg0['t02']), 'dois': W('dois', seg0['t02']),
     'editor': W('editor', seg0['t02']), 'pagar2': W('pagar', seg0['t02']), 'convidado2': seg0['t03'], 'so2': W('só', seg0['t03']),
     'agora': W('agora'), 'outras': W('outras'), 'ferr': W('ferramentas'), 'fica': W('fica'), 'injusta': W('injusta'),
     'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['tap'] = round(SPEECH + 2.9, 3)
T['type0'] = round(SPEECH + 1.6, 3)
T['wide'] = round(T['fica'] - 0.35, 3)
T['pile0'] = round(T['se'] - 0.15, 3)        # câmera abre para a pilha do editor por fora

HEADS = [
    ('h1', 0, T['pelo'] - 0.05, 'A pergunta do Apresentador', [('Barata ou cara?', 0), ('<em>“De graça.”</em>', T['graca'] - 0.12)]),
    ('h2', T['pelo'] + 0.05, T['pile0'], 'O que o Cortez entrega', [('Pelo que', T['pelo'] + 0.1), ('<em>entrega…</em>', T['entrega'] - 0.1)]),
    ('h3', T['pile0'] + 0.1, T['apresentador'] - 0.02, 'Edição por fora', [('Só a edição', T['pile0'] + 0.2), ('<em>já sairia mais.</em>', T['muito'] - 0.15)]),
    ('h4', T['apresentador'] + 0.05, T['convidado2'] - 0.02, 'A conta do Apresentador', [('Um, dois meses', T['um'] - 0.05), ('<em>só de editor.</em>', T['editor'] - 0.15)]),
    ('h5', T['convidado2'] + 0.05, T['wide'], 'E ainda tem', [('as outras', T['agora'] - 0.05), ('<em>ferramentas.</em>', T['ferr'] - 0.1)]),
    ('h6', T['wide'] + 0.1, None, 'Nas palavras do Convidado', [('“Fica até injusta', T['fica'] - 0.05), ('<em>a comparação.”</em>', T['injusta'] + 0.1)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    end = SPEECH + 0.05 if en is None else en
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(end, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.7, end - 0.34 - at)), 3)} for tx, at in lines_]})

# legendas L01: frase estável em até duas linhas, blocos de até 6 palavras, troca por bloco (quebra por pausa, pontuação e troca de quem fala)
units, g = [], []
for w in WORDS:
    if g:
        p = g[-1]
        if w['s'] - p['e'] > 0.35 or p['w'][-1] in '.?!' or w['who'] != p['who']:
            units.append(g); g = []
    g.append(w)
if g:
    units.append(g)
GOOD_START = {'se', 'que', 'já', 'você', 'só', 'então', 'agora', 'pelo', 'fica', 'o', 'a'}


def split_long(c):
    """oração com mais de 6 palavras: corta antes de uma palavra que abre oração, perto do meio (nunca 'está | de graça')."""
    if len(c) <= 6:
        return [c]
    cands = [i for i in range(2, len(c) - 1) if norm(c[i]['w']) in {norm(x) for x in GOOD_START} and i <= 6 and len(c) - i <= 6]
    i = min(cands, key=lambda i: abs(i - len(c) / 2)) if cands else len(c) // 2
    return split_long(c[:i]) + split_long(c[i:])


groups = []
for u in units:
    clauses, cur_ = [], []
    for x in u:                                     # orações pela pontuação
        cur_.append(x)
        if x['w'][-1] in ',.;?!':
            clauses.append(cur_); cur_ = []
    if cur_:
        clauses.append(cur_)
    blocks = []
    for c in clauses:
        for part in split_long(c):
            if blocks and (len(blocks[-1]) + len(part) <= 6 or (len(part) == 1 and len(blocks[-1]) + 1 <= 7)):
                blocks[-1] = blocks[-1] + part
            else:
                blocks.append(part)
    groups += blocks


def lines(ws):
    if len(' '.join(x['w'] for x in ws)) <= 22:
        return [ws]
    best, bi = 1e9, 1
    for k in range(1, len(ws)):
        a = len(' '.join(x['w'] for x in ws[:k])); b = len(' '.join(x['w'] for x in ws[k:]))
        sc = max(a, b) - (4 if ws[k - 1]['w'][-1] in ',;' else 0) + (6 if norm(ws[k]['w']) in ('de', 'da', 'do') else 0)
        if sc < best:
            best, bi = sc, k
    return [ws[:bi], ws[bi:]]


KEY = {'graça', 'graça,', 'graça.', 'injusta'}
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s'] - 0.04
    e = groups[i + 1][0]['s'] - 0.04 if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.6 else gw[-1]['e'] + 0.3
    e = min(e, SPEECH)
    ls = lines(gw)
    spans = ['<span class="cl">' + ' '.join(f'<span class="cw{" k" if x["w"].lower() in KEY else ""}">{html.escape(x["w"])}</span>' for x in ln) + '</span>' for ln in ls]
    caps_html.append(f'<div class="cap" id="cg{i}"><div class="cb">{"".join(spans)}</div></div>')
    caps_data.append({'s': round(max(0, s), 3), 'e': round(e, 3), 'who': gw[0]['who'], 'text': ' / '.join(' '.join(x['w'] for x in ln) for ln in ls)})

spk = [{'t': round(s['start'], 3), 'who': s['speaker']} for s in EDL['segments']]
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'spk': spk, 'seq': seq}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n  '.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{VID}}', f'{SPEECH + 1.0:.3f}'))
CTA_MODE, _cta = snippets(J / 'src', top=1236, acc='#D6B46A', dark='#171714', light_rgb='241,238,229', muted='#B6B09F', font='"Inter", sans-serif', typed_weight=600)
for k, v in _cta.items():
    out = out.replace('{{' + k + '}}', v)
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if CTA_MODE != 'saiba':
    O = J / f'comp-cta-{CTA_MODE}'
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir():
            d.mkdir(parents=True, exist_ok=True)
        elif not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True); os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': CTA_MODE, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2] if h[2] is not None else SPEECH, 3), 'label': h[3],
           'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Edição profissional, sem pagar editor. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: RenderPass + UnrealBloom suave + Output; sombras PCF suaves) via hf-seek',
    'identity': 'ID04', 'caption_style': 'L01', 'format': 'F22', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['etiqueta de preço dourada (frente "Preço — — —", verso "De graça.") pendurada num cordão, balanço amortecido e giro na palavra "graça"',
                 'impressora do Cortez sobre pedestal imprimindo o recibo do que ele entrega (papel sobe com curvatura, linhas na fala)',
                 'polaroides com entregas reais editadas pelo Cortez (EXEMPLO_2, EXEMPLO_3) presas ao lado do recibo',
                 'pedestal "editor por fora": notas caindo a cada edição paga por fora, maços "mês 1" e "mês 2" na fala do Apresentador',
                 'plano aberto final com os dois pedestais (comparação)'],
    'T': T, 'speakers': spk, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['who'], c['text'])
print(json.dumps(T, ensure_ascii=False))
