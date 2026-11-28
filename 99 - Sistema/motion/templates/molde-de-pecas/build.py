#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir da voz final, da transcrição alinhada e de src/index.tpl.html.
IDP01 Navy e Dourado + legenda L08 (contorno reforçado, até 5 palavras por bloco, palavra falada em ouro).
Ideia: o vídeo é montado peça por peça como um mosaico 9:16 de 7 blocos (voz, capa, thumbnail, legenda, cena, trilha, animação);
cada peça entra na palavra em que é citada; em "uma inteligência artificial que edita vídeo" os blocos viram em onda e o verso de todos
forma um único vídeo pronto (entrega real do Cortez); "do começo ao fim" a barra de progresso enche; "Você só grava" → botão REC;
"Ou nem isso" → o REC some e um vídeo narrado por IA, sem gravação (exemplo do F13 feito pelo Cortez), toca sozinho.
CTA=comment gera a variante "Comente CORTEZ" numa comp separada (comp-cta-comment) com os mesmos materiais.
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cta as CTAm

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
HIT_TRACK = 16.81                       # batida forte da faixa (volta depois da pausa em 16 s)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0, end=False):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['e'] if end else x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


T = {'voz': W('voz'), 'ouv': W('ouvindo'), 'fui': W('fui'), 'gerei': W('gerei'), 'capaA': W('a', 3.0), 'capa': W('capa'), 'faco_eu': W('eu', 4.4),
     'faco': W('faco'), 'thumb': W('thumbnail'), 'leg': W('legenda'), 'cena': W('cena'), 'mus': W('musica'), 'anim': W('animacao'),
     'animE': W('animacao', end=True), 'eusou': W('eu', 9.5), 'cortez': W('cortez'), 'uma': W('uma'), 'edita': W('edita'), 'do': W('do', 13.7),
     'fim': W('fim'), 'fimE': W('fim', end=True), 'voce': W('voce', 15.0), 'grava': W('grava'), 'ou': W('ou', 16.5), 'nem': W('nem', 16.8),
     'isso': W('isso', 16.8), 'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['capaFly'] = round(T['faco_eu'] - 0.05, 3); T['capaLand'] = round(T['capaFly'] + 0.62, 3)
for k in ('thumb', 'leg', 'cena', 'mus', 'anim'):
    T['d_' + k] = round(T[k] - 0.14, 3)
T['sweep'] = round(T['eusou'] - 0.08, 3)
T['flip0'] = round(T['uma'] - 0.06, 3)
T['bar0'] = round(T['do'] - 0.05, 3); T['bar1'] = round(T['fimE'], 3)
T['rec0'] = round(T['voce'] - 0.18, 3)
T['recOut'] = round(T['ou'] - 0.06, 3)
T['tap'] = round(SPEECH + 2.75, 3)
T['musicOff'] = round(HIT_TRACK - T['ou'], 3)          # a batida da trilha cai no "Ou nem isso"
assert T['capaLand'] < T['d_thumb'], (T['capaLand'], T['d_thumb'])

HEADS = [
    ('h1', 0, T['fui'] - 0.1, 'Voz gerada por IA', [('Essa <em>voz?</em>', 0)]),
    ('h2', T['fui'] - 0.02, T['capaA'] - 0.08, 'Voz gerada por IA', [('Fui <em>eu.</em>', T['fui'] + 0.02)]),
    ('h3', T['capaA'], T['d_thumb'] - 0.05, 'Capa do vídeo', [('A capa? <em>Também eu.</em>', T['capa'] - 0.1)]),
    ('h4', T['d_thumb'], T['eusou'] - 0.12, 'Peças do vídeo', [('Peça por <em>peça.</em>', T['thumb'] - 0.05)]),
    ('h5', T['eusou'] - 0.05, T['flip0'] + 0.4, 'Inteligência artificial', [('Eu sou o <em>Cortez.</em>', T['eusou'])]),
    ('h6', T['voce'] - 0.05, T['ou'] - 0.12, 'Você', [('Você só', T['voce']), ('<em>grava.</em>', T['grava'] - 0.1)]),
    ('h7', T['ou'] - 0.03, SPEECH - 0.02, 'Ou', [('Ou <em>nem isso.</em>', T['ou'])]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.6, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legendas L08: blocos estáveis de até 5 palavras (quebras nas pausas e vírgulas), palavra falada em ouro
STARTS = {0, 3, 6, 10, 14, 17, 22, 26, 29, 32, 36, 39}
assert len(WORDS) == 42, len(WORDS)
groups, g = [], []
for i, w in enumerate(WORDS):
    if i in STARTS and g:
        groups.append(g); g = []
    g.append(w)
groups.append(g)
assert all(len(x) <= 5 for x in groups)


def lines(ws):
    if len(' '.join(x['w'] for x in ws)) <= 28:
        return [ws]
    best, bi = 1e9, 1
    for k in range(1, len(ws)):
        a = len(' '.join(x['w'] for x in ws[:k])); b = len(' '.join(x['w'] for x in ws[k:]))
        if max(a, b) < best:
            best, bi = max(a, b), k
    return [ws[:bi], ws[bi:]]


caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = 0.0 if i == 0 else gw[0]['s'] - 0.04
    e = groups[i + 1][0]['s'] - 0.04 if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.6 else gw[-1]['e'] + 0.3
    e = min(e, SPEECH)
    ls, j, out = lines(gw), 0, []
    for ln in ls:
        fg = []
        for x in ln:
            fg.append(f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>'); j += 1
        txt = html.escape(' '.join(x['w'] for x in ln))
        out.append(f'<span class="cl"><span class="bk">{txt}</span><span class="fg">{" ".join(fg)}</span></span>')
    top = 1452 - (86 if len(ls) == 2 else 0)
    if T['bar0'] - 0.1 <= s < T['rec0']:
        top = 1356            # a barra de progresso fica na base do quadro
    if s >= T['ou'] - 0.1:
        top = 1484            # abaixo do quadro do F13 (que tem legenda própria)
    caps_html.append(f'<div class="cap" id="cg{i}" style="top:{top}px">{"".join(out)}</div>')
    ww = [x for ln in ls for x in ln]
    caps_data.append({'s': round(s, 3), 'e': round(e, 3),
                      'w': [{'s': x['s'], 'e': round(min(x['e'] + 0.05, ww[k + 1]['s']) if k + 1 < len(ww) else x['e'] + 0.15, 3)} for k, x in enumerate(ww)],
                      'text': ' / '.join(' '.join(x['w'] for x in ln) for ln in ls)})


def env_of(path, n, ss=None, dur=None):
    a = ['ffmpeg', '-v', 'error'] + (['-ss', f'{ss:.3f}', '-t', f'{dur:.3f}'] if ss is not None else []) + ['-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-']
    x = np.frombuffer(subprocess.run(a, capture_output=True, check=True).stdout, np.float32)
    v = np.array([np.sqrt((s_ ** 2).mean() + 1e-12) for s_ in np.array_split(x, n)])
    return x, v


# a voz real vira a placa de ouro: envelope de toda a narração em 150 pontos (suavizado), + envelope por quadro para o pulso
x, wave = env_of(J / 'renders/voice.wav', 150)
wave = np.convolve(wave, np.ones(3) / 3, mode='same'); wave = (wave / wave.max()) ** 0.75
fr = np.array_split(x, int(len(x) / 16000 * 30))
env = np.array([np.sqrt((s_ ** 2).mean() + 1e-12) for s_ in fr]); env = np.clip(env / np.percentile(env, 98), 0, 1)
# trilha real do vídeo (o trecho usado) desenhada no bloco TRILHA
off = max(0.0, T['musicOff'])
_, mw = env_of(MUSIC, 120, off, DUR)
mw = (mw / mw.max()) ** 1.3

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
mode = CTAm.mode()
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'wave': [round(float(v), 4) for v in wave], 'env': [round(float(v), 3) for v in env],
        'music': [round(float(v), 4) for v in mw], 'cta': mode}
tpl = (J / 'src/index.tpl.html').read_text()
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}'))
top = CTAm.layout(mode)
for k, v in CTAm.snippets(mode, top).items():
    out = out.replace('{{' + k + '}}', v)
out = out.replace('{{BTN_TOP}}', str(top))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if mode != 'saiba':
    O = J / f'comp-cta-{mode}'
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir(): d.mkdir(parents=True, exist_ok=True)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            if d.exists(): d.unlink()
            os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': mode, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes += [{'id': 'voz', 'start': 0, 'end': T['fui'], 'label': 'placa de ouro = envelope real da narração, desenhada pela cabeça de leitura'},
           {'id': 'molde', 'start': T['fui'], 'end': T['capaA'], 'label': 'câmera recua: o molde 9:16 com 7 vagas tracejadas; a VOZ já ocupa a primeira'},
           {'id': 'capa', 'start': T['capaA'], 'end': T['capaLand'], 'label': 'capa real feita pelo Cortez (mini curso) perto da câmera → encaixa'},
           {'id': 'pecas', 'start': T['d_thumb'], 'end': T['animE'], 'label': 'thumbnail, legenda, cena (EXEMPLO_2), trilha (disco + onda da trilha real), animação (onion skin) caem nas vagas'},
           {'id': 'flip', 'start': T['flip0'], 'end': T['bar0'], 'label': 'varredura dourada; os 7 blocos viram em onda e o verso forma o vídeo pronto (EXEMPLO_2)'},
           {'id': 'fim', 'start': T['bar0'], 'end': T['rec0'], 'label': 'de frente, sem emendas; barra de progresso do começo ao fim'},
           {'id': 'rec', 'start': T['rec0'], 'end': T['recOut'], 'label': 'botão REC 3D'},
           {'id': 'f13', 'start': T['ou'], 'end': SPEECH, 'label': 'o REC some; vídeo narrado por IA sem gravação (exemplo do F13 feito pelo Cortez) toca sozinho'},
           {'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': f'CTA escrito ({mode})', 'title': 'Do começo ao fim. / Feito pelo Cortez. / Voz, capa, legenda, cena, música e animação.'}]
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: UnrealBloom + Output) via hf-seek',
    'identity': 'IDP01', 'caption_style': 'L08', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['mosaico 9:16 de 7 blocos extrudados (vidro navy, aro dourado)', 'placa de ouro extrudada = envelope real da narração, revelada por plano de recorte',
                 'disco dourado com sulcos (trilha)', 'cubo dourado com rastro onion-skin (animação)', 'virada em onda: verso UV-recortado do mesmo vídeo pronto',
                 'botão REC 3D (toro + disco)', 'molde tracejado das vagas'],
    'T': T, 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'T': {k: T[k] for k in ('fui', 'capaA', 'capaLand', 'd_thumb', 'anim', 'eusou', 'flip0', 'bar0', 'rec0', 'ou', 'musicOff')}}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
