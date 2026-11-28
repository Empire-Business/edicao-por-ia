#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA do Cortez, das palavras alinhadas
(ElevenLabs, conferidas por transcrição) e de src/index.tpl.html. F10 · ID07 Laranja · legenda L04 (bloco fixo, palavra falada em laranja).
Estilo: "a estrada da edição" — de noite, uma linha do tempo genérica (sem marca) se estende até o horizonte, lotada de clipes; janelas de
trabalho manual se empilham (cortar silêncio, procurar cena, ajustar legenda) e um contador de horas não para. No "Eu sou o Cortez" os
720 clipes decolam da linha do tempo e se encaixam como ladrilhos de um mosaico que vira o vídeo pronto (EXEMPLO_2, entrega real do Cortez);
"enquanto você cuida do que dá dinheiro" a noite vira dia; "Você só confere e aprova" → toque no Aprovar.
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
assert [w['w'] for w in W][:2] == ['Quantas', 'horas'] and W[16]['w'] == 'Cortez.' and W[38]['w'] == 'aprova.', [w['w'] for w in W]

T = {'cortando': s_(7), 'silencio': s_(8), 'procurando': s_(9), 'cena': s_(10), 'ajustando': s_(11), 'legenda': s_(12), 'eu': s_(13),
     'cortez': s_(16), 'faco': s_(18), 'tudo': s_(19), 'isso': s_(20), 'voce1': s_(22), 'vinte': s_(24), 'trinta': s_(25), 'minutos': s_(26),
     'enquanto': s_(27), 'cuida': s_(29), 'dinheiro': s_(33), 'voce2': s_(34), 'confere': s_(36), 'aprova': s_(38), 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR

# legenda L04: bloco fixo de até 4 palavras; a palavra falada fica laranja
BLOCKS = [(0, 2), (3, 6), (7, 8), (9, 10), (11, 12), (13, 16), (17, 20), (21, 22), (23, 26), (27, 29), (30, 33), (34, 36), (37, 38)]
assert BLOCKS[-1][1] == len(W) - 1 and all(b - a < 4 for a, b in BLOCKS)
caps_html, caps_data = [], []
for bi, (a, b) in enumerate(BLOCKS):
    ws = [W[i] for i in range(a, b + 1)]
    s = 0.0 if bi == 0 else ws[0]['s'] - 0.05
    nxt = W[BLOCKS[bi + 1][0]]['s'] - 0.05 if bi + 1 < len(BLOCKS) else None
    e = nxt if nxt is not None and nxt - ws[-1]['e'] < 0.7 else ws[-1]['e'] + 0.3
    e = min(e, SPEECH - 0.05)
    spans = ' '.join(f'<span class="w" id="w{a + k}">{html.escape(x["w"])}</span>' for k, x in enumerate(ws))
    i = len(caps_data)
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl">{spans}</span></div>')
    words = [{'i': a + k, 's': q(x['s']), 'e': q(W[a + k + 1]['s'] if a + k + 1 < len(W) and a + k + 1 <= b else x['e'] + 0.05)} for k, x in enumerate(ws)]
    caps_data.append({'s': q(s), 'e': q(e), 'text': ' '.join(x['w'] for x in ws), 'words': words})

CHIPS = [('c0', 0.0, T['eu'] - 0.12, 'Do jeito antigo', 'você editando'), ('c1', T['eu'] - 0.12, T['vinte'] - 0.12, 'Com o Cortez', 'IA que edita vídeo'),
         ('c2', T['vinte'] - 0.12, T['enquanto'] - 0.1, 'Tempo de máquina', '20 a 30 min'),
         ('c3', T['enquanto'] - 0.1, T['voce2'] - 0.08, 'Enquanto isso', 'você no que dá dinheiro'),
         ('c4', T['voce2'] - 0.08, T['cta0'] - 0.05, 'Você', 'só confere e aprova')]
chips_html = '\n  '.join(f'<div class="chip" id="{c}"><i></i><span>{a}</span><b>{b}</b></div>' for c, s, e, a, b in CHIPS)
chips_data = [{'id': c, 's': q(s), 'e': q(e)} for c, s, e, a, b in CHIPS]

# trilha: Lyria 3 do tutorial da Cami (reuso sem custo), trecho ≈125–144 s (o EXEMPLO_3 usou 12–36 s + 169–173 s; o EXEMPLO_4 78,6–108,2 s + 170–174 s).
# A faixa tem um respiro em ≈130,8 s; a volta forte depois dele cai no "Eu sou o Cortez".
r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '130.2', '-t', '1.6', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
en = 20 * np.log10(np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1)) + 1e-9)
dip = 5 + int(np.argmin(en[5:]))                         # ignora o atraso do decodificador mp3 nos primeiros quadros
onset = 130.2 + (dip + int(np.argmax(en[dip:] > -25))) * 0.01
MOFF = round(onset - T['eu'], 3)

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
    {'id': 'hook', 'start': 0, 'end': T['cortando'], 'what': '"Quantas horas você já perdeu editando vídeo?" — de noite, linha do tempo genérica até o horizonte, lotada de clipes; contador "TEMPO EDITANDO" disparando'},
    {'id': 'silencio', 'start': T['cortando'], 'end': T['procurando'], 'what': 'janela de áudio: a lâmina corta, um a um, os trechos de silêncio da onda'},
    {'id': 'cena', 'start': T['procurando'], 'end': T['ajustando'], 'what': 'janela de busca: grade cinza genérica rolando sem fim, "buscando cena…"'},
    {'id': 'legenda', 'start': T['ajustando'], 'end': T['eu'], 'what': 'monitor com a gravação bruta real; a caixa de legenda é empurrada pixel a pixel (X/Y mudando)'},
    {'id': 'cortez', 'start': T['eu'], 'end': T['faco'], 'what': '"Eu sou o Cortez." — as janelas somem; os 720 clipes decolam e viram ladrilhos de um mosaico com as cores do vídeo pronto, que vira o EXEMPLO_2'},
    {'id': 'tudo', 'start': T['faco'], 'end': T['vinte'], 'what': 'o EXEMPLO_2 (editado pelo Cortez) toca; selos 3D: silêncios cortados, cenas encontradas (cenas reais do EXEMPLO_2), legendas no ritmo'},
    {'id': 'tempo', 'start': T['vinte'], 'end': T['enquanto'], 'what': 'barra laranja "20–30 min · tempo de máquina" enche sob o vídeo'},
    {'id': 'dia', 'start': T['enquanto'], 'end': T['voce2'], 'what': 'a noite vira dia; a câmera vira para cartões de tarefas do negócio (ilustração) enquanto o Cortez segue editando ao fundo'},
    {'id': 'aprova', 'start': T['voce2'], 'end': T['cta0'], 'what': '"Você só confere e aprova." — volta ao vídeo pronto; toque em "Aprovar"'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': '"Pare de perder horas editando." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + UnrealBloom + Output) via hf-seek',
    'identity': 'ID07', 'caption_style': 'L04', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; PRNG de semente fixa',
    'concept': 'a estrada da edição: horas de trabalho manual numa linha do tempo sem fim; o Cortez transforma os clipes no vídeo pronto; a noite vira dia',
    'T': T, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'offset': MOFF, 'onset_track_s': round(onset, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'music_offset': MOFF, 'onset': round(onset, 2), 'T': T}, ensure_ascii=False))
