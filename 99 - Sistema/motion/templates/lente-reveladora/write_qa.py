#!/usr/bin/env python3
"""EXEMPLO_1 — grava qa/qa.json a partir de tmp/qa/qa_report.json, analysis/mix_report.json e analysis/hidden_retakes_final.json."""
import json
from pathlib import Path
J = Path(__file__).resolve().parents[1]
r = json.loads((J / 'tmp/qa/qa_report.json').read_text()); m = json.loads((J / 'analysis/mix_report.json').read_text())
h = json.loads((J / 'analysis/hidden_retakes_final.json').read_text())
qa = {'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'version': 'V2', 'file': r['file'],
      'checks': {'duration_s': r['duration'], 'integrated_lufs': r['integrated_lufs'], 'true_peak_dbtp': r['true_peak'], 'black_segments': len(r['black_segments']),
                 'voice_lufs': m['qa_voice_lufs'], 'background_under_speech_lufs': m['qa_background_stem_lufs_under_speech'],
                 'intelligibility': f"transcrição do áudio final × voz limpa: {r['intelligibility_similarity']} literal; 0,951 normalizando grafias do Whisper (pra/para, tá/está, presou/presuma=prezou, sendo/cena=cenas, Iara=IA); a diferença restante é o 'né?' que o Whisper omite no mix e uma alucinação no CTA só com música ('E aí'/'Salão' — retranscrito isolado: sem voz depois de 25,93 s)",
                 'edges': 'check_edges.py: cauda/cabeça perdida ≤ 30 ms em todos os pedaços (máx. 27 ms); exclusões deliberadas documentadas (pre… antes de prezou; na alongado)',
                 'hidden_retakes': f"{len(h['candidates']) if isinstance(h['candidates'], list) else h['candidates']} candidato(s) na voz final: 'presuma' longo = Whisper juntando 'gente' + 'prezou' (pausa de 0,18 s entre eles, palavras inteiras); repetição intencional de 'editor profissional' (frases diferentes, tese do corte); 'pre… prezou' e 'na… na internet' removidos no EDL",
                 'proof': 'só entregas do usuário (EXEMPLO_2 V2, EXEMPLO_3, EXEMPLO_4, EXEMPLO_5); sem marca PRODUTO AI, sem cenas de filme/série, sem tela da live do YouTube',
                 'visual': 'folha de contato 1 q/s + recortes em tamanho real do gancho, "Aqui não", pesquisa, encaixe da cena, passagem para tela cheia e CTA conferidos',
                 'listening': 'pendente: escuta humana do usuário'},
      'status': 'preview_for_user'}
(J / 'qa').mkdir(exist_ok=True); (J / 'qa/qa.json').write_text(json.dumps(qa, ensure_ascii=False, indent=1)); print(json.dumps(qa['checks'], ensure_ascii=False))
