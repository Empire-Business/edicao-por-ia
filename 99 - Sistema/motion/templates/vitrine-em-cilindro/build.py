#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
ID05 Roxo + legenda L05 (caixa na palavra) + three.js r186. Tempos = palavras realmente faladas na voz final (segundos do master).
O texto das legendas segue a fala conferida na fonte: o Whisper da voz cortada ouve "vídeo de desfoque fundo" e "depende disso";
o trecho foi conferido em janelas maiores (tmp/probe: "vídeo, a gente desfoca o fundo"; fonte: "vídeo onde a gente desfoca o fundo, né?").
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
RAW = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
       for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
SEG = {s['take']: s for s in EDL['segments'] if s['piece'] == 0}
# CTA=more (padrão, "Saiba mais") ou CTA=comment (variante "Comente CORTEZ" — jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md)
CTA_MODE = os.environ.get('CTA', 'more')
assert CTA_MODE in ('more', 'comment'), CTA_MODE
TK = lambda tid: SEG[tid]['start']


def out_t(take, src):
    """tempo no vídeo final de um instante da fonte (dentro de um pedaço do EDL)."""
    for s in EDL['segments']:
        if s['take'] == take and s['in'] - 1e-6 <= src <= s['out'] + 1e-6:
            return round(s['start'] + src - s['in'], 3)
    raise SystemExit(f'{take} {src} fora do EDL')


# --- correções de texto (palavras ditas na fonte; tempos do envelope de energia / transcrição da fonte) ---
A0, A1 = TK('t01') + 5.2, TK('t02')
MANUAL = [('vídeo', out_t('t01', 473.74), out_t('t01', 473.98)), ('onde', out_t('t01', 474.0), out_t('t01', 474.2)),
          ('a', out_t('t01', 474.22), out_t('t01', 474.3)), ('gente', out_t('t01', 474.3), out_t('t01', 474.52)),
          ('desfoca', out_t('t01b', 475.53), out_t('t01b', 476.2)), ('o', out_t('t01b', 476.22), out_t('t01b', 476.38)),
          ('fundo.', out_t('t01b', 476.43), out_t('t01b', 476.69))]
WORDS = [w for w in RAW if not (A0 <= w['s'] < A1)]
WORDS += [{'w': a, 's': b, 'e': c} for a, b, c in MANUAL]
WORDS.sort(key=lambda w: w['s'])
fixed = []
for w in WORDS:
    if w['w'] == 'disso,' or w['w'] == 'disso':
        m = round((w['s'] + w['e']) / 2 - 0.04, 3)
        fixed += [{'w': 'da', 's': w['s'], 'e': m}, {'w': 'edição', 's': m, 'e': w['e']}]
    elif w['w'].startswith('-') and fixed:
        fixed[-1] = {'w': fixed[-1]['w'] + w['w'], 's': fixed[-1]['s'], 'e': w['e']}
    elif w['w'] == 'à':
        fixed.append({**w, 'w': 'a'})
    else:
        fixed.append(w)
WORDS = fixed


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


LEAD = 0.06   # a imagem chega um pouco antes da sílaba
T = {'sem': W('sem') - LEAD, 'apa': W('aparecendo') - LEAD, 'cen': W('com', 4.0) - LEAD, 'des': W('desfoca') - LEAD,
     'apresentador': TK('t02'), 'esc': W('escolhe') - LEAD, 't03': TK('t03'), 'letra': W('letra') - LEAD, 'tam': W('tamanho') - LEAD,
     'cor': W('cores') - LEAD, 't04': TK('t04'), 'efe': W('efeito'), 'mus': W('música'), 'tudo': W('tudo'), 'vis': W('visual'),
     't05': TK('t05'), 'poss': W('possibilidades'), 'dif': W('difícil'), 'tranq': W('tranquilo'), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T = {k: round(v, 3) for k, v in T.items()}
T['tap'] = round(SPEECH + 2.75, 3)

# quem fala (miniatura redonda)
spk, cur = [], None
for s in EDL['segments']:
    if not spk or s['speaker'] != spk[-1]['who']:
        spk.append({'who': s['speaker'], 'a': s['start'], 'b': None})
for i, s in enumerate(spk):
    s['b'] = spk[i + 1]['a'] if i + 1 < len(spk) else SPEECH + 0.1
    s['a'] = round(s['a'] + (0.05 if i else 0.0), 3)
    s['b'] = round(s['b'], 3)

HEADS = [
    ('h1', 0, T['apresentador'] - 0.05, 'Formatos · editados pelo Cortez', [('Tem formato', 0), ('<em>pra tudo.</em>', 0)]),
    ('h2', T['apresentador'] + 0.45, T['t03'] - 0.3, 'Os formatos prontos', [('Você escolhe', T['apresentador'] + 0.6), ('<em>o formato.</em>', T['esc'] - 0.1)]),
    ('h3', T['t04'] + 0.15, T['t05'] - 0.05, 'EXEMPLO_2 · editado pelo Cortez', [('Bem editado.', T['t04'] + 0.25), ('<em>Com tudo.</em>', T['tudo'] - 0.12)]),
    ('h4', T['t05'] + 0.4, T['dif'] - 0.2, 'Formatos · editados pelo Cortez', [('São N', T['t05'] + 0.5), ('<em>possibilidades.</em>', T['poss'] + 0.1)]),
    ('h5', T['dif'] - 0.05, SPEECH + 0.05, 'Nas palavras do Convidado', [('Tranquilo', T['dif'] + 0.05), ('<em>de mexer.</em>', T['tranq'] - 0.12)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.32 - at)), 3)} for tx, at in lines_]})

PILLS = [('fp0', T['sem'] + 0.3, T['apa'] - 0.12, 'Sem aparecer', '01'), ('fp1', T['apa'] + 0.3, T['cen'] - 0.12, 'Aparecendo', '02'),
         ('fp2', T['cen'] + 0.3, T['des'] - 0.12, 'Com cenas', '03'), ('fp3', T['des'] + 0.3, T['apresentador'] - 0.05, 'Fundo desfocado', '04')]
pills_html = '\n  '.join(f'<div class="fpill" id="{i}"><span><i>{n}</i>{html.escape(tx)}</span></div>' for i, a, b, tx, n in PILLS)
pills_data = [{'id': i, 'a': round(a, 3), 'b': round(b, 3)} for i, a, b, tx, n in PILLS]
SWL = ['ID01', 'ID04', 'ID07', 'ID03', 'ID05']
swl_html = ''.join(f'<span id="sw{i}">{x}</span>' for i, x in enumerate(SWL))
swl_data = [{'a': round(T['cor'] - 0.2 + i * 0.06, 3)} for i in range(len(SWL))]

# legendas L05: blocos de até 4 palavras (uma linha), quebrando em pausa, pontuação e troca de quem fala
spk_at = lambda t: next(s['speaker'] for s in reversed(EDL['segments']) if s['start'] <= t + 1e-6)
mid = lambda x: (x['s'] + x['e']) / 2
WEAK = {'que', 'e', 'com', 'de', 'a', 'o', 'da', 'do', 'em', 'no', 'na', 'os', 'as', 'um', 'uma'}
units, g = [], []
for w in WORDS:
    if g:
        prev = g[-1]
        hard = w['s'] - prev['e'] > 0.32 or prev['w'][-1] in '.?!,' or spk_at(mid(w)) != spk_at(mid(prev))
        full = len(g) >= 4 or len(' '.join(x['w'] for x in g + [w])) > 28
        if hard or full:
            carry = []
            if full and not hard and len(g) > 1 and norm(g[-1]['w']) in WEAK:   # não termina o bloco em "que", "e", "com"...
                carry = [g.pop()]
            units.append(g); g = carry
    g.append(w)
if g:
    units.append(g)
# junta sobras de uma palavra curta ao bloco anterior quando cabe
groups = []
for u in units:
    tag = groups and len(u) == 1 and norm(u[0]['w']) == 'ne'          # o "né?" de apoio fica no bloco anterior
    if tag or (groups and len(u) == 1 and len(u[0]['w']) <= 4 and len(groups[-1]) < 4 and len(' '.join(x['w'] for x in groups[-1] + u)) <= 24
               and u[0]['s'] - groups[-1][-1]['e'] < 0.3 and groups[-1][-1]['w'][-1] not in '.?!'):
        groups[-1] = groups[-1] + u
    else:
        groups.append(u)
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s']
    e = groups[i + 1][0]['s'] if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.5 else gw[-1]['e'] + 0.25
    e = min(e, SPEECH)
    light = T['t03'] - 0.02 <= s < T['t04'] - 0.02
    spans = ' '.join(f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, x in enumerate(gw))
    caps_html.append(f'<div class="cap {"lt" if light else "dk"}" id="cg{i}">{spans}</div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'light': light,
                      'w': [{'s': x['s'], 'e': round(min(x['e'] + 0.04, gw[k + 1]['s']) if k + 1 < len(gw) else e, 3)} for k, x in enumerate(gw)],
                      'text': ' '.join(x['w'] for x in gw)})

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'spk': spk, 'pills': pills_data, 'swl': swl_data, 'seq': seq}
if CTA_MODE == 'comment':
    typ = [round(T['cta0'] + 1.62 + i * 0.1, 3) for i in range(6)]          # C O R T E Z digitado, uma letra a cada 0,1 s
    car, k = [], 0
    for x in [round(T['cta0'] + 1.5 + 0.25 * i, 3) for i in range(int((DUR - T['cta0'] - 1.5) / 0.25))]:
        car.append([x, 1 if (x < typ[-1] + 0.05 or k % 2 == 0) else 0]); k += 1   # cursor de texto pisca depois de digitar
    data.update({'cta': 'comment', 'typing': typ, 'caret': car})
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{CTA_HTML}}', (J / ('src/cta_comment.html' if CTA_MODE == 'comment' else 'src/cta_more.html')).read_text().rstrip('\n'))
       .replace('{{PILLS}}', pills_html).replace('{{SWL}}', swl_html).replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH + 1.0:.3f}'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.insert(2, {'id': 'tipos', 'start': T['t03'], 'end': T['t04'], 'label': 'máquina de tipos (letra · tamanho · cor)', 'title': 'Seu estilo.'})
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Tem formato pra tudo. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
if CTA_MODE == 'comment':
    scenes[-1] = {'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito "Comente CORTEZ" (voz já terminou)', 'title': 'Tem formato pra tudo. / Comente CORTEZ / campo de comentário com CORTEZ digitado e enviado / aqui nos comentários ↓'}
SUF = '-comment' if CTA_MODE == 'comment' else ''
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / f'analysis/caption_groups{SUF}.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: UnrealBloom + Output) via hf-seek',
    'identity': 'ID05', 'caption_style': 'L05', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['torre/anel de telas curvas com entregas reais (sombreador: curvatura, cantos, desfoque por mip, borda de seleção)',
                 'formato citado avança e aplaina; no "desfoca o fundo" o resto da torre desfoca', 'câmera sai por cima da torre; tela escolhida vem até a câmera e a câmera mergulha nela',
                 'máquina de tipos: texto extrudado troca de fonte (giro), de tamanho e de cor (IDs reais) com sombra projetada', 'fichas 3D (efeitos · música · visual)',
                 'poço de telas (N possibilidades) e coroa no CTA claro'],
    'T': T, 'spk': spk, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
print(json.dumps(T))
for c in caps_data:
    print(c['s'], c['e'], 'L' if c['light'] else 'D', c['text'])
