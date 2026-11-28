#!/usr/bin/env python3
"""<PREENCHER: fonte ou prova própria>"Editor caro" da live do Instagram (Apresentador + Convidado), F10 + ID02.
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
    ('t01', 'convidado', 'hook', ('Parece', 393.16), ('caro', 396.20), 'Parece que o Cortez faz melhor e a galera ainda cobrava mais caro.'),
    ('t02', 'apresentador', 'pergunta', ('Quando', 383.96), ('nível', 388.80), 'Quando você pagava ali, você contratava a galera para fazer, era do mesmo nível?'),
    ('t03', 'convidado', 'resposta', ('É', 390.18), ('parecido', 392.52), 'É, tinha a edição que ficava parecido.'),
    ('t04', 'convidado', 'resultado', ('o', 358.46), ('baratos', 362.82), 'o resultado que eu mais gostei foi de um vídeo que eu postei em relação a hotéis baratos'),
    ('t05', 'convidado', 'cortez', ('E', 367.10), ('Cortez', 368.78), 'E quem fez toda a edição foi o próprio Cortez.'),
    ('t06', 'convidado', 'itens', ('pegou', 371.74), ('sonoros', 375.84), 'pegou as imagens bonitas de hotéis, colocou os cortes, colocou os efeitos sonoros.'),
    ('t07', 'convidado', 'hollywood', ('Então', 376.46), ('Hollywood', 379.52), 'Então, a minha reação foi tipo de, sei lá, de Hollywood.'),
    ('t08', 'convidado', 'nunca', ('Quando', 380.08), ('pô', 382.68), 'Quando eu vi aquilo lá, eu falei, nossa, eu nunca fiz uma edição assim, pô.'),
    ('t09', 'apresentador', 'detalhe', ('E', 398.20), ('atenção', 401.24), 'E qual foi o detalhe que mais chamou atenção?'),
    ('t10', 'convidado', 'animacao', ('A', 403.74), ('Effects', 405.24), 'A animação estilo After Effects.'),
    ('t11', 'convidado', 'maravilhado', ('quando', 411.96), ('aquilo', 417.62), 'quando eu vi a ferramenta fazendo isso, aqueles efeitos visuais de animação, pô, eu fiquei maravilhado com aquilo.'),
]
SIL_DB, GAP, KEEP = -44.0, 0.15, 0.05   # política global: pausas > 0,15 s cortadas, ~0,05 s de cada lado
# Bordas e pausas pela ENERGIA da fonte limpa (o tempo de palavra do Whisper é só a âncora): a emenda cai em silêncio.
import numpy as np
from scipy.io import wavfile
_sr, _x = wavfile.read(SH / 'audio/ig-clean-a18.wav')
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
IN_OVERRIDE = {'t06': 371.875}
segments, report, edges, t = [], [], [], 0.0
for tid, who, scene, (w0, n0), (w1, n1), text in TAKES:
    a, b = find(w0, n0), find(w1, n1)
    prev = [w for w in WORDS if w['end'] <= a['start'] + 1e-6]
    nxt = [w for w in WORDS if w['start'] >= b['end'] - 1e-6]
    lo, qi = quiet_in(max(a['start'] - 0.40, (prev[-1]['start'] + 0.08) if prev else 0), a['start'] + 0.03)
    hi, qo = quiet_out(b['end'] - 0.05, min(b['end'] + 0.45, (nxt[0]['start'] + 0.05) if nxt else b['end'] + 0.45))
    if tid in IN_OVERRIDE:
        lo, qi = IN_OVERRIDE[tid], True
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

edl = {'version': 1, 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'pattern': 'f10-v1', 'format_code': 'F10', 'visual_identity': 'ID02',
       'source': SRC, 'fps': FPS, 'output': {'width': 1080, 'height': 1920, 'fps': FPS},
       'note': 'Corte do depoimento do Convidado (cliente) e perguntas do Apresentador; ordem editorial: gancho (resposta) → pergunta → história → detalhe.',
       'takes': [{'id': x[0], 'speaker': x[1], 'scene': x[2], 'text': x[5]} for x in TAKES],
       'segments': segments, 'duration': round(t, 4)}
(J / 'edit').mkdir(exist_ok=True)
(J / 'edit/edl.json').write_text(json.dumps(edl, ensure_ascii=False, indent=1))
(J / 'analysis/silence_edit_report.json').write_text(json.dumps({'policy': 'global tight cap: gaps > 0.15 s cut, 0.05 s kept each side', 'cuts': report,
                                                                 'removed_total_s': round(sum(r['removed'] for r in report), 3), 'take_edges': edges}, ensure_ascii=False, indent=1))
print(json.dumps({'segments': len(segments), 'duration': edl['duration'], 'internal_cuts': len(report)}))
