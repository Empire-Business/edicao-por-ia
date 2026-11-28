#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
F22 Corte de Live 3D + ID05 Roxo + legenda L04 (palavra ativa: o bloco fica, a palavra falada muda de cor).
Estilo novo: "o painel em relevo" — a interface REAL do painel de modelos vira objetos físicos: tecla 3D "Copiar pedido", folha do pedido
que sai da tecla, cartões de modelo que se levantam da página como livro pop-up, carimbos "testado/editado", botões de ID em leque com a
prévia real trocando de cor, aviso "Copiado." e o vídeo que saiu exatamente desse pedido (EXEMPLO_2, F16 + ID07, editado na própria live).
Tempos = palavras realmente faladas na voz final. Texto da legenda = palavras conferidas na fonte ("Cortex" → Cortez; "para" → "pra"
como ele fala; "é ver aqui, usar" — o Whisper da voz final juntou "ver aqui" dentro de "usar"; tempos tirados da fonte pelo EDL).
Variante de CTA: CTA=comment → "Comente CORTEZ" (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md); padrão = "Saiba mais".
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
CTA_MODE = os.environ.get('CTA', 'saiba')
assert CTA_MODE in ('saiba', 'comment'), CTA_MODE


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


# "é ver aqui, usar esse modelo": a voz final tem as três palavras; o Whisper colou "ver aqui" em "usar". Tempos da fonte via EDL.
seg5 = next(s for s in EDL['segments'] if s['take'] == 't05')
src2out = lambda x: round(x - seg5['in'] + seg5['start'], 3)
iu = next(i for i, w in enumerate(WORDS) if norm(w['w']) == 'usar')
if norm(WORDS[iu - 1]['w']) == 'e' and not any(norm(w['w']) == 'ver' for w in WORDS[iu - 3:iu]):
    eu = WORDS[iu]['e']
    WORDS[iu:iu + 1] = [{'w': 'ver', 's': src2out(469.72), 'e': src2out(469.80)}, {'w': 'aqui,', 's': src2out(469.80), 'e': src2out(470.00)},
                        {'w': 'usar', 's': src2out(470.08), 'e': eu}]
FIX = {'Cortex,': 'Cortez,', 'Cortex.': 'Cortez.', 'para': 'pra', 'Então': 'Então,', 'modelo,': 'modelo.', 'Esses': 'Esses', 'formatos': 'formatos'}
for w in WORDS:
    w['w'] = FIX.get(w['w'], w['w'])
WORDS[[i for i, w in enumerate(WORDS) if norm(w['w']) == 'formatos'][1]]['w'] = 'formatos,'
for i, w in enumerate(WORDS):
    if norm(w['w']) == 'voce' and i > 0 and norm(WORDS[i - 1]['w']) == 'modelo':
        w['w'] = 'Você'


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


TS = {}
for s in EDL['segments']:
    TS.setdefault(s['take'], s['start'])
T = {'clique': W('clique'), 'cortez1': W('Cortez'), 'copiar1': W('copiar'), 'colar1': W('colar'), 'voce1': W('você'),
     'copiar2': W('copiar', W('consegue')), 'estilo': W('estilo'), 'edicao1': W('edição'), 'nessa': W('nessa'), 'qual1': W('qualidade'),
     'aqui1': W('aqui'), 't02': TS['t02'], 'formatos1': W('formatos'), 't03': TS['t03'], 'testamos': W('testamos'), 'editamos': W('editamos'),
     't04': TS['t04'], 'varios': W('vários'), 'videos': W('vídeos'), 'editados': W('editados'), 'alta': W('alta'),
     'diferentes': W('diferentes'), 'objetivo': W('objetivo'), 't05': TS['t05'], 'ver': W('ver', TS['t05']), 'usar': W('usar'),
     'modelo': W('modelo'), 'escolhe': W('escolhe'), 'id': W('ID'), 'visual': W('visual'), 't06': TS['t06'], 'pedido': W('pedido'),
     'colar2': W('colar', TS['t06']), 'cortez2': W('Cortez', TS['t06']), 'tudo': W('Tudo', TS['t06']), 'prontinho': W('prontinho'),
     'editar': W('editar'), 'formato': W('formato', TS['t06']), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['press1'] = round(T['clique'] + 0.12, 3)             # a tecla afunda no "clique"
T['press2'] = round(T['colar2'] + 0.10, 3)             # no painel: "Copiar pedido de edição" no "colar"
T['toast'] = round(T['press2'] + 0.18, 3)
T['tap'] = round(SPEECH + 2.9, 3)
T['type0'] = round(SPEECH + 1.75, 3)
T = {k: round(v, 3) for k, v in T.items()}

HEADS = [
    ('h1', 0, T['t02'] - 0.05, 'Modelos do Cortez', [('Um clique.', 0), ('<em>O mesmo estilo.</em>', T['estilo'] - 0.18)]),
    ('h4', T['t05'] + 0.05, T['t06'] - 0.05, 'No painel do Cortez', [('Use o modelo.', T['t05'] + 0.12), ('<em>Escolha a ID.</em>', T['escolhe'] - 0.12)]),
    ('h5', T['t06'] + 0.05, SPEECH + 0.02, 'No painel do Cortez', [('Pedido pronto.', T['pedido'] - 0.15), ('<em>É só colar.</em>', T['colar2'] - 0.15)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legenda L04 (palavra ativa): blocos de até 4 palavras pelo sentido
SIZES = [3, 2, 3, 3, 3, 4, 3, 4, 2, 2, 3, 1, 3, 3, 3, 4, 3, 2, 4, 3, 3, 2, 2, 3, 4, 4, 4, 2, 3, 3, 2]
assert sum(SIZES) == len(WORDS), (sum(SIZES), len(WORDS), [w['w'] for w in WORDS])
groups, k0 = [], 0
for n in SIZES:
    groups.append(WORDS[k0:k0 + n]); k0 += n
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s']
    nxt = groups[i + 1][0]['s'] if i + 1 < len(groups) else None
    e = nxt if nxt is not None and nxt - gw[-1]['e'] < 0.6 else gw[-1]['e'] + 0.3
    e = min(e, SPEECH)
    parts = [f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, x in enumerate(gw)]
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl">{" ".join(parts)}</span></div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'w': [{'s': x['s'], 'e': x['e']} for x in gw], 'text': ' '.join(x['w'] for x in gw)})

seq = {}
for d in sorted((C / 'assets/seq').iterdir()):
    if d.is_dir():
        seq[d.name] = {'n': len(list(d.glob('*.jpg'))), 'fps': 15 if d.name.startswith('c_') else 30}
PEDIDO = (J / 'tmp/gal/pedido.txt').read_text().strip()
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'cta': CTA_MODE, 'pedido': PEDIDO}
out = (J / 'src/index.tpl.html').read_text()
out = (out.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH:.3f}').replace('{{CTAMODE}}', CTA_MODE))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

SUF = '-comment' if CTA_MODE == 'comment' else ''
scenes = [
    {'id': 'hook', 'start': 0, 'end': T['t02'], 'label': 'Gancho: tecla 3D "Copiar pedido" afunda no "clique"; a folha do pedido real sai da tecla e entra na tela; '
     '"só a gravação" vira o vídeo editado pelo Cortez numa varredura no "estilo"; "nessa qualidade aqui" aproxima o resultado (EXEMPLO_2)'},
    {'id': 'formatos', 'start': T['t02'], 'end': T['t04'], 'label': 'A página real "Escolha como editar seu vídeo." e seis cartões de modelo levantam como livro pop-up '
     '(F07, F08, F10, F16, F18, F22 — cada um com uma entrega do próprio usuário naquele formato); carimbos "Testado" e "Editado"'},
    {'id': 'objetivos', 'start': T['t04'], 'end': T['t05'], 'label': 'Câmera passeia pelos cartões; etiquetas de objetivo surgem em cada um'},
    {'id': 'modelo_id', 'start': T['t05'], 'end': T['t06'], 'label': 'Os outros cartões deitam; o F16 vem à frente e "Usar este modelo" é tocado; '
     'botões reais das IDs em leque e a prévia real "Clareza em cada cena" trocando de cor até a Laranja (ID07)'},
    {'id': 'pedido', 'start': T['t06'], 'end': SPEECH, 'label': 'A folha do pedido real (F16 + ID07) sobe; toque em "Copiar pedido de edição" e o aviso real "Copiado."; '
     'a folha vira e mostra o vídeo que saiu desse pedido (EXEMPLO_2)'},
    {'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)',
     'title': 'Escolha o modelo. / O Cortez edita. / ' + ('Comente CORTEZ' if CTA_MODE == 'comment' else 'Saiba mais')}]
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V1', 'cta': CTA_MODE,
    'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: RenderPass, UnrealBloomPass suave, BokehPass, OutputPass; sombras reais)',
    'identity': 'ID05', 'caption_style': 'L04', 'format': 'F22 f22-corte-de-live-3d-v1',
    'determinism': 'tudo em função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
print(json.dumps(T))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
