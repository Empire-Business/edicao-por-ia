#!/usr/bin/env python3
"""EXEMPLO_1 — junta os relatórios de QA das duas versões em qa/qa.json."""
import json
from pathlib import Path
J = Path(__file__).resolve().parents[1]
out = {'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'format': 'F10', 'visual_identity': 'ID07', 'caption_style': 'L05', 'version': 'V1', 'paid_calls': 0,
       'voice': 'narração ElevenLabs já gerada no lote (d2-v1.wav, voz plASsyS7JE6GCAvx9uIc) + tropeço real da gravação bruta (1,04–2,86 s)',
       'checks': {}}
for suf, name in [('', 'saiba_mais'), ('-comment', 'comente_cortez')]:
    p = J / f'tmp/qa/qa_report{suf}.json'
    if p.exists():
        r = json.loads(p.read_text()); r.pop('streams', None); out['checks'][name] = r
out['visual_review'] = json.loads((J / 'tmp/qa/visual_review.json').read_text()) if (J / 'tmp/qa/visual_review.json').exists() else None
(J / 'qa/qa.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'final_transcript'} for k, v in out['checks'].items()}, ensure_ascii=False))
