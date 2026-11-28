#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
F22 Corte de Live 3D + ID07 Laranja + legenda L05 (caixa laranja que passa de palavra em palavra, blocos de até 4 palavras).
Estilo novo: "o arquivo do Cortez" — uma parede monumental de gavetas de arquivo num salão escuro (azul-tinta #101828 da ID); cada gaveta
que abre entrega fichas com a prova real: NOTÍCIAS (prints de matérias usadas no LONGO_1), PRINTS (telas reais dos produtos no EXEMPLO_2),
BANCO DE IMAGENS (fichas cinzas genéricas que levam o carimbo e a gaveta bate), CENAS (as cenas que o Cortez achou para o EXEMPLO_3), e no fim
as gavetas abrem em onda e sobem 15 entregas reais formando um mural.
Tempos = palavras realmente faladas na voz final; o texto das legendas usa as palavras conferidas na fonte (Whisper: "a roda" →
"rodando", "e editou o" → "de editor", pontuação das frases).
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
T = {'repara': W('Repara'), 'qual2': W('qualidade'), 'colocou': W('colocou'), 'animac': W('animaçõezinhas'), 'aleat': W('aleatórias'),
     'como1': W('como'), 'insta': W('Instagram'), 't02': TS['t02'], 'aqui2': W('aqui', TS['t02'] + 0.3), 'pesquisas': W('pesquisas'),
     'cenas': W('cenas'), 'internet': W('internet'), 't03': TS['t03'], 'ele1': W('Ele', TS['t03'] - 0.3), 'noticias': W('notícias'),
     'ele2': W('ele', TS['t03'] + 2.0), 'prints': W('prints'), 'reais': W('reais'), 't04': TS['t04'], 'nao': W('não', TS['t04'] - 0.1),
     'imagens1': W('imagens', TS['t04']), 'genericas': W('genéricas'), 'banco': W('banco'), 'imagens2': W('imagens', W('banco')),
     't05': TS['t05'], 'ja': W('Já'), 'resultados': W('resultados'), 'cortez': W('Cortez'), 'saiu': W('saiu'), 'extrema': W('extrema'),
     'qual3': W('qualidade', W('saiu')), 'editor': W('editou'), 'prof': W('profissional'),
     'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['aqui1'] = TS['t02']
T['tap'] = round(SPEECH + 2.9, 3)
T['type0'] = round(SPEECH + 1.75, 3)
T = {k: round(v, 3) for k, v in T.items()}

# títulos: rótulo (mono, laranja) + até 2 linhas (Inter 800); o fim em laranja
HEADS = [
    ('h1', 0, T['colocou'] - 0.25, 'Editado pelo Cortez', 84, [('Repara na', 0), ('<em>qualidade.</em>', 0)]),
    ('h2', T['colocou'] - 0.2, T['t02'] - 0.06, 'O Cortez', 84, [('Sem animação', T['colocou'] - 0.1), ('<em>aleatória.</em>', T['aleat'] - 0.15)]),
    ('h3', T['t02'] + 0.04, T['t03'] - 0.06, 'Aqui não', 84, [('Cenas reais', T['cenas'] - 0.35), ('<em>da internet.</em>', T['internet'] - 0.2)]),
    ('h4', T['t03'] + 0.04, T['ele2'] - 0.06, 'O Cortez pesquisou', 84, [('Notícias', T['noticias'] - 0.25), ('<em>reais.</em>', T['noticias'] + 0.1)]),
    ('h5', T['ele2'] + 0.04, T['t04'] + 0.02, 'O Cortez pesquisou', 84, [('Prints', T['prints'] - 0.2), ('<em>reais.</em>', T['reais'] - 0.15)]),
    ('h6', T['t04'] + 0.1, T['t05'] - 0.05, 'Nada de', 84, [('Banco de', T['banco'] - 0.3), ('<em>imagens.</em>', T['imagens2'] - 0.25)]),
    ('h7', T['t05'] + 0.04, T['saiu'] - 0.1, 'Vídeos editados pelo Cortez', 84, [('Vários', T['ja'] + 0.25), ('<em>resultados.</em>', T['resultados'] - 0.1)]),
    ('h8', T['saiu'] - 0.02, SPEECH + 0.02, 'Vídeos editados pelo Cortez', 66, [('Qualidade de editor', T['qual3'] - 0.2), ('<em>profissional.</em>', T['prof'] - 0.2)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, fs, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}" style="font-size:{fs}px"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legenda L05: blocos de até 4 palavras pelo sentido; a caixa laranja passa de palavra em palavra
FIX = {9: 'aleatórias,', 19: 'Instagram.', 21: 'Aqui', 22: 'não.', 23: 'Aqui', 32: 'internet.', 35: 'notícias.', 36: 'Ele', 39: 'reais.',
       40: 'Não', 48: 'imagens.', 52: 'resultados,', 56: 'fez,', 62: 'de', 63: 'editor', 65: 'profissional.'}
for i, x in FIX.items():
    WORDS[i]['w'] = x
SKIP = set()
for i, w in enumerate(WORDS):
    if norm(w['w']) == 'roda':
        w['w'] = 'rodando'
        if norm(WORDS[i - 1]['w']) == 'a':
            SKIP.add(i - 1)
            w['s'] = WORDS[i - 1]['s']       # "a roda" (Whisper) = "rodando": a caixa entra no começo real da palavra
    if i > 0 and norm(w['w']) == 'o' and norm(WORDS[i - 1]['w']) == 'editor':
        SKIP.add(i)                          # "e editou o profissional" (Whisper) = "de editor profissional"
    if norm(w['w']) == 'isso' and i + 1 < len(WORDS) and norm(WORDS[i + 1]['w']) == 'aqui':
        SKIP.add(i); WORDS[i + 1]['s'] = w['s']   # o 1º "Aqui" saiu "Isso aqui" no Whisper: a caixa entra no começo real
SIZES = [3, 4, 2, 1, 4, 4, 2, 3, 4, 4, 2, 3, 2, 2, 3, 2, 4, 2, 2, 4, 4, 3, 2]
assert sum(SIZES) == len(WORDS), (sum(SIZES), len(WORDS), [w['w'] for w in WORDS])
groups, k0 = [], 0
for n in SIZES:
    g = [(i, WORDS[i]) for i in range(k0, k0 + n) if i not in SKIP]
    groups.append(g); k0 += n
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0][1]['s']
    nxt = groups[i + 1][0][1]['s'] if i + 1 < len(groups) else None
    e = nxt if nxt is not None and nxt - gw[-1][1]['e'] < 0.5 else gw[-1][1]['e'] + 0.25
    e = min(e, SPEECH)
    ws = []
    for j, (_, x) in enumerate(gw):
        we = gw[j + 1][1]['s'] if j + 1 < len(gw) else e
        ws.append({'s': x['s'], 'e': round(we, 3)})
    parts = [f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, (_, x) in enumerate(gw)]
    caps_html.append(f'<div class="cap" id="cg{i}">{" ".join(parts)}</div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'w': ws, 'text': ' '.join(x['w'] for _, x in gw)})

seq = {}
for d in sorted((C / 'assets/seq').iterdir()):
    if d.is_dir():
        seq[d.name] = {'n': len(list(d.glob('*.jpg'))), 'fps': 30 if d.name in ('h_hook', 'r_e91', 'e117') else 15}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'cta': CTA_MODE}
out = (J / 'src/index.tpl.html').read_text()
out = (out.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{SPEECH}}', f'{SPEECH:.3f}').replace('{{CTAMODE}}', CTA_MODE))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

SUF = '-comment' if CTA_MODE == 'comment' else ''
scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[5])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)',
               'title': 'Pesquisa de verdade. / Edição de editor. / Notícias, prints e cenas reais. Sem cara de banco de imagens. / ' + ('Comente CORTEZ' if CTA_MODE == 'comment' else 'Saiba mais')})
scenes.sort(key=lambda x: x['start'])
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V2', 'cta': CTA_MODE,
    'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: RenderPass, UnrealBloomPass suave, BokehPass, OutputPass) via hf-seek',
    'identity': 'ID07', 'caption_style': 'L05', 'format': 'F22 f22-corte-de-live-3d-v1',
    'determinism': 'tudo em função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['<PREENCHER: fonte ou prova própria>',
                 'parede monumental de 35 gavetas de arquivo (azul-tinta, laca com verniz, etiquetas em fonte mono, puxadores)',
                 'gaveta NOTÍCIAS abre: a ficha do gancho é arquivada e 3 prints de matérias sobem em leque',
                 'gaveta PRINTS: 3 telas reais dos produtos do usuário (EXEMPLO_2) sobem',
                 'gaveta BANCO DE IMAGENS: fichas cinzas genéricas sobem sem vida, levam o carimbo GENÉRICO e a gaveta bate',
                 'repara: entrega 9:16 (EXEMPLO_4) sobe à frente; chips cinzas de "animação pronta" tentam grudar e caem riscados',
                 'gaveta CENAS: as cenas reais que o Cortez achou para o EXEMPLO_3 sobem e entram na tela, que passa a tocar o EXEMPLO_3',
                 'resultados: as gavetas abrem em onda e 15 entregas reais sobem formando um mural curvo; varredura laranja no "Cortez"; a câmera entra na do centro'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data)}, ensure_ascii=False))
print(json.dumps(T))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
