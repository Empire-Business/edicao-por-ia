#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
ID06 Azul Claro + legenda L07 (ênfase pontual) + three.js r186: diorama isométrico (câmera ortográfica), sombras VSM, GTAO, tilt-shift.
Tempos = palavras realmente faladas na voz final (segundos do master limpo). O texto das legendas usa as palavras conferidas na fonte
("Cloud" → Claude; "mata" → máquina — o Whisper ouve errado o fim cortado). Grava analysis/scene_plan.json, motion_plan.json e caption_groups.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
FIX = {'Cloud': 'Claude', 'mata.': 'máquina.', 'Mílias,': 'Milhas,'}
for w in WORDS:
    w['w'] = FIX.get(w['w'], w['w'])
SPEECH = EDL['duration']
CTA = 4.6
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


TS = {}
for s in EDL['segments']:
    TS.setdefault(s['take'], s['start'])
T = {'tech': W('técnico'), 'nada': W('nada', 2.3), 'pdf0': TS['t02'], 'pdfw': W('PDF'), 'cl0': TS['t03'], 'send': W('Claude'), 'inst': W('instalar'),
     'soz': W('sozinho'), 'simp': W('Simples'), 'pas0': TS['t04'], 'apar': W('aparecer'), 'maq': W('máquina'), 'jo0': TS['t05'], 'convidado': W('Convidado'),
     'comprou': W('comprou'), 'ele': W('Ele', TS['t05'] + 3), 'tec': W('tecnológica'), 'editar': W('editar'), 'result': W('resultados'),
     'fala0': TS['t06'], 'tranq': W('tranquilo'), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['raw0'] = round(W('e', T['tec'] + 0.3) - 0.05, 3)
T['raw1'] = round(T['editar'] + 0.06, 3)
T['hero0'] = round(T['raw1'] + 0.12, 3)
T['tap'] = round(SPEECH + 2.9, 3)
CTA_MODE = os.environ.get('CTA', 'saiba')          # 'saiba' (Saiba mais) ou 'comment' (Comente CORTEZ) — mesma peça, só a tela final muda
assert CTA_MODE in ('saiba', 'comment'), CTA_MODE
T['type0'] = round(SPEECH + 1.75, 3)               # CORTEZ digitado no campo de comentário (variante comment)
T['ask0'] = round(T['ele'] + 0.25, 3)          # digitando o pedido em linguagem comum
T['askSend'] = round(T['ele'] + 1.65, 3)
T['askReply'] = round(T['ele'] + 2.0, 3)

HEADS = [
    ('h1', 0, T['pdf0'] - 0.02, 'Instalação do Cortez', [('Você não precisa', 0), ('<em>saber programar.</em>', T['tech'] - 0.1)]),
    ('h2', T['pdf0'] + 0.06, T['cl0'], 'Passo 1', [('Baixe o', T['pdf0'] + 0.16), ('<em>PDF.</em>', T['pdfw'] - 0.15)]),
    ('h3', T['cl0'] + 0.06, T['pas0'], 'Passo 2', [('O Claude instala', T['send'] - 0.25), ('<em>sozinho.</em>', T['soz'] - 0.15)]),
    ('h4', T['pas0'] + 0.06, T['jo0'], 'Passo 3', [('O Cortez aparece', T['pas0'] + 0.2), ('<em>na sua máquina.</em>', T['maq'] - 0.25)]),
    ('h5', T['jo0'] + 0.06, T['ele'] - 0.05, 'Cliente do Cortez', [('O Convidado comprou', T['convidado'] - 0.05), ('<em>o Cortez.</em>', T['comprou'] - 0.1)]),
    ('h6', T['ele'] + 0.02, T['fala0'], 'Cliente do Cortez', [('Não é técnico…', T['ele'] + 0.12), ('<em>e já edita.</em>', T['editar'] - 0.15)]),
    ('h7', T['fala0'] + 0.06, SPEECH + 0.05, 'Nas palavras dele', [('“Não é difícil.', T['fala0'] + 0.16), ('<em>Bem tranquilo.”</em>', T['tranq'] - 0.12)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legenda L07: frases de até 4 palavras, agrupadas à mão pelo sentido e pelo ritmo da fala (nenhum grupo atravessa troca de quem fala);
# ênfase = no máximo uma palavra por frase, escolhida editorialmente (não toda frase tem destaque)
SIZES = [4, 3, 2, 2, 3, 2, 4, 4, 2, 3, 3, 4, 3, 2, 4, 2, 3, 3, 2, 3, 4, 3, 2, 2, 3, 2, 3, 2, 4, 3, 4]
assert sum(SIZES) == len(WORDS), (sum(SIZES), len(WORDS), [w['w'] for w in WORDS])
groups, k0 = [], 0
for n in SIZES:
    groups.append(WORDS[k0:k0 + n]); k0 += n
EMPH_G = {1: 'técnico', 5: 'PDF', 9: 'Claude', 12: 'sozinho.', 16: 'máquina.', 17: 'Convidado', 23: 'tecnológica', 25: 'editar', 27: 'bons.', 30: 'tranquilo'}
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s']
    e = groups[i + 1][0]['s'] if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.5 else gw[-1]['e'] + 0.25
    e = min(e, SPEECH)
    kidx = next((j for j, x in enumerate(gw) if x['w'] == EMPH_G[i]), None) if i in EMPH_G else None
    if i in EMPH_G and kidx is None:
        raise SystemExit(f'ênfase {EMPH_G[i]!r} não está no grupo {i}: {[x["w"] for x in gw]}')
    parts = [f'<span class="cw{" k" if j == kidx else ""}" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, x in enumerate(gw)]
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl">{" ".join(parts)}</span></div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'w': [{'s': x['s'], 'k': j == kidx} for j, x in enumerate(gw)],
                      'text': ' '.join(x['w'] for x in gw), 'emphasis': gw[kidx]['w'] if kidx is not None else None})

SCREEN = (0, 177, -212)
# [t, foco x, y, z (cena), zoom, y do foco na tela, azimute extra em graus] — planos mais fechados e baixos, com dolly/órbita entre os momentos
CAMK = [
    [0, 0, 430, -20, 1.08, 1000, 9], [T['nada'] + 0.2, 0, 430, -20, 1.2, 1000, -3],
    [T['nada'] + 0.85, 0, 260, 0, 1.85, 990, -9], [T['cl0'], 0, 260, 0, 2.08, 990, 5],
    [T['cl0'] + 0.95, *SCREEN, 2.4, 975, 0], [T['simp'] + 0.35, *SCREEN, 2.5, 975, 2],
    [T['pas0'] + 0.6, 0, 300, -60, 1.05, 1010, 8], [T['jo0'] - 0.1, 0, 300, -60, 1.1, 1010, -2],
    [T['convidado'] + 0.7, -150, 230, 40, 1.42, 1010, -9], [T['ele'] - 0.1, -150, 230, 40, 1.5, 1010, -3],
    [T['ele'] + 0.6, *SCREEN, 2.2, 980, 0], [T['raw0'] - 0.6, *SCREEN, 2.26, 980, 2],
    [T['raw0'] + 0.3, -20, 300, 0, 1.07, 1030, 7], [T['hero0'] + 0.5, 40, 290, 30, 1.13, 1030, 3], [T['fala0'] - 0.08, 282, 250, 128, 1.95, 1000, -7],
    [T['fala0'] + 0.6, -282, 150, 128, 2.3, 880, 6], [SPEECH, -282, 150, 128, 2.42, 880, 10],
    [T['cta0'] + 0.85, 0, 250, 40, 1.12, 1010, -5], [DUR, 0, 250, 40, 1.16, 1010, 4]]
CAMK = [[round(x, 3) for x in k] for k in CAMK]
LOOK = {'EXPOSURE': 1.05, 'ENVI': 0.3, 'HEMI': 0.5, 'KEY': 2.3, 'FILL': 0.3, 'AOI': 1.25, 'TILT': 1.8, 'ORBIT': 3.0}
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
pip_frames = json.loads((J / 'analysis/proof_assets.json').read_text())['apresentador_pip_frames']
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'cta': CTA_MODE}
out = (J / 'src/index.tpl.html').read_text()
out = (out.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{PIPDUR}}', f'{pip_frames / 30:.3f}').replace('{{CAMK}}', json.dumps(CAMK)).replace('{{CTAMODE}}', CTA_MODE))
for k, v in LOOK.items():
    out = out.replace('{{' + k + '}}', str(v))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Edição profissional, sem ser técnico. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: GTAO + tilt-shift + Output) via hf-seek',
    'identity': 'ID06', 'caption_style': 'L07', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; telas desenhadas a partir do tempo; PRNG de semente fixa',
    'three_js': ['diorama isométrico em câmera ortográfica (mesa, notebook, pastas) com sombras VSM e oclusão GTAO',
                 'janelas de terminal flutuando que implodem no PDF ("nada disso")', 'PDF voa para dentro do notebook; tela com a instalação acontecendo sozinha',
                 'pastas do Cortez saem da tela e formam um arco', 'cartão do Convidado (foto → vídeo da live quando ele fala)',
                 'antes → depois: gravação bruta entra na pasta 01, vídeo editado pelo Cortez sai da pasta 02', 'cartão final com três vídeos editados pelo Cortez'],
    'T': T, 'camera_keys': CAMK, 'look': LOOK, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
print(json.dumps(T))
for c in caps_data:
    print(c['s'], c['e'], c['text'], '|', c['emphasis'])
