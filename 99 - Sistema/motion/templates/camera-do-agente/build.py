#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
F22 Corte de Live 3D + IDP02 Black Alto Valor + legenda L07 (ênfase pontual, escolhida pelo sentido).
Estilo novo: "o agente por dentro" — câmera no ponto de vista do Cortez navegando os produtos: constelação de motions no escuro,
mira do agente entrando na plataforma, print (flash + recorte que levanta), gravação de tela (REC + tira de quadros) e montagem do motion
pronto; depois monólitos verticais de vidro preto no chão para "do seu negócio / do seu site / software".
Tempos = palavras realmente faladas na voz final. O texto das legendas usa as palavras conferidas na fonte (Whisper: "PRODUTOr" →
PRODUTO; "cortês" → Cortez; "com cortês" → "com o Cortez"; "para" → "pra" como ele fala; "ele" antes de "gravou" e o "a" de
"pra a gente" ficam fora da legenda).
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


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


TS = {}
for s in EDL['segments']:
    TS.setdefault(s['take'], s['start'])
T = {'caro': W('caríssimo'), 'ant': W('antigamente'), 't02': TS['t02'], 'hta': W('PRODUTO'), 'inst1': W('institucionais'),
     'feitos': W('feitos'), 'reveal': W('cortês'), 'ele': W('Ele', 9), 'plat': W('plataformas'), 'tirou': W('tirou'), 'print': W('print'),
     'grav1': W('gravou'), 'grav2': W('gravou', W('gravou') + 0.3), 'tela': W('tela'), 'fez': W('fez'), 'prop': W('propaganda'),
     'inst2': W('institucional', 15), 'usando': W('usando'), 'dentro': W('dentro'), 'outros': W('outros'), 't03': TS['t03'],
     'negocio': W('negócio'), 'site': W('site'), 'voce2': W('Você', W('site') + 0.2), 'inst3': W('institucional', W('site') + 0.2),
     't04': TS['t04'], 'vender': W('vender'), 'ferr': W('ferramentas'), 'soft': W('software'), 'quem': W('quem'), 'produto': W('produto'),
     'maravilha': W('maravilha'), 'precisa1': W('precisa'), 'todo': W('todo'), 'precisa2': W('precisa', W('todo')),
     'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['tap'] = round(SPEECH + 2.9, 3)
T['type0'] = round(SPEECH + 1.75, 3)
T['plat_tick'] = round(T['plat'] + 0.55, 3)
T['print_tick'] = round(T['print'] + 0.25, 3)
T['tela_tick'] = round(T['tela'] + 0.3, 3)
T['prop_tick'] = round(T['inst2'] + 0.5, 3)
T['enter_ui'] = round(T['tirou'] - 0.32, 3)      # a mira entra no módulo PRODUTO e a plataforma abre
T = {k: round(v, 3) for k, v in T.items()}

HEADS = [
    ('h1', 0, T['t02'] - 0.05, 'Vídeo institucional', [('Isso era', 0), ('<em>caríssimo.</em>', T['caro'] - 0.12)]),
    ('h2', T['t02'] + 0.05, T['ele'] - 0.08, 'Os vídeos da nossa empresa', [('Esses vídeos…', T['t02'] + 1.1), ('<em>feitos pelo Cortez.</em>', T['feitos'] - 0.15)]),
    ('h4', T['usando'] - 0.32, T['t03'] - 0.04, 'E ainda', [('Usado dentro de', T['usando'] - 0.22), ('<em>outros vídeos.</em>', T['outros'] - 0.15)]),
    ('h5', T['t03'] + 0.05, T['t04'] - 0.05, 'Vídeos institucionais', [('Do seu negócio,', T['negocio'] - 0.35), ('<em>do seu site.</em>', T['site'] - 0.25)]),
    ('h6', T['t04'] + 0.05, T['todo'] - 0.3, 'Software e ferramentas', [('Pra vender', T['vender'] - 0.15), ('<em>software.</em>', T['soft'] - 0.12)]),
    ('h7', T['todo'] - 0.25, SPEECH + 0.05, 'Software e ferramentas', [('Todo mundo', T['todo'] - 0.15), ('<em>precisa.</em>', T['precisa2'] - 0.12)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.34 - at)), 3)} for tx, at in lines_]})
# lista do agente (no lugar do título enquanto ele conta o que o Cortez fez sozinho)
CHECK = [('Entrou na plataforma', T['ele'] + 0.05, T['plat_tick']), ('Tirou o print', T['tirou'] - 0.05, T['print_tick']),
         ('Gravou a tela', T['grav1'] - 0.05, T['tela_tick']), ('Montou a propaganda', T['fez'] - 0.1, T['prop_tick'])]
CK_END = T['usando'] - 0.36

# legenda L07: frases de até 4 palavras pelo sentido; no máximo uma palavra de ênfase por frase, escolhida editorialmente
FIX = {'para': 'pra', 'PRODUTO': 'PRODUTO', 'Air': 'AI', 'cortês.': 'Cortez.'}
SKIP = set()
for w in WORDS:
    w['w'] = FIX.get(w['w'], w['w'])
for i, w in enumerate(WORDS):
    if norm(w['w']) == 'com' and i + 1 < len(WORDS) and norm(WORDS[i + 1]['w']) == 'cortez':
        w['w'] = 'com o'
    if norm(w['w']) == 'ele' and i + 1 < len(WORDS) and norm(WORDS[i + 1]['w']) == 'gravou':
        SKIP.add(i)                      # "ele" antes de "gravou" é apoio da fala, fora da legenda
    if norm(w['w']) == 'a' and i > 0 and WORDS[i - 1]['w'] == 'pra' and i + 1 < len(WORDS) and norm(WORDS[i + 1]['w']) == 'gente' and WORDS[i - 1]['s'] > 15:
        SKIP.add(i)                      # "pra a gente" → "pra gente" (como ele fala)
SIZES = [3, 3, 1, 3, 4, 4, 3, 3, 2, 3, 2, 2, 3, 3, 4, 3, 3, 2, 4, 4, 2, 4, 3, 3, 3, 3, 3, 3, 3, 4, 2, 3, 4, 3, 2, 3]
assert sum(SIZES) == len(WORDS), (sum(SIZES), len(WORDS), [w['w'] for w in WORDS])
EMPH_G = {1: 'caríssimo', 8: 'institucionais', 10: 'Cortez.', 12: 'plataformas,', 13: 'print,', 15: 'tela', 17: 'propaganda', 21: 'outros',
          23: 'institucionais.', 25: 'negócio,', 26: 'site.', 30: 'software,', 33: 'maravilha', 35: 'precisa.'}
groups, k0 = [], 0
for n in SIZES:
    groups.append([(i, WORDS[i]) for i in range(k0, k0 + n) if i not in SKIP]); k0 += n
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0][1]['s']
    nxt = groups[i + 1][0][1]['s'] if i + 1 < len(groups) else None
    e = nxt if nxt is not None and nxt - gw[-1][1]['e'] < 0.5 else gw[-1][1]['e'] + 0.25
    e = min(e, SPEECH)
    kidx = next((j for j, (_, x) in enumerate(gw) if x['w'] == EMPH_G[i]), None) if i in EMPH_G else None
    if i in EMPH_G and kidx is None:
        raise SystemExit(f'ênfase {EMPH_G[i]!r} não está no grupo {i}: {[x["w"] for _, x in gw]}')
    parts = [f'<span class="cw{" k" if j == kidx else ""}" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, (_, x) in enumerate(gw)]
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl">{" ".join(parts)}</span></div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'w': [{'s': x['s'], 'k': j == kidx} for j, (_, x) in enumerate(gw)],
                      'text': ' '.join(x['w'] for _, x in gw), 'emphasis': gw[kidx][1]['w'] if kidx is not None else None})

seq = {}
for d in sorted((C / 'assets/seq').iterdir()):
    if d.is_dir():
        seq[d.name] = {'n': len(list(d.glob('*.jpg'))), 'fps': 15 if d.name[:2] in ('c_', 'v_') else 30}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'cta': CTA_MODE,
        'check': [{'text': c[0], 'in': round(c[1], 3), 'tick': round(c[2], 3)} for c in CHECK], 'ckEnd': round(CK_END, 3)}
ck_html = ''.join(f'<div class="ck" id="ck{i}"><span class="bx"><svg viewBox="0 0 30 30"><path d="M7 15.5 L13 21 L23 9" /></svg></span>'
                  f'<span class="ct">{html.escape(c[0])}</span></div>' for i, c in enumerate(CHECK))
out = (J / 'src/index.tpl.html').read_text()
out = (out.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{CHECK}}', ck_html).replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH:.3f}').replace('{{CTAMODE}}', CTA_MODE))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

SUF = '-comment' if CTA_MODE == 'comment' else ''
scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'check', 'start': round(CHECK[0][1], 3), 'end': round(CK_END, 3), 'label': 'O Cortez, sozinho', 'title': ' / '.join(c[0] for c in CHECK)})
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)',
               'title': 'Seu institucional, feito pelo Cortez. / Você pede. O Cortez faz. Você aprova. / ' + ('Comente CORTEZ' if CTA_MODE == 'comment' else 'Saiba mais')})
scenes.sort(key=lambda x: x['start'])
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V1', 'cta': CTA_MODE,
    'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: RenderPass, UnrealBloomPass suave, BokehPass, OutputPass) via hf-seek',
    'identity': 'IDP02', 'caption_style': 'L07', 'format': 'F22 f22-corte-de-live-3d-v1',
    'determinism': 'tudo em função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['gancho: placa de vidro preto com o motion pronto do PRODUTO (colagem 3D dos módulos)',
                 'constelação de 12 motions institucionais no escuro, ligados por linhas finas; varredura carimba "feito pelo Cortez" em cada um',
                 'ponto de vista do agente: mira "Cortez" entra no módulo PRODUTO dentro da plataforma; print com flash e recorte que levanta',
                 'gravação de tela: selo REC com contador e tira de quadros saindo da tela',
                 'montagem: print + quadros convergem e o motion pronto aparece numa varredura (interface crua → motion com título)',
                 'o mesmo trecho encaixa dentro do vídeo do PRODUTO ("usado dentro de outros vídeos")',
                 'monólitos verticais de vidro preto sobem do chão com os motions 9:16 (negócio, site, ferramentas, software); câmera sobe e revela a constelação'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
print(json.dumps(T))
for c in caps_data:
    print(c['s'], c['e'], c['text'], '|', c['emphasis'])
