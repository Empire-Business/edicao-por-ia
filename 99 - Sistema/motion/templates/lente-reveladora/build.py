#!/usr/bin/env python3
"""EXEMPLO_1 — gera comp/index.html (HyperFrames + GSAP + three.js) a partir do EDL, da transcrição da voz final e de src/index.tpl.html.
ID07 Laranja + legenda L08 (contorno e contraste). Tempos = palavras realmente faladas na voz final (segundos do master limpo).
Texto das legendas conferido na fonte: o Whisper ouve "presou/presuma" (prezou), "sendo/cena" (cenas), "aí um dado" (tá inundado), "Iara" (IA).
Grava analysis/scene_plan.json, analysis/motion_plan.json e analysis/caption_groups.json.
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
FPS = 30


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def W(word, after=0.0, alts=()):
    ns = {norm(word), *map(norm, alts)}
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) in ns:
            return x['s']
    raise SystemExit(f'palavra {word!r} não encontrada após {after}')


q = lambda x: round(round(x * FPS) / FPS, 4)
take0 = {}
for s in EDL['segments']:
    take0.setdefault(s['take'], s['start'])
T = {'rolar': W('rolar'), 'inund': round(W('está', 1.6, ('ele', 'ta')) + 0.14, 3), 't02': take0['t02'], 'aqui': W('aqui', 8.0)}
T['nao'] = W('não', T['aqui'])
T['t03'] = take0['t03']
T['ela'] = W('ela', 15.0)
T['type0'] = W('pesquisa', T['ela']); T['type1'] = T['type0'] + 0.75
T['cenas'] = W('cenas', T['type0'], ('sendo', 'cena'))
T['colocar'] = W('colocar', T['cenas'])
T['full'] = q(W('isso', T['colocar']) - 0.03)
T['land'] = q(T['full'] - 45 / FPS)            # a sequência "card" (45 quadros = EXEMPLO_2 15,45–16,95 s) termina exatamente no corte p/ tela cheia
T['pick'] = round(T['colocar'] + 0.05, 3)
T['fly0'] = round(T['pick'] + 0.5, 3)
T['lens2'] = round(T['cenas'] + 0.42, 3)
T['p1a'] = round(T['t03'] + 1.7, 3); T['p1b'] = round(T['ela'] - 0.45, 3)
T['p2a'] = round(T['cenas'] + 0.55, 3); T['p2b'] = round(T['pick'] + 0.25, 3)
T['p3a'] = round(T['full'] + 0.4, 3); T['p3b'] = round(SPEECH - 0.05, 3)
T.update({'speechEnd': SPEECH, 'cta0': SPEECH, 'end': DUR, 'tap': round(SPEECH + 2.95, 3), 'type2': round(SPEECH + 1.95, 3)})
# variante de CTA (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md): CTA=comment gera a tela final "Comente CORTEZ"; padrão = "Saiba mais"
CTA = os.environ.get('CTA', 'saiba')
assert CTA in ('saiba', 'comment'), CTA
SUF = '' if CTA == 'saiba' else '-comment'
assert T['fly0'] < T['land'] - 0.4, T

# rótulos (canto superior esquerdo)
LABS = [('O feed hoje', 0, T['t02'], ''), ('Cara de IA', T['t02'], T['aqui'], 'grey'), ('Com o Cortez', T['aqui'], T['ela'] - 0.35, ''),
        ('Pesquisa de cenas', T['ela'] - 0.35, T['pick'] + 0.3, ''), ('Como um editor faria', T['pick'] + 0.3, T['full'] - 0.4, ''),
        ('Entrega final', T['full'] - 0.4, SPEECH, 'onvid')]
labs_html = '\n  '.join(f'<div class="lab {cl}" id="lab{i}"><span class="in"><i></i>{html.escape(tx)}</span></div>' for i, (tx, a, b, cl) in enumerate(LABS))
labs = [{'s': round(a, 3), 'e': round(b, 3)} for _, a, b, _ in LABS]

# Apresentador aparece só nos trechos da live do Instagram (os do YouTube são só áudio)
pip, cur = [], None
for s in EDL['segments']:
    e = s['start'] + s['frames'] / FPS
    if s['src'] == 'ig':
        if cur and abs(cur['e'] - s['start']) < 0.05:
            cur['e'] = e
        else:
            cur = {'s': s['start'], 'e': e}; pip.append(cur)
    else:
        cur = None
pip = [{'s': round(p['s'], 3), 'e': round(p['e'], 3)} for p in pip]

# legendas L08: blocos estáveis de até 5 palavras (texto conferido); âncora = 1ª palavra falada do bloco
# (texto | quebra de linha, palavra-âncora (+ grafias do Whisper), ajuste) — âncoras buscadas em sequência, cada uma depois da anterior
G = [('Se a gente for rolar', None, 0.0), ('o Instagram,', ('o',), 0), ('tá inundado de vídeo', ('está', 'ele', 'ta'), -0.12),
     ('editado por <em>IA</em>,', ('editado',), 0), ('você encontra|um monte, né?', ('você',), 0), ('Tem <em>cara de IA.</em>', ('tem',), 0),
     ('Tem umas animações', ('umas',), -0.18), ('que todo mundo faz', ('que',), 0), ('e fica de|qualquer jeito.', ('e',), 0),
     ('<em>Aqui não.</em>', ('aqui',), 0, 'big'), ('A gente prezou', ('a',), 0), ('por montar|a ferramenta', ('por',), 0),
     ('de uma forma|que realmente', ('de',), 0), ('chega num nível', ('chega',), 0), ('<em>profissional</em>|de edição.', ('profissional',), 0),
     ('Ela realmente|pesquisa', ('ela',), 0), ('<em>cenas</em> na internet', ('cenas', 'sendo', 'cena'), 0),
     ('para colocar como', ('para', 'pra'), 0), ('um editor|<em>profissional</em> faria.', ('um',), 0),
     ('Isso daqui,', ('isso',), 0), ('nessa qualidade aqui,', ('nessa',), 0), ('é a qualidade de um', ('é',), 0),
     ('<em>editor profissional.</em>', ('editor',), 0)]
starts, after = [], 0.0
for g in G:
    a = g[1]
    st = 0.0 if a is None else W(a[0], after, a[1:]) + g[2]
    starts.append(round(max(0.0, st), 3)); after = (st - g[2]) + 0.05
assert starts == sorted(starts), starts
caps_html, caps_data = [], []
for i, g in enumerate(G):
    s = starts[i]; e = starts[i + 1] if i + 1 < len(G) else SPEECH
    lines = g[0].split('|')
    big = len(g) > 3 and g[3] == 'big'
    top_area = s >= T['full'] - 0.1
    lh = 124 * 1.14 if big else 74 * 1.14
    top = (236 if top_area else 1296) - (len(lines) - 1) * (lh if not top_area else 0) * 0.18
    spans = ''.join(f'<span class="cl"><span class="bk">{re.sub("<[^>]+>", "", ln)}</span><span class="fg">{ln}</span></span>' for ln in lines)
    caps_html.append(f'<div class="cap{" big" if big else ""}" id="cg{i}" style="top:{round(top)}px">{spans}</div>')
    caps_data.append({'s': s, 'e': round(e, 3), 'big': big, 'text': re.sub('<[^>]+>', '', ' / '.join(lines))})

seq = {d.name: len(list(d.glob('*.jpg'))) for d in sorted((C / 'assets/seq').iterdir()) if d.is_dir()}
nst = len(list((C / 'assets/stills').glob('*.jpg')))
data = {'T': T, 'labs': labs, 'pip': pip, 'caps': caps_data, 'seq': seq, 'stills': nst, 'cta': CTA}
tpl = (J / 'src/index.tpl.html').read_text()
pill = lambda txt: str(round(540 - (len(txt) * 11.9 + 58) / 2))
out = (tpl.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)).replace('{{CAPS}}', '\n'.join(caps_html)).replace('{{LABS}}', labs_html)
       .replace('{{DUR}}', f'{DUR:.3f}').replace('{{PIPDUR}}', f'{SPEECH + 1.0:.3f}').replace('{{FULL0}}', f"{T['full']:.4f}")
       .replace('{{P1X}}', pill('Vídeos editados pelo Cortez')).replace('{{P2X}}', pill('Cenas que o Cortez achou para um vídeo real'))
       .replace('{{P3X}}', pill('Vídeo entregue · editado pelo Cortez'))
       .replace('{{CTACSS}}', '#btn { display:none; }' if CTA == 'comment' else '#cmh, #cmf, #cms { display:none; }'))
assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
(C / 'index.html').write_text(out)

scenes = [
    {'id': 'feed', 'start': 0, 'end': T['t02'], 'label': 'O feed hoje', 'what': 'feed 3D de vídeos-modelo cinzas rolando; a lente de vidro já mostra, ampliado, um vídeo real do Cortez; recuo no "inundado"'},
    {'id': 'template', 'start': T['t02'], 'end': T['aqui'], 'label': 'Cara de IA', 'what': 'todos os cartões fazem a mesma animação de modelo (estrela girando, selo pulando) em sincronia'},
    {'id': 'reveal', 'start': T['aqui'], 'end': T['t03'] + 1.0, 'label': 'Aqui não', 'what': 'a lente pousa no cartão do EXEMPLO_2 (Apresentador, "4 clientes por indicação") e os cartões viram, em onda, para os vídeos editados pelo Cortez'},
    {'id': 'pro', 'start': T['t03'] + 1.0, 'end': T['ela'] - 0.35, 'label': 'Com o Cortez', 'what': 'campo inteiro virado; a lente passeia ampliando os vídeos reais'},
    {'id': 'search', 'start': T['ela'] - 0.35, 'end': T['pick'] + 0.3, 'label': 'Pesquisa de cenas', 'what': 'barra de busca digitando "escritório vazio"; 3 cenas que o Cortez achou para o EXEMPLO_2; a lente escolhe a do escritório'},
    {'id': 'place', 'start': T['pick'] + 0.3, 'end': T['full'], 'label': 'Como um editor faria', 'what': 'a cena voa e encaixa no vídeo 9:16 do EXEMPLO_2 exatamente onde ele foi usado'},
    {'id': 'delivery', 'start': T['full'], 'end': SPEECH, 'label': 'Entrega final', 'what': 'EXEMPLO_2 em tela cheia: escritório e call center vazios (EXEMPLO_2 16,95–18,82 s) e, no fechamento, a abertura do EXEMPLO_2 — agenda rosa sendo preenchida + apresentador (EXEMPLO_2 0–2,1 s)'},
    {'id': 'cta', 'start': SPEECH, 'end': DUR, 'label': 'CTA escrito (voz já terminou)', 'what': 'Edição com cara de editor. Não de IA. / Você grava. O Cortez edita. Você aprova. / ' +
     ('Comente CORTEZ (balão) + campo de comentário com CORTEZ digitado e enviado + "aqui nos comentários" ↓' if CTA == 'comment' else 'Saiba mais')}]
(J / f'analysis/scene_plan{SUF}.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=1))
(J / f'analysis/caption_groups{SUF}.json').write_text(json.dumps(caps_data, ensure_ascii=False, indent=1))
(J / f'analysis/motion_plan{SUF}.json').write_text(json.dumps({'version': 'V2', 'cta': CTA, 'engine': 'HyperFrames 0.8.92 (GSAP) + three.js r186 ESM (EffectComposer: Bokeh + overlay da lente + Output) via hf-seek',
    'identity': 'ID07', 'caption_style': 'L08', 'determinism': 'função do tempo do quadro; texturas = quadros JPG indexados pelo tempo; PRNG de semente fixa',
    'three_js': ['feed 3D de 130 cartões (modelo cinza procedural em shader na frente, vídeo real no verso)', 'lente de vidro: recorte da câmera ampliado (setViewOffset) num alvo próprio, com borda de vidro, aberração cromática e sombra',
                 'onda de cartões virando a partir do cartão revelado', 'pesquisa de cenas (barra digitando + 3 resultados) e a cena voando até o vídeo real', 'profundidade de campo (miniatura leve no feed; fundo desfocado na pesquisa e no CTA)'],
    'T': T, 'labs': labs, 'pip': pip, 'seq': seq, 'stills': nst, 'edl_duration': SPEECH, 'cta_seconds': CTA}, ensure_ascii=False, indent=1))
print(json.dumps({'dur': DUR, 'groups': len(caps_data), 'T': {k: round(v, 3) for k, v in T.items()}}, ensure_ascii=False))
for c in caps_data:
    print(c['s'], c['e'], c['text'])
