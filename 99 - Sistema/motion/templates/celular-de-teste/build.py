#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA do Cortez (palavras alinhadas pelo
ElevenLabs, conferidas por transcrição) e de src/index.tpl.html. F10 · ID08 Azul e Papel · legenda L05 (caixa na palavra).
CTA=saiba (padrão, comp/) ou CTA=comment (comp-cta-comment/). Grava analysis/scene_plan.json, motion_plan.json e caption_groups.json
(só na versão padrão). Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cta_variant import mode, layout, snippets

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
NW = json.loads((J / 'analysis/narration_words.json').read_text())
W = NW['words']
SPEECH = NW['speech']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
q = lambda x: round(round(x * 30) / 30, 4)
s_ = lambda i: W[i]['s']
e_ = lambda i: W[i]['e']
assert [w['w'] for w in W][:4] == ['Faz', 'um', 'teste', 'comigo.'] and W[21]['w'] == 'manda.' and W[39]['w'] == 'Cortez.', [w['w'] for w in W]

T = {'pega': s_(4), 'parado': s_(9), 'celular': s_(12), 'porque': s_(13), 'editar': s_(19), 'me': s_(20), 'manda': s_(21), 'em': s_(22),
     'vinte': s_(23), 'trinta': s_(24), 'minutosE': e_(25), 'ele': s_(26), 'volta': s_(27), 'pronto': s_(28), 'limpo': s_(29),
     'cortado': s_(30), 'legendado': s_(31), 'cena': s_(33), 'musica': s_(35), 'eu': s_(36), 'cortez': s_(39), 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


# ---------- legenda L05 (caixa azul que passa de palavra em palavra; blocos de até 4 palavras) ----------
WEAK = {'que', 'e', 'com', 'de', 'a', 'o', 'da', 'do', 'em', 'no', 'na', 'um', 'uma', 'eu', 'me', 'seu'}
units, g = [], []
for w in W:
    if g:
        prev = g[-1]
        hard = w['s'] - prev['e'] > 0.30 or prev['w'][-1] in '.?!,:' or norm(w['w']) == 'porque'
        full = len(g) >= 4 or len(' '.join(x['w'] for x in g + [w])) > 24
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
    if groups and len(u) == 1 and len(u[0]['w']) <= 6 and len(groups[-1]) < 4 and len(' '.join(x['w'] for x in groups[-1] + u)) <= 22 \
            and u[0]['s'] - groups[-1][-1]['e'] < 0.3 and groups[-1][-1]['w'][-1] not in '.?!:':
        groups[-1] = groups[-1] + u
    else:
        groups.append(u)
for i in range(1, len(groups)):
    if len(groups[i]) == 1 and len(groups[i - 1]) >= 3 and groups[i - 1][-1]['w'][-1] not in '.?!,:' and groups[i][0]['s'] - groups[i - 1][-1]['e'] < 0.3:
        groups[i] = [groups[i - 1].pop()] + groups[i]
# o título grande do gancho já diz "Faz um teste comigo." — sem legenda duplicada nesse trecho
groups = [gw for gw in groups if not gw[-1]['e'] <= T['pega'] - 0.01]
EMPH = {'teste', 'parado', 'celular', 'editar', 'manda', 'vinte', 'trinta', 'minutos', 'pronto', 'limpo', 'cortado', 'legendado', 'cena', 'musica', 'cortez'}
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s'] - 0.04
    e = groups[i + 1][0]['s'] - 0.04 if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.5 else gw[-1]['e'] + 0.25
    e = min(e, SPEECH - 0.05)
    spans = ' '.join(f'<span class="cw{" em" if norm(x["w"]) in EMPH else ""}" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, x in enumerate(gw))
    caps_html.append(f'<div class="cap" id="cg{i}">{spans}</div>')
    caps_data.append({'s': q(s), 'e': q(e), 'w': [{'s': q(x['s'] - 0.03), 'e': q(min(x['e'] + 0.04, gw[k + 1]['s'] - 0.03) if k + 1 < len(gw) else e)} for k, x in enumerate(gw)],
                      'text': ' '.join(x['w'] for x in gw)})

# ---------- capítulos (topo) ----------
CHIPS = [('c1', T['manda'] + 0.1, T['em'] - 0.05, 'Enviado', 'para o Cortez'),
         ('c2', T['em'] - 0.05, T['ele'] - 0.05, 'Tempo de máquina', '20 a 30 min'), ('c3', T['ele'] - 0.05, T['eu'] - 0.05, 'Voltou pronto', 'editado pelo Cortez'),
         ('c4', T['eu'] - 0.05, T['cta0'] - 0.05, 'Cortez', 'IA que edita vídeo')]
chips_html = '\n  '.join(f'<div class="chip" id="{c}"><i></i><span>{a}</span><b>{b}</b></div>' for c, s, e, a, b in CHIPS)
chips_data = [{'id': c, 's': q(s), 'e': q(e)} for c, s, e, a, b in CHIPS]

# ---------- trilha: Lyria 1 do tutorial da Cami (reuso sem custo) ----------
# O EXEMPLO_2 usou 37,5–58,2 / 105,8–119,2 / 169,2–173,6 s e o EXEMPLO_3 ≈147–170 s. Aqui: trecho ≈69–88 s — parte cheia no gancho, respiro em ≈76–78 s
# sob "em vinte, trinta minutos" e a retomada (subida mais forte entre 76,5 e 80 s) cai no "ele volta pronto".
r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '76.5', '-t', '3.5', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
en = np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1))
es = np.convolve(en, np.ones(4) / 4, mode='same')
onset = 76.5 + (int(np.argmax(es[5:] - es[:-5])) + 2) * 0.01
MOFF = round(onset - T['volta'], 3)

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
roll = sorted(p.name for p in (C / 'assets/roll').glob('*.jpg'))
M = mode()
top = layout(M)
data = {'T': T, 'caps': caps_data, 'chips': chips_data, 'seq': seq, 'roll': roll, 'cta': M}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{CHIPS}}', chips_html)
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{BTN_TOP}}', str(top)))
for k, v in snippets(M, top).items():
    out = out.replace('{{' + k + '}}', v)
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if M != 'saiba' or os.environ.get('COMP_OUT'):
    O = Path(os.environ.get('COMP_OUT') or (J / f'comp-cta-{M}'))
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir():
            d.mkdir(parents=True, exist_ok=True)
        elif not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True); os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': M, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [
    {'id': 'hook', 'start': 0, 'end': T['pega'], 'what': '"Faz um teste comigo." — celular 3D (alumínio e vidro) sobe girando, galeria de vídeos na tela; título grande'},
    {'id': 'parado', 'start': T['pega'], 'end': T['me'], 'what': 'a câmera entra na galeria; o vídeo parado (gravação bruta real, 1:43) acende com contorno azul e o selo "sem editar"; os outros escurecem'},
    {'id': 'manda', 'start': T['me'], 'end': T['em'], 'what': '"Me manda." — o vídeo sai da tela como cartão 3D, gira e voa para a pasta de papel "01 · Enviar vídeos" do Cortez'},
    {'id': 'tempo', 'start': T['em'], 'end': T['ele'], 'what': 'anel de progresso 3D em volta da pasta enche: 20 min → 30 min'},
    {'id': 'volta', 'start': T['ele'], 'end': T['limpo'], 'what': '"ele volta pronto" — o vídeo editado (EXEMPLO_4) sobe da pasta e volta para o celular, encaixando na tela'},
    {'id': 'chips', 'start': T['limpo'], 'end': T['eu'], 'what': 'o celular toca o EXEMPLO_4; etiquetas de papel entram nas palavras: limpo · cortado · legendado · com cena · com música'},
    {'id': 'cortez', 'start': T['eu'], 'end': T['cta0'], 'what': '"Eu sou o Cortez." — recuo da câmera, celular de frente'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': '"Manda o vídeo parado. Ele volta pronto." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + UnrealBloom + Output) via hf-seek',
    'identity': 'ID08', 'caption_style': 'L05', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; sem aleatoriedade',
    'concept': 'o desafio tátil: o vídeo parado no celular sai da galeria, vai para a pasta do Cortez e volta pronto em 20–30 min',
    'T': T, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'offset': MOFF, 'onset_track_s': round(onset, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'music_offset': MOFF, 'onset': round(onset, 2)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
