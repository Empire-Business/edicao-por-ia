#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA (palavras alinhadas do ElevenLabs,
conferidas por transcrição) e de src/index.tpl.html. F10 · ID05 Roxo · legenda L01 (frase estável em blocos de até 6 palavras).
CTA=saiba (padrão, comp/) ou CTA=comment (comp-cta-comment/). Grava analysis/scene_plan.json, motion_plan.json e caption_groups.json.
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

T = {'cores': s_(3), 'marca': s_(6), 'fonte': s_(9), 'estilo': s_(12), 'eu': s_(13), 'monto': s_(14), 'identidade': s_(17), 'visual': s_(18),
     'e0': s_(19), 'todo': s_(20), 'video': s_(21), 'editar': s_(24), 'sai': s_(25), 'sua': s_(28), 'cara': s_(29), 'nao': s_(30), 'modelo': s_(34),
     'pronto': s_(35), 'nem': s_(36), 'ia': s_(40), 'eu2': s_(41), 'cortez': s_(44), 'edito': s_(47), 'seu': s_(49), 'jeito': s_(50),
     'cta0': SPEECH, 'speechEnd': SPEECH}
T['dock1'] = T['monto'] + 0.12
T['dock2'] = T['identidade'] + 0.22
T['dock3'] = T['visual'] + 0.18
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR

KEY = {'cores', 'marca,', 'fonte,', 'estilo.', 'identidade', 'visual,', 'modelo', 'pronto,', 'IA.', 'Cortez,', 'seu', 'jeito.'}
BLOCKS = [(0, 3), (4, 6), (7, 9), (10, 12), (13, 16), (17, 18), (19, 24), (25, 29), (30, 33), (34, 35), (36, 40), (41, 44), (45, 50)]
caps_html, caps_data = [], []
for bi, (a, b) in enumerate(BLOCKS):
    ws = [{'w': W[i]['w'], 'k': W[i]['w'] in KEY or (bi == 7 and W[i]['w'] in ('sua', 'cara.'))} for i in range(a, b + 1)]
    s = W[a]['s'] - 0.06
    nxt = W[BLOCKS[bi + 1][0]]['s'] - 0.06 if bi + 1 < len(BLOCKS) else None
    e = nxt if nxt is not None and nxt - W[b]['e'] < 0.7 else W[b]['e'] + 0.3
    e = min(e, SPEECH - 0.04)
    spans = '<span class="cl">' + ' '.join(f'<span class="{"k" if x["k"] else "w"}">{html.escape(x["w"])}</span>' for x in ws) + '</span>'
    i = len(caps_data)
    caps_html.append(f'<div class="cap" id="cg{i}" style="top:1468px">{spans}</div>')
    caps_data.append({'s': q(s), 'e': q(e), 'text': ' '.join(x['w'] for x in ws)})

HEADS = [('Suas <em>cores.</em>', 0, T['fonte'] - 0.06), ('Sua <em>fonte.</em>', T['fonte'] - 0.02, T['estilo'] - 0.06),
         ('Seu <em>estilo.</em>', T['estilo'] - 0.02, T['eu'] - 0.02), ('Sua <em>identidade.</em>', T['eu'] + 0.02, T['e0']),
         ('Com a <em>sua cara.</em>', T['e0'] + 0.04, T['nao'] - 0.02), ('Não é|<em>modelo pronto.</em>', T['nao'] + 0.02, T['nem'] - 0.02),
         ('Nem <em>cara de IA.</em>', T['nem'] + 0.02, T['eu2'] - 0.02), ('Do <em>seu jeito.</em>', T['eu2'] + 0.02, T['cta0'] + 0.1)]
heads_html = '\n  '.join(f'<div class="hd" id="hd{i}">' + ''.join(f'<span class="ln"><span class="in">{ln}</span></span>' for ln in h.split('|')) + '</div>'
                         for i, (h, a, b) in enumerate(HEADS))
heads_data = [{'s': q(a), 'e': q(b)} for h, a, b in HEADS]
LABS = [('Leque de cores · <b>IDs reais</b>', 0, T['fonte'] - 0.06), ('Fontes das <b>identidades</b>', T['fonte'], T['estilo'] - 0.06),
        ('Estilos de <b>legenda</b>', T['estilo'], T['eu'] - 0.04), ('Montando a <b>sua identidade</b>', T['eu'], T['e0']),
        ('Mesmo vídeo · <b>identidades diferentes</b>', T['e0'] + 0.04, T['nao']), ('Descartado · <b>modelo pronto</b>', T['nao'] + 0.04, T['nem']),
        ('Descartado · <b>cara de IA</b>', T['nem'] + 0.04, T['eu2']), ('Vídeos reais · <b>editados pelo Cortez</b>', T['eu2'] + 0.04, T['cta0'])]
labs_html = '\n  '.join(f'<div class="lab" id="lb{i}"><i></i><span>{t}</span></div>' for i, (t, a, b) in enumerate(LABS))
labs_data = [{'s': q(a), 'e': q(b)} for t, a, b in LABS]

SWATCHES = [{'code': 'ID07', 'name': 'Laranja', 'hex': '#F05A28'}, {'code': 'ID01', 'name': 'Verde', 'hex': '#25D366'}, {'code': 'ID03', 'name': 'Azul', 'hex': '#4A92E6'},
            {'code': 'ID05', 'name': 'Roxo', 'hex': '#820AD1', 'hero': True}, {'code': 'ID04', 'name': 'Dourado', 'hex': '#D6B46A'},
            {'code': 'IDP02', 'name': 'Black', 'hex': '#F6C6C3'}, {'code': 'ID02', 'name': 'Lima', 'hex': '#D7FF3A'}, {'code': 'ID06', 'name': 'Azul Claro', 'hex': '#0A4DFF'}]
SORTS = [{'font': 'baskerville', 'glyph': 'Aa', 'size': 88, 'label': 'BASKERVILLE'}, {'font': 'manrope', 'glyph': 'Aa', 'size': 94, 'label': 'MANROPE', 'hero': True},
         {'font': 'instrument', 'glyph': 'Aa', 'size': 110, 'label': 'INSTRUMENT'}, {'font': 'jetbrains', 'glyph': 'Aa', 'size': 84, 'label': 'JETBRAINS'}]
PLATES = [{'kind': 'serif', 'label': 'SERIFADA'}, {'kind': 'pill', 'label': 'DESTAQUE', 'hero': True}, {'kind': 'mono', 'label': 'CAIXA ALTA'}]
CARDS = [{'kind': 'template', 'tag': 'MODELO PRONTO', 'at': q(T['nao'] - 0.05), 'kill': q(T['pronto'] + 0.08)},
         {'kind': 'ai', 'tag': 'CARA DE IA', 'at': q(T['nem'] - 0.05), 'kill': q(T['ia'] + 0.08)}]
SKINS = [{'raw': True, 'bg': '#FFFFFF'},
         {'bg': '#171714', 'fg': '#F1EEE5', 'accent': '#D6B46A', 'muted': '#B6B09F', 'cap': 'serif', 'tagL': 'MESMO VÍDEO', 'tagR': 'ID04 · DOURADO'},
         {'bg': '#0B141A', 'fg': '#E9EDEF', 'accent': '#25D366', 'boxText': '#0B141A', 'muted': '#AEBAC1', 'cap': 'box', 'tagL': 'MESMO VÍDEO', 'tagR': 'ID01 · VERDE'},
         {'bg': '#F7F6F3', 'fg': '#101828', 'accent': '#F05A28', 'muted': '#667085', 'cap': 'under', 'tagL': 'MESMO VÍDEO', 'tagR': 'ID07 · LARANJA'},
         {'bg': '#131211', 'fg': '#f0ede4', 'accent': '#f6c6c3', 'muted': '#d8d4ca', 'cap': 'instrument', 'tagL': 'MESMO VÍDEO', 'tagR': 'IDP02 · BLACK'},
         {'bg': '#F7F4FB', 'fg': '#17092C', 'accent': '#820AD1', 'muted': '#5C0F8B', 'cap': 'pill', 'tagL': 'SUA MARCA', 'tagR': 'SUA IDENTIDADE'}]
SKIN_AT = [{'t': 0, 'skin': 0}, {'t': T['todo'], 'skin': 1}, {'t': T['video'], 'skin': 2}, {'t': T['editar'], 'skin': 3}, {'t': T['sai'], 'skin': 4},
           {'t': q(T['cara'] - 0.08), 'skin': 5}]
PA = json.loads((J / 'analysis/proof_assets.json').read_text())
PROOF = [{'seq': n, 'label': PA[n]['label'].upper(), 'src': PA[n]['src'], 'ss': PA[n]['ss']} for n in ('p0', 'p1', 'p2', 'p4')]
TYPEFACES = {'manrope': 'assets/manrope-800.typeface.json', 'baskerville': 'assets/baskerville-700.typeface.json',
             'instrument': 'assets/instrument-400.typeface.json', 'jetbrains': 'assets/jetbrains-700.typeface.json'}

# trilha: trecho cheio da Lyria 2 (≈141–157 s, não usado por EXEMPLO_2 103–129 s nem EXEMPLO_3 26,5–64 s); a queda da faixa (≈157 s) cai no CTA
r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '153', '-t', '8', '-i', str(MUSIC), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
x = np.frombuffer(r, np.int16).astype(np.float32) / 32768
e = np.sqrt((x[:len(x) // 800 * 800].reshape(-1, 800) ** 2).mean(1))
best = max(range(20, len(e) - 20), key=lambda i: e[i - 20:i].mean() - e[i:i + 20].mean())   # maior queda sustentada (1 s antes × 1 s depois)
fall = 153 + best * 0.05 + 0.3
MOFF = round(fall - T['cta0'], 3)

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
M = mode()
top = layout(M)
data = {'T': T, 'caps': caps_data, 'heads': heads_data, 'labs': labs_data, 'swatches': SWATCHES, 'sorts': SORTS, 'plates': PLATES, 'cards': CARDS,
        'skins': SKINS, 'skinAt': SKIN_AT, 'proof': PROOF, 'seq': seq, 'typefaces': TYPEFACES, 'cta': M}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', heads_html)
       .replace('{{LABS}}', labs_html).replace('{{DUR}}', f'{DUR:.3f}').replace('{{BTN_TOP}}', str(top)))
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
    {'id': 'cores', 'start': 0, 'end': T['fonte'], 'what': 'leque laqueado de 8 cores reais das IDs (código, nome e hex em cada lâmina); abre no "cores"; a lâmina roxa (ID05) sobe no "marca"'},
    {'id': 'fonte', 'start': T['fonte'], 'end': T['estilo'], 'what': '4 tipos de metal com "Aa" 3D nas fontes reais das IDs (Baskerville, Manrope, Instrument Serif, JetBrains Mono); o Manrope sobe e fica roxo'},
    {'id': 'estilo', 'start': T['estilo'], 'end': T['eu'], 'what': '3 placas de estilo de legenda entram pela direita; a de destaque em pílula é escolhida'},
    {'id': 'monta', 'start': T['eu'], 'end': T['e0'], 'what': 'a prancha "Sua identidade visual" sobe; cor, fonte e legenda voam e encaixam (monto / identidade / visual); a ficha preenche COR, FONTE, LEGENDA'},
    {'id': 'mesmo_video', 'start': T['e0'], 'end': T['nao'], 'what': 'a placa com o MESMO vídeo (imagem de câmera do EXEMPLO_4) entra sem identidade e troca de pele em cada palavra: ID04, ID01, ID07, IDP02; no "sua cara" a prancha carimba a placa e ela vira a identidade roxa da pessoa'},
    {'id': 'descartes', 'start': T['nao'], 'end': T['eu2'], 'what': 'cartão de "modelo pronto" (cinza genérico) e cartão de "cara de IA" (gradiente genérico) entram na frente e são riscados e descartados'},
    {'id': 'seu_jeito', 'start': T['eu2'], 'end': T['cta0'], 'what': 'a placa da pessoa encolhe para o centro de um arco de 4 entregas reais do Cortez em IDs diferentes (EXEMPLO_4 ID07, EXEMPLO_5 ID04, EXEMPLO_6 ID08, EXEMPLO_7 IDP02)'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': 'câmera recua; "Com a sua cara." + "Você grava. O Cortez edita. Você aprova." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"')},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (WebGLRenderer com sombras PCF suaves, NeutralToneMapping, RoomEnvironment) via hf-seek',
    'identity': 'ID05', 'caption_style': 'L01', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; telas desenhadas em canvas a cada quadro; PRNG fixo',
    'concept': 'kit de marca físico (leque de cores laqueado, tipos de metal com as fontes reais das IDs, placas de legenda) montado na identidade da pessoa; o mesmo vídeo troca de identidade; modelo pronto e cara de IA descartados; arco de entregas reais',
    'T': T, 'seq': seq, 'music': {'file': '<PREENCHER: fonte ou prova própria>', 'offset': MOFF, 'fall_track_s': round(fall, 3)},
    'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'music_offset': MOFF}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
