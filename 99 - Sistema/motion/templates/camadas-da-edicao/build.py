#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA, das palavras alinhadas
(ElevenLabs, conferidas por transcrição) e de src/index.tpl.html. F10 · IDP01 Navy e Dourado · legenda L01 (frase estável em até
duas linhas). CTA=saiba (padrão, comp/) ou CTA=comment (comp-cta-comment/).
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

T = {'explode': s_(4), 'cortez': s_(6), 'voz': s_(13) - 0.1, 'corte0': s_(22) - 0.12, 'corte': s_(23), 'legenda0': s_(24) - 0.08,
     'anim0': s_(26) - 0.08, 'anim': s_(27), 'fiz0': s_(28) - 0.05, 'fiz': s_(32), 'seus': s_(33), 'grava': s_(42), 'pasta': s_(44) - 0.05,
     'drop': s_(48), 'fill': s_(49), 'col': s_(54), 'full': s_(57) + 0.30, 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR

KEY = {'cortez,', 'voz', 'corte,', 'legenda,', 'animação', 'fiz.', 'seus', 'vídeos:', 'grava,', 'pasta,', 'vinte,', 'trinta', 'minutos', 'pronto.'}
BLOCKS = [(0, 3), (4, 5), (6, 9), (10, 12), (13, 15), (16, 21), (22, 27), (28, 32), (33, 37), (38, 41), (42, 43), (44, 48), (49, 53), (54, 57)]
FIRST_2D = 2                                       # gancho (blocos 0–1) vai como título grande; legenda L01 começa no "Eu sou o Cortez"


def split_lines(ws):
    txt = lambda a: ' '.join(x['w'] for x in a)
    if len(txt(ws)) <= 22:
        return [ws]
    best, bi = 1e9, 1
    for k in range(1, len(ws)):
        a, b = len(txt(ws[:k])), len(txt(ws[k:]))
        sc = max(a, b) - (5 if ws[k - 1]['w'][-1] in ',;:' else 0)
        if sc < best:
            best, bi = sc, k
    return [ws[:bi], ws[bi:]]


l3, caps_html, caps_data = [], [], []
for bi, (a, b) in enumerate(BLOCKS):
    ws = [{'w': W[i]['w'], 's': W[i]['s'], 'e': W[i]['e'], 'k': W[i]['w'].lower() in KEY} for i in range(a, b + 1)]
    ls = split_lines(ws)
    l3.append({'s': ws[0]['s'], 'lines': ls})
    if bi < FIRST_2D:
        continue
    s = ws[0]['s'] - 0.05
    nxt = W[BLOCKS[bi + 1][0]]['s'] - 0.05 if bi + 1 < len(BLOCKS) else None
    e = nxt if nxt is not None and nxt - ws[-1]['e'] < 0.6 else ws[-1]['e'] + 0.3
    e = min(e, SPEECH - 0.05, T['full'])
    spans = ''.join('<span class="cl">' + ' '.join(f'<span class="{"k" if x["k"] else "w"}">{html.escape(x["w"])}</span>' for x in ln) + '</span>' for ln in ls)
    i = len(caps_data)
    caps_html.append(f'<div class="cap" id="cg{i}" style="top:{1500 if len(ls) == 2 else 1532}px">{spans}</div>')
    caps_data.append({'s': q(s), 'e': q(e), 'text': ' / '.join(' '.join(x['w'] for x in ln) for ln in ls)})

CHIPS = [('c0', T['cortez'], T['voz'], 'Este vídeo · <b>em camadas</b>'), ('c1', T['voz'], T['corte0'], 'Camada 04 · <b>voz de IA</b>'),
         ('c2', T['corte0'], T['legenda0'], 'Camada 01 · <b>corte</b>'), ('c3', T['legenda0'], T['anim0'], 'Camada 03 · <b>legenda</b>'),
         ('c4', T['anim0'], T['fiz0'], 'Camada 02 · <b>animação</b>'), ('c5', T['fiz0'], T['seus'], 'Tudo isso · <b>feito por IA</b>'),
         ('c6', T['seus'], T['grava'], 'Agora · <b>o seu vídeo</b>'), ('c7', T['grava'], T['pasta'], 'Passo 1 · <b>você grava</b>'),
         ('c8', T['pasta'], T['fill'], 'Passo 2 · <b>pasta 01</b>'), ('c9', T['fill'], T['col'], 'Passo 3 · <b>20 a 30 min</b>'),
         ('c10', T['col'], T['cta0'], 'Pronto · <b>editado pelo Cortez</b>')]
chips_html = '\n  '.join(f'<div class="chip" id="{c}"><i></i><span>{t}</span></div>' for c, a, b, t in CHIPS)
chips_data = [{'id': c, 's': a, 'e': b} for c, a, b, t in CHIPS]


def env(path, ss, dur, rate=25, floor=-52.0, top=-12.0):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ss:.3f}', '-t', f'{dur:.3f}', '-i', str(path), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                       capture_output=True).stdout
    x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
    h = 16000 // rate
    n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    return [round(float(v), 3) for v in np.clip((db - floor) / (top - floor), 0, 1)]


# trilha: a volta da faixa depois da pausa (≈104 s da Lyria 2 do tutorial da Cami) cai na explosão das camadas ("Fui eu.")
r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '102.5', '-t', '3.5', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
e = np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1))
es = np.convolve(e, np.ones(4) / 4, mode='same')
jump = es[5:] - es[:-5]
onset = 102.5 + (int(np.argmax(jump)) + 2) * 0.01
MOFF = round(onset - T['explode'], 3)
venv = env(J / 'renders/voice.wav', 0, DUR)
menv = env(MUSIC, MOFF, DUR, floor=-40.0, top=-10.0)

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
M = mode()
card, top = layout(M)
data = {'T': T, 'caps': caps_data, 'l3': l3, 'chips': chips_data, 'seq': seq, 'venv': venv, 'menv': menv, 'envRate': 25, 'card': card, 'cta': M}
tpl = (J / 'src/index.tpl.html').read_text()
cw, chh = 1080 * card['s'], 1920 * card['s']
fin_left, fin_top = round(540 - cw / 2 + 22), round(960 + card['y'] - chh / 2 + 22)
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{CHIPS}}', chips_html)
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{FIN0}}', f"{T['fill']:.4f}").replace('{{FINDUR}}', f"{DUR - T['fill']:.4f}")
       .replace('{{BTN_TOP}}', str(top)).replace('<div id="fintag">', f'<div id="fintag" style="left:{fin_left}px;top:{fin_top}px">'))
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
    {'id': 'hook', 'start': 0, 'end': T['explode'], 'what': 'o quadro deste vídeo, parado e escurecido, sob "Ninguém editou este vídeo."'},
    {'id': 'explode', 'start': T['explode'], 'end': T['voz'], 'what': '"Fui eu." — o quadro se desmonta em 5 camadas 3D (cenas reais do EXEMPLO_2, animação, legenda, voz de IA, trilha) com mola; câmera orbita'},
    {'id': 'voz', 'start': T['voz'], 'end': T['corte0'], 'what': 'a camada VOZ sai da pilha: onda real da narração com cabeça de leitura e código de tempo'},
    {'id': 'corte', 'start': T['corte0'], 'end': T['legenda0'], 'what': 'camada CENAS sai da pilha; lâmina dourada corta do apresentador para a cena do escritório no "corte"'},
    {'id': 'legenda', 'start': T['legenda0'], 'end': T['anim0'], 'what': 'camada LEGENDA: as palavras desta legenda entram uma a uma'},
    {'id': 'animacao', 'start': T['anim0'], 'end': T['fiz0'], 'what': 'camada ANIMAÇÃO: curva de keyframes se apaga e é redesenhada, keyframes pulsam'},
    {'id': 'fiz', 'start': T['fiz0'], 'end': T['seus'], 'what': 'todas as camadas de volta; brilho nas bordas no "fiz"'},
    {'id': 'seu_video', 'start': T['seus'], 'end': T['grava'], 'what': 'camadas esvaziam: o mesmo esqueleto, agora para o vídeo da pessoa'},
    {'id': 'grava', 'start': T['grava'], 'end': T['pasta'], 'what': 'a gravação bruta real (do EXEMPLO_2) entra na camada CENAS'},
    {'id': 'pasta', 'start': T['pasta'], 'end': T['fill'], 'what': 'um cartão da gravação bruta voa para a pasta 3D "01 Enviar vídeos", que fecha'},
    {'id': 'preenche', 'start': T['fill'], 'end': T['col'], 'what': 'camadas se preenchem em sequência (cena final, curva, legenda, voz, trilha); barra 20 a 30 min'},
    {'id': 'pronto', 'start': T['col'], 'end': T['cta0'], 'what': 'as camadas colapsam num quadro só que ocupa a tela: o EXEMPLO_2 editado pelo Cortez em resolução cheia'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': 'vídeo vira cartão; "Você grava. Eu edito." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + UnrealBloom + Output) via hf-seek',
    'identity': 'IDP01', 'caption_style': 'L01', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; telas internas desenhadas em canvas a cada quadro; PRNG fixo',
    'concept': 'o próprio vídeo desmontado em camadas 3D e remontado (meta: a IA mostra que editou este vídeo)',
    'T': T, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'offset': MOFF, 'onset_track_s': round(onset, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'music_offset': MOFF}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
