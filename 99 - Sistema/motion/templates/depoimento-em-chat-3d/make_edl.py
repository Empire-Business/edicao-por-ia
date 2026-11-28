#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Isso daqui é sinistro" (F10 + ID01): áudio real do Convidado (mensagem de voz que o Apresentador tocou na
live do YouTube) + trechos do Convidado e do Apresentador na live do Instagram.
V2 (regra nova do usuário: nada de final de palavra comido) — mesma regra do EXEMPLO_1 (jobs/cortez-live-c7/src/make_edl.py):
- limiar de silêncio RELATIVO por trecho, na voz isolada (ElevenLabs) que vai para o vídeo: ref = percentil 90 do envelope de 10 ms
  dentro do trecho; silêncio = ref − 35 dB;
- nunca corta dentro de palavra; corte interno só em silêncio contínuo ≥ 0,30 s (0,12 s depois do decaimento, 0,08 s antes do ataque),
  conferido com o mesmo envelope de check_edges.py (respiro/cauda fraca contam como som);
- saída = decaimento real da última palavra + 0,10 s (mín. fim da palavra + 0,15 s), sem passar de (próxima palavra excluída − 0,04 s);
  entrada = ataque − 0,06 s (mín. início − 0,08 s), sem voltar antes de (fim da palavra anterior + 0,04 s); pedaços ≥ 0,25 s.
Ajuste documentado: t10 entra em "já" (519,435), no vale entre "Dinheiro" e "já" — sem pausa na fala; a regra recuaria 40 ms dentro
do "já". t07 começa em "um": o "E… de" arrastado antes do silêncio real (1717,92–1717,98) fica fora.
Validação: ../material-compartilhado/bin/check_edges.py . Saídas: edit/edl.json e analysis/silence_edit_report.json.
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
SRC = {'yt': '<PREENCHER: fonte ou prova própria>',
       'ig': '<PREENCHER: fonte ou prova própria>'}
FPS = 30
WORDS = {k: [w for s in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s['words']] for k in SRC}
ISO = [('yt', SH / 'audio/yt-1682-1762-el.wav', 1682.0, 1762.0), ('ig', SH / 'audio/ig-240-530-el.wav', 240.0, 530.0)]


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
    ('t01', 'yt', 'audio', 'hook', ('Caraca', 1724.22), ('hein', 1725.46), 'Caraca, muito brabo mesmo, hein?'),
    ('t02', 'ig', 'apresentador', 'pergunta', ('Quanto', 494.34), ('ferramenta', 495.40), 'Quanto tempo você tá usando a ferramenta?'),
    ('t03', 'ig', 'convidado', 'dois_dias', ('Estou', 496.00), ('dias', 497.08), 'Tô usando, acho que há dois dias.'),
    ('t04', 'ig', 'convidado', 'mensagem', ('Quando', 507.08), ('ferramenta', 507.54), 'Quando eu vi a ferramenta'),
    ('t05', 'ig', 'convidado', 'mensagem', ('na', 510.58), ('sinistro', 512.98), 'na prática, já mandei mensagem pro Apresentador: caramba, isso daqui é sinistro, hein?'),
    ('t06', 'yt', 'audio', 'estilos', ('Aí', 1697.14), ('cor', 1703.56), 'Aí já pedi pra ele montar um prompt pra mim, de acordo com a edição que eu gostei muito. Só mudar o estilo de vídeo e estilo de cor.'),
    ('t07', 'yt', 'audio', 'cortes', ('um', 1718.06), ('bom', 1721.96), 'Um vídeo longo que eu fiz aí no YouTube já gerou uns 10 cortes do Instagram. Corte muito bom.'),
    ('t08', 'ig', 'convidado', 'bem_editado', ('E', 341.56), ('bacana', 344.56), 'E é bem editado também, com efeito, com música, com tudo, visual bacana.'),
    ('t09', 'ig', 'convidado', 'postei', ('E', 515.74), ('vídeo', 516.74), 'E eu já postei um vídeo,'),
    ('t10', 'ig', 'convidado', 'postei', ('já', 519.44), ('ferramenta', 521.34), 'já tenho o vídeo lá, editado 100% pela ferramenta.'),
    ('t11', 'yt', 'audio', 'fecho', ('Muito', 1735.70), ('sinistro', 1736.14), 'Muito sinistro.'),
]

# Ajustes documentados (bordas que a regra deixaria cair no resto de uma palavra EXCLUÍDA, conferidos no envelope de 10 ms):
# t10: "já" colado em "Dinheiro" (vale de 519,435); t11: a voz do áudio tem ruídos/hesitação 1734,67–1735,66 acima do limiar relativo
# (o Whisper põe "Muito" em 1735,70, mas o ataque real é 1735,84) → entra no silêncio 1735,72–1735,83.
# t04/t09: "ferramenta|já" e "vídeo|já" sem pausa; a saída vai no vale real (508,00–508,03 e 516,98), não 40 ms antes.
IN_OVERRIDE = {'t10': 519.435, 't11': 1735.775}
OUT_OVERRIDE = {'t04': 508.025, 't09': 516.985}
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


segments, report, edges, t = [], [], [], 0.0
for tid, src, who, scene, (w0_, n0), (w1_, n1), text in TAKES:
    W = WORDS[src]
    ia, ib = find(src, w0_, n0), find(src, w1_, n1)
    kept, prev, nxt = W[ia:ib + 1], W[ia - 1], W[ib + 1]
    k = iso_for(src, prev['end'], nxt['start'])
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

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_2', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID01',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'Gancho = áudio real do Convidado ("Caraca, muito brabo mesmo") → 2 dias de uso → "caramba, isso daqui é sinistro" → estilos → 1 vídeo longo, 10 cortes → bem editado → postou (Reel real do Convidado) → "Muito sinistro."',
       'takes': [{'id': x[0], 'src': x[1], 'speaker': x[2], 'scene': x[3], 'text': x[6]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo por trecho (p90 − 35 dB); bordas pelo ataque/decaimento reais (entrada ataque−0,06 s, saída decaimento+0,10 s, sem invadir palavra vizinha excluída); cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque); pedaços ≥ 0,25 s',
    'cuts': report, 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
for e in edges: print(e)
for r in report: print(r)
