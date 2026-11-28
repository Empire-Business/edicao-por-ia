#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Tem formato pra tudo" da live do Instagram (Apresentador + Convidado), F10 + ID05.
Monta o EDL a partir das palavras reais da transcrição da fonte (cache em material-compartilhado/analysis):
cada trecho vai da 1ª à última palavra pedida, com respiro nas bordas, e é partido nas pausas internas > 0,15 s
(mantém ~0,05 s de cada lado), conforme a política global de silêncio. Cada pedaço é quantizado em quadros de 30 fps
para voz e imagem andarem no mesmo relógio. Saídas: edit/edl.json e analysis/silence_edit_report.json.
Run: ../../../.venv/bin/python src/make_edl.py
"""
import json, re, unicodedata
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
SRC = '<PREENCHER: fonte ou prova própria>'
FPS = 30
WORDS = [w for s in json.loads((SH / 'analysis/ig.transcript.json').read_text())['segments'] for w in s['words']]


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def find(word, near):
    """palavra com início mais próximo de `near` (±0,4 s)."""
    c = [w for w in WORDS if norm(w['word']) == norm(word) and abs(w['start'] - near) < 0.4]
    if not c:
        raise SystemExit(f'palavra {word!r} perto de {near} não encontrada')
    return min(c, key=lambda w: abs(w['start'] - near))


# (id, quem fala, cena, primeira palavra @ início, última palavra @ início, texto esperado)
TAKES = [
    ('t01', 'convidado', 'lista', ('Tem', 468.08), ('gente', 474.38), 'Tem formato de vídeo sem aparecer, vídeo aparecendo, vídeo aparecendo com cenas, vídeo onde a gente'),
    ('t01b', 'convidado', 'desfoca', ('desfoca', 475.90), ('fundo', 476.42), 'desfoca o fundo.'),
    ('t02', 'apresentador', 'escolhe', ('Depende', 456.60), ('quer', 460.92), 'Depende da edição que você quer também, né? Tem os formatos lá pré-cadastrados, você escolhe qual formato você quer.'),
    ('t03', 'convidado', 'letra', ('tem', 480.08), ('cores', 483.16), 'Tem variações em relação a letra, tamanho, cores.'),
    ('t04', 'convidado', 'editado', ('E', 341.56), ('bacana', 344.56), 'E é bem editado também, com efeito, com música, com tudo, visual bacana.'),
    ('t05', 'convidado', 'tranquilo', ('são', 484.74), ('mexer', 488.74), 'São N possibilidades que a ferramenta faz e não é difícil, o negócio é bem tranquilo de mexer.'),
]
SIL_DB, GAP, KEEP = -44.0, 0.15, 0.05   # política global: pausas > 0,15 s cortadas, ~0,05 s de cada lado
# Bordas e pausas pela ENERGIA da fonte limpa (o tempo de palavra do Whisper é só a âncora): a emenda cai em silêncio.
import numpy as np
from scipy.io import wavfile
_sr, _x = wavfile.read(SH / 'audio/ig-clean-a18.wav')   # envelope de energia (DFN local) só para achar silêncios
_x = _x.astype(np.float32) / 32768
H = int(_sr * 0.01)
_n = len(_x) // H
ENV = 20 * np.log10(np.sqrt((_x[:_n * H].reshape(_n, H) ** 2).mean(1)) + 1e-9)
SM = np.convolve(ENV, np.ones(3) / 3, mode='same')          # janela de 30 ms


def quiet_in(lo, hi):
    a, b = int(lo / 0.01), int(hi / 0.01)
    idx = [i for i in range(a, b) if SM[i] < SIL_DB]
    return (idx[-1] * 0.01 if idx else (a + int(np.argmin(SM[a:b]))) * 0.01), bool(idx)


def quiet_out(lo, hi):
    a, b = int(lo / 0.01), int(hi / 0.01)
    idx = [i for i in range(a, b) if SM[i] < SIL_DB]
    return (idx[0] * 0.01 + 0.01 if idx else (a + int(np.argmin(SM[a:b]))) * 0.01), bool(idx)


# Ajuste fino conferido no envelope de 5 ms: o Whisper marcou "pegou" em 371,74, mas o fim de "realmente" vai até 371,83
# e o fechamento do /p/ está em 371,86–371,90. Começar ali evita o resto de palavra ("a gente") na emenda.
# Ajustes conferidos no envelope de 10 ms (voz isolada) e em transcrições curtas da janela (tmp/probe):
# - t01/t01b: "a gente... é... desfoca": a hesitação "é..." (474,54–475,11) sai; "gente" termina em 474,535 (vale), "desfoca" começa em 475,53.
# - t01b: análise por bandas (tmp/probe): "fundo" = 476,43–476,69 (f, ũ, d, ʊ), "né" = 476,69–476,81; corte em 476,70, no fim do ʊ, antes do /n/.
# - t02: "né?" anterior termina em 456,53 e "Depende" começa em 456,75; o fim em 460,97 deixa de fora o "né?" (461,03–461,27).
# - t05: "enfim" (484,25–484,66) fica de fora; "são" começa em 484,76.
IN_OVERRIDE = {'t01b': 475.50, 't02': 456.70, 't05': 484.74}
OUT_OVERRIDE = {'t01': 474.535, 't01b': 476.70, 't02': 460.97}
segments, report, edges, t = [], [], [], 0.0
for tid, who, scene, (w0, n0), (w1, n1), text in TAKES:
    a, b = find(w0, n0), find(w1, n1)
    prev = [w for w in WORDS if w['end'] <= a['start'] + 1e-6]
    nxt = [w for w in WORDS if w['start'] >= b['end'] - 1e-6]
    lo, qi = quiet_in(max(a['start'] - 0.40, (prev[-1]['start'] + 0.08) if prev else 0), a['start'] + 0.03)
    hi, qo = quiet_out(b['end'] - 0.05, min(b['end'] + 0.45, (nxt[0]['start'] + 0.05) if nxt else b['end'] + 0.45))
    if tid in IN_OVERRIDE:
        lo, qi = IN_OVERRIDE[tid], True
    if tid in OUT_OVERRIDE:
        hi, qo = OUT_OVERRIDE[tid], True
    if segments and segments[-1]['in'] < lo < segments[-1]['out'] + 0.001 and lo < segments[-1]['out']:
        lo = segments[-1]['out']          # trecho contíguo ao anterior: sem repetir áudio
    edges.append({'take': tid, 'in': round(lo, 3), 'in_silent': qi, 'out': round(hi, 3), 'out_silent': qo})
    # pausas internas pela energia
    pieces, s0 = [], lo
    i, end = int(lo / 0.01) + 1, int(hi / 0.01) - 1
    while i < end:
        if SM[i] < SIL_DB:
            j = i
            while j < end and SM[j] < SIL_DB:
                j += 1
            if (j - i) * 0.01 > GAP + 2 * KEEP:
                pieces.append((s0, i * 0.01 + KEEP))
                report.append({'take': tid, 'gap': [round(i * 0.01, 3), round(j * 0.01, 3)], 'removed': round((j - i) * 0.01 - 2 * KEEP, 3)})
                s0 = j * 0.01 - KEEP
            i = j
        i += 1
    pieces.append((s0, hi))
    for k, (pi, po) in enumerate(pieces):
        n = max(1, round((po - pi) * FPS))
        segments.append({'source': SRC, 'take': tid, 'speaker': who, 'scene': scene, 'piece': k,
                         'in': round(pi, 4), 'out': round(pi + n / FPS, 4), 'frames': n, 'start': round(t, 4)})
        t += n / FPS

edl = {'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID05',
       'source': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'Gancho = a lista de formatos do Convidado → Apresentador: você escolhe o formato → letra, tamanho, cores → bem editado, com efeito e música → N possibilidades, tranquilo de mexer.',
       'takes': [{'id': x[0], 'speaker': x[1], 'scene': x[2], 'text': x[5]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'global tight cap: gaps > 0.15 s cut, 0.05 s kept each side', 'cuts': report,
                                                                 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
