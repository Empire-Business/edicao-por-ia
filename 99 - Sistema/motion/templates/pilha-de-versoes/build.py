#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA do Cortez, das palavras alinhadas
(ElevenLabs, conferidas por transcrição) e de src/index.tpl.html. F10 · ID01 Verde · legenda L02 (blocos curtos de até 3 palavras,
entrada suave). Conceito: três pedidos de exemplo, três ajustes visíveis na MESMA entrega real (EXEMPLO_2 V2) numa tela 3D grande — troca de
cena (varredura), legenda maior (placa cresce sobre a legenda queimada), troca de música (faixa vira e a trilha muda de verdade);
cada "Me fala." cai numa batida; placas de versão V1→V4 empilham sob a tela; "quantas vezes precisar" → V5–V7; "sem esperar dois dias"
→ dois blocos de calendário dobram e somem. CTA=saiba (comp/) ou CTA=comment (comp-cta-comment/).
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
e_ = lambda i: W[i]['e']
ws_ = [w['w'] for w in W]
assert ws_[:7] == ['Não', 'gostou', 'de', 'uma', 'cena?', 'Me', 'fala.'] and ws_[18] == 'fala.' and ws_[22] == 'Cortez,' and ws_[43] == 'dias.', ws_

T = {'cena': s_(4), 'me1': s_(5), 'mf1': s_(6), 'leg': s_(9), 'me2': s_(11), 'mf2': s_(12), 'mus': s_(16), 'me3': s_(17), 'mf3': s_(18),
     'eu': s_(19), 'cortez': s_(22), 'ajusto': s_(25), 'video': s_(27), 'pedir': s_(32), 'quantas': s_(33), 'vezes': s_(34), 'precisar': s_(35),
     'sem': s_(36), 'feia': s_(38), 'esperar': s_(41), 'dois': s_(42), 'dias': s_(43), 'diasEnd': e_(43), 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR

# legenda L02: blocos de até 3 palavras, sem quebrar expressão; palavras-chave em verde
KEY = {'cena?', 'maior?', 'música?', 'fala.', 'cortez,', 'ajusto', 'precisar.', 'dois', 'dias.'}
BLOCKS = [(0, 1), (2, 4), (5, 6), (7, 9), (10, 10), (11, 12), (13, 14), (15, 16), (17, 18), (19, 20), (21, 22), (23, 25), (26, 27), (28, 29),
          (30, 32), (33, 34), (35, 35), (36, 38), (39, 41), (42, 43)]
assert BLOCKS[-1][1] == len(W) - 1 and all(b - a < 3 for a, b in BLOCKS)
caps_html, caps_data = [], []
for bi, (a, b) in enumerate(BLOCKS):
    ws = [W[i] for i in range(a, b + 1)]
    s = 0.0 if bi == 0 else ws[0]['s'] - 0.05
    nxt = W[BLOCKS[bi + 1][0]]['s'] - 0.05 if bi + 1 < len(BLOCKS) else None
    e = nxt if nxt is not None and nxt - ws[-1]['e'] < 0.6 else ws[-1]['e'] + 0.28
    e = min(e, SPEECH - 0.05)
    txt = ' '.join(x['w'] for x in ws)
    spans = ' '.join(f'<em>{html.escape(x["w"])}</em>' if x['w'].lower() in KEY else html.escape(x['w']) for x in ws)
    i = len(caps_data)
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl"><span class="bk">{html.escape(txt)}</span><span class="fg">{spans}</span></span></div>')
    caps_data.append({'s': q(s), 'e': q(e), 'text': txt})

# cabeçalho: rótulo (mono) + título (pedido de exemplo → resultado). Os títulos só aparecem nos três ajustes (complementam a fala).
HEAD = [  # id, início, fim, rótulo, título (None = só rótulo), estilo
    ('h0', 0.0, T['me1'] - 0.1, 'Seu vídeo · versão 1', None, ''),
    ('h1', T['me1'] - 0.1, T['mf1'] + 0.26, 'Exemplo de pedido', '“Troca essa cena.”', 'ask'),
    ('h2', T['mf1'] + 0.26, T['me2'] - 0.12, 'Versão 2', '✓ Cena trocada.', 'ok'),
    ('h3', T['me2'] - 0.12, T['mf2'] + 0.26, 'Exemplo de pedido', '“Legenda maior.”', 'ask'),
    ('h4', T['mf2'] + 0.26, T['me3'] - 0.12, 'Versão 3', '✓ Legenda maior.', 'ok'),
    ('h5', T['me3'] - 0.12, T['mf3'] + 0.26, 'Exemplo de pedido', '“Troca a música.”', 'ask'),
    ('h6', T['mf3'] + 0.26, T['cortez'] - 0.1, 'Versão 4', '✓ Música nova.', 'ok'),
    ('h7', T['cortez'] - 0.1, T['quantas'] - 0.1, 'Cortez · IA que edita vídeo', None, ''),
    ('h8', T['quantas'] - 0.1, T['esperar'] - 0.1, 'Quantas versões precisar', None, ''),
    ('h9', T['esperar'] - 0.1, T['cta0'] - 0.05, 'Sem esperar 2 dias', None, ''),
]
head_html, head_data = [], []
for hid, a, b, lab, ttl, sty in HEAD:
    head_html.append(f'<div class="lab" id="{hid}l"><i></i><span>{html.escape(lab)}</span></div>')
    if ttl:
        head_html.append(f'<div class="ttl {sty}" id="{hid}t"><span class="in">{html.escape(ttl)}</span></div>')
    head_data.append({'id': hid, 's': q(a), 'e': q(b), 'ttl': bool(ttl)})

# trilha: Namoral 03 (gerada e paga antes; reuso sem custo). Trilha 1 = abertura esparsa da faixa (0 s…), Trilha 2 = retomada cheia depois
# da pausa em ≈49–50 s; a troca acontece de verdade no "Me fala." da música (≈T.mf3). Combinação e pontos de entrada diferentes dos
# cortes 2 (19,3–51,7), 5 (52–83,5), 8 (40,7–68,9 / 78,1–80,5) e EXEMPLO_3 (3,0–22,6 / 31,4–38,3).
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
en = np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1))      # 10 ms
es = np.convolve(en, np.ones(4) / 4, mode='same')
i0, i1 = 4980, 5160
onB = (i0 + int(np.argmax(es[i0 + 5:i1] - es[i0:i1 - 5])) + 2) * 0.01
B_OFF = round(onB - T['mf3'], 3)                                               # tempo na faixa = tempo no vídeo + B_OFF
def bars(t0, n=44, span=4.4):
    v = []
    for k in range(n):
        a = int((t0 + k * span / n) * 100); b = int((t0 + (k + 1) * span / n) * 100)
        v.append(float(en[a:b].max()))
    v = np.array(v); return v / max(1e-6, v.max())
BA = [round(float(0.16 + 0.5 * y), 3) for y in bars(0.2)]
BB = [round(float(0.32 + 0.68 * y), 3) for y in bars(onB)]

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
M = mode()
top = layout(M)
data = {'T': T, 'caps': caps_data, 'head': head_data, 'seq': seq, 'cta': M, 'bars': {'a': BA, 'b': BB}}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEAD}}', '\n  '.join(head_html))
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
    {'id': 'hook', 'start': 0, 'end': T['mf1'], 'what': 'tela 3D grande com a entrega EXEMPLO_2 (versão 1, apresentador); cantoneiras verdes selecionam "a cena"; pedido de exemplo "Troca essa cena."'},
    {'id': 'cena', 'start': T['mf1'], 'end': T['me2'], 'what': 'no "fala." a varredura verde desce e troca a cena pela do call center vazio da mesma entrega; placa V2 entra sob a tela'},
    {'id': 'legenda', 'start': T['me2'], 'end': T['me3'], 'what': 'cantoneiras vão para a legenda; no "fala." uma placa cresce sobre a legenda queimada: "a agenda esvazia" grande; placa V3'},
    {'id': 'musica', 'start': T['me3'], 'end': T['eu'], 'what': 'faixa de áudio "Trilha 1" na base da tela; no "fala." ela vira para "Trilha 2" e a trilha muda de verdade; placa V4'},
    {'id': 'ajusto', 'start': T['eu'], 'end': T['quantas'], 'what': 'câmera recua; a tela mostra a entrega EXEMPLO_2 (editada pelo Cortez) tocando'},
    {'id': 'quantas', 'start': T['quantas'], 'end': T['sem'], 'what': 'V5, V6, V7 empilham em sequência rápida; a pilha de versões sobe a tela'},
    {'id': 'dois_dias', 'start': T['sem'], 'end': T['cta0'], 'what': 'dois blocos de calendário "DIA 1 / DIA 2" entram e dobram até sumir'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': '"Me fala. Eu ajusto." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + UnrealBloom + Output) via hf-seek',
    'identity': 'ID01', 'caption_style': 'L02', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; sem aleatoriedade',
    'concept': 'três pedidos de exemplo, três ajustes visíveis na mesma entrega real; pilha de versões; dois dias que dobram e somem',
    'T': T, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'a_offset': 0.0, 'b_offset': B_OFF, 'b_onset_track_s': round(onB, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'b_onset': round(onB, 2), 'b_off': B_OFF}, ensure_ascii=False))
