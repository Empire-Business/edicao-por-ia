#!/usr/bin/env python3
# Modelo F22 Corte de Live 3D — derivado da edição de exemplo E119 (prévia aprovada pelo autor em 27/11/2026).
# Copie para jobs/<trabalho>/src e preencha: fonte, falas (TAKES), cenas/legendas, provas próprias e trilha. Ver README.md desta pasta.
"""Gera comp/index.html (HyperFrames + GSAP + three.js) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
ID e legenda do trabalho (exemplo: ID04 Dourado + L04) + three.js r186 com pós-processamento. Tempos = palavras realmente faladas na voz final (segundos do master limpo).
O texto das legendas segue a transcrição com contexto da fonte quando a voz cortada confunde o Whisper ("a hotéis" ≠ "ao Téz").
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
# texto conferido na transcrição contínua da fonte (tempo aproximado, palavra ouvida → palavra dita)
FIXES = []
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
T = {'flip1': F[0], 'flip2': F[1], 'dull0': F[1], 'reveal': W('nossa'), 'long0': W('ou', 14.5), 'shorts0': W('e', 18.7), 'back': W('o', 22.6),
     'word': round(W('é', 26.8) - 0.05, 3), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['tap'] = round(SPEECH + 2.7, 3)
PUNCH = [('host', T['flip1'], 1.0), ('host', W('achou') - 0.3, 1.13), ('guest', T['flip2'], 1.0), ('guest', W('que', 8.3) - 0.05, 1.12),
         ('guest', W('mas', 10.3), 1.0), ('guest', T['back'], 1.0), ('guest', W('e', 25.3), 1.12)]
punches = [{'who': w, 't': round(t, 3), 's': sc} for w, t, sc in PUNCH]
HEADS = [
    ('h1', 0, T['flip1'], 'Depoimento · cliente do Cortez', [('“Os vídeos tão', 0), ('<em>sinistros.”</em>', W('sinistros') - 0.2)]),
    ('h2', T['flip1'] + 0.1, T['flip2'], 'A pergunta', [('O que você', T['flip1'] + 0.2), ('<em>esperava?</em>', W('achou') - 0.15)]),
    ('h3', T['flip2'] + 0.1, T['reveal'] - 0.05, 'A expectativa', [('Só um', W('imaginei') - 0.1), ('<em>cortezinho.</em>', W('cortezinho') - 0.15)]),
    ('h4', T['reveal'], T['long0'], 'A surpresa', [('Faz tudo', T['reveal'] + 0.05), ('<em>isso mesmo?</em>', W('isso', 13.5) - 0.15)]),
    ('h5', T['long0'] + 0.05, T['shorts0'], 'Vídeo longo', [('Edita o vídeo', T['long0'] + 0.15), ('<em>longo.</em>', T['long0'] + 0.8)]),
    ('h6', T['shorts0'] + 0.05, T['back'], 'Vídeos curtos', [('E ainda gera', T['shorts0'] + 0.15), ('<em>vários cortes.</em>', W('vários', 20) - 0.15)]),
    ('h7', T['back'] + 0.05, T['word'] - 0.05, 'Nas palavras dele', [('1 vídeo longo →', T['back'] + 0.15), ('<em>vários cortes.</em>', T['back'] + 0.7)]),
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
HIDE_FROM = 1e9
units, g = [], []
for w in WORDS:
    if w['s'] >= HIDE_FROM:
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
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'wipes': wipes, 'heads': heads_data, 'caps': caps_data, 'punches': punches, 'seq': seq}
tpl = (J / 'src/index.tpl.html').read_text()
pill = lambda txt: str(round(540 - (len(txt) * 13.0 + 50) / 2))
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH + 1.0:.3f}')
       .replace('{{P1X}}', pill('Vídeos editados pelo Cortez')).replace('{{P2X}}', pill('Vídeo longo · editado pelo Cortez'))
       .replace('{{P3X}}', pill('Vídeos curtos · editados pelo Cortez')).replace('{{P4X}}', pill('Editados pelo Cortez')))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'word3d', 'start': T['word'], 'end': SPEECH, 'label': 'texto 3D dourado', 'title': 'Incrível.'})
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Edição profissional, sem editor. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: UnrealBloom + Bokeh + Output) via hf-seek',
    'identity': '<ID escolhida>', 'caption_style': '<Lxx>', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['parede viva de vídeos curtos editados pelo Cortez (desfocada atrás do cartão)', 'tela 16:9 com o vídeo longo e reflexo', 'celulares dourados em leque e em órbita', 'texto 3D dourado extrudado (Libre Baskerville)', 'bloom e profundidade de campo'],
    'T': T, 'wipes': wipes, 'punches': punches, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
