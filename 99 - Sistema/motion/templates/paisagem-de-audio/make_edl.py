#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"O áudio do cliente" (F22 Corte de Live 3D + ID03 Azul, legenda L06). Live do YouTube: o Apresentador toca na live o
áudio de WhatsApp real do Convidado (cliente). Ordem: teaser "Caraca, muito brabo mesmo, hein?" → Apresentador apresenta o áudio → o áudio do Convidado
quase inteiro e na ordem (sem o trecho sobre outras ferramentas e sem a repetição do teaser) → Apresentador: quem é o Convidado.
Regras de borda do lote (usuário: "vc comeu muito o final das palavras"; a fala precisa fazer sentido do começo ao fim):
- limiar de silêncio RELATIVO por trecho, na voz limpa que vai para o vídeo: ref = percentil 90 do envelope de 10 ms; silêncio = ref − 35 dB;
- nunca corta dentro de palavra; corte interno só em silêncio contínuo ≥ 0,30 s (0,12 s depois do decaimento, 0,08 s antes do ataque);
- saída = decaimento real da última palavra + 0,10 s (mín. fim da palavra + 0,15 s, sem invadir a próxima palavra excluída);
  entrada = ataque − 0,06 s (mín. início − 0,08 s); nenhum pedaço < 0,25 s; quantização a 30 fps sem encurtar.
Voz: janela yt-1682-1762-el.wav (ElevenLabs, já feita no lote) e, só para a apresentação do Apresentador (1679–1682,5 s, que cai entre duas janelas
isoladas), a limpeza local DeepFilterNet da live (audio/yt-1676-1690-dfn.wav, recorte de material-compartilhado/audio/yt-clean-a18.wav).
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
SRC = {'yt': '<PREENCHER: fonte ou prova própria>',
       'ig': '<PREENCHER: fonte ou prova própria>'}
FPS = 30
WORDS = {k: [w for s in json.loads((SH / f'analysis/{k}.transcript.json').read_text())['segments'] for w in s['words']] for k in SRC}
ISO = [('yt', SH / 'audio/yt-1682-1762-el.wav', 1682.0, 1762.0), ('yt', J / 'audio/yt-1676-1690-dfn.wav', 1676.0, 1690.0)]


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
    ('t00', 'yt', 'convidado', 'hook', ('Caraca', 1724.22), ('hein', 1725.46), 'Caraca, muito brabo mesmo, hein?'),
    ('t01', 'yt', 'apresentador', 'intro', ('Deixa', 1679.22), ('clientes', 1681.78), 'Deixa eu mostrar pra vocês aqui um áudio de um dos nossos clientes.'),
    ('t02', 'yt', 'convidado', 'craque', ('Aí', 1691.34), ('hein', 1694.14), 'Aí, Apresentador. Aí, tô ficando craque, hein?'),
    ('t03', 'yt', 'convidado', 'estilo', ('Aí', 1697.14), ('negócio', 1704.78), 'Aí já pedi pra ele montar um prompt pra mim, de acordo com a edição que eu gostei muito. Só mudar o estilo de vídeo e estilo de cor, de acordo com o negócio.'),
    ('t04', 'yt', 'convidado', 'cortes', ('E', 1717.62), ('bom', 1721.96), 'E de um vídeo longo que eu fiz aí no YouTube, já gerou uns 10 cortes do Instagram. Corte muito bom.'),
    ('t05', 'yt', 'convidado', 'sinistro', ('Muito', 1735.70), ('sinistro', 1736.14), 'É muito sinistro.'),
    ('t06', 'yt', 'apresentador', 'convidado', ('O', 1739.50), ('bons', 1751.78), 'O Convidado aí, do canal Canal do convidado, ele comprou o Cortez. Ele não é uma pessoa muito tecnológica e ele está conseguindo editar e tendo resultados muito bons.'),
]
# Bordas conferidas no envelope de 10 ms (palavra vizinha EXCLUÍDA colada, sem silêncio entre elas): corte no mínimo de energia.
IN_OVERRIDE = {'t00': 1724.245,   # "esse..." (falso começo) termina em 1724,22; mínimo −58 dB em 1724,25; "Caraca" ataca em 1724,27
               't04': 1717.16,    # "Instagram." termina em ~1717,12 (mínimo −44 dB em 1717,17); o "E…" arrastado começa em 1717,19
               't05': 1735.47}    # antes: risadas/estalos em rajada 1734,68–1735,3; mínimo −47/−51 dB em 1735,46–1735,52; "É" ataca em ~1735,55
                                  # (transcrição isolada do trecho: "É muito sinistro."; o Whisper contínuo marcou "Muito" em 1735,70)
OUT_OVERRIDE = {'t01': 1682.42,   # "clientes" decai até −60 dB em 1682,38; o "que" seguinte só vem em ~1684,2 (o Whisper contínuo o marcou em 1682,34)
                't03': 1705.09,   # "negócio" decai até 1705,07 (mínimo −44 dB em 1705,10); o "do" seguinte ataca em 1705,14
                't05': 1736.76}   # "sinistro." decai até −43/−52 dB em 1736,75–77; "Daqui" ataca em 1736,79
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

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f22-corte-de-live-3d-v1', 'format_code': 'F22', 'visual_identity': 'ID03',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'Teaser do áudio real do Convidado → Apresentador apresenta o áudio de um cliente → o áudio na ordem (craque → pediu outro estilo e cor → 10 cortes de um vídeo longo → muito sinistro) → Apresentador: o Convidado não é técnico e tem resultados.',
       'takes': [{'id': x[0], 'src': x[1], 'speaker': x[2], 'scene': x[3], 'text': x[6]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo por trecho (p90 − 35 dB); bordas pelo ataque/decaimento reais (entrada ataque−0,06 s, saída decaimento+0,10 s, sem invadir palavra vizinha excluída); cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque); pedaços ≥ 0,25 s',
    'cuts': report, 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
for e in edges: print(e)
for r in report: print(r)
