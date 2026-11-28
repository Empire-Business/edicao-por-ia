#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
ID08 Azul e Papel + legenda L06 (frase que se constrói). Mundo 3D: uma mesa de papel em plano-sequência (sombras reais, profundidade de campo).
Tempos = palavras realmente faladas na voz final. O texto da legenda é o texto conferido na fonte (o Whisper erra em recortes curtos:
"no vídeo" = "um vídeo", "de massa" = "em massa", "dúvida" = "dor", "jogar uma" = "de alguma"); o alinhamento texto→tempo é por sequência.
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import difflib, html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = round(EDL['duration'], 3)
CTA = 4.3
DUR = round(SPEECH + CTA, 3)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


def Wa(words, after=0.0):
    for w in words:
        try:
            return W(w, after)
        except SystemExit:
            pass
    raise SystemExit(f'nenhuma de {words} após {after}')


tk = {t['id']: [s for s in EDL['segments'] if s['take'] == t['id']][0]['start'] for t in EDL['takes']}
t1, t2, t3, t4, t5 = (tk[f't0{i}'] for i in range(1, 6))
T = {'five': Wa(('5', 'cinco')), 'minutos': W('minutos'), 'dia': W('dia'), 'editar': W('editar'), 'qualidade': W('qualidade'), 'prof': W('profissional'),
     'imposs': W('impossível'), 'ed0': t2, 'mandar': W('mandar', t2), 'dois': W('dois', t2), 'manda': W('manda', W('dias', t2)), 'pedir': W('pedir', t2),
     'correcao': W('correção', t2), 'pr0': t3, 'fazer': W('fazer', t3), 'em': W('em', W('editar', t3)), 'v20': Wa(('20', 'vinte'), t3), 'v30': Wa(('30', 'trinta'), t3),
     'termina2': W('termina', Wa(('30', 'trinta'), t3)), 'video2': W('vídeo', Wa(('30', 'trinta'), t3)), 'se': W('se', W('vídeo', Wa(('30', 'trinta'), t3))), 'correcao2': W('correção', t3),
     'manda2': W('manda', W('correção', t3)), 'pronto': W('pronto', t3), 'jo0': t4, 'massa1': W('massa', t4), 'massa2': W('massa', W('conseguir', t4)),
     'dor': round(W('uma', t4) + 0.12, 3), 'anos': W('anos', t4), 'ocupado': W('ocupado', t4), 'bp0': t5, 'postar': W('postar', t5),
     'dois2': Wa(('2', 'dois'), t5), 'tres': Wa(('3', 'três'), t5), 'dia2': W('dia', t5),
     'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['tap'] = round(SPEECH + 2.75, 3)
T = {k: round(v, 3) for k, v in T.items()}

# ---------- legenda L06: texto conferido alinhado aos tempos do Whisper ----------
TEXT = [   # "|" = troca de bloco da legenda (até 5 palavras; frases inteiras quando possível); "pô" omitido na legenda
    ('apresentador', 'Você vai gastar | 5 minutos do seu dia | para editar um vídeo | com extrema qualidade. | Um vídeo profissional | que antes era impossível.'),
    ('apresentador', 'É muito melhor do que: | "ah, vou mandar pro editor | e daqui a dois dias | ele me manda". | E ainda vou pedir correção.'),
    ('apresentador', 'E você vai fazer | outra coisa enquanto | ele termina de editar. | Em 20 minutos, | 30 minutos, | ele termina o seu vídeo. | '
              'Se você precisar | de alguma correção, | você manda pra ele | e pronto.'),
    ('convidado', 'Ou seja, | produzir conteúdo em massa | lá no YouTube | e conseguir produzir | conteúdo em massa | aqui no Instagram também, | '
             'que é uma dor | que eu tenho enfrentado | nos últimos dois anos, | de não conseguir | produzir em massa | aqui no Instagram | '
             'e já estar ocupado | no YouTube.'),
    ('apresentador', 'Agora você vai poder | postar tranquilamente, | se quiser, | dois, três vídeos no dia.'),
]
starts = [tk[f't0{i + 1}'] for i in range(5)] + [SPEECH]
toks = []
for i, (who, txt) in enumerate(TEXT):
    ww = [w for w in WORDS if starts[i] - 0.05 <= w['s'] < starts[i + 1] - 0.02]
    raw = txt.split()
    vt, brk = [], []
    for x in raw:
        if x == '|':
            brk.append(len(vt)); continue
        vt.append(x)
    a, b = [norm(x) for x in vt], [norm(x['w']) for x in ww]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    tm = [None] * len(vt)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            tm[blk.a + k] = ww[blk.b + k]['s']
    # substituições 1:1 (palavra ouvida errada) herdam o tempo da posição correspondente
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'replace' and i2 - i1 == j2 - j1:
            for k in range(i2 - i1):
                tm[i1 + k] = ww[j1 + k]['s']
    # palavras sem tempo (o Whisper engoliu): interpola entre vizinhas
    known = [k for k, v in enumerate(tm) if v is not None]
    for k in range(len(tm)):
        if tm[k] is None:
            lo = max([q for q in known if q < k], default=None); hi = min([q for q in known if q > k], default=None)
            t0 = tm[lo] if lo is not None else starts[i]; t1 = tm[hi] if hi is not None else starts[i + 1] - 0.1
            n0 = lo if lo is not None else -1; n1 = hi if hi is not None else len(tm)
            tm[k] = t0 + (t1 - t0) * (k - n0) / (n1 - n0)
    for k, w in enumerate(vt):
        toks.append({'w': w, 's': round(max(tm[k], starts[i]), 3), 'take': i, 'who': who, 'brk': k == 0 or k in brk})
for k in range(1, len(toks)):
    if toks[k]['s'] < toks[k - 1]['s'] + 0.04 and toks[k]['take'] == toks[k - 1]['take']:
        toks[k]['s'] = round(toks[k - 1]['s'] + 0.04, 3)

groups, g = [], []
for x in toks:
    if g and x['brk']:
        groups.append(g); g = []
    g.append(x)
if g:
    groups.append(g)


def lines(ws):
    if len(' '.join(x['w'] for x in ws)) <= 24:
        return [ws]
    best, bi = 1e9, 1
    for k in range(1, len(ws)):
        a = len(' '.join(x['w'] for x in ws[:k])); b = len(' '.join(x['w'] for x in ws[k:]))
        sc = max(a, b) - (3 if ws[k - 1]['w'][-1] in ',;:' else 0)
        if sc < best:
            best, bi = sc, k
    return [ws[:bi], ws[bi:]]


caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s'] - 0.02
    nxt = groups[i + 1][0]['s'] - 0.02 if i + 1 < len(groups) else SPEECH + 0.2
    e = min(nxt, gw[-1]['s'] + 1.4) if nxt - gw[-1]['s'] > 1.4 else nxt
    e = min(e, SPEECH + 0.15)
    ls, j, spans = lines(gw), 0, []
    for ln in ls:
        parts = []
        for x in ln:
            parts.append(f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>')
            j += 1
        spans.append(f'<span class="cl">{" ".join(parts)}</span>')
    top = 1560 if len(ls) == 2 else 1600
    caps_html.append(f'<div class="cap" id="cg{i}" style="top:{top}px">{"".join(spans)}</div>')
    ww = [x for ln in ls for x in ln]
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'w': [round(x['s'], 3) for x in ww], 'text': ' / '.join(' '.join(x['w'] for x in ln) for ln in ls)})

# ---------- títulos (topo) ----------
HEADS = [
    ('h1', 0.0, T['prof'] - 0.12, 'O seu tempo', [('5 minutos', 0.0, True), ('do seu dia.', T['dia'] - 0.25, False)]),
    ('h2', T['prof'] - 0.05, T['ed0'] + 0.25, 'Editado pelo Cortez', [('Vídeo profissional,', T['prof'] - 0.02, False), ('antes impossível.', T['imposs'] - 0.3, True)]),
    ('h3', T['ed0'] + 0.35, T['pedir'] - 0.3, 'Do jeito antigo', [('Mandar pro editor', T['mandar'] - 0.2, False), ('e esperar 2 dias.', T['dois'] - 0.2, True)]),
    ('h4', T['pedir'] - 0.2, T['pr0'] + 0.15, 'Do jeito antigo', [('E ainda pedir', T['pedir'] - 0.15, False), ('correção…', T['correcao'] - 0.1, True)]),
    ('h5', T['pr0'] + 0.3, T['em'] - 0.1, 'Com o Cortez', [('Você faz', T['fazer'] - 0.15, False), ('outra coisa.', T['fazer'] + 0.45, True)]),
    ('h6', T['em'], T['se'] - 0.1, 'Tempo de máquina', [('20 a 30 min', T['v20'] - 0.1, True), ('e está pronto.', T['termina2'] - 0.1, False)]),
    ('h7', T['se'], T['jo0'] + 0.3, 'Correção?', [('É só pedir.', T['correcao2'] - 0.2, False), ('Pronto.', T['pronto'] - 0.1, True)]),
    ('h8', T['jo0'] + 0.35, T['bp0'] - 0.1, 'Convidado · cliente do Cortez', [('Conteúdo em massa', T['massa1'] - 0.3, False), ('— a dor de 2 anos.', T['dor'] - 0.1, True)]),
    ('h9', T['bp0'] - 0.05, T['speechEnd'] - 0.05, 'Na sua semana', [('Postar 2, 3 vídeos', T['bp0'] - 0.02, False), ('por dia.', T['bp0'] + 0.08, True)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    # cada linha termina de entrar antes de o título sair (evita entrada e saída sobrepostas na mesma linha)
    lines_ = [(tx, min(at, en - 0.6), em) for tx, at, em in lines_]
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{"<em>" + html.escape(tx) + "</em>" if em else html.escape(tx)}</span></span>'
                 for j, (tx, at, em) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': 0.3 if hid == 'h9' else round(max(0.2, min(0.6, en - 0.36 - at)), 3)} for tx, at, em in lines_]})

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
stills = len(list((C / 'assets/stills').glob('*.jpg')))
pip_spans = []
for s in EDL['segments']:
    if s['speaker'] == 'apresentador':
        if pip_spans and abs(pip_spans[-1][1] - s['start']) < 0.05:
            pip_spans[-1][1] = round(s['start'] + s['frames'] / EDL['fps'], 3)
        else:
            pip_spans.append([s['start'], round(s['start'] + s['frames'] / EDL['fps'], 3)])
CTA_MODE = os.environ.get('CTA', 'saiba')           # 'saiba' (Saiba mais) ou 'comment' (Comente CORTEZ) — mesmo vídeo, só muda a tela final
OUTDIR = J / ('comp' if CTA_MODE == 'saiba' else 'comp-comment')
data = {'cta': CTA_MODE, 'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'stills': stills, 'pip': pip_spans}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{PIPDUR}}', f'{SPEECH + 1.0:.3f}'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
OUTDIR.mkdir(exist_ok=True)
if OUTDIR != C and not (OUTDIR / 'assets').exists():
    (OUTDIR / 'assets').symlink_to('../comp/assets')          # mesmos materiais, link relativo dentro do trabalho
(OUTDIR / 'index.html').write_text(out)
if CTA_MODE != 'saiba':
    print(json.dumps({'dur': DUR, 'cta': CTA_MODE, 'out': str(OUTDIR / 'index.html')})); raise SystemExit(0)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(l[0] for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': '5 minutos seus. / O Cortez faz o resto. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1',
    'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (sombras VSM, EffectComposer: Render + Bokeh + Output) via hf-seek',
    'identity': 'ID08', 'caption_style': 'L06', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['mesa de papel em plano-sequência com sombras reais e profundidade de campo', 'relógio de papel com fatia azul de 5 min que se ergue',
                 'cópias impressas das entregas tocando como vídeo', 'calendário de mesa com páginas que viram (jeito antigo: 2 dias + correção)',
                 'tela com o time-lapse real do Cortez trabalhando na live + relógio 20–30 min', 'cópia que sai da tela, ajuste V2',
                 'depoimento do Convidado como foto na mesa', 'agenda da semana preenchida com 2–3 vídeos por dia', 'cartão azul-marinho do CTA com botão físico'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
