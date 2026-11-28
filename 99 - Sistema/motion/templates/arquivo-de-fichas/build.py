#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração de IA (palavras alinhadas pelo ElevenLabs e
conferidas por transcrição) e de src/index.tpl.html. F10 · ID08 Azul e Papel · legenda L02 (blocos curtos de até 3 palavras).
CTA=saiba (padrão, comp/) ou CTA=comment (comp-cta-comment/).
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json (só na versão padrão).
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cta_variant import mode, layout, snippets

J = Path(__file__).resolve().parent.parent
SYS = J.parents[1]
C = J / 'comp'
NW = json.loads((J / 'analysis/narration_words.json').read_text())
W = NW['words']
SPEECH = NW['speech']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
q = lambda x: round(round(x * 30) / 30, 4)
s_ = lambda i: W[i]['s']

# formatos F01–F22 (nomes atuais das pastas visíveis do catálogo)
FMT = []
for d in sorted((SYS.parent / '04 - Formatos').iterdir()):
    m = re.match(r'^(F\d\d) - (.+)$', d.name)
    if m:
        FMT.append({'code': m.group(1), 'name': m.group(2)})
assert len(FMT) == 22, FMT
slot = {f['code']: i for i, f in enumerate(FMT)}

T = {'names0': s_(9), 'escolhe': s_(22), 'cores0': s_(26), 'edito': s_(31), 'estilo': s_(33), 'cortez': s_(37), 'cortezW': s_(40),
     'sim': s_(47), 'este': s_(49), 'tambem': s_(51), 'cta0': SPEECH, 'speechEnd': SPEECH}
T = {k: q(v) for k, v in T.items()}
T['tap'] = q(SPEECH + 2.9)
T['end'] = DUR

NAMES = [('f02', 'F02', 9), ('f05', 'F05', 11), ('f13', 'F13', 13), ('f22', 'F22', 16), ('f12', 'F12', 19), ('f07', 'F07', 20)]
names = [{'key': k, 'slot': slot[c], 't': q(s_(i))} for k, c, i in NAMES]
CARDS = [{'key': 'f02', 'code': 'F02', 'name': 'Talking Head', 'left': 'EXEMPLO_2', 'right': 'exemplo editado pelo Cortez'},
         {'key': 'f05', 'code': 'F05', 'name': 'Notícia Comentada', 'left': 'F05', 'right': 'formato do catálogo'},
         {'key': 'f13', 'code': 'F13', 'name': 'Sem aparecer', 'left': 'F13 · Dados Dark', 'right': 'exemplo original do Cortez'},
         {'key': 'f22', 'code': 'F22', 'name': 'Corte de Live', 'left': 'EXEMPLO_3', 'right': 'exemplo editado pelo Cortez'},
         {'key': 'f12', 'code': 'F12', 'name': 'Documentário', 'left': 'F12', 'right': 'exemplo original do Cortez'},
         {'key': 'f07', 'code': 'F07', 'name': 'Motion Institucional', 'left': 'EXEMPLO_4', 'right': 'exemplo editado pelo Cortez'},
         {'key': 'f10', 'code': 'F10', 'name': 'Este vídeo', 'left': 'F10 · EXEMPLO_1', 'right': 'este vídeo · feito pelo Cortez'}]

IDS = []
for code in ['ID01', 'ID02', 'ID03', 'ID04', 'ID05', 'ID06', 'ID07', 'ID08']:
    d = json.loads((SYS / f'context/visual-identities/{code}/identity-v1.json').read_text())
    p = d['palette']
    IDS.append({'code': code, 'name': d['name'], 'bg': p['background'], 'primary': p['primary'], 'surface': p['surface'], 'text': p['text'],
                'font': d['typography']['headline']})
PICKS = [{'t': q(s_(26)), 'id': 2}, {'t': q(s_(27)), 'id': 6}, {'t': q(s_(28)), 'id': 4}, {'t': q(s_(29)), 'id': 3}]   # ID03 → ID07 → ID05 → ID04

# legenda L02 (gancho fica no título grande; legenda começa nos formatos)
BLOCKS = [((9, 10), 'Talking head,'), ((11, 12), 'notícia comentada,'), ((13, 15), 'vídeo sem aparecer,'), ((16, 18), 'corte de live,'),
          ((19, 19), 'documentário,'), ((20, 21), 'motion institucional.'), ((22, 23), 'Você escolhe'), ((24, 25), 'o formato,'),
          ((26, 28), 'escolhe as cores,'), ((29, 31), 'e eu edito'), ((32, 33), 'no estilo'), ((34, 36), 'que você quiser.'), ((37, 38), 'Eu sou'),
          ((39, 40), 'o Cortez,'), ((41, 42), 'uma inteligência'), ((43, 43), 'artificial'), ((44, 46), 'que edita vídeos.'), ((47, 48), 'E sim:'),
          ((49, 50), 'este aqui'), ((51, 53), 'também fui eu.')]
KEY = {'formato,', 'cores,', 'estilo', 'cortez,', 'fui', 'eu.'}
caps_html, caps_data = [], []
for bi, ((a, b), txt) in enumerate(BLOCKS):
    words = [W[i]['w'] for i in range(a, b + 1)]
    assert ' '.join(words).lower().replace(',', '').replace('.', '').replace(':', '') == txt.lower().replace(',', '').replace('.', '').replace(':', ''), (words, txt)
    s = s_(a) - 0.05
    nxt = s_(BLOCKS[bi + 1][0][0]) - 0.05 if bi + 1 < len(BLOCKS) else None
    e = nxt if nxt is not None and nxt - W[b]['e'] < 0.6 else W[b]['e'] + 0.3
    e = min(e, SPEECH - 0.04)
    spans = ' '.join(f'<span class="{"k" if w.lower() in KEY else "w"}">{html.escape(w)}</span>' for w in txt.split(' '))
    caps_html.append(f'<div class="cap" id="cg{bi}">{spans}</div>')
    caps_data.append({'s': q(s), 'e': q(e), 'text': txt})

CH = []
for k, (key, code, i) in enumerate(NAMES):
    a = names[k]['t'] - 0.15
    b = (names[k + 1]['t'] - 0.15) if k + 1 < len(names) else T['escolhe'] - 0.12
    nm = next(f['name'] for f in FMT if f['code'] == code)
    CH.append((f'n{k}', a, b, f'<b>{code}</b> · {html.escape(nm)} · <u>de 22</u>'))
CH += [('p1', T['escolhe'] - 0.1, T['cores0'] - 0.1, 'Passo 1 · <b>o formato</b>'), ('p2', T['cores0'] - 0.1, T['edito'] - 0.15, 'Passo 2 · <b>as cores</b> · IDs visuais'),
       ('p3', T['edito'] - 0.15, T['cortez'] - 0.12, 'Passo 3 · <b>o Cortez edita</b>'), ('p4', T['cortez'] - 0.12, T['sim'] - 0.12, 'Cortez · <b>IA que edita vídeos</b>'),
       ('p5', T['sim'] - 0.12, T['cta0'], '<b>F10</b> · <u>este vídeo</u>')]
chips_html = '\n  '.join(f'<div class="chip" id="{c}"><i></i><span>{t}</span></div>' for c, a, b, t in CH)
chips_data = [{'id': c, 's': q(a), 'e': q(b)} for c, a, b, t in CH]

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
M = mode()
top = layout(M)
data = {'T': T, 'caps': caps_data, 'chips': chips_data, 'seq': seq, 'formats': FMT, 'cards': CARDS, 'names': names, 'f22slot': slot['F22'],
        'f10slot': slot['F10'], 'ids': IDS, 'picks': PICKS, 'cta': M}
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
    {'id': 'hook', 'start': 0, 'end': T['names0'], 'what': 'título "22 jeitos de editar." desde o quadro 0; câmera sai de um close das etiquetas F01/F02 e revela o arquivo de 22 gavetas; onda de gavetas no "vinte e dois"'},
    *[{'id': f"nome-{n['key']}", 'start': n['t'], 'end': (names[k + 1]['t'] if k + 1 < len(names) else T['escolhe']),
       'what': f"gaveta {FMT[n['slot']]['code']} abre; a ficha sobe e vem para a frente com o exemplo real ({next(c['left'] for c in CARDS if c['key'] == n['key'])}); depois fica em pé na gaveta"}
      for k, n in enumerate(names)],
    {'id': 'formato', 'start': T['escolhe'], 'end': T['cores0'], 'what': 'a ficha F22 volta à frente com contorno azul (escolhida)'},
    {'id': 'cores', 'start': T['cores0'], 'end': T['edito'], 'what': 'leque de amostras das 8 IDs abre; ID03 → ID07 → ID05 → ID04 recolorem a faixa "Corte de live" e o papel da ficha'},
    {'id': 'estilo', 'start': T['edito'], 'end': T['cortez'], 'what': 'o vídeo da ficha (EXEMPLO_3, que é ID04) toca; o leque fecha'},
    {'id': 'cortez', 'start': T['cortez'], 'end': T['sim'], 'what': 'fichas voltam; câmera abre; as 22 gavetas abrem em cascata; brilho corre na placa CORTEZ · 22 FORMATOS'},
    {'id': 'este-video', 'start': T['sim'], 'end': T['cta0'], 'what': 'gaveta F10 abre; a ficha mostra este próprio vídeo (recursão de 2 níveis) e a câmera mergulha nela'},
    {'id': 'cta', 'start': T['cta0'], 'end': DUR, 'what': '"22 jeitos de editar. Escolha o seu." + ' + ('"Saiba mais"' if M == 'saiba' else '"Comente CORTEZ"') + '; arquivo ao fundo'},
]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + UnrealBloom + Output) via hf-seek',
    'identity': 'ID08', 'caption_style': 'L02', 'determinism': 'função do tempo do quadro; texturas = quadros JPG pelo tempo; recursão por 2 render targets no mesmo quadro; PRNG fixo',
    'concept': 'arquivo físico de 22 gavetas (F01–F22); fichas de papel com exemplos reais; leque de amostras das IDs; ficha F10 mostra este próprio vídeo',
    'T': T, 'names': names, 'picks': PICKS, 'seq': seq, 'speech_seconds': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'names': [(n['key'], n['t']) for n in names]}, ensure_ascii=False))
