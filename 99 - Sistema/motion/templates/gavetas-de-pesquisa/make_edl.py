#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Pesquisa de verdade" (F22 Corte de Live 3D + ID07 Laranja), trechos da live do YouTube (Apresentador).
Versão B do briefing: não há antes/depois de troca de roupa do próprio usuário na fábrica (os trabalhos OMX/PRODUTO só guardam o render
final, sem a gravação original), então o corte da troca de roupa não pode ser provado — vai a "pesquisa de verdade".
Lógica de bordas do EXEMPLO_1 V2 / EXEMPLO_2 (regras do usuário: não comer começo/fim de palavra; fala com sentido):
- limiar de silêncio RELATIVO por trecho: ref = p90 do envelope de 10 ms; silêncio = ref − 35 dB;
- nunca corta dentro de palavra; cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque);
- saída = decaimento real + 0,10 s (mín. fim da palavra + 0,15 s), sem invadir palavra vizinha excluída;
- entrada = ataque − 0,06 s (mín. início − 0,08 s), sem voltar antes do fim da palavra anterior + 0,04 s; nenhum pedaço < 0,25 s.
Fontes de voz: janelas isoladas no ElevenLabs (yt-399-423, yt-773-806). Duas falas caem fora delas — "Não são aquelas imagens
genéricas de banco de imagens." (a janela 399–423 termina no começo do último "imagens") e "Já mostrei vários resultados…" (2189 s) —
e usam a limpeza local DeepFilterNet da live inteira (yt-clean-a18.wav, sincronia 0 ms conferida), sem chamada paga.
Desvio documentado da receita F22 (silêncio > 0,15 s cortado com 0,05 s): a regra do usuário de 27/11 prevalece.
Saídas: edit/edl.json e analysis/silence_edit_report.json. Run: ../../../.venv/bin/python src/make_edl.py
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
ISO = [('yt', SH / 'audio/yt-399-423-el.wav', 399.0, 423.0), ('yt', SH / 'audio/yt-773-806-el.wav', 773.0, 806.0),
       ('yt', SH / 'audio/yt-clean-a18.wav', 0.0, 2211.0)]   # a última é a limpeza local (DeepFilterNet), só onde não há janela isolada


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def find(src, word, near):
    c = [i for i, w in enumerate(WORDS[src]) if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'{src}: palavra {word!r} perto de {near} não encontrada')
    return min(c, key=lambda i: abs(WORDS[src][i]['start'] - near))


# (id, fonte, quem fala, cena, primeira palavra @ início, última palavra @ início, texto conferido)
# V2 (usuário: "nos primeiros segundos de 137 tem um áudio esquisito ininteligível"): em 413,0–414,45 o vídeo de exemplo da galeria
# (a matéria do CEO substituído por IA) ainda tocava COM SOM por baixo do "Olha a qualidade disso" — o isolamento mantém as duas vozes.
# Conferência por diferença de quadros a cada 0,1 s (tela da live sem a webcam): parado a partir de 414,5 s. O "Olha a qualidade disso"
# sai. Diferença de quadros: o último quadro que ainda muda é 414,3→414,4 (0,35); de 414,4 em diante a tela fica parada (≤ 0,09).
# Revisão do diretor: o "disso" vai até 414,62 e ainda tem a cauda "-so" em 414,72–414,78 (transcrição isolada de 414,40–414,90:
# "de… just"); vale de 414,80–414,90 (−31 a −37 dB) e o "E-" ataca em ~414,92 (transcrição isolada de 414,87: "ele pesquisou").
# O trecho começa em 414,865, dentro do vale, com fade de 15 ms — 0,45 s depois da pausa do exemplo.
# Os outros trechos foram conferidos do mesmo jeito: 776–778,5 o reel está pausado; de 778,6 em diante ele volta a passar na tela, mas
# SEM SOM (nas pausas do Apresentador o áudio bruto cai ao piso da sala, −55 a −60 dB, em 783,05–783,30, 784,45–784,80 e 794,25–794,80);
# 415–424,4 e 2189–2199 a tela está parada. Nova ordem (frases inteiras, "ele" = o Cortez, com o rótulo "O Cortez" na tela).
TAKES = [
    ('t01', 'yt', 'apresentador', 'repara', ('repara', 776.74), ('Instagram', 783.88),
     'Repara na qualidade e que ele não colocou animaçõezinhas aleatórias como a gente vê por aí rodando no Instagram.'),
    ('t02', 'yt', 'apresentador', 'cenas', ('Aqui', 791.16), ('internet', 793.56), 'Aqui não. Aqui ele de fato fez pesquisas de cenas na internet.'),
    ('t03', 'yt', 'apresentador', 'noticias', ('Ele', 414.88), ('reais', 419.46), 'Ele pesquisou notícias. Ele pesquisou prints reais.'),
    ('t04', 'yt', 'apresentador', 'generico', ('Não', 420.18), ('imagens', 423.02), 'Não são aquelas imagens genéricas de banco de imagens.'),
    ('t05', 'yt', 'apresentador', 'resultados', ('Já', 2189.82), ('profissional', 2198.02),
     'Já mostrei vários resultados, como o Cortez fez, e saiu com extrema qualidade de editor profissional.'),
]
# Ajustes conferidos no envelope de 10 ms (o Whisper atrasa o "Não" ~0,2 s e põe o 2º "Aqui" antes do vale real):
# t02: na live ele diz "Aqui não. Aqui ele de fato…" emendado — o trecho começa no 1º "Aqui": "jeito." (excluído) decai até 791,07 e
#      o vale fica em 791,10–791,13 (−40 a −55 dB).
# t03: entra em 414,865 (vale antes do "E-" de 414,92), sem a cauda "-so" do "disso"; 0,45 s depois da pausa do exemplo (414,4).
# t02: o 1º "Aqui" sai reduzido ("'qui não") — a transcrição isolada de 790,55–791,115 é só "de qualquer jeito.", então nada dele fica antes do corte.
# t03→t04: "reais." decai até 419,79 e o "Não" ataca em ~419,95 — vale em 419,80–419,88 (−50 a −65 dB); as duas falas são contíguas na
#      live e a emenda só troca de fonte (ElevenLabs → limpeza local) dentro do vale, sem tirar som.
IN_OVERRIDE = {'t02': 791.115, 't03': 414.865, 't04': 419.86}
OUT_OVERRIDE = {'t03': 419.84}
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

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_3', 'version': 'V2', 'pattern': 'f22-corte-de-live-3d-v1', 'format_code': 'F22', 'visual_identity': 'ID07',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'V2 — Gancho "Repara na qualidade e que ele não colocou animaçõezinhas aleatórias…" → aqui não: ele de fato pesquisou cenas na internet → pesquisou notícias e prints reais → não são imagens genéricas de banco de imagens → vários resultados, qualidade de editor profissional. Nenhum trecho com vídeo de exemplo tocando com som.',
       'takes': [{'id': x[0], 'src': x[1], 'speaker': x[2], 'scene': x[3], 'text': x[6]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo por trecho (p90 − 35 dB); bordas pelo ataque/decaimento reais (entrada ataque−0,06 s, saída decaimento+0,10 s, sem invadir palavra vizinha excluída); cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque); pedaços ≥ 0,25 s',
    'cuts': report, 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
for e in edges: print(e)
for r in report: print(r)
