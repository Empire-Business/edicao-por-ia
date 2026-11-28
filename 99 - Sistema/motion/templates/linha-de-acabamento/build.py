#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da voz (analysis/voice_words.json), dos blocos reais da
gravação bruta (analysis/raw_blocks.json) e de src/index.tpl.html. F10 + ID07 Laranja + legenda L05 (caixa na palavra).
Estilo deste criativo: "linha de acabamento" — a gravação bruta vira uma fileira de blocos físicos (um bloco por trecho real: fala, erro,
hesitação, silêncio; largura ∝ duração) sobre uma esteira; cinco estações (arcos) passam pela fileira e cada uma faz o que a narração diz.
CTA=comment gera a variante "Comente CORTEZ" (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md); padrão = "Saiba mais".
Grava analysis/scene_plan*.json, analysis/motion_plan*.json e analysis/caption_groups*.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
V = json.loads((J / 'analysis/voice_words.json').read_text())
RB = json.loads((J / 'analysis/raw_blocks.json').read_text())
WORDS = [w for w in V['words'] if w['src'] == 'ia']
N0 = V['n0']
FPS = 30
q = lambda x: round(round(x * FPS) / FPS, 4)
SE = V['speech_end']
CTA0 = q(SE + 0.15)
CTA_S = 4.6
DUR = q(CTA0 + CTA_S)
MODE = os.environ.get('CTA', 'saiba')
assert MODE in ('saiba', 'comment'), MODE
SUF = '' if MODE == 'saiba' else '-comment'


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0, end=False):
    for x in WORDS:
        if x['s'] >= after - 0.02 and norm(x['w']) == norm(word):
            return x['e'] if end else x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


T = {'n0': N0, 'manda': W('manda'), 'bruto': W('bruto'), 'aquele': W('aquele'), 'ruido1': W('ruído'), 'silencio': W('silêncio'),
     'gagu': W('gaguejada'), 'erro': W('erro'), 'frase': W('frase', end=True)}
T['eu1'] = W('eu', T['frase']); T['cortez'] = W('cortez', T['eu1']); T['ia'] = W('inteligência', T['cortez']); T['edita'] = W('edita', T['ia'])
T['eu2'] = W('eu', T['edita']); T['ruido2'] = W('ruído', T['eu2']); T['corto'] = W('corto', T['eu2']); T['silencios'] = W('silêncios', T['corto'])
T['removo'] = W('removo', T['corto']); T['erros'] = W('erros', T['removo']); T['procuro'] = W('procuro', T['removo']); T['cenas'] = W('cenas', T['procuro'])
T['coloco'] = W('coloco', T['cenas']); T['legenda'] = W('legenda', T['coloco']); T['musica'] = W('música', T['legenda']); T['animacao'] = W('animação', T['musica'])
T['anim_end'] = W('animação', T['musica'], end=True)
T['voce'] = W('você', T['animacao']); T['aprova'] = W('aprova', T['voce']); T['quer'] = W('quer', T['aprova']); T['coisa'] = W('coisa', T['quer'], end=True)
T['pedir'] = W('pedir', T['coisa']); T['igual'] = W('igual', T['pedir']); T['editor'] = W('editor', T['igual'])
# estações (o arco atravessa a parte visível da fileira, do fundo para a frente)
T['s1a'], T['s1b'] = round(T['eu2'] - 0.12, 3), round(T['corto'] - 0.02, 3)
T['s2a'], T['s2b'] = round(T['corto'] - 0.02, 3), round(T['removo'] - 0.08, 3)
T['c1a'] = round(T['s2b'] + 0.02, 3); T['c1b'] = round(T['c1a'] + 0.34, 3)
T['s3a'], T['s3b'] = round(T['removo'] - 0.06, 3), round(T['procuro'] - 0.12, 3)
T['c2a'] = round(T['s3b'] + 0.02, 3); T['c2b'] = round(T['c2a'] + 0.34, 3)
T['s4a'], T['s4b'] = round(T['procuro'] - 0.05, 3), round(T['coloco'] - 0.08, 3)
T['c3a'] = round(T['procuro'] + 0.05, 3); T['c3b'] = round(T['c3a'] + 0.32, 3)
T['drop0'] = round(T['cenas'] - 0.15, 3)
T['s5a'], T['s5b'] = round(T['coloco'] - 0.05, 3), round(T['animacao'] + 0.15, 3)
T['merge0'] = round(T['anim_end'] - 0.05, 3); T['merge1'] = round(T['aprova'] - 0.05, 3)
T['tapA'] = round(T['aprova'] + 0.12, 3)
T['chat0'] = round(T['quer'] - 0.05, 3); T['reply'] = round(T['pedir'] - 0.15, 3); T['v2'] = round(T['igual'] + 0.25, 3)
T.update({'speechEnd': SE, 'cta0': CTA0, 'end': DUR, 'tap': round(CTA0 + 2.95, 3), 'type2': round(CTA0 + 1.95, 3)})
for k in ('s1a', 's1b', 's2a', 's2b', 's3a', 's3b', 's4a', 's4b', 's5a', 's5b'):
    T[k] = round(T[k], 3)
assert T['s1a'] < T['s1b'] <= T['s2a'] < T['s2b'] < T['c1b'] < T['s3b'] < T['c2b'] < T['s4b'] < T['s5b'] < T['merge1'], T

# ---------- fileira de blocos (gravação bruta real 0–35,48 s) ----------
K, GAP, H = 56.0, 12.0, 300.0
MINW = {'err': 110, 'keep': 70, 'sil': 22, 'hes': 16}
FIN = {4, 12, 13, 14, 15, 16, 17}
blocks = RB['blocks']
bricks = []
for i, b in enumerate(blocks):
    w = max(MINW[b['k']], (b['e'] - b['s']) * K)
    bricks.append({'i': i, 'k': b['k'], 's': b['s'], 'e': b['e'], 'w': round(w, 1), 'tex': (f'raw/{i:02d}.jpg' if b['k'] != 'sil' else None),
                   'fin': (f'fin/{i:02d}.jpg' if i in FIN else None), 'txt': b['txt']})
BROLL = [('agenda', 4), ('reuniao', 12), ('escritorio', 16), ('callcenter', 17)]   # cena entra logo depois do trecho que ela cobre no EXEMPLO_2
for n, after in BROLL:
    bricks.append({'i': len(bricks), 'k': 'broll', 'w': 210.0, 'tex': f'broll/{n}.jpg', 'after': after, 'name': n})


def layout(keep_kinds, with_broll):
    order = []
    for b in bricks:
        if b['k'] == 'broll':
            continue
        if b['k'] in keep_kinds:
            order.append(b)
            if with_broll:
                order += [x for x in bricks if x['k'] == 'broll' and x['after'] == b['i']]
    x, pos = 0.0, {}
    for b in order:
        pos[b['i']] = round(x + b['w'] / 2, 1); x += b['w'] + GAP
    return pos, round(x - GAP, 1)


L0, len0 = layout({'sil', 'err', 'hes', 'keep'}, False)
L1, len1 = layout({'err', 'hes', 'keep'}, False)
L2, len2 = layout({'keep'}, False)
L3, len3 = layout({'keep'}, True)
for b in bricks:
    b['x0'] = L0.get(b['i']); b['x1'] = L1.get(b['i']); b['x2'] = L2.get(b['i']); b['x3'] = L3.get(b['i'])
# barras do envelope (0,1 s) sobre cada bloco
bars = []
wr, wc = RB['wave_raw'], RB['wave_clean']
for k in range(min(len(wr), 355)):
    tk = k * 0.1 + 0.05
    b = next((x for x in bricks if x['k'] != 'broll' and x['s'] <= tk < x['e']), None)
    if b is None:
        continue
    u = (tk - b['s']) / (b['e'] - b['s'])
    bars.append({'b': b['i'], 'u': round(u, 4), 'r': wr[k], 'c': wc[k]})
for b in bricks:
    if b['k'] == 'broll':
        for j in range(17):
            bars.append({'b': b['i'], 'u': round((j + 0.5) / 17, 4), 'r': 0.0, 'c': 0.0})
# rótulos das falhas (no instante em que a narração cita cada uma)
TAGS = [{'id': 'tg0', 'b': 6, 'at': T['ruido1'], 'txt': 'Ruído de fundo', 'sub': '−61 dB'},
        {'id': 'tg1', 'b': 9, 'at': T['silencio'], 'txt': 'Silêncio', 'sub': '2,5 s'},
        {'id': 'tg2', 'b': 3, 'at': T['gagu'], 'txt': 'Gaguejada', 'sub': '“É assim… é assim que…”'},
        {'id': 'tg3', 'b': 10, 'at': T['erro'], 'txt': 'Erro no meio da frase', 'sub': '“…15 anos de mercado, que…”'}]
tags_html = '\n  '.join(f'<div class="tag" id="{g["id"]}"><b>{html.escape(g["txt"])}</b><span>{html.escape(g["sub"])}</span></div>' for g in TAGS)

# ---------- rótulos de seção (canto superior esquerdo) ----------
LABS = [('Gravação bruta · real', 0.0, T['eu1'] - 0.1, 'grey'), ('Cortez · IA que edita vídeo', T['eu1'] - 0.1, T['s1a'] - 0.15, ''),
        ('Linha de acabamento', T['s1a'] - 0.15, T['merge0'], ''), ('Vídeo pronto · editado pelo Cortez', T['merge0'], T['chat0'], '')]
labs_html = '\n  '.join(f'<div class="lab {cl}" id="lab{i}"><span class="in"><i></i>{html.escape(tx)}</span></div>' for i, (tx, a, b, cl) in enumerate(LABS))
labs = [{'s': round(a, 3), 'e': round(b, 3)} for _, a, b, _ in LABS]

# ---------- legenda L05 (só a narração; blocos de até 4 palavras numa linha) ----------
WEAK = {'que', 'e', 'com', 'de', 'a', 'o', 'da', 'do', 'em', 'no', 'na', 'os', 'as', 'um', 'uma', 'eu', 'me'}
units, g = [], []
for w in WORDS:
    if g:
        prev = g[-1]
        hard = w['s'] - prev['e'] > 0.30 or prev['w'][-1] in '.?!,'
        full = len(g) >= 4 or len(' '.join(x['w'] for x in g + [w])) > 26
        if hard or full:
            carry = []
            if full and not hard and len(g) > 1 and norm(g[-1]['w']) in WEAK:
                carry = [g.pop()]
            units.append(g); g = carry
    g.append(w)
if g:
    units.append(g)
groups = []
for u in units:
    if groups and len(u) == 1 and len(u[0]['w']) <= 5 and len(groups[-1]) < 4 and len(' '.join(x['w'] for x in groups[-1] + u)) <= 24 \
            and u[0]['s'] - groups[-1][-1]['e'] < 0.3 and groups[-1][-1]['w'][-1] not in '.?!':
        groups[-1] = groups[-1] + u
    else:
        groups.append(u)
# não termina com um bloco de uma palavra só ("vídeo."): puxa a última palavra do bloco anterior
for i in range(1, len(groups)):
    if len(groups[i]) == 1 and len(groups[i - 1]) >= 3 and groups[i - 1][-1]['w'][-1] not in '.?!,' and groups[i][0]['s'] - groups[i - 1][-1]['e'] < 0.3:
        groups[i] = [groups[i - 1].pop()] + groups[i]
# os títulos grandes já dizem "Me manda o seu pior vídeo bruto." e "Eu sou o Cortez." — sem legenda duplicada nesses trechos
HIDE = lambda gw: gw[-1]['e'] <= T['aquele'] + 0.01 or (gw[0]['s'] >= T['eu1'] - 0.01 and gw[-1]['e'] <= T['cortez'] + 0.75)
groups = [gw for gw in groups if not HIDE(gw)]
EMPH = {'pior', 'bruto', 'cortez', 'ruido', 'silencios', 'erros', 'cenas', 'aprova', 'pedir'}
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s']
    e = groups[i + 1][0]['s'] if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.5 else gw[-1]['e'] + 0.25
    e = min(e, SE + 0.1)
    spans = ' '.join(f'<span class="cw{" em" if norm(x["w"]) in EMPH else ""}" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, x in enumerate(gw))
    caps_html.append(f'<div class="cap" id="cg{i}">{spans}</div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3),
                      'w': [{'s': x['s'], 'e': round(min(x['e'] + 0.04, gw[k + 1]['s']) if k + 1 < len(gw) else e, 3)} for k, x in enumerate(gw)],
                      'text': ' '.join(x['w'] for x in gw)})

# ---------- lista das estações (topo) ----------
ST = [('01', 'Ruído', T['s1b']), ('02', 'Silêncios', T['c1b']), ('03', 'Erros', T['c2b']), ('04', 'Cenas', T['s4b']), ('05', 'Legenda · música · animação', T['s5b'])]
st_html = '\n    '.join(f'<div class="st" id="st{i}"><span class="n">{n}</span><span class="t">{html.escape(t)}</span><i class="ck"><svg viewBox="0 0 24 24"><path d="M5 12.5 L10 17 L19 7.5" fill="none" stroke="#FFFFFF" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg></i></div>' for i, (n, t, _) in enumerate(ST))
st_data = [{'done': round(d, 3)} for _, _, d in ST]

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'labs': labs, 'caps': caps_data, 'tags': TAGS, 'st': st_data, 'seq': seq, 'cta': MODE,
        'bricks': bricks, 'bars': bars, 'H': H, 'len': [len0, len1, len2, len3]}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{LABS}}', labs_html)
       .replace('{{TAGS}}', tags_html).replace('{{ST}}', st_html).replace('{{DUR}}', f'{DUR:.3f}')
       .replace('{{CTACSS}}', '#btn { display:none; }' if MODE == 'comment' else '#cmh, #cmf, #cms { display:none; }'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [
    {'id': 'hook', 'start': 0, 'end': N0, 'label': 'Gravação bruta · real', 'what': 'close nos blocos do tropeço real ("É assim… É assim que…") tocando em sincronia; título "Me manda o seu pior vídeo bruto."'},
    {'id': 'line', 'start': N0, 'end': T['frase'], 'label': 'Gravação bruta · real', 'what': 'a câmera recua: a gravação real (0–35 s) é uma fileira de blocos sobre a esteira; rótulos nas falhas reais citadas (ruído −61 dB, silêncio 2,5 s, gaguejada, erro no meio da frase)'},
    {'id': 'cortez', 'start': T['eu1'], 'end': T['s1a'], 'label': 'Cortez · IA que edita vídeo', 'what': 'as cinco estações (arcos) aparecem alinhadas no fim da esteira'},
    {'id': 'stations', 'start': T['s1a'], 'end': T['merge0'], 'label': 'Linha de acabamento', 'what': '01 ruído (cor volta, ruído some, envelope limpo) · 02 silêncios afundam e a fileira fecha · 03 erros e hesitações saem · 04 cenas do EXEMPLO_2 descem nos vãos · 05 legenda, música e animação: faces viram a entrega EXEMPLO_2'},
    {'id': 'approve', 'start': T['merge0'], 'end': T['quer'], 'label': 'Vídeo pronto', 'what': 'a fileira se junta num só vídeo 9:16 (EXEMPLO_2 tocando) e o toque em "Aprovar"'},
    {'id': 'ask', 'start': T['quer'], 'end': SE, 'label': 'Vídeo pronto', 'what': 'exemplo de pedido de ajuste no chat e resposta do Cortez; selo V2'},
    {'id': 'cta', 'start': CTA0, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'what': 'Mande o bruto. Receba pronto. / Você grava. O Cortez edita. Você aprova. / ' +
     ('Comente CORTEZ (balão) + campo de comentário com CORTEZ digitado e enviado + "aqui nos comentários" ↓' if MODE == 'comment' else 'Saiba mais')}]
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / f'analysis/caption_groups{SUF}.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V1', 'cta': MODE, 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + Output) via hf-seek',
    'identity': 'ID07', 'caption_style': 'L05', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['fileira de blocos físicos (RoundedBox + face com o quadro real) sobre esteira, sombras reais', 'barras do envelope real (bruto → limpo) por cima de cada bloco (InstancedMesh)',
                 'cinco arcos-estação atravessando a fileira; silêncios afundam na esteira, erros sobem e saem, cenas descem nos vãos', 'fusão da fileira num vídeo 9:16 (EXEMPLO_2) + profundidade de campo'],
    'T': T, 'labs': labs, 'seq': seq, 'lengths': [len0, len1, len2, len3], 'cta_seconds': CTA_S}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'len': [len0, len1, len2, len3], 'T': {k: round(v, 2) for k, v in T.items()}}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
