#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da narração (analysis/voice_words.json), do envelope real da
gravação bruta (analysis/raw_wave.json) e de src/index.tpl.html. F10 + ID06 Azul Claro + legenda L03 (uma palavra por vez; palavras de
função curtíssimas vão junto da seguinte). Estilo deste criativo: "dentro da pasta" — a pasta 01 e a pasta 02 numa mesa clara, ligadas por
um tubo de vidro (o caminho); a câmera mergulha no tubo e, lá dentro (escuro), o vídeo bruto real atravessa os portões do Cortez e sai pronto
pela pasta 02. CTA=comment gera a variante "Comente CORTEZ"; padrão = "Saiba mais".
Grava analysis/scene_plan*.json, analysis/motion_plan*.json e analysis/caption_groups*.json.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
V = json.loads((J / 'analysis/voice_words.json').read_text())
RW = json.loads((J / 'analysis/raw_wave.json').read_text())
WORDS = V['words']
N0 = V['n0']
FPS = 30
q = lambda x: round(round(x * FPS) / FPS, 4)
SE = V['speech_end']
CTA0 = q(SE + 0.15)
CTA_S = 4.6
DUR = q(CTA0 + CTA_S)
MODE = os.environ.get('CTA', 'saiba')
assert MODE in ('saiba', 'comment'), MODE
SUF = '' if MODE == 'saiba' else '-comment'


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0, end=False):
    for x in WORDS:
        if x['s'] >= after - 0.02 and norm(x['w']) == norm(word):
            return x['e'] if end else x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


T = {'n0': N0, 'pasta1': W('pasta'), 'comp_end': W('computador', end=True), 'voce': W('você'), 'video1': W('vídeo'), 'bruto': W('bruto')}
T['pasta2'] = W('pasta', T['bruto']); T['um'] = W('um', T['pasta2']); T['um_end'] = W('um', T['pasta2'], end=True)
T['video2'] = W('vídeo', T['um']); T['pronto'] = W('pronto', T['um']); T['aparece'] = W('aparece', T['pronto']); T['pasta3'] = W('pasta', T['aparece'])
T['dois'] = W('dois', T['pasta3']); T['dois_end'] = W('dois', T['pasta3'], end=True)
T['no'] = W('no', T['dois']); T['caminho'] = W('caminho', T['no']); T['caminho_end'] = W('caminho', T['no'], end=True)
T['limpo'] = W('limpo', T['caminho']); T['audio'] = W('áudio', T['limpo']); T['audio_end'] = W('áudio', T['limpo'], end=True)
T['corto'] = W('corto', T['audio']); T['silencios'] = W('silêncios', T['corto']); T['erros'] = W('erros', T['silencios'])
T['erros_end'] = W('erros', T['silencios'], end=True)
T['procuro'] = W('procuro', T['erros']); T['cenas'] = W('cenas', T['procuro']); T['coloco'] = W('coloco', T['cenas'])
T['legenda'] = W('legenda', T['coloco']); T['musica'] = W('música', T['legenda']); T['animacao'] = W('animação', T['musica'])
T['animacao_end'] = W('animação', T['musica'], end=True)
T['sem1'] = W('sem', T['animacao']); T['programa'] = W('programa', T['sem1']); T['edicao'] = W('edição', T['programa'])
T['edicao_end'] = W('edição', T['programa'], end=True)
T['sem2'] = W('sem', T['edicao']); T['linha'] = W('linha', T['sem2']); T['tempo'] = W('tempo', T['linha']); T['tempo_end'] = W('tempo', T['linha'], end=True)
T['eu3'] = W('eu', T['tempo']); T['cortez'] = W('cortez', T['eu3'])
# transições de cenário (ocorrem sob a cortina escura / clara)
T['tube0'] = round(T['dois'] - 0.45, 3)                     # o tubo de vidro cresce de 01 até 02
T['dive0'] = round(T['no'] - 0.05, 3)                       # mergulho no meio do caminho
T['tun'] = round(T['caminho_end'] + 0.02, 3)                # troca para o túnel (cortina escura no máximo)
T['exit'] = round(T['eu3'] - 0.07, 3)                       # saída pela pasta 02 (cortina clara no máximo)
T.update({'speechEnd': SE, 'cta0': CTA0, 'end': DUR, 'tap': round(CTA0 + 2.95, 3), 'type2': round(CTA0 + 1.95, 3)})
assert T['tube0'] < T['dive0'] < T['tun'] < T['limpo'] < T['corto'] < T['procuro'] < T['legenda'] < T['sem1'] < T['sem2'] < T['exit'] < SE, T

# ---------- trilha da gravação bruta real (0,90–9,90 s) dentro do túnel ----------
segs = []
for b in RW['blocks']:
    s = max(0.0, b['s'] - RW['raw_from_s']); e = min(9.0, b['e'] - RW['raw_from_s'])
    if e - s > 0.05:
        segs.append({'k': b['k'], 's': round(s, 3), 'e': round(e, 3), 'txt': b['txt']})
# buracos sem bloco (entre os blocos medidos) contam como silêncio
full, t0 = [], 0.0
for sg in segs:
    if sg['s'] - t0 > 0.05:
        full.append({'k': 'sil', 's': round(t0, 3), 'e': sg['s'], 'txt': 'silêncio'})
    full.append(sg); t0 = sg['e']
if 9.0 - t0 > 0.05:
    full.append({'k': 'sil', 's': round(t0, 3), 'e': 9.0, 'txt': 'silêncio'})
KEEP = [i for i, s in enumerate(full) if s['k'] == 'keep']
assert len(KEEP) == 1, full
keep = full[KEEP[0]]

# ---------- rótulos (canto superior esquerdo) ----------
LABS = [('Seu computador · pasta do Cortez', 0.0, T['dive0'] + 0.25, ''), ('Dentro da pasta · 01 · áudio', T['tun'] + 0.12, T['corto'] - 0.1, 'dk'),
        ('02 · silêncios e erros', T['corto'] - 0.1, T['procuro'] - 0.1, 'dk'), ('03 · cenas', T['procuro'] - 0.1, T['coloco'] - 0.1, 'dk'),
        ('04 · legenda · música · animação', T['coloco'] - 0.1, T['sem1'] - 0.1, 'dk'), ('Sem programa · sem linha do tempo', T['sem1'] - 0.1, T['exit'] - 0.1, 'dk'),
        ('Pasta 02 · vídeo pronto', T['exit'] + 0.2, CTA0, '')]
labs_html = '\n  '.join(f'<div class="lab {cl}" id="lab{i}"><span class="in"><i></i>{html.escape(tx)}</span></div>' for i, (tx, a, b, cl) in enumerate(LABS))
labs = [{'s': round(a, 3), 'e': round(b, 3)} for _, a, b, _ in LABS]

# ---------- legenda L03: uma palavra por vez (palavras de função curtas grudam na seguinte) ----------
WEAK = {'o', 'a', 'os', 'as', 'do', 'da', 'de', 'na', 'no', 'e', 'um', 'eu', 'seu', 'numa', 'sem'}
units, i = [], 0
while i < len(WORDS):
    w = WORDS[i]; u = [w]
    if norm(w['w']) in WEAK and w['w'][-1] not in '.,?!' and i + 1 < len(WORDS) and WORDS[i + 1]['s'] - w['e'] < 0.2:
        u.append(WORDS[i + 1]); i += 1
        if norm(u[-1]['w']) in WEAK and u[-1]['w'][-1] not in '.,?!' and i + 1 < len(WORDS) and WORDS[i + 1]['s'] - u[-1]['e'] < 0.2:
            u.append(WORDS[i + 1]); i += 1
    units.append(u); i += 1
HIDE = lambda u: u[-1]['e'] <= T['comp_end'] + 0.01 or u[0]['s'] >= T['eu3'] - 0.01
EMPH = {'pasta', 'bruto', 'pronto', 'caminho', 'audio', 'silencios', 'erros', 'cenas', 'legenda', 'musica', 'animacao', 'programa', 'edicao', 'tempo', 'um', 'dois'}
caps_html, caps_data = [], []
vis = [u for u in units if not HIDE(u)]
for k, u in enumerate(vis):
    s = u[0]['s']
    nxt = vis[k + 1][0]['s'] if k + 1 < len(vis) else None
    e = nxt if nxt is not None and nxt - u[-1]['e'] < 0.45 else u[-1]['e'] + 0.22
    e = min(e, SE + 0.1, T['eu3'] - 0.02 if u[-1]['e'] < T['eu3'] else 99)
    txt = ' '.join(x['w'].rstrip(',.') for x in u)
    em = any(norm(x['w']) in EMPH for x in u)
    dark = bool(T['tun'] <= s < T['exit'])
    caps_html.append(f'<div class="cap{" em" if em else ""}{" dark" if dark else ""}" id="cg{k}">{html.escape(txt)}</div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3), 'text': txt, 'dark': dark})

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'labs': labs, 'caps': caps_data, 'seq': seq, 'cta': MODE, 'segs': full, 'keep': keep,
        'wave_raw': RW['wave_raw'], 'wave_clean': RW['wave_clean'], 'broll': ['agenda', 'reuniao', 'escritorio', 'callcenter']}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{LABS}}', labs_html)
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{CTACSS}}', '#btn { display:none; }' if MODE == 'comment' else '#cmh, #cmf, #cms { display:none; }'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [
    {'id': 'hook', 'start': 0, 'end': T['comp_end'], 'label': 'Seu computador', 'what': 'close na pasta 01 (3D) com o título "Eu moro numa pasta do seu computador."; a aba frontal abre e mostra o interior azul'},
    {'id': 'drop', 'start': T['voce'], 'end': T['um_end'], 'label': 'Seu computador', 'what': 'o vídeo bruto real (cinza, granulado, tocando) aparece sobre a pasta 01 e cai dentro dela'},
    {'id': 'appear', 'start': T['video2'], 'end': T['dois_end'], 'label': 'Seu computador', 'what': 'a câmera vai até a pasta 02: a entrega EXEMPLO_2 sobe de dentro dela; o tubo de vidro (o caminho) liga as duas pastas'},
    {'id': 'dive', 'start': T['no'], 'end': T['tun'], 'label': 'Seu computador', 'what': 'no "meio do caminho" a câmera mergulha no tubo'},
    {'id': 'tunnel', 'start': T['tun'], 'end': T['sem1'], 'label': 'Dentro da pasta', 'what': 'túnel escuro com portões: 01 o envelope cinza vira limpo · 02 silêncios e erros reais caem e a trilha fecha (o vídeo pula para a fala boa) · 03 cenas do EXEMPLO_2 saem das paredes e entram na trilha · 04 a face vira a entrega EXEMPLO_2 (legenda), as barras viram música, o cartão gira (animação)'},
    {'id': 'nolinear', 'start': T['sem1'], 'end': T['exit'], 'label': 'Sem programa · sem linha do tempo', 'what': 'um painel genérico de programa de edição (sem marca) tomba e some; a própria trilha recolhe; o cartão acelera para a luz'},
    {'id': 'exit', 'start': T['exit'], 'end': SE, 'label': 'Pasta 02 · vídeo pronto', 'what': 'a entrega EXEMPLO_2 sai pela pasta 02, grande, com o título "Eu sou o Cortez."'},
    {'id': 'cta', 'start': CTA0, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'what': 'Joga o bruto. Pega pronto. / Você grava. O Cortez edita. Você aprova. / ' +
     ('Comente CORTEZ (balão) + campo de comentário com CORTEZ digitado e enviado + "aqui nos comentários" ↓' if MODE == 'comment' else 'Saiba mais')}]
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / f'analysis/caption_groups{SUF}.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V1', 'cta': MODE, 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Bokeh + Output) via hf-seek',
    'identity': 'ID06', 'caption_style': 'L03', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['duas pastas 3D (painel de trás azul, aba frontal com dobradiça) numa mesa clara com sombras reais', 'tubo de vidro (o caminho) com o fluxo de dados indo da 01 para a 02',
                 'túnel escuro de costelas arredondadas com quatro portões rotulados', 'cartão 9:16 com a gravação bruta real tocando + envelope real (bruto → limpo) + trilha com os silêncios/erros reais',
                 'cenas do EXEMPLO_2 nas paredes do túnel; painel genérico de programa de edição que tomba', 'saída pela pasta 02 com a entrega EXEMPLO_2'],
    'T': T, 'labs': labs, 'seq': seq, 'segs': full, 'cta_seconds': CTA_S}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'caps': len(caps_data), 'T': {k: round(v, 2) for k, v in T.items()}}, ensure_ascii=False))
print([ (s['k'], s['s'], s['e']) for s in full])
for c in caps_data:
    print(c['s'], c['e'], c['text'], 'D' if c['dark'] else '')
