#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA, das palavras alinhadas
(ElevenLabs, conferidas por transcrição) e de src/index.tpl.html. F10 · ID03 Azul · legenda L07 (Ênfase pontual: grupos de até 4
palavras; uma palavra escolhida pelo sentido ganha tamanho e cor com movimento breve). CTA=saiba (padrão, comp/) ou CTA=comment.
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json (só na versão padrão).
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, subprocess, sys
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

T = {'assisto': s_(5) - 0.05, 'scan0': s_(6) - 0.05, 'scan1': s_(8) + 0.05, 'peaks0': s_(8) + 0.05, 'peaks1': s_(11) + 0.25, 'rise': s_(13),
     'hero': s_(20), 'legenda': s_(23), 'cena': s_(24), 'musica': s_(26), 'cliente': s_(27), 'youtube': s_(35), 'dez': s_(39), 'insta': s_(42),
     'cortez': s_(43), 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR
COUNTER = [q(T['cliente'] + 0.4 + k * (T['dez'] - T['cliente'] - 0.4) / 9) for k in range(10)]

# grupos L07 (índices de palavras) e a palavra de ênfase (-1 = sem ênfase); o gancho (0–4) vai como título grande
GROUPS = [((5, 7), 7), ((8, 11), 10), ((12, 14), 13), ((15, 16), 16), ((17, 19), 17), ((20, 23), 23), ((24, 24), 24), ((25, 26), 26),
          ((27, 30), 28), ((31, 33), -1), ((34, 35), 35), ((36, 38), -1), ((39, 40), 39), ((41, 42), 42), ((43, 46), 46)]
caps_html, caps_data = [], []
for gi, ((a, b), k) in enumerate(GROUPS):
    ws = W[a:b + 1]
    s = ws[0]['s'] - 0.05
    nxt = W[GROUPS[gi + 1][0][0]]['s'] - 0.05 if gi + 1 < len(GROUPS) else None
    e = nxt if nxt is not None and nxt - ws[-1]['e'] < 0.6 else ws[-1]['e'] + 0.3
    e = min(e, SPEECH - 0.05)
    spans = ' '.join(f'<span class="{"k" if (a + j) == k else "w"}">{html.escape(w["w"])}</span>' for j, w in enumerate(ws))
    caps_html.append(f'<div class="cap" id="cg{gi}" style="top:1448px">{spans}</div>')
    caps_data.append({'s': q(s), 'e': q(e), 'k': k, 'kt': q(W[k]['s'] - 0.02) if k >= 0 else 0, 'text': ' '.join(w['w'] for w in ws),
                      'key': W[k]['w'] if k >= 0 else None})

CHIPS = [('c1', T['assisto'], T['peaks0'], 'Assistindo inteiro · <span id="tcode">00:00</span>'),
         ('c2', T['peaks0'], T['rise'], '<b>10</b> trechos escolhidos'),
         ('c3', T['rise'], T['hero'], 'Cortes prontos <b>pra postar</b>'),
         ('c5', T['cliente'], T['cortez'], 'Um cliente · <b>1 vídeo do YouTube</b>'),
         ('c6', T['cortez'], T['cta0'], 'Cortez · <b>IA que edita vídeo</b>')]
chips_html = '\n  '.join(f'<div class="chip" id="{c}"><i></i><span>{t}</span></div>' for c, a, b, t in CHIPS)
chips_data = [{'id': c, 's': a, 'e': b} for c, a, b, t in CHIPS]

# trilha: a volta da faixa depois da pausa (≈38 s da Namoral 02) cai no "Um cliente…"
r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '36.5', '-t', '3.0', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
e = np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1))
es = np.convolve(e, np.ones(4) / 4, mode='same')
jump = es[5:] - es[:-5]
onset = 36.5 + (int(np.argmax(jump)) + 2) * 0.01
MOFF = round(onset - T['cliente'], 3)

ENVD = json.loads((J / '<PREENCHER: fonte ou prova própria>').read_text())
EXEMPLO_2 = json.loads((J / 'analysis/e117_env.json').read_text())
seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
M = mode()
_, top = layout(M)
data = {'T': T, 'caps': caps_data, 'chips': chips_data, 'seq': seq, 'counter': COUNTER, 'cta': M,
        'env': {'smooth': ENVD['smooth'], 'raw': ENVD['raw'], 'peaks': ENVD['peaks']}, 'e117': EXEMPLO_2}
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
    {'id': 'hook', 'start': 0, 'end': T['assisto'], 'what': '<PREENCHER: fonte ou prova própria>'},
    {'id': 'leitura', 'start': T['assisto'], 'end': T['peaks0'], 'what': '<PREENCHER: fonte ou prova própria>'},
    {'id': 'trechos', 'start': T['peaks0'], 'end': T['rise'], 'what': '"encontro os melhores trechos" — 10 picos acendem em sequência com etiquetas 01–10'},
    {'id': 'cortes', 'start': T['rise'], 'end': T['hero'], 'what': 'cada pico se levanta como um cartão 9:16 tocando um corte editado pelo Cortez (exemplos)'},
    {'id': 'camadas', 'start': T['hero'], 'end': T['cliente'], 'what': 'o primeiro cartão vem para a câmera: imagem de câmera do EXEMPLO_2 → ganha a legenda real → a cena do escritório → a faixa de música (envelope real)'},
    {'id': 'cliente', 'start': T['cliente'], 'end': T['cortez'], 'what': 'os cortes formam uma grade 3×3 (exemplos) e o Reel real do Convidado vem para a frente, rotulado "Reel do Convidado · @perfil-do-convidado"; contador até 10 no "dez cortes"'},
    {'id': 'cortez', 'start': T['cortez'], 'end': T['cta0'], 'what': '"Eu sou o Cortez." — a câmera recua e mostra a cordilheira inteira com os 10 cortes pairando sobre os picos'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': '"Um vídeo longo. Vários cortes prontos." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + UnrealBloom + Output) via hf-seek',
    'identity': 'ID03', 'caption_style': 'L07', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; telas internas desenhadas em canvas a cada quadro; PRNG fixo',
    'concept': 'o vídeo longo vira um mapa topográfico da sua energia; a leitura varre, os picos acendem e cada pico se levanta como um corte',
    'T': T, 'counter': COUNTER, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'offset': MOFF, 'onset_track_s': round(onset, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'music_offset': MOFF, 'onset': onset}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'], '|', c['key'])
