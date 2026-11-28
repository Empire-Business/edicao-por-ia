#!/usr/bin/env python3
"""Inteligibilidade contra o TEXTO CONFERIDO (edit/edl.json), não contra outra transcrição automática.
Normaliza grafias da fala (tô/tá/pra/pro/aí…) e números. Uso: intellig.py <transcript.json> → similaridade e diferenças."""
import difflib, json, re, sys, unicodedata
from pathlib import Path
J = Path(__file__).resolve().parents[1]
EQ = {'esta': 'ta', 'estou': 'to', 'para': 'pra', 'bravo': 'brabo', 'dez': '10', 'cem': '100', 'cortes': 'corte', 'bons': 'bom'}
def n(w):
    w = ''.join(c for c in unicodedata.normalize('NFD', w.lower()) if unicodedata.category(c) != 'Mn'); w = re.sub(r'[^a-z0-9]', '', w)
    return EQ.get(w, w)
def toks(ws):
    out = []
    for w in ws:
        w = n(w)
        if w == 'pro': out += ['pra', 'o']
        elif w: out.append(w)
    return out
ref = toks(' '.join(t['text'] for t in json.loads((J / 'edit/edl.json').read_text())['takes']).split())
d = json.loads(Path(sys.argv[1]).read_text()); hyp = toks([w['word'] for s in d['segments'] for w in s['words']])
sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
print(json.dumps({'similarity_vs_verified_text': round(sm.ratio(), 3), 'prompt_recognized': 'prompt' in hyp,
                  'diffs': [[op, ref[i1:i2], hyp[j1:j2]] for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']}, ensure_ascii=False))
