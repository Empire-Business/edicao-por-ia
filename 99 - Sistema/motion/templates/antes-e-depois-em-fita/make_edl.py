#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Antes e depois" (F10 + ID03). EDL de várias fontes, todas originais imutáveis.
V2 (usuário: "ficou meio sem sentido, no final vc cortou minha fala do nada" / "comeu muito o final das palavras"):
  • roteiro com começo, meio e fim, só frases inteiras:
      ANTES (gagueira real da gravação bruta) → Apresentador: "Ó, ele errou. Ele vai errar várias vezes." → "Esse é o vídeo bruto. E em breve
      vocês vão ver esse vídeo aí totalmente com uma outra cara, uma edição profissional." → (O Cortez:) "Ele tira o ruído e corta os
      silêncios… Vai remontar aquele vídeo de forma fluida e pronta." → "Ele vai cortar esses erros ali que o Apresentador cometeu na gravação e
      vai entregar algo realmente pronto." → DEPOIS: a mesma frase do ANTES, inteira, na entrega EXEMPLO_1 com o apresentador na tela.
  • bordas novas (nunca dentro de palavra), limiar de silêncio RELATIVO por take na voz isolada (ElevenLabs):
      SIL = p90 do envelope de 10 ms no take − 35 dB;
      entrada = início real da voz − 0,06 s (no mínimo palavra − 0,08 s; nunca antes do fim da palavra anterior + 0,04 s);
      saída = fim do decaimento (envelope < SIL por 80 ms) + 0,10 s, no mínimo fim da palavra + 0,15 s, nunca depois do início da
      próxima palavra excluída − 0,04 s;
      cortes internos só em pausas com ≥ 0,30 s abaixo de SIL, mantendo 0,12 s depois do decaimento e 0,08 s antes da próxima voz,
      e nunca dentro de [palavra − 0,04, palavra + 0,15] (palavra "inchada" pelo Whisper sobre uma pausa real não protege a pausa);
      nenhum pedaço menor que 0,25 s (junta). Tudo quantizado em quadros de 30 fps.
Saídas: edit/edl.json e analysis/silence_edit_report.json. Conferir com ../material-compartilhado/bin/check_edges.py .
Run: ../../../.venv/bin/python src/make_edl.py
"""
import json, re, unicodedata
from pathlib import Path
import numpy as np
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
E117J = J.parent / '<PREENCHER: fonte ou prova própria>'
FPS = 30
SRC = {
    'raw': '<PREENCHER: fonte ou prova própria>',
    'e117': '<PREENCHER: fonte ou prova própria>',
    'yt': '<PREENCHER: fonte ou prova própria>',
}
YTW = [w for s in json.loads((SH / 'analysis/yt.transcript.json').read_text())['segments'] for w in s['words']]
YTWIN = [(1279.0, 1350.0, SH / 'audio/yt-1279-1350-el.wav'), (1558.0, 1584.0, SH / 'audio/yt-1558-1584-el.wav'),
         (1660.0, 1681.0, SH / 'audio/yt-1660-1681-el.wav')]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def find(word, near):
    c = [w for w in YTW if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'yt: palavra {word!r} perto de {near} não encontrada')
    return min(c, key=lambda w: abs(w['start'] - near))


_env = {}


def envelope(path):
    if path not in _env:
        sr, x = wavfile.read(path)
        x = x.astype(np.float32) / 32768
        x = x.mean(1) if x.ndim > 1 else x
        h = int(sr * 0.01); n = len(x) // h
        e = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
        _env[path] = np.convolve(e, np.ones(3) / 3, mode='same')      # 30 ms
    return _env[path]


def runs(mask, val):
    out, i = [], 0
    while i < len(mask):
        if mask[i] == val:
            j = i
            while j < len(mask) and mask[j] == val:
                j += 1
            out.append((i, j)); i = j
        else:
            i += 1
    return out


def subtract(iv, cuts):
    out = [iv]
    for a, b in cuts:
        nxt = []
        for x, y in out:
            if b <= x or a >= y:
                nxt.append((x, y))
            else:
                if a > x: nxt.append((x, a))
                if b < y: nxt.append((b, y))
        out = nxt
    return out


# entrada fixa (o Whisper marcou "Se" em 1306,56 s em cima do fim de "ideal", que vai até 1306,62 s; o "Se" começa em 1306,72 s
# e entre as duas palavras não há silêncio: entrar em 1306,69 s, com o resto de "ideal" já em −41/−47 dB e fade de 20 ms)
IN_FIX = {'b05': 1306.69,
          # "Ele" do fecho: o Whisper marcou 1671,74 s, mas a voz começa em 1672,00 s (antes disso é o fim de "profissional", que já está no b02)
          'b04': 1671.94}


def yt_take(tid, w0, w1):
    a, b = find(*w0), find(*w1)
    W = [w for w in YTW if a['start'] - 1e-6 <= w['start'] <= b['start'] + 1e-6]
    prev = max([w['end'] for w in YTW if w['end'] <= a['start'] + 1e-6] or [a['start'] - 1])
    nxt = min([w['start'] for w in YTW if w['start'] > b['start'] + 1e-6] or [b['end'] + 1])
    lo_w, hi_w, path = next(x for x in YTWIN if x[0] <= a['start'] - 0.3 and x[1] >= b['end'] + 0.3)
    env = envelope(path)
    ix = lambda t: int(round((t - lo_w) / 0.01))
    tt = lambda i: lo_w + i * 0.01
    ref = float(np.percentile(env[ix(a['start']):ix(b['end'])], 90)); SIL = ref - 35.0
    voiced = env >= SIL
    # entrada: início real da voz (volta enquanto há voz, até 0,3 s antes da palavra)
    i = ix(a['start'] + 0.03)
    while i > ix(a['start'] - 0.3) and voiced[i - 1]:
        i -= 1
    onset = tt(i)
    t_in = max(min(onset - 0.06, a['start'] - 0.08), prev + 0.04)
    if tid in IN_FIX:
        t_in = onset = IN_FIX[tid]
    # saída: decaimento da última palavra (80 ms abaixo de SIL)
    j = ix(max(b['start'] + 0.05, b['end'] - 0.05)); lim = ix(min(nxt - 0.04, b['end'] + 1.2))
    decay = tt(lim)
    while j < lim:
        if not voiced[j:j + 8].any():
            decay = tt(j); break
        j += 1
    t_out = min(max(decay + 0.10, b['end'] + 0.15), nxt - 0.04)
    # pausas internas ≥ 0,30 s abaixo de SIL
    i0 = ix(t_in)
    rr = [(tt(i0 + p), tt(i0 + q)) for p, q in runs(voiced[i0:ix(t_out)], False) if (q - p) * 0.01 >= 0.30]
    protect = []
    for w in W:
        span = [(w['start'] - 0.04, w['end'] + 0.15)]
        inner = [(p, q) for p, q in rr if p >= w['start'] + 0.03 and q <= w['end'] + 0.15]
        if inner:                   # palavra "inchada" pelo Whisper sobre uma pausa real: a pausa não fica protegida
            span = subtract(span[0], [(p + 0.12, q - 0.08) for p, q in inner])
        protect += span
    cuts = []
    for p, q in rr:
        c = (p + 0.20, q - 0.08)            # 0,20 s depois do decaimento (≥ 0,12): o rabo das palavras fica inteiro
        for x, y in subtract(c, protect):
            if y - x >= 0.05:
                cuts.append((x, y))
    cuts.sort()
    pieces = subtract((t_in, t_out), cuts)
    # nenhum pedaço < 0,25 s: desfaz o corte vizinho
    changed = True
    while changed:
        changed = False
        for k, (x, y) in enumerate(pieces):
            if y - x < 0.25 and len(pieces) > 1:
                if k == 0:
                    pieces[0:2] = [(pieces[0][0], pieces[1][1])]
                else:
                    pieces[k - 1:k + 1] = [(pieces[k - 1][0], pieces[k][1])]
                changed = True; break
    removed = [(pieces[k][1], pieces[k + 1][0]) for k in range(len(pieces) - 1)]
    info = {'take': tid, 'sil_db': round(SIL, 1), 'speech_ref_db': round(ref, 1), 'onset': round(onset, 3), 'decay': round(decay, 3),
            'in': round(t_in, 3), 'out': round(t_out, 3), 'cuts': [[round(x, 3), round(y, 3), round(y - x, 3)] for x, y in removed],
            'first_word': [a['word'].strip(), a['start']], 'last_word': [b['word'].strip(), b['end']], 'next_excluded_word_at': round(nxt, 3)}
    return pieces, info


# (id, fonte, papel, âncoras ou bordas fixas, texto conferido)
TAKES = [
    ('a01', 'raw', 'antes', (0.98, 2.86), 'É assim. … É assim que…'),
    ('b01', 'yt', 'errou', (('Ó', 1571.90), ('vezes', 1574.46)), 'Ó, ele errou. Ele vai errar várias vezes.'),
    ('b02', 'yt', 'bruto', (('esse', 1663.20), ('profissional', 1670.80)),
     'Esse é o vídeo bruto. E em breve vocês vão ver esse vídeo aí totalmente com uma outra cara, uma edição profissional.'),
    # parte 4 aparada só em frases inteiras para caber em 40 s: fora "Se você gravou, talvez, num ambiente não ideal" e
    # "Vai tirar os momentos que você ficou sem falar nada no vídeo" (os silêncios já estão na 1ª frase)
    ('b03', 'yt', 'cortez', (('Ele', 1301.82), ('silêncios', 1303.10)), 'Ele tira o ruído e corta os silêncios.'),
    ('b05', 'yt', 'erros', (('Se', 1306.56), ('limpar', 1310.14)), 'Se você errou muito, ele vai pegar todos os seus erros. Vai limpar.'),
    ('b06', 'yt', 'remontar', (('Vai', 1313.58), ('pronta', 1317.34)), 'Vai remontar aquele vídeo de forma fluida e pronta.'),
    ('b04', 'yt', 'fecho', (('Ele', 1671.74), ('pronto', 1678.36)), 'Ele vai cortar esses erros ali que o Apresentador cometeu na gravação e vai entregar algo realmente pronto.'),
    ('d01', 'e117', 'depois', (0.00, 4.56), 'É assim que eu encheria minha agenda se eu fosse consultor e vivesse de indicação.'),
]
# Bordas fixas conferidas no envelope:
#  • a01 (gravação bruta): a fala começa em 1,1 s ("É assim."), a 2ª tentativa ("É assim que…") termina em 2,70 s; silêncio até 2,94 → 0,98–2,86
#    (a pausa entre as duas tentativas fica: a gagueira é o conteúdo do ANTES)
#  • d01 (entrega EXEMPLO_1): "indicação." termina em 4,42 s na voz da entrega; "Tem" começa em 4,70 → saída 4,56, frase inteira
segments, report, t = [], [], 0.0
for tid, src, role, edge, text in TAKES:
    if src == 'yt':
        pieces, info = yt_take(tid, *edge)
        report.append(info)
    else:
        pieces = [edge]
        report.append({'take': tid, 'fixed': edge})
    for k, (pi, po) in enumerate(pieces):
        n = max(1, round((po - pi) * FPS))
        segments.append({'source': SRC[src], 'src': src, 'take': tid, 'role': role, 'speaker': {'raw': 'apresentador', 'e117': 'entrega', 'yt': 'apresentador'}[src],
                         'piece': k, 'in': round(pi, 4), 'out': round(pi + n / FPS, 4), 'frames': n, 'start': round(t, 4)})
        t += n / FPS

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_2', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID03',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'V2: ANTES (gagueira real) → "Ó, ele errou" → "Esse é o vídeo bruto… uma edição profissional" → O Cortez: ruído, silêncios, erros, '
               'remontagem (fita 3D) → "Ele vai cortar esses erros… algo realmente pronto" → DEPOIS (mesma frase, inteira, na entrega EXEMPLO_1) → CTA.',
       'takes': [{'id': x[0], 'src': x[1], 'role': x[2], 'text': x[4],
                  **({'w0': x[3][0][1], 'w1': x[3][1][1]} if x[1] == 'yt' else {'in': x[3][0], 'out': x[3][1]})} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo por take (p90 − 35 dB na voz isolada); cortes só em pausas ≥ 0,30 s, '
    'mantendo 0,12 s após o decaimento e 0,08 s antes da voz; nunca dentro de [palavra − 0,04, palavra + 0,15]; pedaços ≥ 0,25 s', 'takes': report,
    'removed_total_s': round(sum(c[2] for r in report for c in r.get('cuts', [])), 3)}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration']}))
for r in report:
    print(r)
