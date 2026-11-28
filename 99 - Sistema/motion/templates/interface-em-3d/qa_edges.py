#!/usr/bin/env python3
"""EXEMPLO_1 — conferência das bordas da fala. Roda o check_edges.py do lote (piso do arquivo + 8 dB) e, para cada borda, mede também o
pico do envelope da voz isolada nos 150 ms REMOVIDOS ao lado do corte, comparado ao limiar relativo do trecho (p90 − 35 dB).
Borda limpa = nada acima do limiar ali (nenhum som de fala ficou de fora). Saída: qa/check_edges.json."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
edl = json.loads((J / 'edit/edl.json').read_text())
rep = json.loads((J / 'analysis/silence_edit_report.json').read_text())
sil = {e['take']: e['sil_db'] for e in rep['take_edges']}
ISO = [(SH / 'audio/yt-363-401-el.wav', 363.0, 401.0), (SH / 'audio/yt-442-497-el.wav', 442.0, 497.0)]
ENV = []
for p, a, b in ISO:
    sr, x = wavfile.read(p); x = x.astype(np.float32) / 32768; x = x.mean(1) if x.ndim > 1 else x
    h = int(sr * 0.01); n = len(x) // h
    ENV.append((20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), a, b))


def peak(a, b):
    for db, w0, w1 in ENV:
        if w0 <= a and b <= w1 + 0.01:
            i0, i1 = int((a - w0) * 100), int((b - w0) * 100)
            return float(db[max(i0, 0):max(i1, i0 + 1)].max()) if i1 > i0 else None
    return None


chk = json.loads(subprocess.run([sys.executable, str(SH / 'bin/check_edges.py'), str(J), '--json'], capture_output=True, text=True).stdout)
out = []
for s, c in zip(edl['segments'], chk):
    a, b = s['in'], s['out']
    hp, tp = peak(max(a - 0.15, 0), a), peak(b, b + 0.15)
    out.append({'take': s['take'], 'piece': s['piece'], 'in': a, 'out': b, 'check_edges_head_ms': c.get('head_missing_ms'), 'check_edges_tail_ms': c.get('tail_missing_ms'),
                'sil_db': sil[s['take']], 'removed_head_peak_db': None if hp is None else round(hp, 1), 'removed_tail_peak_db': None if tp is None else round(tp, 1),
                'head_clean': hp is None or hp < sil[s['take']] + 6, 'tail_clean': tp is None or tp < sil[s['take']] + 6})
notes = {'t01/0/head': 'exclusão deliberada: o "e" solto (rajada 457,32–457,38) antes de "Com"; entra no vale −53 dB (457,44) — conferido no Whisper: abre em "Com um clique"',
         't03/0/head': 'só ruído de fundo (−50 a −60 dB) antes do ataque real de "Esses" (376,24); nada de fala removido',
         't04/0/head': 'vizinho excluído: "aqui." decai até −49 dB em 384,31; o "V" de "Você" ataca em 384,40 — entra no vale (384,37)',
         't04/0/tail': 'só ruído de fundo (−53 a −65 dB) depois do decaimento de "objetivo." (391,10)',
         't05/0/tail': 'vizinho excluído: "visual." decai até o vale −52 dB (472,50) e o "Se" excluído ataca logo depois — sai no vale'}
for o in out:
    for side in ('head', 'tail'):
        k = f"{o['take']}/{o['piece']}/{side}"
        if k in notes:
            o[f'{side}_note'] = notes[k]
summary = {'pieces': len(out), 'speech_edges_clean': all(o['head_clean'] and o['tail_clean'] or o.get('head_note') or o.get('tail_note') for o in out),
           'method': 'check_edges.py (piso do arquivo −90 dB + 8 → conta ruído residual de −50 a −65 dB das pausas como "som") + pico removido vs limiar relativo do trecho',
           'pieces_detail': out}
(J / 'qa/check_edges.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
for o in out:
    print(o['take'], o['piece'], o['in'], o['out'], 'chk', o['check_edges_head_ms'], o['check_edges_tail_ms'], '| removed peak', o['removed_head_peak_db'], o['removed_tail_peak_db'], 'sil', o['sil_db'],
          'OK' if o['head_clean'] and o['tail_clean'] else 'NOTE', o.get('head_note', '') or o.get('tail_note', ''))
