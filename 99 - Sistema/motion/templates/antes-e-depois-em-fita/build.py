#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js) a partir do EDL, da fita real (analysis/tape.json) e de src/index.tpl.html.
ID03 Azul + legenda L03 (uma palavra por vez, só a fala do Apresentador). Tempos das palavras = palavras da fonte (Whisper da live) levadas
pelo EDL para o relógio do vídeo, com o texto conferido; a retranscrição da voz final fica para o QA.
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, re, sys, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
SH = J.parent / 'material-compartilhado'
EDL = json.loads((J / 'edit/edl.json').read_text())
TAPE = json.loads((J / 'analysis/tape.json').read_text())
YTW = [w for s in json.loads((SH / 'analysis/yt.transcript.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA_MODE = 'comment' if '--cta' in sys.argv and sys.argv[sys.argv.index('--cta') + 1] == 'comment' else 'more'   # 'more' = Saiba mais; 'comment' = Comente CORTEZ
CTA = 4.6
DUR = round(SPEECH + CTA, 3)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


# palavras do Apresentador no relógio do vídeo: cada palavra da fonte dentro do take vai para o pedaço do EDL que contém o seu meio;
# se o Whisper marcou o início dentro de uma pausa cortada (ex.: "Vai" antes de "limpar"), ela encosta no começo do pedaço seguinte
WORDS = []
FPS = EDL['fps']
for tid in dict.fromkeys(s['take'] for s in EDL['segments'] if s['src'] == 'yt'):
    ps = [s for s in EDL['segments'] if s['take'] == tid]
    lo, hi = ps[0]['in'] - 0.45, ps[-1]['in'] + ps[-1]['frames'] / FPS
    tk = next(x for x in EDL['takes'] if x['id'] == tid)
    ws = [w for w in YTW if tk['w0'] - 0.01 <= w['start'] <= tk['w1'] + 0.01]       # palavras do take (âncoras do EDL)
    out = []
    for w in ws:
        mid = (w['start'] + w['end']) / 2
        p = next((q for q in ps if q['in'] - 0.02 <= mid < q['in'] + q['frames'] / FPS), None)
        if p is None:
            p = next((q for q in ps if q['in'] > w['start']), None)
            if p is None:
                continue
            st_, en_ = p['start'], p['start'] + 0.12
        else:
            st_ = p['start'] + max(0, w['start'] - p['in'])
            en_ = min(p['start'] + p['frames'] / FPS, p['start'] + (w['end'] - p['in']))
        out.append({'w': w['word'].strip(), 's': round(st_, 3), 'e': round(max(en_, st_ + 0.08), 3), 'take': tid})
    for i in range(len(out) - 1):          # sem sobreposição dentro do take
        if out[i]['e'] > out[i + 1]['s']:
            out[i]['e'] = out[i + 1]['s']
        if out[i + 1]['s'] < out[i]['s'] + 0.06:
            out[i + 1]['s'] = round(out[i]['s'] + 0.06, 3)
    if out:
        out[0]['w'] = out[0]['w'][:1].upper() + out[0]['w'][1:]          # cada take começa uma frase
    WORDS += out
# texto conferido (o Whisper da live separa/junta pontuação de forma irregular)
WORDS = [w for w in WORDS if norm(w['w'])]


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


seg0 = {s['take']: s for s in EDL['segments'] if s['piece'] == 0}
T = {'errou0': seg0['b01']['start'], 'bruto0': seg0['b02']['start'], 'bruto': W('bruto'), 'breve': W('breve'), 'profissional': W('profissional'),
     'cortez0': seg0['b03']['start'], 'ruido': W('ruído'), 'silencios': W('silêncios'),
     'erros0': seg0['b05']['start'], 'errou2': W('errou', seg0['b05']['start']), 'erros': W('erros', seg0['b05']['start']), 'limpar': W('limpar'),
     'remontar0': seg0['b06']['start'], 'remontar': W('remontar'), 'fluida': W('fluida'), 'pronta': W('pronta'),
     'fecho0': seg0['b04']['start'], 'erros3': W('erros', seg0['b04']['start']), 'apresentador': W('Apresentador'), 'entregar': W('entregar'), 'pronto': W('pronto'),
     'dep0': seg0['d01']['start'], 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['sweepEnd'] = round(T['erros0'] - 0.05, 3)                 # a leitura da fita termina antes de "Se você errou muito"
T['tap'] = round(SPEECH + 2.9, 3)
T['type0'] = round(SPEECH + 1.75, 3)            # variante Comente CORTEZ: digitação de C-O-R-T-E-Z (0,16 s por letra), envio no toque
nerr = sum(1 for b in TAPE['blocks'] if b['k'] == 'err')
f0, f1 = T['errou2'] + 0.12, T['erros'] + 0.08          # o 6º erro aparece antes do "Vai limpar"
T['flags'] = [round(f0 + i * (f1 - f0) / (nerr - 1), 3) for i in range(nerr)]

# gagueira do ANTES (tempos no relógio do vídeo: a01 começa em 0,98 s da gravação)
a = seg0['a01']['in']
STUT = [{'s': round(1.06 - a, 3), 'x': round(1.45 - a, 3), 'e': round(1.80 - a, 3)}, {'s': round(1.84 - a, 3), 'x': round(2.45 - a, 3), 'e': round(T['errou0'] - 0.04, 3)}]

st = TAPE['stats']
fmt = lambda s: f"{int(s // 60)}:{int(round(s % 60)):02d}"
sil_txt = f"{st['silence_s']:.1f} s".replace('.', ',')
HEADS = [
    ('h0', 0, T['bruto0'] - 0.05, 'Gravação bruta', [('ANTES', 0)], True),
    ('h1', T['bruto0'], T['cortez0'] - 0.05, 'Vídeo bruto', [(f'{fmt(st["raw_s"])} de gravação,', T['bruto'] - 0.25), ('<em>com erros e pausas.</em>', T['breve'] - 0.1)], False),
    ('h2', T['cortez0'], T['erros0'] - 0.05, 'Agora, a edição', [('O Cortez:', T['cortez0'] + 0.02), ('tira o ruído,', T['ruido'] - 0.15), ('<em>corta o silêncio.</em>', T['silencios'] - 0.15)], False),
    ('h3', T['erros0'], T['remontar0'] - 0.05, 'O Cortez · erros', [('<span id="nerr" class="num">0 erros</span>', T['errou2'] + 0.05), ('<em>encontrados.</em>', T['erros'] - 0.25)], False),
    ('h4', T['remontar0'], T['fecho0'] - 0.05, 'O Cortez · montagem', [(f'{fmt(st["raw_s"])} gravados →', T['remontar0'] + 0.05), ('<em><span id="ndur" class="num">1:43</span> pronto.</em>', T['remontar'] + 0.2)], False),
    ('h5', T['fecho0'], T['dep0'] - 0.05, 'O que saiu', [(f'{nerr} erros e {sil_txt}', T['fecho0'] + 0.1), ('<em>de pausa, fora.</em>', T['apresentador'] - 0.1)], False),
    ('h6', T['dep0'], SPEECH - 0.05, 'Depois · editado pelo Cortez', [('A mesma frase,', T['dep0'] + 0.1), ('<em>sem travar.</em>', T['dep0'] + 0.5)], False),
]
heads_html, heads_data = [], []
for hid, s0, e0, lab, lines_, big in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd{" big" if big else ""}" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(s0, 3), 'end': round(e0, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, e0 - 0.32 - at)), 3)} for tx, at in lines_]})

# legenda L03: uma palavra por vez (palavra ativa entra e sai no próprio tempo; buracos curtos fechados até a próxima)
KEYW = {'ruido', 'silencios', 'errou', 'erros', 'limpar', 'remontar', 'fluida', 'pronta', 'musica', 'cenas', 'animacoes', 'momentos'}
caps, caps_html = [], []
# unidades: uma palavra por vez; palavra curta de função falada em < 0,13 s ("Se", "os", "ele") vai junto com a seguinte,
# senão pisca por 2 quadros e não dá para ler
units, i = [], 0
while i < len(WORDS):
    w = WORDS[i]
    if i + 1 < len(WORDS) and w['e'] - w['s'] < 0.13 and len(norm(w['w'])) <= 4 and WORDS[i + 1]['s'] - w['e'] < 0.1 and WORDS[i + 1]['take'] == w['take']:
        units.append({'w': w['w'] + ' ' + WORDS[i + 1]['w'], 's': w['s'], 'e': WORDS[i + 1]['e']}); i += 2
    else:
        units.append(dict(w)); i += 1
for i, w in enumerate(units):
    nxt = units[i + 1]['s'] if i + 1 < len(units) else 1e9
    e = nxt if nxt - w['e'] < 0.25 else w['e'] + 0.12
    e = min(e, nxt, SPEECH)
    txt = ' '.join(re.sub(r'[,.;:]+$', '', x) for x in w['w'].split())     # L03: sem vírgula/ponto pendurado
    caps.append({'s': w['s'], 'e': round(e, 3), 'text': txt})
    key = any(norm(x) in KEYW for x in txt.split())
    caps_html.append(f'<div class="cw{" k" if key else ""}" id="cw{i}">{html.escape(txt)}</div>')

# etiquetas dos erros (as duas tentativas de "É assim" viram uma etiqueta só)
blocks = TAPE['blocks']
errs = [i for i, b in enumerate(blocks) if b['k'] == 'err']
chips, chips_html = [], []
groups = [[errs[0], errs[1]]] + [[i] for i in errs[2:]]
for j, gidx in enumerate(groups):
    b = blocks[gidx[0]]
    why = 'começo repetido · 2×' if len(gidx) == 2 else b['why']
    txt = ' '.join(blocks[i]['txt'] for i in gidx)
    side = 1 if j % 2 == 0 else -1
    chips.append({'block': gidx[0] if len(gidx) == 1 else gidx[1], 'order': errs.index(gidx[0]), 'side': side, 'dy': 0, 'why': why, 'text': txt})
    chips_html.append(f'<div class="lead" id="lead{j}"></div><div class="chip" id="chip{j}"><b><i>✕</i>{html.escape(why)}</b><span>{html.escape(txt)}</span></div>')
# o chip do "É assim" fica preso ao segundo bloco; a ordem do sinal é a do primeiro erro
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'cta': CTA_MODE, 'T': T, 'heads': heads_data, 'caps': caps, 'stut': STUT, 'chips': chips, 'seq': seq, 'tape': TAPE}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{CHIPS}}', '\n  '.join(chips_html)).replace('{{NERR}}', str(nerr)).replace('{{NSIL}}', sil_txt).replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH + 1.0:.3f}'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Grave do seu jeito. / O Cortez deixa pronto. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (sombras PCF suaves, EffectComposer: UnrealBloom leve + Bokeh só na abertura e no fechamento + Output) via hf-seek',
    'identity': 'ID03', 'caption_style': 'L03', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; fita gerada de dados reais (ilhas de fala do job EXEMPLO_2)',
    'three_js': ['tela 9:16 com a gravação bruta (ANTES) que deita na mesa e vira a fita; no fim a fita fica de pé e gira como a tela do DEPOIS (entrega EXEMPLO_2)', 'fita 3D da gravação inteira (103 s): blocos reais de fala, silêncio, hesitação e erro, com miniatura, texto e forma de onda real',
                 'linha de leitura que troca a onda bruta (cinza, com ruído) pela limpa (azul)', 'erros marcados, riscados e retirados para a direita; silêncios retirados para a esquerda',
                 'remontagem: os blocos mantidos se juntam (1:43 → 1:03); erros e pausas empilhados dos lados ("o que saiu")', 'leque desfocado com cenas da mesma entrega no fechamento'],
    'T': T, 'tape_stats': st, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'words': len(caps), 'T': {k: v for k, v in T.items() if k != 'flags'}}, ensure_ascii=False))
print(' '.join(c['text'] for c in caps))
