#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA do Cortez, das palavras alinhadas
(ElevenLabs, conferidas por transcrição) e de src/index.tpl.html. F10 · ID01 Verde · legenda L08 (blocos estáveis, contorno reforçado).
CTA=saiba (padrão, comp/) ou CTA=comment (comp-cta-comment/). Grava analysis/scene_plan.json, motion_plan.json e caption_groups.json
(só na versão padrão). Run: ../../../.venv/bin/python src/build.py
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
e_ = lambda i: W[i]['e']
assert [w['w'] for w in W][:5] == ['Mandar', 'pro', 'editor:', 'dois', 'dias.'] and W[51]['w'] == 'comigo.', [w['w'] for w in W]

T = {'land1': s_(3), 'fall2': s_(7) - 0.05, 'land2': s_(8), 'cortez': s_(12), 'scanEnd': s_(14) + 0.35, 'comp0': s_(15), 'comp1': s_(18),
     'grava': s_(20), 'run0': s_(23), 'run1': e_(25), 'pronto': s_(29), 'nao': s_(30), 'ajusto': s_(39), 'voce': s_(40), 'cinco': s_(43),
     'resto': s_(49), 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR

# legenda L08: blocos estáveis de até 5 palavras; palavras-chave em verde
KEY = {'dois', 'dias.', 'mais', 'um.', 'cortez,', 'vinte,', 'trinta', 'minutos', 'pronto.', 'ajusto.', 'cinco', 'comigo.'}
BLOCKS = [(0, 2), (3, 4), (5, 6), (7, 8), (9, 12), (13, 15), (16, 18), (19, 20), (21, 25), (26, 29), (30, 34), (35, 39), (40, 44), (45, 47), (48, 51)]
assert BLOCKS[-1][1] == len(W) - 1
caps_html, caps_data = [], []
for bi, (a, b) in enumerate(BLOCKS):
    ws = [W[i] for i in range(a, b + 1)]
    s = 0.0 if bi == 0 else ws[0]['s'] - 0.06          # o gancho já abre com a frase na tela
    nxt = W[BLOCKS[bi + 1][0]]['s'] - 0.06 if bi + 1 < len(BLOCKS) else None
    e = nxt if nxt is not None and nxt - ws[-1]['e'] < 0.7 else ws[-1]['e'] + 0.3
    e = min(e, SPEECH - 0.05)
    txt = ' '.join(x['w'] for x in ws)
    spans = ' '.join(f'<em>{html.escape(x["w"])}</em>' if x['w'].lower() in KEY else html.escape(x['w']) for x in ws)
    i = len(caps_data)
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl"><span class="bk">{html.escape(txt)}</span><span class="fg">{spans}</span></span></div>')
    caps_data.append({'s': q(s), 'e': q(e), 'text': txt})

CHIPS = [('c0', 0.0, T['cortez'] - 0.5, 'Do jeito antigo', 'editor'), ('c1', T['cortez'] - 0.5, T['grava'] - 0.3, 'Com o Cortez', 'IA que edita vídeo'),
         ('c2', T['grava'] - 0.3, T['nao'] - 0.1, 'Tempo de máquina', '20 a 30 min'), ('c3', T['nao'] - 0.1, T['voce'] - 0.05, 'Correção?', 'é só pedir'),
         ('c4', T['voce'] - 0.05, T['resto'] - 0.1, 'Seu tempo', '~5 min'), ('c5', T['resto'] - 0.1, T['cta0'] - 0.05, 'O resto', 'com o Cortez')]
chips_html = '\n  '.join(f'<div class="chip" id="{c}"><i></i><span>{a}</span><b>{b}</b></div>' for c, s, e, a, b in CHIPS)
chips_data = [{'id': c, 's': q(s), 'e': q(e)} for c, s, e, a, b in CHIPS]

# trilha: Lyria 1 do tutorial da Cami (reuso sem custo) — trecho 146,9 s em diante (o EXEMPLO_2 usou 37,5–58,2 / 105,8–119,2 / 169,2–173,6 s);
# a entrada forte da faixa em ≈151,7 s cai no "Eu sou o Cortez" (varredura verde que comprime o tempo).
r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '150.0', '-t', '3.5', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
en = np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1))
es = np.convolve(en, np.ones(4) / 4, mode='same')
onset = 150.0 + (int(np.argmax(es[5:] - es[:-5])) + 2) * 0.01
MOFF = round(onset - T['cortez'], 3)

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
M = mode()
top = layout(M)
data = {'T': T, 'caps': caps_data, 'chips': chips_data, 'seq': seq, 'cta': M}
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
    {'id': 'hook', 'start': 0, 'end': T['fall2'], 'what': '"Mandar pro editor: dois dias." — bloco maciço "2 DIAS" (48 fatias de 1 h) cai sobre a régua de horas e assenta com peso'},
    {'id': 'mais_um', 'start': T['fall2'], 'end': T['cortez'], 'what': '"Pedir correção: mais um." — o bloco "+1 DIA" cai atrás; a câmera sobe e mostra 72 h de régua'},
    {'id': 'cortez', 'start': T['cortez'], 'end': T['comp1'], 'what': '"Eu sou o Cortez…" — varredura verde percorre os blocos; as 72 fatias se soltam e comprimem num segmento verde curto'},
    {'id': 'grava', 'start': T['comp1'], 'end': T['pronto'], 'what': 'a gravação bruta real cai sobre o segmento; cabeça de leitura corre 0→30 min ("vinte, trinta minutos")'},
    {'id': 'pronto', 'start': T['pronto'], 'end': T['nao'], 'what': 'o cartão gira e vira o EXEMPLO_3 editado pelo Cortez'},
    {'id': 'ajuste', 'start': T['nao'], 'end': T['voce'], 'what': 'pedido "Troca essa cena?"; no "ajusto" o cartão gira para a versão 2 (exemplo de ajuste, outra cena da mesma entrega)'},
    {'id': 'cinco', 'start': T['voce'], 'end': T['resto'], 'what': '"5 MIN" em 3D se ergue do chão na frente do vídeo pronto'},
    {'id': 'resto', 'start': T['resto'], 'end': T['cta0'], 'what': 'fileira de entregas reais do Cortez sobe ao longo da régua (EXEMPLO_4, EXEMPLO_5, EXEMPLO_6, EXEMPLO_7)'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': '"5 minutos seus. O resto é com o Cortez." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + UnrealBloom + Output) via hf-seek',
    'identity': 'ID01', 'caption_style': 'L08', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; sem aleatoriedade',
    'concept': 'o tempo como objeto físico: 3 dias de editor viram blocos maciços que o Cortez comprime num segmento de 20–30 min; 5 min seus',
    'T': T, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'offset': MOFF, 'onset_track_s': round(onset, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'music_offset': MOFF, 'onset': round(onset, 2)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
