#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Modelo pronto, um clique" (F22 Corte de Live 3D + ID05 Roxo), trechos da live do
YouTube (Apresentador). Lógica de bordas herdada do EXEMPLO_1 V2 (regras do usuário: não comer começo/fim de palavra; fala com sentido):
- limiar de silêncio RELATIVO por trecho na voz isolada (ElevenLabs): ref = p90 do envelope de 10 ms; silêncio = ref − 35 dB;
- nunca corta dentro de palavra; cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque);
- saída = decaimento real + 0,10 s (mín. fim da palavra + 0,15 s), sem invadir palavra vizinha excluída nem passar do fim da janela isolada;
- entrada = ataque − 0,06 s (mín. início − 0,08 s), sem voltar antes do fim da palavra anterior + 0,04 s; nenhum pedaço < 0,25 s.
Desvio documentado da receita F22 (silêncio > 0,15 s cortado com 0,05 s): a regra do usuário de 27/11 (não comer palavras) prevalece.
Validação: ../material-compartilhado/bin/check_edges.py <job>. Saídas: edit/edl.json e analysis/silence_edit_report.json.
Run: ../../../.venv/bin/python src/make_edl.py
"""
import json, math, re, unicodedata
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'material-compartilhado/bin'))
import check_edges as CHK   # mesmo envelope da validação

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
SRC = {'yt': '<PREENCHER: fonte ou prova própria>'}
FPS = 30
WORDS = {k: [w for s in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s['words']] for k in SRC}
ISO = [('yt', SH / 'audio/yt-363-401-el.wav', 363.0, 401.0), ('yt', SH / 'audio/yt-442-497-el.wav', 442.0, 497.0)]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def find(src, word, near):
    c = [i for i, w in enumerate(WORDS[src]) if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'{src}: palavra {word!r} perto de {near} não encontrada')
    return min(c, key=lambda i: abs(WORDS[src][i]['start'] - near))


# (id, fonte, quem fala, cena, primeira palavra @ início, última palavra @ início, texto conferido)
TAKES = [
    ('t01', 'yt', 'apresentador', 'hook', ('com', 457.36), ('aqui', 465.62),
     'Com um clique no Cortez, copiar e colar, você consegue copiar o mesmo estilo de edição pra você nessa qualidade aqui.'),
    ('t02', 'yt', 'apresentador', 'formatos', ('Aqui', 370.90), ('edição', 372.48), 'Aqui estão os formatos de edição.'),
    ('t03', 'yt', 'apresentador', 'testados', ('Esses', 375.82), ('editamos', 379.40), 'Esses formatos, nós já testamos, editamos.'),
    ('t04', 'yt', 'apresentador', 'objetivos', ('Você', 384.60), ('objetivo', 390.56),
     'Você pode ver que já tem vários vídeos aqui editados em alta qualidade para diferentes tipos de objetivo.'),
    ('t05', 'yt', 'apresentador', 'modelo_id', ('Então', 468.04), ('visual', 471.82),
     'Então, tudo o que você precisa fazer é ver aqui, usar esse modelo. Você escolhe a ID visual.'),
    ('t06', 'yt', 'apresentador', 'pedido', ('E', 484.86), ('aqui', 494.00),
     'E aqui, ele já me dá o pedido pra colar no Cortez. Tudo prontinho pra eu editar o vídeo nesse formato aqui.'),
]
# Ajustes conferidos no envelope de 10 ms da voz isolada:
# t01 — "qualidade" decai até ~457,16 e o "e" (excluído, conector solto) é a rajada curta 457,32–457,38; "com" ataca em ~457,48
#       (vale entre −53 e −47 dB em 457,40–457,48): entra em 457,44 — o gancho abre limpo em "Com um clique" (conferido no Whisper).
# t02 — "Aqui" ataca em ~371,20 (o Whisper adiantou para 370,90): entra em 371,10 com folga.
# t03 — "Esses" ataca em ~376,24 (Whisper: 375,82): entra em 376,16 para não abrir com meio segundo de silêncio.
# t04 — "aqui." (excluído) decai até −49 dB em ~384,31 e o "V" de "Você" já ataca em 384,40 (Whisper: 384,60): entra em 384,37.
# t05 — "visual." decai até o mínimo de −52 dB em ~472,50 e o "Se" (excluído) começa logo depois: sai em 472,505.
IN_OVERRIDE = {'t01': 457.44, 't02': 371.10, 't03': 376.16, 't04': 384.37, 't05': 468.40}   # t05: 10 ms antes, só para a quantização em quadros alcançar a saída 472,50
OUT_OVERRIDE = {'t05': 472.505}
FORCED_CUTS = {}
ENV = {}


def envelope(k):
    if k not in ENV:
        _, p, w0, _ = ISO[k]
        sr, x = wavfile.read(p)
        x = x.astype(np.float32) / 32768
        x = x.mean(1) if x.ndim > 1 else x
        h = int(sr * 0.01); n = len(x) // h
        ENV[k] = (20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), w0)
    return ENV[k]


def iso_for(src, a, b):
    for k, (s, _, w0, w1) in enumerate(ISO):
        if s == src and w0 <= a and b <= w1:
            return k
    raise SystemExit(f'{src} {a}–{b} fora das janelas isoladas')


class _W(dict):
    pass


segments, report, edges, t = [], [], [], 0.0
for tid, src, who, scene, (w0_, n0), (w1_, n1), text in TAKES:
    W = WORDS[src]
    ia, ib = find(src, w0_, n0), find(src, w1_, n1)
    kept, prev, nxt = W[ia:ib + 1], dict(W[ia - 1]), dict(W[ib + 1])
    k = iso_for(src, kept[0]['start'] - 0.3, kept[-1]['end'] + 0.03)
    _, _, w0_, w1_ = ISO[k]
    prev['end'] = max(prev['end'], w0_ + 0.05)          # limites nunca fora da janela isolada (fades de 20 ms nas pontas)
    nxt['start'] = min(nxt['start'], w1_ - 0.0)
    db, base = envelope(k)
    fr = lambda tt: int(round((tt - base) / 0.01))
    tm = lambda i: base + i * 0.01
    ref = float(np.percentile(db[fr(kept[0]['start']):fr(kept[-1]['end'])], 90))
    SIL = ref - 35.0
    quiet = db < SIL

    def decay_end(w, limit):
        """início do 1º trecho de 80 ms abaixo do limiar depois da palavra (fim real do decaimento)."""
        i, lim = fr(w['end'] - 0.05), fr(limit)
        while i < lim:
            if quiet[i:i + 8].all():
                return tm(i)
            i += 1
        return limit

    def onset(w, limit):
        """fim do último trecho de 50 ms abaixo do limiar antes do ataque da palavra."""
        i, lim = fr(w['start'] + 0.05), fr(limit)
        while i - 5 >= lim:
            if quiet[i - 5:i].all():
                return tm(i)
            i -= 1
        return limit

    on = onset(kept[0], prev['end'])
    tin = max(min(on - 0.06, kept[0]['start'] - 0.08), prev['end'] + 0.04)
    dec = decay_end(kept[-1], nxt['start'])
    tout = min(max(dec + 0.10, kept[-1]['end'] + 0.15), nxt['start'] - 0.04)
    tin = IN_OVERRIDE.get(tid, tin); tout = OUT_OVERRIDE.get(tid, tout)
    # Pausas reais: o Whisper às vezes estica a palavra por cima do silêncio ("dentro" 179,48–180,56 começa de fato em 180,22;
    # "muito" 1746,54–1747,80 tem 0,6 s de silêncio no meio). Por isso as pausas são achadas no ENVELOPE da voz isolada:
    # só trechos contínuos ≥ 0,30 s abaixo do limiar relativo (nenhum som de palavra), com 0,12 s depois do decaimento e 0,08 s antes do ataque.
    runs, i0 = [], None
    for i in range(fr(tin), fr(tout) + 1):
        if i < fr(tout) and quiet[i]:
            i0 = i if i0 is None else i0
        else:
            if i0 is not None and i - i0 >= 30:
                runs.append([tm(i0), tm(i)])
            i0 = None
    # Conferência com o mesmo envelope de check_edges.py (piso do arquivo + 8 dB): respiro/cauda fraca conta como som; o corte não pode comê-la.
    cdb, cfloor = CHK.env(ISO[k][1]); cthr = cfloor + 8
    cfr = lambda tt: int((tt - base) * 100)

    def chk_tail(tt, lim):          # onde o som realmente acaba depois de tt (6 quadros abaixo do piso+8)
        j, run = max(cfr(tt) - 3, 0), 0
        while j < cfr(lim):
            run = run + 1 if cdb[j] < cthr else 0
            if run >= 6:
                return base + (j - 5) / 100
            j += 1
        return lim

    def chk_head(tt, lim):          # onde o som realmente começa antes de tt (4 quadros abaixo do piso+8)
        j, run = cfr(tt), 0
        while j > cfr(lim):
            run = run + 1 if cdb[j] < cthr else 0
            if run >= 4:
                return base + (j + 4) / 100
            j -= 1
        return lim
    cuts = []
    for r0, r1 in runs:
        if r0 <= tin + 0.05:                       # silêncio no começo do trecho (Whisper adiantou a 1ª palavra): entra no ataque − 0,06 s
            tin = max(tin, r1 - 0.06); continue
        if r1 >= tout - 0.05:                      # silêncio no fim: sai no decaimento + 0,10 s
            tout = min(tout, r0 + 0.10); continue
        ca, cb = r0 + 0.12, r1 - 0.08
        ca = max(ca, chk_tail(ca, r1) + 0.02)     # sem comer respiro/cauda fraca
        cb = min(cb, chk_head(cb, r0) - 0.02)
        if cb - ca >= 0.10:
            cuts.append([ca, cb])
    cuts = sorted(cuts + [c for c in FORCED_CUTS.get(tid, []) if tin < c[0] < c[1] < tout])
    bounds = [tin] + [x for c in cuts for x in c] + [tout]
    pieces = [[bounds[i], bounds[i + 1]] for i in range(0, len(bounds), 2)]
    while len(pieces) > 1 and min(b - a for a, b in pieces) < 0.25:        # junta pedaço curto com o vizinho (desfaz o corte)
        j = min(range(len(pieces)), key=lambda i: pieces[i][1] - pieces[i][0])
        m = j - 1 if j > 0 else j
        pieces[m:m + 2] = [[pieces[m][0], pieces[m + 1][1]]]
    real_cuts = [[pieces[i][1], pieces[i + 1][0]] for i in range(len(pieces) - 1)]
    for c in real_cuts:
        report.append({'take': tid, 'src': src, 'cut': [round(c[0], 3), round(c[1], 3)], 'removed': round(c[1] - c[0], 3)})
    edges.append({'take': tid, 'src': src, 'ref_db': round(ref, 1), 'sil_db': round(SIL, 1), 'in': round(tin, 3), 'onset': round(on, 3),
                  'first_word': [kept[0]['word'].strip(), kept[0]['start']], 'out': round(tout, 3), 'decay_end': round(dec, 3),
                  'last_word': [kept[-1]['word'].strip(), kept[-1]['end']], 'prev_word_end': prev['end'], 'next_word_start': nxt['start']})
    for pi_, (a, b) in enumerate(pieces):
        cap = b + 0.03 if pi_ < len(pieces) - 1 else nxt['start'] - 0.01
        n = math.ceil((b - a) * FPS - 1e-6)
        if a + n / FPS > cap:
            n -= 1
        segments.append({'source': SRC[src], 'src': src, 'take': tid, 'speaker': who, 'scene': scene, 'piece': pi_,
                         'in': round(a, 4), 'out': round(a + n / FPS, 4), 'frames': n, 'start': round(t, 4)})
        t += n / FPS

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_2', 'pattern': 'f22-corte-de-live-3d-v1', 'format_code': 'F22', 'visual_identity': 'ID05',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'Gancho "com um clique no Cortez, copiar e colar, você copia o mesmo estilo de edição" → os formatos de edição já testados → vários vídeos em alta qualidade para objetivos diferentes → é só usar o modelo e escolher a ID → o painel entrega o pedido pronto pra colar no Cortez.',
       'takes': [{'id': x[0], 'src': x[1], 'speaker': x[2], 'scene': x[3], 'text': x[6]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo por trecho (p90 − 35 dB); bordas pelo ataque/decaimento reais (entrada ataque−0,06 s, saída decaimento+0,10 s, sem invadir palavra vizinha excluída); cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque); pedaços ≥ 0,25 s',
    'cuts': report, 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
for e in edges: print(e)
for r in report: print(r)
