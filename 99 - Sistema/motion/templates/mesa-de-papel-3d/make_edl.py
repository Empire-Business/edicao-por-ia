#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"5 minutos do seu dia" (F10 + ID08), montado com trechos das DUAS lives (YT = Apresentador com a tela do Cortez;
IG = Apresentador + Convidado). V2 (usuário: "vc comeu muito o final das palavras"; regra: a fala faz sentido do começo ao fim, nunca corta frase/ideia):
- Limiar de silêncio RELATIVO por trecho: ref = percentil 90 do envelope de 10 ms da voz isolada (ElevenLabs) dentro do trecho; SIL = ref − 35 dB
  (para achar o fim real do decaimento usa-se o mais baixo entre SIL e piso do arquivo + 8 dB, o mesmo critério do check_edges).
- Nunca corta dentro de palavra: protege [início − 0,04; fim + 0,15] de cada palavra mantida. Corte interno só entre palavras com intervalo
  ≥ 0,30 s E envelope abaixo de SIL por ≥ 0,30 s; mantém ≥ 0,12 s depois do decaimento real e ≥ 0,08 s antes do próximo ataque.
- Saída do trecho = decaimento da última palavra (abaixo do limiar por 80 ms) + 0,10 s, no mínimo fim + 0,15, limitada ao início da palavra
  seguinte excluída − 0,04. Entrada = ataque − 0,06, no mínimo início − 0,08, limitada ao fim da palavra anterior + 0,04.
- Nenhum pedaço < 0,25 s (junta). Quantização em quadros de 30 fps sem passar dos limites.
Bordas coladas na fala vizinha (sem silêncio real) usam o ponto de menor energia medido e conferido por transcrição de recortes (EDGE_FIX).
Saídas: edit/edl.json e analysis/silence_edit_report.json. Run: ../../../.venv/bin/python src/make_edl.py
"""
import json, math, re, subprocess, unicodedata
from pathlib import Path
import numpy as np

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
SRC = {'yt': '<PREENCHER: fonte ou prova própria>',
       'ig': '<PREENCHER: fonte ou prova própria>'}
FPS = 30
WORDS = {k: [w for s in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s['words']] for k in SRC}
WIN = [('yt', 626, 672), ('yt', 1370, 1396), ('ig', 655, 712)]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def idx(src, word, near):
    c = [i for i, w in enumerate(WORDS[src]) if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'{src}: palavra {word!r} perto de {near} não encontrada')
    return min(c, key=lambda i: abs(WORDS[src][i]['start'] - near))


_env = {}


def envelope(src, t0, t1):
    for s, a, b in WIN:
        if s == src and a <= t0 and t1 <= b:
            f = SH / f'audio/{s}-{a}-{b}-el.wav'
            if f not in _env:
                r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
                x = np.frombuffer(r, np.int16).astype(np.float32) / 32768; h = 160; n = len(x) // h
                db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12) + 1e-9)
                _env[f] = (db, float(a), float(np.percentile(db, 10)))
            return _env[f]
    raise SystemExit(f'sem janela isolada para {src} {t0}-{t1}')


# (id, fonte, quem fala, cena, primeira palavra @ início, última palavra @ início, texto conferido)
TAKES = [
    ('t01', 'yt', 'apresentador', 'hook', ('Você', 656.46), ('impossível', 664.96),
     'Você vai gastar ali 5 minutos do seu dia para editar um vídeo com extrema qualidade. Um vídeo profissional que antes era impossível.'),
    ('t02', 'yt', 'apresentador', 'editor', ('é', 1383.34), ('correção', 1388.48),
     'É muito melhor do que: "ah, vou mandar pro editor e daqui a dois dias ele me manda". E, pô, ainda vou pedir correção.'),
    ('t03', 'yt', 'apresentador', 'processo', ('E', 647.90), ('Pronto', 656.18),
     'E você vai fazer outra coisa enquanto ele termina de editar. Em 20 minutos, 30 minutos, ele termina o seu vídeo. '
     'Se você precisar de alguma correção, você manda pra ele e pronto.'),
    ('t04', 'ig', 'convidado', 'massa', ('Ou', 688.26), ('YouTube', 700.32),
     'Ou seja, produzir conteúdo em massa lá no YouTube e conseguir produzir conteúdo em massa aqui no Instagram também, que é uma dor que eu '
     'tenho enfrentado nos últimos dois anos, de não conseguir produzir em massa aqui no Instagram e já estar ocupado no YouTube.'),
    ('t05', 'ig', 'apresentador', 'por_dia', ('Agora', 703.84), ('dia', 707.54),
     'Agora você vai poder postar tranquilamente, se quiser, dois, três vídeos no dia.'),
]
# Bordas sem silêncio real (fala colada na palavra vizinha EXCLUÍDA): ponto de menor energia, conferido transcrevendo os recortes (tmp/probe).
EDGE_FIX = {
    ('t01', 'in'): (656.49, '"(e) pronto." (excluído) vai até 656,48 e "Você" começa em 656,49; recorte transcrito: "Você vai gastar…"'),
    ('t03', 'out'): (656.485, '"pronto." termina em 656,48 colado no "Você" seguinte (excluído); recorte transcrito: "…manda pra ele e pronto."'),
    ('t03', 'in'): (647.62, 'o fim de "mostrei." marcado pelo Whisper (647,76) cobre o "E" que já começa em 647,67; vale real 647,60–647,66 (−58 dB)'),
    ('t02', 'in'): (1383.165, '"assim," (excluído) e "é" sem pausa; vale de energia em 1383,16–1383,17 (−38 dB)'),
    ('t05', 'out'): (1e9, '"dia" e o conectivo "e" (excluído, a frase segue com outra ferramenta) sem pausa; vale em 707,63–707,65'),
}
T05_OUT = 707.645
GAP_MIN, QUIET_MIN, KEEP_AFTER, KEEP_BEFORE, PROT_PRE, PROT_POST, MIN_PIECE = 0.30, 0.30, 0.12, 0.08, 0.04, 0.15, 0.25

segments, report, edges, t = [], [], [], 0.0
for tid, src, who, scene, (w0, n0), (w1, n1), text in TAKES:
    W = WORDS[src]
    ia, ib = idx(src, w0, n0), idx(src, w1, n1)
    kept, prevw, nextw = W[ia:ib + 1], W[ia - 1], W[ib + 1]
    db, off, floor = envelope(src, prevw['end'], nextw['start'])
    I = lambda tt: int(round((tt - off) * 100))
    T_ = lambda i: off + i / 100
    ref = float(np.percentile(db[I(kept[0]['start']):I(kept[-1]['end'])], 90))
    SIL = ref - 35.0
    DEC = min(SIL, floor + 8.0)
    # entrada: ataque real (40 ms abaixo de SIL antes da primeira palavra)
    i, run = I(kept[0]['start']) + 2, 0
    lo = I(prevw['end'])
    onset = kept[0]['start']
    while i > lo:
        run = run + 1 if db[i] < SIL else 0
        if run >= 4:
            onset = T_(i + 4); break
        i -= 1
    tin = max(min(onset - 0.06, kept[0]['start'] - 0.08), prevw['end'] + 0.04)
    # saída: decaimento real (80 ms abaixo do limiar) + 0,10
    i, run = I(kept[-1]['end']) - 3, 0
    hi = I(nextw['start'])
    decay = None
    while i < hi:
        run = run + 1 if db[i] < DEC else 0
        if run >= 8:
            decay = T_(i - 7); break
        i += 1
    tout = max((decay if decay is not None else nextw['start']) + 0.10, kept[-1]['end'] + 0.15)
    tout = min(tout, nextw['start'] - 0.04)
    notes = []
    if (tid, 'in') in EDGE_FIX:
        tin = EDGE_FIX[(tid, 'in')][0]; notes.append('in: ' + EDGE_FIX[(tid, 'in')][1])
    if (tid, 'out') in EDGE_FIX:
        tout = T05_OUT if tid == 't05' else EDGE_FIX[(tid, 'out')][0]; notes.append('out: ' + EDGE_FIX[(tid, 'out')][1])
    # cortes internos: só pausas reais longas entre palavras
    cuts = []
    for wa, wb in zip(kept, kept[1:]):
        # o Whisper costuma esticar o fim da palavra até o início da seguinte; o intervalo real vem do envelope:
        # procura silêncio (< SIL) entre o início da palavra + 0,12 s e o início da seguinte
        a, b = I(wa['start'] + 0.12), I(wb['start']) + 3
        best, cur = None, None
        for k in range(a, b):
            if db[k] < SIL:
                cur = [k, k] if cur is None else [cur[0], k]
                if best is None or cur[1] - cur[0] > best[1] - best[0]:
                    best = list(cur)
            else:
                cur = None
        if not best or (best[1] - best[0] + 1) / 100 < QUIET_MIN:
            continue
        # fim do decaimento (limiar baixo) dentro do silêncio
        k0 = best[0]; run = 0
        for k in range(best[0], best[1] + 1):
            run = run + 1 if db[k] < DEC else 0
            if run >= 8:
                k0 = k - 7; break
        ac_end = min(wa['end'], T_(best[0]))                 # fim acústico da palavra (não pode haver fala dentro do silêncio medido)
        if wb['start'] - ac_end < GAP_MIN:
            continue
        c0 = max(T_(k0) + KEEP_AFTER, ac_end + PROT_POST)
        c1 = min(T_(best[1] + 1) - KEEP_BEFORE, wb['start'] - PROT_PRE)
        if c1 - c0 >= 0.05:
            cuts.append((round(c0, 3), round(c1, 3), wa['word'].strip(), wb['word'].strip()))
    # pedaços; junta os < 0,25 s
    bounds = [tin] + [x for c in cuts for x in c[:2]] + [tout]
    pieces = [[bounds[2 * k], bounds[2 * k + 1]] for k in range(len(cuts) + 1)]
    k = 0
    while k < len(pieces):
        if pieces[k][1] - pieces[k][0] < MIN_PIECE and len(pieces) > 1:
            if k + 1 < len(pieces):
                pieces[k + 1][0] = pieces[k][0]; cuts.pop(k)
            else:
                pieces[k - 1][1] = pieces[k][1]; cuts.pop(k - 1)
            pieces.pop(k); continue
        k += 1
    for c in cuts:
        report.append({'take': tid, 'removed': [c[0], c[1]], 'between': [c[2], c[3]], 'seconds': round(c[1] - c[0], 3)})
    edges.append({'take': tid, 'src': src, 'in': round(tin, 3), 'out': round(tout, 3), 'speech_ref_db': round(ref, 1), 'sil_db': round(SIL, 1),
                  'decay_db': round(DEC, 1), 'first_word': kept[0]['word'].strip(), 'last_word': kept[-1]['word'].strip(),
                  'excluded_before': prevw['word'].strip(), 'excluded_after': nextw['word'].strip(), 'notes': notes})
    # quantização em quadros: borda "dura" (EDGE_FIX) fica exata; a outra anda < 1 quadro para dentro do silêncio
    hard_in, hard_out = (tid, 'in') in EDGE_FIX, (tid, 'out') in EDGE_FIX
    for pk, (pi, po) in enumerate(pieces):
        first, last = pk == 0, pk == len(pieces) - 1
        if last and not (first and hard_in and not hard_out):
            n = max(1, round((po - pi) * FPS)); pi = po - n / FPS        # ancora a saída (fim real da fala)
        else:
            n = max(1, math.ceil((po - pi) * FPS - 1e-6)) if not last else max(1, round((po - pi) * FPS))
            po = pi + n / FPS                                            # ancora a entrada; a saída avança no silêncio
        segments.append({'src': src, 'source': SRC[src], 'take': tid, 'speaker': who, 'scene': scene, 'piece': pk,
                         'in': round(pi, 4), 'out': round(po, 4), 'frames': n, 'start': round(t, 4)})
        t += n / FPS

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID08',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'V2: bordas pelo decaimento real (limiar relativo por trecho), sem cortar dentro de palavra; frases completas do começo ao fim.',
       'takes': [{'id': x[0], 'src': x[1], 'speaker': x[2], 'scene': x[3], 'text': x[6]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo (p90 − 35 dB) por trecho; cortes internos só em pausas ≥ 0,30 s; '
    'margens 0,12 s após o decaimento e 0,08 s antes do ataque; palavras protegidas', 'cuts': report,
    'removed_total_s': round(sum(r['seconds'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
for e in edges:
    print(e['take'], e['in'], e['out'], e['speech_ref_db'], e['sil_db'], [ (r['between'], r['seconds']) for r in report if r['take']==e['take']])
