#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Tá de graça" (F22 Corte de Live 3D + ID04), live do Instagram (Convidado, cliente; Apresentador pergunta).
Regras de fala (usuário, 27/11/2026: "vc comeu muito o final das palavras"; "tem que fazer sentido"):
- limiar de silêncio RELATIVO por trecho, na voz isolada (ElevenLabs) que vai para o vídeo: ref = percentil 90 do envelope de 10 ms dentro
  do trecho; silêncio = ref − 35 dB;
- nunca corta dentro de palavra; corte interno só em silêncio contínuo ≥ 0,30 s (0,12 s depois do decaimento, 0,08 s antes do ataque);
- saída = decaimento real da última palavra + 0,10 s (mín. fim + 0,15 s), sem invadir a palavra seguinte excluída; entrada = ataque − 0,06 s;
- nenhum pedaço menor que 0,25 s; quantização em quadros de 30 fps sem encurtar o pedaço.
Bordas conferidas à mão no envelope (o Whisper erra fronteiras entre quem fala; ver IN/OUT_OVERRIDE abaixo).
A janela isolada termina em 782,0 s; o fim de "comparação" decai até ~782,06 s (bruto): a voz usa uma cópia local com a cauda do áudio
bruto da live emendada (audio/ig-757-783-patched.wav, src/make_voice.py).
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
ISO = [('ig', J / 'audio/ig-757-783-patched.wav', 757.0, 783.0)]   # src/make_patch.py: janela isolada + cauda do bruto


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
    ('t01', 'ig', 'convidado', 'hook', ('Pô', 761.02), ('oferta', 771.98),
     'Pô, a oferta está de graça, pô. Pelo que entrega, o negócio está de graça. Só a edição em si, pô, se eu fosse fazer as edições que eu faço, né, o Cortez, pagar fora, já seria muito mais que a oferta.'),
    ('t02', 'ig', 'apresentador', 'meses', ('Em', 773.64), ('né', 776.30), 'Em um, dois meses, só de editor, você já ia pagar muito mais, né?'),
    ('t03', 'ig', 'convidado', 'injusta', ('É', 776.78), ('comparação', 781.44), 'É, sim, só que a edição em si, né? Agora, as outras ferramentas, então, fica até injusta a comparação.'),
]
# Ajustes documentados (conferidos no envelope de 10 ms da voz isolada e no áudio bruto):
# t01 entrada: "contas?" do Apresentador soa até ~760,93 (o Whisper marca 760,56); vale do envelope em 760,96–760,98 (−44 dB), "Pô" ataca em 761,00.
# t01 saída: "oferta" decai a −63 dB em 772,24; "Juntando" (Convidado, excluído) ataca em ~772,28 (o Whisper marca 772,40) → sai em 772,25.
# t03 saída: "comparação" decai até ~782,06 no bruto; o "É" seguinte (Apresentador, excluído) só ataca em ~782,75 (o Whisper marca 781,94).
IN_OVERRIDE = {'t01': 760.96}
OUT_OVERRIDE = {'t01': 772.25, 't03': 782.16}
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

edl = {'version': 2, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f22-corte-de-live-3d-v1', 'format_code': 'F22', 'visual_identity': 'ID04',
       'sources': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'Gancho "a oferta tá de graça" (Convidado) → pelo que entrega → só a edição já seria mais cara → Apresentador: um, dois meses de editor → Convidado: com as outras ferramentas, a comparação fica injusta.',
       'takes': [{'id': x[0], 'src': x[1], 'speaker': x[2], 'scene': x[3], 'text': x[6]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'V2: limiar relativo por trecho (p90 − 35 dB); bordas pelo ataque/decaimento reais (entrada ataque−0,06 s, saída decaimento+0,10 s, sem invadir palavra vizinha excluída); cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s após o decaimento, 0,08 s antes do ataque); pedaços ≥ 0,25 s',
    'cuts': report, 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
for e in edges: print(e)
for r in report: print(r)
