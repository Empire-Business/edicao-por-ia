#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
ID01 Verde (fundo #0B141A · texto #E9EDEF · verde #25D366 · superfície #202C33 · apoio #AEBAC1; Inter + IBM Plex Mono) + legenda L02
(blocos curtos de até 3 palavras, entrada suave). Texto das legendas = texto conferido de cada trecho (edit/edl.json), com o tempo de
cada palavra alinhado às palavras realmente reconhecidas na voz final (o Whisper erra "brabo", "montar", "longo", "Corte").
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import difflib, html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
FPS = EDL['fps']
REC = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
       for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
SH = J.parent / 'material-compartilhado'
SRCW = {k: [w for s_ in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s_['words']] for k in ('ig', 'yt')}
CTA = 4.6
# variante da tela final: CTA=saiba (padrão, botão "Saiba mais") ou CTA=comment ("Comente CORTEZ", jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md)
CTA_MODE = os.environ.get('CTA', 'saiba')
assert CTA_MODE in ('saiba', 'comment'), CTA_MODE
DUR = round(SPEECH + CTA, 3)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9%]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


# 1) palavras conferidas com tempo: alinha o texto de cada trecho às palavras reconhecidas dentro do trecho
span = {}
for s in EDL['segments']:
    a, b = s['start'], s['start'] + s['frames'] / FPS
    x = span.setdefault(s['take'], [a, b]); x[0] = min(x[0], a); x[1] = max(x[1], b)
WORDS = []
for tk in EDL['takes']:
    a, b = span[tk['id']]
    toks = tk['text'].replace('100%', '100%').split()
    # 1º as palavras da transcrição da FONTE (tempos do EDL mapeados para o vídeo: confiáveis também no começo do arquivo, onde o
    # Whisper da voz final às vezes perde a 1ª palavra); depois as reconhecidas na voz final; o resto é interpolado
    rec = []
    for sg in [x for x in EDL['segments'] if x['take'] == tk['id']]:
        for w in SRCW[sg['src']]:
            if sg['in'] - 0.03 <= w['start'] < sg['out'] - 0.03:
                o = sg['start'] + (w['start'] - sg['in'])
                rec.append({'w': w['word'].strip(), 's': round(max(sg['start'], o), 3), 'e': round(min(sg['start'] + sg['frames'] / FPS, o + w['end'] - w['start']), 3)})
    rec2 = [r for r in REC if a - 0.08 <= (r['s'] + r['e']) / 2 <= b + 0.05]
    tt = [None] * len(toks)
    for rr in (rec, rec2):
        sm = difflib.SequenceMatcher(a=[norm(t) for t in toks], b=[norm(r['w']) for r in rr], autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                if tt[blk.a + k] is None:
                    tt[blk.a + k] = (rr[blk.b + k]['s'], rr[blk.b + k]['e'])
    # tempos crescentes (um par fora de ordem vira interpolação)
    last = -1
    for i in range(len(tt)):
        if tt[i] is not None:
            if tt[i][0] < last - 0.01: tt[i] = None
            else: last = tt[i][0]
    # sem par: interpola entre vizinhos conhecidos (ou bordas do trecho)
    known = [(i, v) for i, v in enumerate(tt) if v]
    for i in range(len(toks)):
        if tt[i]:
            continue
        L = max([k for k in known if k[0] < i], default=None, key=lambda k: k[0])
        R = min([k for k in known if k[0] > i], default=None, key=lambda k: k[0])
        t0 = L[1][1] if L else a + 0.02
        t1 = R[1][0] if R else b - 0.05
        nL = i - (L[0] if L else -1); nT = (R[0] if R else len(toks)) - (L[0] if L else -1)
        s0 = t0 + (t1 - t0) * (nL - 1) / max(1, nT - 1) if nT > 1 else t0
        s1 = t0 + (t1 - t0) * nL / max(1, nT - 1) if nT > 1 else t1
        tt[i] = (round(max(a, s0), 3), round(min(b, max(s0 + 0.08, s1)), 3))
    for t, (s0, e0) in zip(toks, tt):
        WORDS.append({'w': t, 's': round(s0, 3), 'e': round(e0, 3), 'take': tk['id'], 'who': tk['speaker']})


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


TS = {k: round(v[0], 3) for k, v in span.items()}
TE = {k: round(v[1], 3) for k, v in span.items()}
T = {'q': TS['t02'], 'd0': TS['t03'], 'flap': W('dois'), 'm0': TS['t04'], 'mandei': W('mandei'), 'caramba': W('caramba'), 'sinistro': W('sinistro', 6),
     'v2': TS['t06'], 'styles': W('só', TS['t06']), 'cor': W('cor', TS['t06']), 'v3': TS['t07'], 'longo': W('longo', TS['t07']), 'ten': W('10', TS['t07']),
     'bom': W('bom', TS['t07']), 'e0': TS['t08'], 'k1': W('efeito'), 'k2': W('música'), 'k3': W('tudo', TS['t08']), 'k4': W('visual'),
     'p0': TS['t09'], 'p1': TS['t10'], 'pct': W('100%'), 'f0': TS['t11'], 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['tap'] = round(SPEECH + 2.75, 3)
notes = {k: {'s': TS[k], 'e': TE[k]} for k in ('t01', 't06', 't07', 't11')}

# 2) cabeçalho (rótulo em IBM Plex Mono + título opcional em Inter 800, só nas batidas principais)
HEADS = [
    ('h1', 0, T['q'], 'Áudio real · Convidado, cliente do Cortez', [('O áudio do', 0), ('<em>cliente.</em>', 0)]),
    ('h2', T['q'] + 0.05, T['m0'] - 0.05, 'Trecho da live', [('Há quanto', T['q'] + 0.15), ('<em>tempo?</em>', T['q'] + 0.45)]),
    ('h3a', T['m0'], T['mandei'] - 0.05, 'Trecho da live', []),
    ('h3', T['mandei'], T['v2'] - 0.1, 'A mensagem dele pro Apresentador', [('“Isso daqui é', T['mandei'] + 0.1), ('<em>sinistro.”</em>', T['caramba'] - 0.1)]),
    ('h4', T['v2'] + 0.05, T['styles'] - 0.1, 'Áudio do Convidado · cliente', []),
    ('h5', T['styles'], T['v3'] - 0.25, 'Editados pelo Cortez', [('Outro estilo,', T['styles'] + 0.1), ('<em>outra cor.</em>', T['cor'] - 0.35)]),
    ('h6', T['v3'] + 0.3, T['ten'] - 0.1, 'Exemplo · editado pelo Cortez', [('1 vídeo', T['v3'] + 0.4), ('<em>longo.</em>', T['longo'])]),
    ('h7', T['ten'] - 0.05, T['p0'] - 0.45, 'Vídeos curtos · editados pelo Cortez', [('Vários', T['ten']), ('<em>cortes.</em>', T['ten'] + 0.25)]),
    ('h8', T['p0'], T['f0'] - 0.1, 'Reel do Convidado · @perfil-do-convidado', [('Ele já', T['p0'] + 0.1), ('<em>postou.</em>', T['p0'] + 0.4)]),
    ('h9', T['f0'], SPEECH - 0.05, 'Áudio do Convidado · cliente', []),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.34 - at)), 3)} for tx, at in lines_]})

# 3) legendas L02: blocos curtos (até 3 palavras; 4 quando são monossílabos), quebras escolhidas à mão no texto conferido
CAPBREAKS = {
    't01': 'Caraca, | muito brabo | mesmo, hein?', 't02': 'Quanto tempo | você tá usando | a ferramenta?', 't03': 'Tô usando, | acho que há | dois dias.',
    't04': 'Quando eu vi | a ferramenta', 't05': 'na prática, | já mandei mensagem | pro Apresentador: | caramba, | isso daqui | é sinistro, hein?',
    't06': 'Aí já pedi | pra ele montar | um prompt | pra mim, | de acordo | com a edição | que eu gostei muito. | Só mudar o | estilo de vídeo | e estilo | de cor.',
    't07': 'Um vídeo longo | que eu fiz | aí no YouTube | já gerou | uns 10 cortes | do Instagram. | Corte muito bom.',
    't08': 'E é bem | editado também, | com efeito, | com música, | com tudo, | visual bacana.',
    't09': 'E eu já | postei um vídeo,', 't10': 'já tenho | o vídeo lá, | editado 100% | pela ferramenta.', 't11': 'Muito sinistro.'}
KEY = {'brabo', 'dois', 'dias', 'sinistro', 'estilo', 'cor', 'longo', '10', 'cortes', 'efeito', 'música', 'tudo', 'visual', 'bacana', '100%', 'bom'}
groups, k = [], 0
for tk in EDL['takes']:
    ws = [w for w in WORDS if w['take'] == tk['id']]
    blocks = [b.split() for b in CAPBREAKS[tk['id']].split('|')]
    assert [x for b in blocks for x in b] == [w['w'] for w in ws], (tk['id'], blocks, [w['w'] for w in ws])
    i = 0
    for b in blocks:
        groups.append(ws[i:i + len(b)]); i += len(b)
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s']
    nxt = groups[i + 1][0]['s'] if i + 1 < len(groups) else None
    e = nxt if nxt is not None and nxt - gw[-1]['e'] < 0.6 else gw[-1]['e'] + 0.3
    e = min(e, SPEECH)
    parts = []
    for x in gw:
        cls = ' class="k"' if norm(x['w']).rstrip('%') in {norm(k).rstrip('%') for k in KEY} else ''
        parts.append(f'<span{cls}>{html.escape(x["w"])}</span>')
    caps_html.append(f'<div class="cap" id="cg{i}">{" ".join(parts)}</div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'text': ' '.join(x['w'] for x in gw)})

who = [{'s': s['start'], 'e': round(s['start'] + s['frames'] / FPS, 3), 'who': s['speaker']} for s in EDL['segments']]
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
wave = json.loads((C / 'assets/wave.json').read_text())
data = {'T': T, 'notes': notes, 'who': who, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'wave': wave}
CTA_HTML = {'saiba': '''  <div class="cta-h" id="ch"><span class="ln"><span class="in" id="ch1">Edição profissional</span></span><span class="ln"><span class="in" id="ch2"><em>com IA.</em></span></span></div>
  <div class="cta-s" id="cs">Você grava. <b>O Cortez edita.</b> Você aprova.</div>
  <div id="btn">Saiba mais <span>→</span></div>''',
 'comment': '''  <div class="cta-h" id="ch"><span class="ln"><span class="in" id="ch1"><svg class="bal" viewBox="0 0 64 64"><path d="M13 8 H51 A9 9 0 0 1 60 17 V39 A9 9 0 0 1 51 48 H29 L16 58 V48 H13 A9 9 0 0 1 4 39 V17 A9 9 0 0 1 13 8 Z" fill="none" stroke="#25D366" stroke-width="5" stroke-linejoin="round"/><circle cx="20" cy="28" r="3.8" fill="#25D366"/><circle cx="32" cy="28" r="3.8" fill="#25D366"/><circle cx="44" cy="28" r="3.8" fill="#25D366"/></svg>Comente</span></span><span class="ln big"><span class="in" id="ch2"><em>CORTEZ</em></span></span></div>
  <div class="cta-s" id="cs">aqui nos comentários<svg class="arr" viewBox="0 0 32 32"><path d="M16 5 V26 M7 18 L16 27 L25 18" fill="none" stroke="#25D366" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
  <div id="cbox"><span id="cph">Adicione um comentário…</span><span id="ctx">''' + ''.join(f'<span class="l" id="tc{i}">{c}</span>' for i, c in enumerate('CORTEZ')) + '''<span id="caret"></span></span>
    <div id="csend"><svg viewBox="0 0 32 32"><path d="M16 26 V7 M8 14 L16 6 L24 14" fill="none" stroke="#0B141A" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div>'''}[CTA_MODE]
CTA_JS = {'saiba': '''  IN('#ch1',T.cta0+.2,.75); IN('#ch2',T.cta0+.38,.75);
  tl.fromTo('#cs',{opacity:0,y:20},{opacity:1,y:0,duration:.55,ease:'power3.out',immediateRender:false},T.cta0+.75);
  tl.fromTo('#btn',{opacity:0,y:36,scale:.92},{opacity:1,y:0,scale:1,duration:.55,ease:'back.out(1.6)',immediateRender:false},T.cta0+1.0);
  tl.fromTo('#cursor',{opacity:0,x:820,y:900},{opacity:1,x:610,y:556,duration:.8,ease:'power2.inOut',immediateRender:false},T.tap-.85);
  tl.to('#btn',{scale:.95,duration:.09,yoyo:true,repeat:1,ease:'power2.out'},T.tap-.02);
  tl.to('#cursor',{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'},T.tap-.02);
  tl.to('#cursor',{x:680,y:660,opacity:0,duration:.6,ease:'power2.in'},T.tap+.5);''',
 'comment': '''  IN('#ch1',T.cta0+.2,.75); IN('#ch2',T.cta0+.38,.75);
  tl.fromTo('#cs',{opacity:0,y:20},{opacity:1,y:0,duration:.55,ease:'power3.out',immediateRender:false},T.cta0+.75);
  tl.fromTo('#cbox',{opacity:0,y:36,scale:.94},{opacity:1,y:0,scale:1,duration:.55,ease:'back.out(1.6)',immediateRender:false},T.cta0+1.0);
  for(let k=0;k<8;k++) tl.set('#caret',{opacity:k%2?0:1},T.cta0+1.25+k*.25);
  tl.set('#caret',{opacity:1},T.typeK0);
  tl.set('#cph',{opacity:0},T.typeK0);
  'CORTEZ'.split('').forEach((c,i)=>tl.set('#tc'+i,{display:'inline'},T.typeK0+i*.11));
  tl.fromTo('#cursor',{opacity:0,x:900,y:980},{opacity:1,x:866,y:572,duration:.8,ease:'power2.inOut',immediateRender:false},T.tap-.85);
  tl.to('#csend',{scale:.9,duration:.09,yoyo:true,repeat:1,ease:'power2.out'},T.tap-.02);
  tl.to('#cursor',{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'},T.tap-.02);
  tl.to('#ctx',{y:-46,opacity:0,duration:.32,ease:'power2.in'},T.tap+.08);
  tl.set('#cph',{opacity:1},T.tap+.42);
  tl.to('#cursor',{x:930,y:700,opacity:0,duration:.6,ease:'power2.in'},T.tap+.5);'''}[CTA_MODE]
if CTA_MODE == 'comment':
    T['typeK0'] = round(T['cta0'] + 1.6, 3)
    data['T'] = T
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{CTA_HTML}}', CTA_HTML).replace('{{CTA_JS}}', CTA_JS).replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

if CTA_MODE == 'comment':
    cs = [{'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou) — variante Comente CORTEZ', 'title': 'Comente CORTEZ / aqui nos comentários / campo de comentário: CORTEZ digitado e enviado'}]
    (J / 'analysis/scene_plan_comente-cortez.json').write_text(json.dumps(cs, ensure_ascii=False, indent=1))
    print(json.dumps({'dur': DUR, 'cta': CTA_MODE, 'typeK0': T['typeK0'], 'tap': T['tap']})); raise SystemExit(0)
scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Edição profissional com IA. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: UnrealBloom + Output; render target para o "portal")',
    'identity': 'ID01', 'caption_style': 'L02', 'determinism': 'tudo em função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; telas desenhadas em canvas por quadro; PRNG de semente fixa',
    'three_js': ['celular 3D de vidro com a conversa desenhada quadro a quadro', 'bolha de áudio 3D + fita de ondas 3D guiada pelo envelope real do áudio',
                 'placar de palhetas 3D (split-flap) para "2 dias" e "100%"', 'mensagem 3D saindo da tela', 'baralho de estilos (vídeos editados pelo Cortez)',
                 'mergulho na tela: vídeo longo fatiado em 10 cortes que viram cartões e carrossel; volta pelo portal (render target)'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'T': T}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
