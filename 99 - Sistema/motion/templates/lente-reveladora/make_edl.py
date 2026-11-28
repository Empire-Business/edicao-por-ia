#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Cara de IA" (F10 + ID07). V2: edição de fala que NÃO come o fim das palavras.
Usuário (V1 dos cortes do lote): "vc comeu muito o final das palavras que eu disse" + regra durável: a fala tem de fazer sentido do começo
ao fim, nunca cortar uma frase/ideia no meio.
Regras (V2):
- limiar de silêncio RELATIVO por take: ref = percentil 90 do envelope de 10 ms (voz isolada ElevenLabs) dentro do take; SIL = ref − 35 dB;
- nunca cortar dentro de palavra: cortes internos só entre palavras com vão ≥ 0,30 s E envelope < SIL por ≥ 0,30 s; o pedaço anterior
  termina ≥ 0,12 s depois do decaimento real da palavra (e ≥ fim + 0,15 s); o seguinte começa ≥ 0,08 s antes do ataque;
- entrada do take = ataque − 0,06 s (o ataque vem do envelope; o Whisper às vezes adianta a palavra em 0,3–0,4 s), nunca antes do fim real
  da palavra anterior + 0,04 s; saída = decaimento (< SIL por 80 ms) + 0,10 s, no mínimo fim + 0,15 s, limitada ao início real da próxima
  palavra excluída − 0,04 s;
- pedaços < 0,25 s não existem (o corte interno não é feito); quadros de 30 fps arredondados para FORA (nunca encurta a palavra), exceto
  quando o limite é a próxima palavra (aí para dentro).
Exclusões deliberadas (documentadas): falso começo "pre…" antes de "prezou" (IG 439,46–439,80) e o "na" alongado de "cenas na… na internet"
(IG ≈446,86–447,25). Saídas: edit/edl.json e analysis/silence_edit_report.json.
Run: ../../../.venv/bin/python src/make_edl.py
"""
import json, math, re, unicodedata
from pathlib import Path
import numpy as np
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
FPS = 30
SRC = {'ig': '<PREENCHER: fonte ou prova própria>',
       'yt': '<PREENCHER: fonte ou prova própria>'}
ISO = {'ig': (SH / 'audio/ig-240-530-el.wav', 240.0), 'yt': (SH / 'audio/yt-773-806-el.wav', 773.0)}
WORDS = {k: [w for s in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s['words']] for k in SRC}
ENV = {}
for k, (p, off) in ISO.items():
    sr, x = wavfile.read(p)
    x = x.astype(np.float32) / 32768
    x = x.mean(1) if x.ndim > 1 else x
    H = int(sr * 0.01); n = len(x) // H
    ENV[k] = (20 * np.log10(np.sqrt((x[:n * H].reshape(n, H) ** 2).mean(1)) + 1e-9), off)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def widx(src, word, near):
    c = [i for i, w in enumerate(WORDS[src]) if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'palavra {word!r} perto de {near} não encontrada em {src}')
    return min(c, key=lambda i: abs(WORDS[src][i]['start'] - near))


def fi(src, t): return int(round((t - ENV[src][1]) / 0.01))
def ft(src, i): return ENV[src][1] + i * 0.01


def onset(src, t_lo, t_hi, sil):
    """1º quadro em [t_lo, t_hi] a partir do qual o envelope fica ≥ SIL por 30 ms."""
    e = ENV[src][0]
    for i in range(fi(src, t_lo), fi(src, t_hi)):
        if all(e[i + k] >= sil for k in range(3)):
            return ft(src, i)
    return t_hi


def decay(src, t_from, t_cap, sil):
    """início do 1º trecho de 80 ms com envelope < SIL depois de t_from (ou t_cap)."""
    e = ENV[src][0]
    for i in range(fi(src, t_from), fi(src, t_cap)):
        if all(e[i + k] < sil for k in range(8)):
            return ft(src, i), True
    return t_cap, False


# (id, fonte, cena, 1ª palavra @, última palavra @, exclusões dentro do take [(t0, t1, motivo)], ajustes, texto conferido)
# ajustes: 'next_real' = início REAL (envelope) da palavra seguinte excluída, quando o Whisper a adianta; 'in_word' = ataque real medido;
# 'in_at' = entrada fixa. t01: 422,45–422,53 é o fim do "porque" colado no "se" (começando ali o Whisper ouve "Porque se…"/"E se…");
# entrando em 422,55, no /s/ do "se", ouve "Se a gente for rolar…" — o gancho abre limpo. O "né?" depois de "monte" (427,91–428,10) é
# fala real e fecha a frase (não há silêncio entre "monte" e "né"); fica.
TAKES = [
    ('t01', 'ig', 'hook', ('se', 422.52), ('monte', 427.60), [], {'in_at': 422.55},
     'Se a gente for rolar o Instagram, tá inundado de vídeo editado por IA, você encontra um monte, né?'),
    ('t02', 'yt', 'template', ('tem', 787.12), ('não', 791.28), [], {'next_real': 791.69},
     'Tem cara de IA. Tem umas animações que todo mundo faz e fica de qualquer jeito. Aqui não.'),
    ('t03', 'ig', 'pro', ('A', 437.22), ('cenas', 446.32), [(439.42, 439.84, 'falso começo "pre…" antes de "prezou"')], {'next_real': 446.92},
     'A gente prezou por montar a ferramenta de uma forma que realmente chega num nível profissional de edição. Ela realmente pesquisa cenas'),
    ('t04', 'ig', 'pesquisa', ('internet', 447.88), ('faria', 450.98), [], {'in_word': 447.77, 'prev_real_end': 447.25},
     'na internet para colocar como um editor profissional faria.'),
    ('t05', 'yt', 'qualidade', ('Isso', 798.42), ('profissional', 801.62), [], {},
     'Isso daqui, nessa qualidade aqui, é a qualidade de um editor profissional.'),
]

segments, report, edges, t = [], [], [], 0.0
for tid, src, scene, (w0, n0), (w1, n1), excl, adj, text in TAKES:
    i0, i1 = widx(src, w0, n0), widx(src, w1, n1)
    W = WORDS[src]
    kept = [w for w in W[i0:i1 + 1] if not any(a - 0.02 <= w['start'] and w['end'] <= b + 0.02 for a, b, _ in excl)]
    e, off = ENV[src]
    seg_e = e[fi(src, kept[0]['start']):fi(src, kept[-1]['end'])]
    ref = float(np.percentile(seg_e, 90)); SIL = ref - 35.0
    # entrada: ataque real − 0,06 s; nunca antes do fim real da palavra anterior + 0,04 s
    prev = W[i0 - 1] if i0 > 0 else None
    prev_end = adj.get('prev_real_end') or (decay(src, prev['start'], kept[0]['start'] + 0.1, SIL)[0] if prev else kept[0]['start'] - 1)
    on = adj.get('in_word') or onset(src, max(prev_end, kept[0]['start'] - 0.5), kept[0]['start'] + 0.25, SIL)
    tin = max(on - 0.06, prev_end + 0.04)
    if kept[0]['start'] >= on - 0.10:          # Whisper coerente com o envelope: inclui também 80 ms antes da palavra transcrita
        tin = max(min(tin, kept[0]['start'] - 0.08), prev_end + 0.04)
    if 'in_at' in adj:                         # entrada medida à mão (documentada abaixo)
        tin = adj['in_at']
    # saída: decaimento + 0,10 s (≥ fim + 0,15 s), limitada ao início real da próxima palavra − 0,04 s
    nxt = W[i1 + 1] if i1 + 1 < len(W) else None
    cap = (adj.get('next_real') or (nxt['start'] if nxt else kept[-1]['end'] + 1.0)) - 0.04
    d_end, found = decay(src, kept[-1]['end'] - 0.10, cap, SIL)
    tout = min(max(d_end + 0.10, kept[-1]['end'] + 0.15), cap)
    capped_out = tout >= cap - 1e-6
    # cortes internos: só entre palavras, vão ≥ 0,30 s com envelope < SIL por ≥ 0,30 s; ou exclusão deliberada
    cuts = []
    for a, b in zip(kept, kept[1:]):
        forced = [x for x in excl if a['end'] - 0.02 <= x[0] and x[1] <= b['start'] + 0.3]
        if forced:
            x0, x1, why = forced[0]
            pa, _ = decay(src, a['end'] - 0.10, x0, SIL)
            out_a = min(max(pa + 0.12, a['end'] + 0.15), x0 - 0.02)
            on_b = onset(src, x1, b['start'] + 0.25, SIL)
            in_b = max(on_b - 0.08, x1 + 0.04)
            cuts.append((out_a, in_b, why)); continue
        if b['start'] - a['end'] < 0.30:
            continue
        lo, hi = fi(src, a['end']), fi(src, b['start'] + 0.25)
        run = best = 0
        for i in range(lo, hi):
            run = run + 1 if e[i] < SIL else 0
            best = max(best, run)
        if best < 30:
            continue
        pa, _ = decay(src, a['end'] - 0.10, b['start'], SIL)
        out_a = max(pa + 0.12, a['end'] + 0.15)
        in_b = onset(src, pa, b['start'] + 0.25, SIL) - 0.08
        if in_b - out_a > 0.05:
            cuts.append((out_a, in_b, 'pausa'))
    pieces, s0 = [], tin
    for out_a, in_b, why in cuts:
        pieces.append([s0, out_a]); s0 = in_b
        report.append({'take': tid, 'gap': [round(out_a, 3), round(in_b, 3)], 'removed': round(in_b - out_a, 3), 'reason': why})
    pieces.append([s0, tout])
    # nada menor que 0,25 s: junta com o vizinho (desfaz o corte)
    k = 0
    while k < len(pieces):
        if pieces[k][1] - pieces[k][0] < 0.25 and len(pieces) > 1:
            if k + 1 < len(pieces): pieces[k] = [pieces[k][0], pieces[k + 1][1]]; del pieces[k + 1]
            else: pieces[k - 1] = [pieces[k - 1][0], pieces[k][1]]; del pieces[k]
            continue
        k += 1
    edges.append({'take': tid, 'source': src, 'speech_ref_db': round(ref, 1), 'sil_db': round(SIL, 1), 'in': round(tin, 3), 'onset': round(on, 3),
                  'out': round(tout, 3), 'decay_end': round(d_end, 3), 'decay_found': found, 'out_capped_by_next_word': capped_out})
    for j, (pi, po) in enumerate(pieces):
        last = j == len(pieces) - 1
        n = (math.floor if (last and capped_out) else math.ceil)((po - pi) * FPS - 1e-6)
        segments.append({'source': SRC[src], 'src': src, 'take': tid, 'speaker': 'apresentador', 'scene': scene, 'piece': j,
                         'in': round(pi, 4), 'out': round(pi + n / FPS, 4), 'frames': n, 'start': round(t, 4)})
        t += n / FPS

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID07',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'V2: bordas pelo envelope relativo (SIL = p90 − 35 dB), sem cortar dentro de palavra. Gancho "rolar o Instagram… inundado de vídeo '
               'editado por IA, você encontra um monte" → "tem cara de IA… aqui não" → nível profissional + pesquisa de cenas → "qualidade de um editor profissional".',
       'takes': [{'id': x[0], 'source': x[1], 'scene': x[2], 'text': x[7], 'excluded': [list(e_) for e_ in x[5]]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: SIL relativo por take (p90 − 35 dB); cortes internos só entre palavras com vão ≥ 0,30 s e silêncio ≥ 0,30 s; '
    '≥ 0,12 s após o decaimento e ≥ 0,08 s antes do ataque; pedaços ≥ 0,25 s', 'cuts': report,
    'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}, ensure_ascii=False))
for e_ in edges: print(e_)
for s in segments: print(s['take'], s['piece'], s['in'], s['out'], s['frames'], s['start'])
