#!/usr/bin/env python3
"""EXEMPLO_1 — cópia local da janela isolada IG 757–782 s (ElevenLabs, jobs/material-compartilhado/audio/ig-757-782-el.wav) com a cauda
782,0–783,0 s do áudio bruto da live emendada (ig-raw.wav), porque o fim de "comparação" decai até ~782,06 s e a janela isolada
termina em 782,0 s. Ganho do bruto casado com a voz isolada na fala anterior (780,5–781,95 s); emenda em cross-fade de 30 ms.
A cauda é só decaimento (−40 → −70 dB) e silêncio até o "É" do Apresentador (~782,75 s, excluído). Nenhuma chamada paga.
Saída: audio/ig-757-783-patched.wav. Run: ../../../.venv/bin/python src/make_patch.py"""
import json
import numpy as np
from pathlib import Path
from scipy.io import wavfile

J = Path(__file__).resolve().parents[1]
A = J.parent / 'material-compartilhado/audio'
sr, el = wavfile.read(A / 'ig-757-782-el.wav')
sr2, raw = wavfile.read(A / 'ig-raw.wav')
assert sr == sr2, (sr, sr2)
f = lambda x: (x.astype(np.float32) / 32768) if x.dtype == np.int16 else x.astype(np.float32)
el, raw = f(el), f(raw)
el = el.mean(1) if el.ndim > 1 else el
raw = raw.mean(1) if raw.ndim > 1 else raw
rs = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-12)
a, b = int((780.5 - 757) * sr), int((781.95 - 757) * sr)
g = rs(el[a:b]) / rs(raw[int(780.5 * sr):int(781.95 * sr)])
xf = int(0.03 * sr)
n_el = len(el)
tail = raw[int(782.0 * sr) - xf:int(783.0 * sr)] * g
out = np.concatenate([el[:n_el - xf], el[n_el - xf:] * np.linspace(1, 0, xf) + tail[:xf] * np.linspace(0, 1, xf), tail[xf:]])
(J / 'audio').mkdir(exist_ok=True)
wavfile.write(J / 'audio/ig-757-783-patched.wav', sr, (np.clip(out, -1, 1) * 32767).astype(np.int16))
rep = {'base': 'material-compartilhado/audio/ig-757-782-el.wav (ElevenLabs Audio Isolation, IG 757–782 s)', 'tail': 'material-compartilhado/audio/ig-raw.wav 782,0–783,0 s',
       'raw_gain_linear': round(g, 4), 'crossfade_s': 0.03, 'duration_s': round(len(out) / sr, 3), 'sr': sr}
(J / 'analysis/audio_patch.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(rep)
