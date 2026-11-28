#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da EDL, da transcrição da voz final e de src/index.tpl.html.
F22 + ID06 + legenda L03 (uma palavra por vez; palavras curtas de função vão junto com a seguinte).
Legenda = texto CONFERIDO de cada trecho (edit/edl.json → takes[].text) alinhado aos tempos reais das palavras da voz final: o Whisper
some com "Bom", "Um" e ouve "pra"/"para" etc.; palavras conferidas sem par recebem o tempo interpolado entre as vizinhas.
CTA=saiba (padrão) → botão "Saiba mais"; CTA=comment → "Comente CORTEZ" (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md), em comp-cta-comment/.
Grava analysis/scene_plan.json, motion_plan.json, caption_groups.json (só na versão principal).
Run: ../../../.venv/bin/python src/build.py
"""
import difflib, html, json, os, re, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WH = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
      for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA_S = 4.6
DUR = round(SPEECH + CTA_S, 3)
MODE = os.environ.get('CTA', 'saiba')
NUM = {'5': 'cinco', '2': 'dois', '1': 'um', '10': 'dez', '20': 'vinte', '30': 'trinta'}


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))
    w = NUM.get(w, w)
    return {'para': 'pra'}.get(w, w)


# 1) palavras conferidas, em ordem, com o falante; alinhadas aos tempos do Whisper
spk = {t['id']: t['speaker'] for t in EDL['takes']}
VER = [{'w': x, 'spk': t['speaker'], 'take': t['id']} for t in EDL['takes'] for x in t['text'].split()]
# ordem real das falas na EDL (o gancho t01 vem antes de t02/t03...)
order = list(dict.fromkeys(s['take'] for s in EDL['segments']))
VER = [v for tid in order for v in VER if v['take'] == tid]
a, b = [norm(v['w']) for v in VER], [norm(w['w']) for w in WH]
sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1):
            VER[i1 + k]['s'], VER[i1 + k]['e'] = WH[j1 + k]['s'], WH[j1 + k]['e']
    elif tag == 'replace' and j2 > j1:
        s0, e0 = WH[j1]['s'], WH[j2 - 1]['e']
        n = i2 - i1
        for k in range(n):
            VER[i1 + k]['s'] = round(s0 + (e0 - s0) * k / n, 3); VER[i1 + k]['e'] = round(s0 + (e0 - s0) * (k + 1) / n, 3)
# inserções sem par: interpola entre as vizinhas
for i, v in enumerate(VER):
    if 's' not in v:
        prv = next((VER[j]['e'] for j in range(i - 1, -1, -1) if 's' in VER[j]), 0.0)
        nxt = next((VER[j]['s'] for j in range(i + 1, len(VER)) if 's' in VER[j]), prv + 0.3)
        span = [j for j in range(i, len(VER)) if 's' not in VER[j]]
        run = [j for j in span if all('s' not in VER[q] for q in range(i, j + 1))]
        n = len(run); d = max(0.12, (nxt - prv) / (n + 0.0001))
        for q, j in enumerate(run):
            VER[j]['s'] = round(prv + d * q + 0.01, 3); VER[j]['e'] = round(min(nxt, prv + d * (q + 1)), 3)
missing = [v['w'] for v in VER if 's' not in v]
assert not missing, missing
# palavra conferida sem par no começo de um trecho (ex.: "Bom," — o Whisper juntou com o "O") não pode cair antes do trecho começar;
# depois, ordem crescente com ≥ 0,12 s entre inícios.
t_first = {}
for s_ in EDL['segments']:
    t_first.setdefault(s_['take'], s_['start'])
seen = set()
for v in VER:
    if v['take'] not in seen:
        seen.add(v['take']); v['s'] = max(v['s'], round(t_first[v['take']] + 0.04, 3))
for i in range(len(VER) - 1):
    if VER[i + 1]['s'] < VER[i]['s'] + 0.12 and VER[i + 1]['e'] > VER[i]['s'] + 0.12:
        VER[i + 1]['s'] = round(VER[i]['s'] + 0.12, 3)
for i in range(len(VER) - 1):
    VER[i]['e'] = round(min(max(VER[i]['e'], VER[i]['s'] + 0.08), VER[i + 1]['s']) if VER[i + 1]['s'] > VER[i]['s'] else VER[i]['e'], 3)


def W(word, after=0.0, last=False):
    n = norm(word)
    c = [v for v in VER if v['s'] >= after - 0.05 and norm(v['w']) == n]
    if not c:
        raise SystemExit(f'palavra {word!r} não encontrada após {after}')
    return (c[-1] if last else c[0])['s']


seg_start = {}
for s in EDL['segments']:
    seg_start.setdefault(s['take'], s['start'])
T = {'q0': seg_start['t02'], 't1': seg_start['t03'], 'nossa': W('nossa')}
T['postar'] = W('postar')
T['t2'] = W('e', T['postar'])
T['br'] = W('aí', T['t2'])
T['pd'] = W('aí', T['br'] + 0.5)
q_i0 = next(i for i, v in enumerate(VER) if v['s'] >= T['pd'] and norm(v['w']) == 'de')
q_i1 = next(i for i in range(q_i0, len(VER)) if VER[i]['w'].endswith('?'))
T['qs'], T['qe'] = VER[q_i0]['s'], VER[q_i1]['e']
T['id'] = W('aí', T['qe'])
T['varias'] = W('várias', T['id'])
T['pedi'] = W('pedi', T['id'])
T['fez'] = W('fez', T['pedi'])
T['muito'] = W('muito', T['fez'])
T.update({'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR, 'tap': round(SPEECH + 2.9, 3)})
card = {'words': [v['w'][:1].upper() + v['w'][1:] if i == 0 else v['w'] for i, v in enumerate(VER[q_i0:q_i1 + 1])],
        't': [v['s'] for v in VER[q_i0:q_i1 + 1]], 'end': T['qe']}

swaps, cur = [], EDL['segments'][0]['speaker']
for s in EDL['segments']:
    if s['speaker'] != cur:
        swaps.append({'t': s['start'], 'to': s['speaker']}); cur = s['speaker']

HEADS = [
    ('h1', 0, T['q0'], 'Trecho da live · Convidado, cliente', [('“Nossa, quanta', 0), ('<em>edição boa.”</em>', 0)]),
    ('h2', T['q0'], T['t1'], 'A pergunta do Apresentador', [('Qual foi o', T['q0'] + 0.05), ('<em>primeiro teste?</em>', T['q0'] + 0.3)]),
    ('h3', T['t1'], T['t2'], 'Teste 1', [('Um vídeo', T['t1'] + 0.1), ('<em>curto.</em>', W('curto') - 0.15)]),
    ('h4', T['t2'], T['br'], 'Teste 2', [('Um vídeo', T['t2'] + 0.1), ('<em>longo.</em>', W('longo', T['t2']) - 0.15)]),
    ('h5', T['br'], T['pd'], 'Aí ele foi brincar', [('O que mais', T['br'] + 0.1), ('<em>ele pode fazer?</em>', W('pode', T['br']) - 0.2)]),
    ('h6', T['pd'], T['id'], 'Teste 3 · o pedido', [('Vídeo longo →', T['pd'] + 0.1), ('<em>vídeos curtos?</em>', W('curtos', T['pd']) - 0.2)]),
    ('h7', T['id'], T['pedi'], 'A resposta', [('Ideias para', T['id'] + 0.1), ('<em>cinco cortes.</em>', W('cinco', T['id']) - 0.15)]),
    ('h8', T['pedi'], T['speechEnd'], 'Teste 3 · o resultado', [('Os cinco cortes.', T['pedi'] + 0.1), ('<em>Ficou muito bom.</em>', W('ficou', T['fez']) - 0.15)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.7, en - 0.32 - at)), 3)} for tx, at in lines_]})

# 2) legenda L03 — uma palavra por vez (palavra curta de função vai junto com a seguinte); escondida enquanto o cartão digita a pergunta
EMPH = {'nossa', 'edicao', 'boa', 'primeiro', 'teste', 'curto', 'instagram', 'postar', 'segundo', 'longo', 'youtube', 'brincar', 'ideias',
        'cinco', 'cortes', 'bom', 'ferramenta'}
FUNC = {'o', 'a', 'e', 'eu', 'de', 'um', 'no', 'na', 'ja', 'la', 'que', 'com', 'os', 'as', 'do', 'da', 'dos', 'pra', 'foi', 'ai', 'qual', 'ao', 'se', 'te', 'me'}
words = [v for v in VER if not (T['qs'] - 0.05 <= v['s'] <= T['qe'] + 0.05)]
units, i = [], 0
while i < len(words):
    u = [words[i]]
    if norm(words[i]['w']) in FUNC and i + 1 < len(words) and words[i + 1]['s'] - words[i]['e'] < 0.3 \
            and words[i + 1]['spk'] == words[i]['spk'] and len(words[i]['w'] + words[i + 1]['w']) <= 13 and not words[i]['w'][-1] in '.,?!':
        u.append(words[i + 1]); i += 1
    units.append(u); i += 1
caps_html, caps_data = [], []
for k, u in enumerate(units):
    s = u[0]['s']
    nx = units[k + 1][0]['s'] if k + 1 < len(units) else 1e9
    e = nx if nx - u[-1]['e'] < 0.45 else u[-1]['e'] + 0.25
    e = min(e, SPEECH)
    spans = ' '.join(f'<span class="{"em" if norm(x["w"]) in EMPH else ""}">{html.escape(x["w"].strip(",.;:"))}</span>' for x in u)
    caps_html.append(f'<div class="cap" id="cp{k}">{spans}</div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'text': ' '.join(x['w'] for x in u)})

pill_x = lambda txt: str(round(540 - (len(txt) * 12.6 + 64) / 2))
PILLS = [('pl1', 0.5, T['q0'] - 0.2), ('pl2', T['t1'] + 0.8, T['t2'] - 0.2), ('pl3', T['t2'] + 1.0, T['br'] + 0.4),
         ('pl6', T['fez'] + 1.2, T['speechEnd'] - 0.1), ('pl4', T['fez'] + 1.4, T['speechEnd'] - 0.1), ('pl5', T['cta0'] + 1.4, DUR + 1)]
pills = [{'id': p, 'a': round(a_, 3), 'b': round(b_, 3)} for p, a_, b_ in PILLS]

# 3) CTA
ACC, DARK = '#0A4DFF', '#13233C'
if MODE == 'saiba':
    CTA_CSS = ''
    CTA_HTML = '<div id="btn">Saiba mais <span>→</span></div>'
    CTA_TL = '''  tl.fromTo('#btn',{opacity:0,y:40},{opacity:1,y:0,duration:.6,ease:'power3.out',immediateRender:false},T.cta0+1.05);
  tl.fromTo('#cursor',{opacity:0,x:800,y:1580},{opacity:1,x:600,y:1296,duration:.8,ease:'power2.inOut',immediateRender:false},T.tap-.85);
  tl.to('#btn',{scale:.95,duration:.09,yoyo:true,repeat:1,ease:'power2.out'},T.tap-.02);
  tl.to('#cursor',{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'},T.tap-.02);
  tl.to('#cursor',{x:660,y:1390,opacity:0,duration:.6,ease:'power2.in'},T.tap+.5);'''
else:
    assert MODE == 'comment', MODE
    WORD = 'CORTEZ'
    CTA_CSS = f'''
#cmain {{ position:absolute; left:0; right:0; top:1214px; z-index:10; opacity:0; display:flex; justify-content:center; align-items:center; gap:22px;
  font-family:"Inter", sans-serif; font-weight:800; font-size:64px; letter-spacing:-.03em; color:{DARK}; white-space:nowrap; }}
#cmain b {{ color:#FFFFFF; background:{ACC}; padding:4px 22px 8px; border-radius:18px; letter-spacing:.01em; }}
#cmain svg {{ width:70px; height:70px; flex:none; }}
#cfield {{ position:absolute; left:150px; width:780px; top:1336px; height:108px; z-index:10; opacity:0; border-radius:999px; background:#FFFFFF;
  box-shadow:0 0 0 2.5px rgba(10,77,255,.30), 0 18px 40px rgba(19,35,60,.14); display:flex; align-items:center; padding:0 16px 0 44px; }}
#cfield .tx {{ flex:1; display:flex; align-items:center; font-family:"Inter", sans-serif; font-size:42px; white-space:nowrap; overflow:hidden; height:60px; }}
#ctyped {{ display:inline-block; color:{DARK}; font-weight:700; letter-spacing:.04em; }}
#ctyped .tl {{ display:none; }}
#ccaret {{ display:inline-block; width:4px; height:48px; margin:0 6px 0 3px; background:{ACC}; flex:none; }}
#cph {{ color:#64748B; font-weight:400; }}
#csend {{ flex:none; width:76px; height:76px; border-radius:50%; background:{ACC}; display:flex; align-items:center; justify-content:center; }}
#csend svg {{ width:38px; height:38px; }}
#chint {{ position:absolute; left:0; right:0; top:1466px; z-index:10; opacity:0; display:flex; justify-content:center; align-items:center; gap:12px;
  font-family:"IBM Plex Mono", monospace; font-weight:500; font-size:24px; letter-spacing:.12em; text-transform:uppercase; color:{DARK}; }}
#chint svg {{ width:26px; height:30px; }}'''
    letters = ''.join(f'<span class="tl" id="tc{k}">{c}</span>' for k, c in enumerate(WORD))
    CTA_HTML = (f'<div id="cmain"><svg viewBox="0 0 70 70"><path d="M35 10C20.6 10 9 20 9 32.3c0 6.6 3.4 12.5 8.8 16.6L16 59l11.6-6.2c2.4.6 4.9.9 7.4.9 '
                f'14.4 0 26-10 26-22.4S49.4 10 35 10Z" fill="{ACC}" /><circle cx="24" cy="32" r="3.6" fill="#fff"/><circle cx="35" cy="32" r="3.6" fill="#fff"/>'
                f'<circle cx="46" cy="32" r="3.6" fill="#fff"/></svg>Comente <b>{WORD}</b></div>\n'
                f'  <div id="cfield"><div class="tx"><span id="ctyped">{letters}</span><span id="ccaret"></span><span id="cph">Adicione um comentário…</span></div>'
                f'<div id="csend"><svg viewBox="0 0 38 38"><path d="M19 31V8M9 17l10-10 10 10" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" '
                f'stroke-linejoin="round"/></svg></div></div>\n'
                f'  <div id="chint">aqui nos comentários <svg viewBox="0 0 26 30"><path d="M13 3v22M4 17l9 9 9-9" fill="none" stroke="{ACC}" stroke-width="3.6" '
                f'stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
    sx, sy = 876, 1384
    CTA_TL = f'''  tl.fromTo('#cmain',{{opacity:0,y:40}},{{opacity:1,y:0,duration:.6,ease:'power3.out',immediateRender:false}},T.cta0+1.0);
  tl.fromTo('#cfield',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.5,ease:'power3.out',immediateRender:false}},T.cta0+1.25);
  tl.fromTo('#chint',{{opacity:0,y:14}},{{opacity:1,y:0,duration:.45,ease:'power2.out',immediateRender:false}},T.cta0+1.5);
  {{ const ts=T.cta0+1.6;
    for(let t=T.cta0+1.25,k=0;t<T.end;t+=.27,k++){{ tl.set('#ccaret',{{opacity:(t>ts-.05&&t<T.tap+.3)?1:(k%2?0:1)}},t); }}
    tl.set('#cph',{{display:'none'}},ts);
    '{WORD}'.split('').forEach((c,k)=>tl.set('#tc'+k,{{display:'inline'}},ts+k*.1));
    tl.fromTo('#cursor',{{opacity:0,x:950,y:1560}},{{opacity:1,x:{sx},y:{sy},duration:.8,ease:'power2.inOut',immediateRender:false}},T.tap-.85);
    tl.to('#csend',{{scale:.86,duration:.09,yoyo:true,repeat:1,ease:'power2.out'}},T.tap-.02);
    tl.to('#cursor',{{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'}},T.tap-.02);
    tl.to('#ctyped',{{y:-36,opacity:0,duration:.3,ease:'power2.in'}},T.tap+.06);
    tl.set('#ctyped',{{display:'none'}},T.tap+.38); tl.set('#cph',{{display:'inline'}},T.tap+.4);
    tl.to('#cmain svg',{{scale:1.18,duration:.14,yoyo:true,repeat:1,ease:'power2.out'}},T.tap+.12);
    tl.to('#cursor',{{x:{sx + 50},y:{sy + 110},opacity:0,duration:.6,ease:'power2.in'}},T.tap+.5); }}'''

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'pills': pills, 'swaps': swaps, 'card': card, 'seq': seq}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH + 5.0:.3f}')
       .replace('{{PL1X}}', pill_x('Exemplo · vídeo longo editado pelo Cortez')).replace('{{PL2X}}', pill_x('Reel do Convidado · @perfil-do-convidado'))
       .replace('{{PL3X}}', pill_x('Exemplo · vídeo longo editado pelo Cortez')).replace('{{PL4X}}', pill_x('Demais: ilustração com vídeo longo editado pelo Cortez')).replace('{{PL6X}}', pill_x('Centro: Reel do Convidado · @perfil-do-convidado'))
       .replace('{{PL5X}}', pill_x('Centro: Reel do Convidado · @perfil-do-convidado'))
       .replace('{{CTA_CSS}}', CTA_CSS).replace('{{CTA_HTML}}', CTA_HTML).replace('{{CTA_TL}}', CTA_TL))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if MODE != 'saiba':
    O = J / f'comp-cta-{MODE}'
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir():
            d.mkdir(parents=True, exist_ok=True)
        elif not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True); os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': MODE, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Faça o seu primeiro teste. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: RenderPass + UnrealBloom discreto + Bokeh + Output; NeutralToneMapping; sombras PCF suaves)',
    'identity': 'ID06', 'caption_style': 'L03', 'style': 'escada de testes — plataformas de vidro subindo num céu claro',
    'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; texto do cartão desenhado por tempo de palavra; PRNG de semente fixa',
    'three_js': ['3 plataformas de vidro (transmissão) com degraus entre elas e placas TESTE 01/02/03', 'tela 9:16 (vídeo curto) e tela 16:9 (vídeo longo) com pé e sombra',
                 'cartão de vidro com o pedido do Convidado digitado no ritmo da fala', '5 fichas de ideia que sobem ao 3º degrau', 'cópia do vídeo longo que sobe e se divide em 5 fatias → 5 telas 9:16',
                 'câmera em grua por planos encadeados; brilho na tela no "nossa" e no "muito bom"; profundidade de campo em escala de pixel'],
    'T': T, 'swaps': swaps, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA_S}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data)}, ensure_ascii=False))
print(json.dumps(T))
