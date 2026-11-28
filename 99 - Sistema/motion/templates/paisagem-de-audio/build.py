#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js r186) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
F22 Corte de Live 3D + ID03 Azul + legenda L06 (frase que se constrói). Tempos = palavras realmente faladas na voz final.
A paisagem 3D usa o envelope REAL do áudio do Convidado na voz final (uma barra por 50 ms do trecho do áudio de WhatsApp).
Texto das legendas: transcrição da voz final conferida com a fonte (FIXES). CTA=comment gera a variante "Comente CORTEZ" em comp-cta-comment/.
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json (só na versão principal).
Run: ../../../.venv/bin/python src/build.py
"""
import html, json, os, re, sys, unicodedata
from pathlib import Path
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cta import snippets

J = Path(__file__).resolve().parent.parent
C = J / 'comp'
EDL = json.loads((J / 'edit/edl.json').read_text())
WORDS = [{'w': w['word'].strip(), 's': round(w['start'], 3), 'e': round(w['end'], 3)}
         for s in json.loads((J / 'analysis/transcript_final_voice.json').read_text())['segments'] for w in s['words']]
SPEECH = EDL['duration']
CTA = 4.6
DUR = round(SPEECH + CTA, 3)
# palavra ouvida pelo Whisper na voz cortada → palavra dita (conferida em transcrições separadas do trecho original e do áudio bruto)
FIXES = [(0.56, 'bravo', 'brabo'), (8.48, 'print', 'prompt'), (15.82, 'tem', 'de'), (17.96, 'e', '')]
for w in WORDS:
    for t, a, b in FIXES:
        if w['w'].rstrip(',.?!') == a and abs(w['s'] - t) < 0.45:
            w['w'] = b + w['w'][len(a):] if b else ''
WORDS = [w for w in WORDS if w['w']]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0):
    n = norm(word)
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == n:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


start_of = {}
for s in EDL['segments']:
    start_of.setdefault(s['take'], s['start'])
T = {'i0': start_of['t01'], 'n0': start_of['t02'], 'b0': start_of['t06'], 'muito': start_of['t05'],
     'craque': W('craque'), 'prompt': W('prompt'), 'estilo': W('estilo', 12.0), 'cor': W('cor', 13.0), 'neg': W('negócio', 14.0),
     'longo': W('longo', 16.0), 'dez': W('10', 18.0), 'bom': W('bom', 19.5), 'sinw': W('sinistro', 20.5),
     'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR}
T['audio'] = W('áudio', 2.5)
T['jr0'] = round(W('Instagram', 18.5) - 0.1, 3); T['jr1'] = round(T['muito'] - 0.05, 3); T['jr2'] = round(W('conseguindo', 30) - 0.15, 3)
T['sin'] = round(T['muito'] + 0.05, 3)          # a câmera começa a subir no "muito"
T['tap'] = round(SPEECH + 2.7, 3)

# envelope real do áudio do Convidado (voz final, trecho do áudio de WhatsApp) — uma barra por 50 ms
sr, x = wavfile.read(J / 'renders/voice.wav')
x = x.astype(np.float32) / 32768
x = x.mean(1) if x.ndim > 1 else x
h = int(sr * 0.05)
a0, a1 = int(T['n0'] * sr), int(T['b0'] * sr)
seg = x[a0:a1]
n = len(seg) // h
db = 20 * np.log10(np.sqrt((seg[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
amp = np.clip((db + 50) / 36, 0, 1) ** 1.25
amp = np.convolve(np.pad(amp, 1, mode='edge'), [0.25, 0.5, 0.25], mode='valid')
AMP = [round(float(v), 3) for v in amp]
src_note = (1691.10, 1736.76)
teaser_frac = round((1724.245 - src_note[0]) / (src_note[1] - src_note[0]), 3)

HEADS = [
    ('h0', 0, T['i0'], 'Áudio real · cliente do Cortez', [('“Caraca, muito', 0), ('<em>brabo mesmo.”</em>', 0)]),
    ('h1', T['i0'] + 0.05, T['n0'], 'Na live do Cortez', [('O áudio de', T['i0'] + 0.15), ('<em>um cliente.</em>', W('áudio', 2.5) - 0.1)]),
    ('h2', T['n0'] + 0.05, start_of['t03'], 'Convidado · cliente do Cortez', [('Tô ficando', T['n0'] + 0.15), ('<em>craque.</em>', T['craque'] - 0.2)]),
    ('h3', start_of['t03'] + 0.05, T['estilo'] - 0.15, 'Pediu pro Cortez', [('Um prompt da', T['prompt'] - 0.25), ('<em>edição favorita.</em>', W('edição', 9.5) - 0.15)]),
    ('h4', T['estilo'] - 0.1, start_of['t04'], 'E pediu pra mudar', [('Outro estilo,', T['estilo']), ('<em>outra cor.</em>', T['cor'] - 0.15)]),
    ('h5', start_of['t04'] + 0.05, T['muito'], 'De 1 vídeo longo', [('Uns 10 cortes', T['longo'] - 0.2), ('<em>pro Instagram.</em>', T['dez'] - 0.1)]),
    ('h6', T['muito'] + 0.05, T['b0'], 'O veredito do Convidado', [('Muito', T['muito'] + 0.1), ('<em>sinistro.</em>', T['sinw'] - 0.12)]),
    ('h7', T['b0'] + 0.05, W('Ele', 26.5) - 0.1, 'Quem é o Convidado', [('Canal Canal do convidado.', T['b0'] + 0.2), ('<em>Comprou o Cortez.</em>', W('comprou', 24) - 0.15)]),
    ('h8', W('Ele', 26.5) - 0.05, SPEECH, 'Quem é o Convidado', [('Não é técnico.', W('não', 27.6) - 0.1), ('<em>E já edita.</em>', W('conseguindo', 30) - 0.15)]),
]
heads_html, heads_data = [], []
for hid, st, en, lab, lines_ in HEADS:
    ls = ''.join(f'<span class="ln" id="{hid}l{j}"><span class="in">{tx}</span></span>' for j, (tx, at) in enumerate(lines_))
    heads_html.append(f'<div class="hd" id="{hid}"><div class="lab"><span class="in"><i></i>{html.escape(lab)}</span></div><div class="ttl">{ls}</div></div>')
    heads_data.append({'id': hid, 'start': round(st, 3), 'end': round(en, 3),
                       'lines': [{'at': round(max(0, at), 3), 'd': round(max(0.25, min(0.7, en - 0.34 - at)), 3)} for tx, at in lines_]})

# legendas L06: blocos de até 5 palavras / ~24 caracteres numa linha; palavras aparecem quando ditas (posição reservada)
spk_at = lambda t: next(s['speaker'] for s in reversed(EDL['segments']) if s['start'] <= t + 1e-6)
mid = lambda w: (w['s'] + w['e']) / 2
units, g = [], []
for w in WORDS:
    if w['s'] < T['i0'] - 0.05:                  # no gancho o título já mostra a frase
        continue
    if g:
        p = g[-1]
        if w['s'] - p['e'] > 0.32 or p['w'][-1] in '.?!' or spk_at(mid(w)) != spk_at(mid(p)):
            units.append(g); g = []
    g.append(w)
if g:
    units.append(g)
FUNC = {'de', 'do', 'da', 'dos', 'das', 'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'com', 'e', 'que', 'no', 'na', 'pra', 'para', 'em',
        'muito', 'tô', 'tá', 'ele', 'eu', 'se', 'por', 'teu', 'meu', 'seu', 'aí', 'já', 'só', 'não', 'é'}
NOBREAK = {('video', 'longo'), ('10', 'cortes'), ('uns', '10'), ('de', 'video'), ('de', 'cor')}
clen = lambda ws: len(' '.join(x['w'] for x in ws))


def chunk(u):
    """divide um bloco de fala em pedaços de até 5 palavras / 26 caracteres, sem terminar pedaço em palavra de ligação e sem palavra solta."""
    n = len(u); best = [0.0] + [1e9] * n; prev = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - 5), j):
            c = clen(u[i:j])
            if c > 26 and j - i > 1:
                continue
            last = u[j - 1]['w'].lower().strip(',.?!')
            cost = (c - 18) ** 2 * 0.05
            if j < n and last in FUNC:
                cost += 60
            if j < n and u[j - 1]['w'][-1] == ',':
                cost -= 12
            if j - i == 1 and n > 1:
                cost += 30
            if j < n and (norm(u[j - 1]['w']), norm(u[j]['w'])) in NOBREAK:
                cost += 80
            if best[i] + cost < best[j]:
                best[j], prev[j] = best[i] + cost, i
    out, j = [], n
    while j > 0:
        out.append(u[prev[j]:j]); j = prev[j]
    return out[::-1]


groups = [c for u in units for c in chunk(u)]
caps_html, caps_data = [], []
for i, gw in enumerate(groups):
    s = gw[0]['s'] - 0.02
    e = groups[i + 1][0]['s'] - 0.02 if i + 1 < len(groups) and groups[i + 1][0]['s'] - gw[-1]['e'] < 0.6 else gw[-1]['e'] + 0.35
    e = min(e, SPEECH)
    spans = ' '.join(f'<span class="cw" id="cg{i}w{j}">{html.escape(x["w"])}</span>' for j, x in enumerate(gw))
    caps_html.append(f'<div class="cap" id="cg{i}"><span class="cl">{spans}</span></div>')
    caps_data.append({'s': round(s, 3), 'e': round(e, 3),
                      'w': [{'s': round(x['s'], 3), 'e': round(max(x['s'] + 0.25, min(x['e'] + 0.05, gw[k + 1]['s'])) if k + 1 < len(gw) else x['e'] + 0.2, 3)}
                            for k, x in enumerate(gw)],
                      'text': ' '.join(x['w'] for x in gw)})

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
data = {'T': T, 'heads': heads_data, 'caps': caps_data, 'seq': seq, 'amp': AMP, 'teaserFrac': teaser_frac, 'noteLen': round(T['b0'] - T['n0'], 2)}
tpl = (J / 'src/index.tpl.html').read_text()
pill = lambda txt: str(round(540 - (len(txt) * 13.0 + 50) / 2))
segs_of = lambda tid: [s for s in EDL['segments'] if s['take'] == tid]
b1 = segs_of('t01'); b2 = segs_of('t06')
b1d = sum(s['frames'] for s in b1) / EDL['fps']; b2d = sum(s['frames'] for s in b2) / EDL['fps']
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{HEADS}}', '\n  '.join(heads_html))
       .replace('{{DUR}}', f'{DUR:.3f}')
       .replace('{{B1S}}', f"{b1[0]['start']:.4f}").replace('{{B1D}}', f'{b1d + 0.4:.4f}')
       .replace('{{B2S}}', f"{b2[0]['start']:.4f}").replace('{{B2D}}', f'{b2d + 0.4:.4f}')
       .replace('{{PAX}}', pill('Editados pelo Cortez · 4 identidades visuais')).replace('{{PBX}}', pill('Exemplo · 1 vídeo longo → vários cortes · Cortez'))
       .replace('{{PCX}}', pill('Vídeos editados pelo Cortez')))
CTA_MODE, parts = snippets(top=1196, acc='#4A92E6', dark='#0C1118', light='#F2F6FC', light_rgb='242,246,252', muted='#9AA8B8', font='"Inter", sans-serif')
for k, v in parts.items():
    out = out.replace('{{' + k + '}}', v)
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
if CTA_MODE != 'saiba':
    O = J / f'comp-cta-{CTA_MODE}'
    for f in (C / 'assets').rglob('*'):
        d = O / 'assets' / f.relative_to(C / 'assets')
        if f.is_dir():
            d.mkdir(parents=True, exist_ok=True)
        elif not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True); os.link(f, d)
    (O / 'index.html').write_text(out)
    print(json.dumps({'cta': CTA_MODE, 'comp': str(O), 'dur': DUR}, ensure_ascii=False)); sys.exit(0)
(C / 'index.html').write_text(out)

scenes = [{'id': h[0], 'start': round(h[1], 3), 'end': round(h[2], 3), 'label': h[3], 'title': ' / '.join(re.sub('<[^>]+>', '', l[0]) for l in h[4])} for h in HEADS]
scenes.append({'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'title': 'Edição profissional com IA. / Você grava. O Cortez edita. Você aprova. / Saiba mais'})
(J / 'analysis/scene_plan.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / 'analysis/caption_groups.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / 'analysis/motion_plan.json').write_text(json.dumps({'version': 'V1', 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Render + Render de sobreposição + UnrealBloom + Bokeh + Output; Reflector) via hf-seek',
    'identity': 'ID03', 'caption_style': 'L06', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['paisagem do áudio: uma barra 3D por 50 ms do áudio real do Convidado sobre piso espelhado; a luz acompanha o áudio, rebobina na apresentação',
                 'palavras 3D extrudadas (Inter ExtraBold) que sobem e encaixam: CARACA!, CRAQUE, PROMPT, SINISTRO.',
                 'quatro cartões de vídeo em identidades diferentes (molduras na cor de cada ID acendem no "estilo de cor")',
                 'um vídeo longo 16:9 que distribui dez cartões de vídeos curtos como cartas', 'rua de resultados: vídeos em pé ao longo da paisagem, refletidos no piso',
                 'câmera que acompanha o áudio e sobe no "muito sinistro"', 'bloom suave e profundidade de campo'],
    'T': T, 'amp_bins': len(AMP), 'seq': seq, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'bars': len(AMP)}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
