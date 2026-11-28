#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Ouve quem usa" (F10 + ID04): narração de IA (ElevenLabs, já gerada) + trechos REAIS do Convidado (live do Instagram).
Ordem: IA d6a ("…é melhor você ouvir quem já usa.") → Convidado j1 ("Quando eu vi a ferramenta… caramba, isso daqui é sinistro.")
→ Convidado j2 ("E eu já postei um vídeo… editado 100% pela ferramenta.") → IA d6b ("O Convidado não é uma pessoa muito tecnológica…") → CTA.
Narrações: inteiras, nada removido. Trechos do Convidado: regras do usuário (V2 dos cortes) — limiar de silêncio RELATIVO por trecho na voz
isolada (p90 do envelope de 10 ms − 35 dB); nunca corta dentro de palavra; entrada = ataque − 0,06 s (≥ fim da palavra anterior + 0,04 s);
saída = decaimento (80 ms abaixo do limiar) + 0,10 s, no mínimo fim da palavra + 0,15 s, sem invadir a próxima palavra (− 0,04 s);
cortes internos só em silêncio contínuo ≥ 0,30 s (0,12 s depois do decaimento, 0,08 s antes do ataque); pedaços ≥ 0,25 s.
Respiros entre blocos: só silêncio inserido (nada cortado). Validação: ../material-compartilhado/bin/check_edges.py <job>.
Saídas: edit/edl.json, analysis/silence_edit_report.json. Run: ../../../.venv/bin/python src/make_edl.py
"""
import json, math, re, sys, unicodedata
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'material-compartilhado/bin'))
import check_edges as CHK

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
IGSRC = '<PREENCHER: fonte ou prova própria>'
TTS = {'d6a': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d6a-v1.wav', 'd6b': 'workspace://99 - Sistema/jobs/material-compartilhado/audio/tts/d6b-v1.wav'}
FPS = 30
WORDS = [w for s in json.loads((SH / 'analysis/ig.transcript.json').read_text())['segments'] for w in s['words']]
ISO = (SH / 'audio/ig-240-530-el.wav', 240.0, 530.0)
LEAD = 0.08                      # silêncio antes da 1ª palavra (o gancho começa já falando)
GAP = {'d6a': 0.42, 'j1': 0.36, 'j2': 0.40}   # respiro inserido DEPOIS de cada bloco (troca de voz IA ↔ Convidado)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def find(word, near):
    c = [i for i, w in enumerate(WORDS) if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'palavra {word!r} perto de {near} não encontrada')
    return min(c, key=lambda i: abs(WORDS[i]['start'] - near))


# (id, primeira palavra @ início, última palavra @ início, texto conferido)
TAKES = {
    'j1': (('quando', 507.08), ('sinistro', 512.98),
           'Quando eu vi a ferramenta, já, na hora, via o funcionamento na prática, eu já mandei mensagem pro Apresentador: caramba, isso daqui é sinistro.'),
    'j2': (('E', 515.74), ('ferramenta', 521.34),
           'E eu já postei um vídeo já no canal de Canal do convidado. Já tem um vídeo lá editado 100% pela ferramenta.'),
}
ORDER = ['d6a', 'j1', 'j2', 'd6b']
# Ajustes documentados de borda (envelope de 10 ms conferido): o Whisper põe "Não," (excluída) até 507,04, mas a energia dela vai até 507,12;
# o "quando" começa no estouro do /k/ em 507,16 → entrada no vale de 507,13 (sem resto do "Não"). Em j2, "ver." (excluída) decai até 515,62 e
# há um respiro fraco (−45 a −54 dB) antes do "E eu" (515,93) → entrada em 515,66, já sem o resto de "ver.".
IN_OVERRIDE = {'j1': 507.13, 'j2': 515.66}
# Saída de j1: "sinistro" decai até 513,58 (−50 dB); em 513,64 há um estalo curto (−30 dB, 40 ms) que não é palavra (transcrito isolado vira
# "Marcinho"; com ou sem ele o Whisper acrescenta "hein?"). Saída no vale de 513,63 = fim da palavra (513,48) + 0,15 s, depois do decaimento.
OUT_OVERRIDE = {'j1': 513.63}

sr, x = wavfile.read(ISO[0]); x = x.astype(np.float32) / 32768; x = x.mean(1) if x.ndim > 1 else x
h = int(sr * 0.01); n = len(x) // h
DB = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9); BASE = ISO[1]
fr = lambda tt: int(round((tt - BASE) / 0.01))
tm = lambda i: BASE + i * 0.01
cdb, cfloor = CHK.env(ISO[0]); cthr = cfloor + 8
cfr = lambda tt: int((tt - BASE) * 100)


def ig_take(tid):
    (w0, n0), (w1, n1), text = TAKES[tid]
    ia, ib = find(w0, n0), find(w1, n1)
    kept, prev, nxt = WORDS[ia:ib + 1], WORDS[ia - 1], WORDS[ib + 1]
    ref = float(np.percentile(DB[fr(kept[0]['start']):fr(kept[-1]['end'])], 90)); SIL = ref - 35.0
    quiet = DB < SIL

    def decay_end(w, limit):
        i, lim = fr(w['end'] - 0.05), fr(limit)
        while i < lim:
            if quiet[i:i + 8].all():
                return tm(i)
            i += 1
        return limit

    def onset(w, limit):
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
    runs, i0 = [], None
    for i in range(fr(tin), fr(tout) + 1):
        if i < fr(tout) and quiet[i]:
            i0 = i if i0 is None else i0
        else:
            if i0 is not None and i - i0 >= 30:
                runs.append([tm(i0), tm(i)])
            i0 = None

    def chk_tail(tt, lim):
        j, run = max(cfr(tt) - 3, 0), 0
        while j < cfr(lim):
            run = run + 1 if cdb[j] < cthr else 0
            if run >= 6:
                return BASE + (j - 5) / 100
            j += 1
        return lim

    def chk_head(tt, lim):
        j, run = cfr(tt), 0
        while j > cfr(lim):
            run = run + 1 if cdb[j] < cthr else 0
            if run >= 4:
                return BASE + (j + 4) / 100
            j -= 1
        return lim
    cuts = []
    for r0, r1 in runs:
        if r0 <= tin + 0.05:
            tin = max(tin, r1 - 0.06); continue
        if r1 >= tout - 0.05:
            tout = min(tout, r0 + 0.10); continue
        ca, cb = r0 + 0.12, r1 - 0.08
        ca = max(ca, chk_tail(ca, r1) + 0.02); cb = min(cb, chk_head(cb, r0) - 0.02)
        if cb - ca >= 0.10:
            cuts.append([ca, cb])
    bounds = [tin] + [v for c in cuts for v in c] + [tout]
    pieces = [[bounds[i], bounds[i + 1]] for i in range(0, len(bounds), 2)]
    while len(pieces) > 1 and min(b - a for a, b in pieces) < 0.25:
        j = min(range(len(pieces)), key=lambda i: pieces[i][1] - pieces[i][0]); m = j - 1 if j > 0 else j
        pieces[m:m + 2] = [[pieces[m][0], pieces[m + 1][1]]]
    edge = {'take': tid, 'ref_db': round(ref, 1), 'sil_db': round(SIL, 1), 'in': round(tin, 3), 'onset': round(on, 3), 'first_word': [kept[0]['word'].strip(), kept[0]['start']],
            'out': round(tout, 3), 'decay_end': round(dec, 3), 'last_word': [kept[-1]['word'].strip(), kept[-1]['end']],
            'prev_word': [prev['word'].strip(), prev['end']], 'next_word': [nxt['word'].strip(), nxt['start']]}
    return pieces, [[pieces[i][1], pieces[i + 1][0]] for i in range(len(pieces) - 1)], kept, text, edge


segments, report, edges, words_out, t = [], [], [], [], LEAD
for blk in ORDER:
    if blk in TTS:
        wj = json.loads((SH / f'audio/tts/{blk}-v1.words.json').read_text())['words']
        import subprocess
        dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(SH / f'audio/tts/{blk}-v1.wav')],
                                   capture_output=True, text=True).stdout)
        segments.append({'source': TTS[blk], 'src': 'tts', 'take': blk, 'speaker': 'ia', 'piece': 0, 'in': 0.0, 'out': round(dur, 4), 'start': round(t, 4)})
        words_out += [{'word': w['word'], 'start': round(t + w['start'], 3), 'end': round(t + w['end'], 3), 'speaker': 'ia', 'block': blk} for w in wj]
        t += dur
    else:
        pieces, cuts, kept, text, edge = ig_take(blk)
        edges.append(edge)
        for c in cuts:
            report.append({'take': blk, 'cut': [round(c[0], 3), round(c[1], 3)], 'removed': round(c[1] - c[0], 3)})
        for pi_, (a, b) in enumerate(pieces):
            nfr = math.ceil((b - a) * FPS - 1e-6)
            cap = b + 0.03 if pi_ < len(pieces) - 1 else edge['next_word'][1] - 0.01
            if a + nfr / FPS > cap:
                nfr -= 1
            d = nfr / FPS
            segments.append({'source': IGSRC, 'src': 'ig', 'take': blk, 'speaker': 'convidado', 'piece': pi_, 'in': round(a, 4), 'out': round(a + d, 4),
                             'frames': nfr, 'start': round(t, 4)})
            for w in kept:
                if a - 0.02 <= w['start'] < a + d:
                    words_out.append({'word': w['word'].strip(), 'start': round(t + w['start'] - a, 3), 'end': round(t + min(w['end'], a + d) - a, 3),
                                      'speaker': 'convidado', 'block': blk})
            t += d
    if blk in GAP:
        t += GAP[blk]
SPEECH = round(t + 0.30, 3)          # cauda de 0,30 s depois da última palavra da IA

# texto conferido (maioria de 6 transcrições: voz isolada/bruta/DeepFilter × large-v3/turbo + envelope) para as legendas do Convidado (o Whisper ouve "para" por "pro", "%" separado etc.)
VER = {'j1': TAKES['j1'][2], 'j2': TAKES['j2'][2]}
edl = {'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID04', 'fps': FPS,
       'output': {'width': 1080, 'height': 1920, 'fps': FPS}, 'lead_s': LEAD, 'gaps_after': GAP,
       'note': 'IA (Cortez) se apresenta e "abre espaço" → Convidado, cliente, trecho real da live do Instagram (duas frases inteiras) → IA fecha com o fato → CTA.',
       'blocks': ORDER, 'verified_text': VER, 'segments': segments, 'duration': SPEECH}
(J / 'edit').mkdir(exist_ok=True); (J / 'analysis').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/edl_words.json').write_text(json.dumps(words_out, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'regras V2 do usuário (limiar relativo p90−35 dB, sem corte dentro de palavra, cortes internos só ≥0,30 s); narrações IA inteiras',
    'cuts': report, 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': [(s['take'], s['in'], s['out'], s['start']) for s in segments], 'speech': SPEECH}, ensure_ascii=False))
for e in edges: print(e)
for r in report: print(r)
