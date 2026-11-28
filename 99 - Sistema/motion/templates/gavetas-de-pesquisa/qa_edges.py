#!/usr/bin/env python3
"""EXEMPLO_1 — conferência das bordas da fala. Para cada pedaço do EDL mede, na mesma fonte de voz usada pela mixagem (janela isolada no
ElevenLabs ou limpeza local DeepFilterNet), o pico do envelope de 10 ms nos 150 ms REMOVIDOS de cada lado do corte, comparado ao limiar
relativo do trecho (p90 − 35 dB). Borda limpa = nada de fala ali (pico < limiar + 6 dB), ou vizinho excluído documentado.
Também anexa o resultado do check_edges.py do lote (só conhece as janelas isoladas). Saída: qa/check_edges.json."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
edl = json.loads((J / 'edit/edl.json').read_text())
rep = json.loads((J / 'analysis/silence_edit_report.json').read_text())
sil = {e['take']: e['sil_db'] for e in rep['take_edges']}
ISO = [(SH / 'audio/yt-399-423-el.wav', 399.0, 423.0), (SH / 'audio/yt-773-806-el.wav', 773.0, 806.0), (SH / 'audio/yt-clean-a18.wav', 0.0, 2211.0)]
ENV = []
for p, a, b in ISO:
    sr, x = wavfile.read(p); x = x.astype(np.float32) / 32768; x = x.mean(1) if x.ndim > 1 else x
    h = int(sr * 0.01); n = len(x) // h
    ENV.append((20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), a, b, p.name))


def src_for(a, b):
    for k, (db, w0, w1, nm) in enumerate(ENV):
        if w0 <= a - 0.2 and b + 0.2 <= w1:
            return k
    return len(ENV) - 1


def peak(k, a, b):
    db, w0, _, _ = ENV[k]
    i0, i1 = int((a - w0) * 100), int((b - w0) * 100)
    return float(db[max(i0, 0):max(i1, i0 + 1)].max())


chk = json.loads(subprocess.run([sys.executable, str(SH / 'bin/check_edges.py'), str(J), '--json'], capture_output=True, text=True).stdout)
notes = {'t02/0/head': 'vizinho excluído: cauda de "jeito." até 791,07 — entra no vale de −40 a −55 dB (791,115) antes do 1º "Aqui"',
         't03/0/head': 'antes do corte está o "disso" com a cauda "-so" até 414,78 (excluído: o vídeo de exemplo tocava com som até 414,4) — entra no vale de 414,865 (−31 a −37 dB); o "E-" ataca em ~414,92',
         't03/1/tail': 'emenda contínua com o t04: sai no vale de −50 a −57 dB (419,84) entre "reais." e "Não"; o t04 entra no mesmo vale (419,86) na limpeza local',
         't04/0/head': 'mesma emenda contínua do t03 (troca de fonte dentro do vale de 419,80–419,88)'}
out = []
for s, c in zip(edl['segments'], chk):
    a, b = s['in'], s['out']
    k = src_for(a, b)
    hp, tp = peak(k, max(a - 0.15, 0), a), peak(k, b, b + 0.15)
    o = {'take': s['take'], 'piece': s['piece'], 'in': a, 'out': b, 'voice_source': ENV[k][3], 'sil_db': sil[s['take']],
         'removed_head_peak_db': round(hp, 1), 'removed_tail_peak_db': round(tp, 1),
         'head_clean': hp < sil[s['take']] + 6, 'tail_clean': tp < sil[s['take']] + 6,
         'check_edges_head_ms': c.get('head_missing_ms'), 'check_edges_tail_ms': c.get('tail_missing_ms'), 'check_edges_note': c.get('note')}
    for side in ('head', 'tail'):
        kk = f"{s['take']}/{s['piece']}/{side}"
        if kk in notes:
            o[f'{side}_note'] = notes[kk]
    out.append(o)
ok = all((o['head_clean'] or o.get('head_note')) and (o['tail_clean'] or o.get('tail_note')) for o in out)
(J / 'qa/check_edges.json').write_text(json.dumps({'pieces': len(out), 'speech_edges_clean': ok,
    'method': 'pico do envelope nos 150 ms removidos ao lado de cada corte, na mesma fonte de voz da mixagem, contra o limiar relativo do trecho (p90 − 35 dB) + 6 dB; vizinhos excluídos colados documentados',
    'pieces_detail': out}, ensure_ascii=False, indent=1))
for o in out:
    print(o['take'], o['piece'], o['in'], o['out'], o['voice_source'], 'head', o['removed_head_peak_db'], 'tail', o['removed_tail_peak_db'], 'sil', o['sil_db'],
          'OK' if o['head_clean'] and o['tail_clean'] else 'NOTE', o.get('head_note', '') or o.get('tail_note', ''))
print('speech_edges_clean', ok)
