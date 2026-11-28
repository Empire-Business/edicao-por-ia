#!/usr/bin/env python3
"""EXEMPLO_1 — monta comp/index.html a partir de src/index.tpl.html + tempos reais da voz (analysis/voice_words.json).
CTA=comment (variável de ambiente) gera a variante "Comente CORTEZ"; padrão = "Saiba mais".
Saídas: comp/index.html, analysis/motion_plan[-comment].json, analysis/caption_groups.json, analysis/scene_plan[-comment].json.
Run: ../../../.venv/bin/python src/build.py
"""
import json, os, re
from pathlib import Path

J = Path(__file__).resolve().parents[1]
FPS = 30
CTA = os.environ.get('CTA', 'saiba')
SUF = '-comment' if CTA == 'comment' else ''
V = json.loads((J / 'analysis/voice_words.json').read_text())
W = V['words']
q = lambda x: round(round(x * FPS) / FPS, 4)


def at(word, after=0.0, src=None):
    for w in W:
        if w['w'].lower().strip('?,.…!') == word.lower() and w['s'] >= after and (src is None or w['src'] == src):
            return w['s']
    raise KeyError(word)


def end_of(word, after=0.0):
    for w in W:
        if w['w'].lower().strip('?,.…!') == word.lower() and w['s'] >= after:
            return w['e']
    raise KeyError(word)


T = {}
T['raw_end'] = 2.12
T['travou'] = at('Travou'); T['gague'] = at('Gaguejou'); T['repetiu'] = at('Repetiu'); T['mesma'] = at('mesma')
T['frase1'] = at('frase', T['mesma']); T['tres'] = at('três'); T['vezes'] = at('vezes'); T['relaxa'] = at('Relaxa')
T['eu1'] = at('Eu', T['relaxa']); T['cortez'] = at('Cortez', T['relaxa']); T['ia'] = at('inteligência'); T['edita'] = at('edita'); T['video'] = at('vídeo', T['edita'])
T['eu2'] = at('Eu', T['video']); T['encontro'] = at('encontro'); T['erros'] = at('erros'); T['tiro'] = at('tiro')
T['deixo'] = at('deixo'); T['melhor'] = at('melhor'); T['versao'] = at('versão'); T['frase2'] = at('frase', T['versao'])
T['eb0'] = V['eb0']; T['eb1'] = V['eb1']; T['ninguem'] = at('Ninguém'); T['errou'] = at('errou'); T['so'] = at('Só', T['errou']); T['eu3'] = at('eu', T['so'])
T['speech_end'] = round(end_of('eu', T['so']), 3)
T['cta0'] = q(T['speech_end'] + 0.32)
T['end'] = q(T['cta0'] + 4.6)
T['tap'] = round(T['cta0'] + 2.75, 3)
for k in list(T):
    T[k] = round(T[k], 4)

# legendas L06 ("frase que se constrói"): blocos de até 5 palavras, quebrando na pontuação; sem legenda sobre a entrega (ela tem a dela)
groups, cur = [], []
for w in W:
    if w['src'] == 'entrega':
        if cur: groups.append(cur); cur = []
        continue
    if cur and cur[-1]['src'] != w['src']:
        groups.append(cur); cur = []
    cur.append(w)
    if len(cur) >= 5 or w['w'].endswith(('?', '.', ',', '…')) and len(cur) >= 2 or w['w'].endswith(('?', '.')):
        groups.append(cur); cur = []
if cur: groups.append(cur)
CAPS = []
for i, g in enumerate(groups):
    s = g[0]['s'] - 0.04
    nxt = next((gg[0]['s'] for gg in groups[i + 1:]), None)
    e = g[-1]['e'] + 0.32
    if nxt is not None and nxt - 0.03 < e + 0.6:
        e = min(e + 0.6, nxt - 0.1)
    if g[-1]['src'] == 'bruto':
        e = min(e, T['travou'] - 0.02)
    CAPS.append({'s': round(s, 3), 'e': round(min(e, T['cta0'] - 0.05), 3), 'w': [{'t': x['w'], 's': x['s']} for x in g]})
(J / 'analysis/caption_groups.json').write_text(json.dumps(CAPS, ensure_ascii=False, indent=1))

LABS = [('Gravação bruta real · tomada 2', 0.0, T['travou'] - 0.05), ('Os erros da gravação', T['travou'], T['relaxa'] - 0.1),
        ('Cortez · IA que edita vídeo', T['eu1'], T['eu2'] - 0.05), ('Encontrando os erros', T['eu2'], T['deixo'] - 0.05),
        ('Só a melhor versão', T['deixo'], T['eb0'] - 0.05), ('Depois · editado pelo Cortez', T['eb0'], T['eb1'] + 0.1)]
LABS = [{'t': a, 's': round(b, 3), 'e': round(c, 3)} for a, b, c in LABS]

DATA = {'T': T, 'caps': CAPS, 'labs': LABS, 'cta': CTA,
        'seq': json.loads((J / 'analysis/proof_assets.json').read_text())['frames']}
tpl = (J / 'src/index.tpl.html').read_text()
labs_html = ''.join(f'<div class="lab" id="lab{i}"><span class="in"><i></i>{l["t"]}</span></div>' for i, l in enumerate(LABS))
caps_html = ''.join(f'<div class="cap" id="cap{i}"><span class="cl">' + ' '.join(f'<span class="w" id="cw{i}_{k}">{w["t"]}</span>' for k, w in enumerate(c['w'])) +
                    '</span></div>' for i, c in enumerate(CAPS))
html = (tpl.replace('{{DATA}}', json.dumps(DATA, ensure_ascii=False)).replace('{{DUR}}', f"{T['end']:.3f}")
        .replace('{{LABS}}', labs_html).replace('{{CAPS}}', caps_html).replace('{{CTAMODE}}', CTA))
(J / 'comp/index.html').write_text(html)
mp = {'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'format': 'F10', 'identity': 'IDP02', 'caption_style': 'L06', 'cta': CTA, 'T': T,
      'determinism': 'tudo em função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; Math.random com semente',
      'three_js': ['quatro vidros 9:16 com as tomadas reais da gravação bruta (trava, gagueira, repetida, melhor) num vazio preto',
                   'fileira das três tomadas da mesma frase', 'linha de luz de corte (cut_light da IDP02) varrendo os vidros',
                   'vidros com erro saem; a melhor tomada vira a entrega EXEMPLO_2', 'pilha secreta dos vidros descartados no escuro']}
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps(mp, ensure_ascii=False, indent=1))
scenes = [{'id': 'gancho', 'start': 0.0, 'end': T['travou'], 'what': 'a tomada real que trava ("Tem consultor com 15 anos de mercado, que…") no vidro da frente'},
          {'id': 'travou', 'start': T['travou'], 'end': T['gague'], 'what': 'o vidro congela; etiqueta TRAVOU'},
          {'id': 'gaguejou', 'start': T['gague'], 'end': T['repetiu'], 'what': 'o vidro da gagueira real ("É assim… é assim que…") vem para a frente'},
          {'id': 'repetiu', 'start': T['repetiu'], 'end': T['relaxa'], 'what': 'as três tomadas reais da mesma frase lado a lado, 1ª 2ª 3ª'},
          {'id': 'relaxa', 'start': T['relaxa'], 'end': T['eu1'], 'what': 'tudo desacelera e escurece; "Relaxa."'},
          {'id': 'cortez', 'start': T['eu1'], 'end': T['eu2'], 'what': 'leque de vidros; linha de luz de corte varre todos'},
          {'id': 'erros', 'start': T['eu2'], 'end': T['tiro'], 'what': 'faixas bordô ERRO em três vidros'},
          {'id': 'tiro', 'start': T['tiro'], 'end': T['deixo'], 'what': 'os três vidros com erro saem'},
          {'id': 'melhor', 'start': T['deixo'], 'end': T['eb0'], 'what': 'a melhor tomada da frase da gagueira vem para o centro (MELHOR TOMADA)'},
          {'id': 'depois', 'start': T['eb0'], 'end': T['eb1'], 'what': 'a linha de luz transforma o vidro na entrega EXEMPLO_2 quase em tela cheia (apresentador na câmera, frase limpa, som dela)'},
          {'id': 'ninguem', 'start': T['ninguem'], 'end': T['so'], 'what': 'a câmera recua; os vidros descartados aparecem no escuro, atrás'},
          {'id': 'so_eu', 'start': T['so'], 'end': T['cta0'], 'what': 'só a pilha descartada recebe um brilho; "Só eu."'},
          {'id': 'cta', 'start': T['cta0'], 'end': T['end'], 'what': 'CTA escrito ' + ('"Comente CORTEZ"' if CTA == 'comment' else '"Saiba mais"')}]
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
print(json.dumps({'end': T['end'], 'cta0': T['cta0'], 'caps': len(CAPS), 'cta': CTA}))
