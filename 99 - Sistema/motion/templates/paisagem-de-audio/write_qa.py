#!/usr/bin/env python3
"""EXEMPLO_1 — grava qa/qa.json e qa/format-fidelity.json a partir dos relatórios de src/qa.py (das duas versões), check_edges, mixagem e voz.
Run: ../../../.venv/bin/python src/write_qa.py"""
import json, subprocess, sys
from pathlib import Path

J = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(J.parent / 'material-compartilhado/bin'))
import check_edges as CHK

rd = lambda p: json.loads((J / p).read_text())
main, com = rd('tmp/qa/qa_report.json'), rd('tmp/qa/qa_report_comment.json')
edges = CHK.check(J)
hid = rd('analysis/hidden_retakes_final.json')
qa = {
 'job': '<PREENCHER: fonte ou prova própria>', 'edition': 'EXEMPLO_1', 'version': 'V1', 'format': 'F22', 'visual_identity': 'ID03', 'caption_style': 'L06',
 'deliverables': {'saiba_mais': main, 'comente_cortez': com},
 'checks': {
  'loudness_final_lufs': [main['integrated_lufs'], com['integrated_lufs']], 'true_peak_dbtp': [main['true_peak'], com['true_peak']],
  'voice_lufs': main['voice_lufs'], 'background_under_speech_lufs': main['bg_under_speech_lufs'],
  'black_frames': [main['black_segments'], com['black_segments']],
  'intelligibility_literal_vs_clean_voice': [main['intelligibility_similarity'], com['intelligibility_similarity']],
  'intelligibility_note': 'Normalizado (bravo/brabo, prumpt/prompt, logo/longo, tá/está, pra/para) contra o texto conferido das falas: 0,964. Diferenças restantes são variações do Whisper ("Tá aí"→"Aí", "um corte"→"que eu acho"; "Caraca" no primeiro quadro some em qualquer recorte curto, inclusive no áudio original isolado).',
  'word_edges': edges,
  'word_edges_note': 'Todos ≤ 30 ms, exceto bordas encostadas em palavra EXCLUÍDA sem silêncio entre elas (t03 fim/"do", t04 início/"Instagram", t05 início/risadas e fim/"Daqui", t06 fim/"Ele"); a palavra mantida está inteira (envelope de 10 ms + transcrição isolada). t01 fora das janelas do ElevenLabs: conferido no envelope da limpeza local (silêncio antes e depois).',
  'hidden_retakes_final_voice': {'candidates': len(hid['candidates']), 'verdict': 'nenhum retake: repetições em frases diferentes e palavras arrastadas da fala natural do Apresentador'},
  'visual': 'folha de contato 1 q/s e quadros em tamanho real do gancho, das provas, do "sinistro", da parte do Apresentador e dos dois CTAs conferidos; provas nítidas; sem quadro preto; texto dentro da área segura (nada importante abaixo de ~1560 px)',
  'honesty': 'provas = entregas do usuário feitas pelo Cortez, rotuladas; nenhuma sugere ser vídeo do Convidado; sem logotipos/terceiros; tela da live só no recorte do rosto do Apresentador',
  'paid_calls': 'nenhuma'},
 'self_critique_iterations': ['bloom estourava as palavras brancas → limiar 0,965 e força 0,12', 'placas largas viravam "paredes" → barras de 150', 'câmera não mostrava o progresso → câmera atrás/ao lado olhando a barra atual',
                              'apresentação escura e vazia → visão alta com a luz rebobinando devagar', 'cartões passavam por cima do cartão de quem fala → entram no lugar, saem por cima',
                              'parte do Apresentador parada 12 s → câmera desliza pela rua de resultados', 'título vazio por 7 s → dois blocos de título na fala final'],
 'pending': 'escuta humana do usuário'}
(J / 'qa').mkdir(exist_ok=True)
(J / 'qa/qa.json').write_text(json.dumps(qa, ensure_ascii=False, indent=1))
fid = {'format': 'F22 Corte de Live 3D', 'recipe': 'f22-corte-de-live-3d-v1', 'compared_with': 'examples/reference-library/F22/corte-de-live-3d (EXEMPLO_2 V1) e analysis/format-plan.json',
       'checks': {'duration_25_45': 38.53, 'hook_first_seconds': 'frase mais forte (áudio real) + 3D em movimento no 1º quadro', 'turn': 'rebobina → áudio começa com a subida da trilha',
                  'proof_in_3d_on_the_word': 'identidades no "estilo/cor", vídeo longo → 10 curtos no "vídeo longo/10 cortes", rua de resultados no "muito sinistro"',
                  'keyword_3d_text': 'CARACA!, CRAQUE, PROMPT, SINISTRO.', 'people_small_cards': 'sim (foto do Convidado; recorte da webcam do Apresentador)',
                  'headlines_two_lines': 'sim', 'cta_written_after_voice': 'sim (Saiba mais / Comente CORTEZ)', 'renderer_three_r186_composer': 'sim',
                  'forbidden_look': 'sem partículas, holofotes, neon, glitch; bloom baixo', 'colors_fonts_from_id': 'ID03 (Inter + IBM Plex Mono; azul #4A92E6)'},
       'artistic_similarity': 'mesma mecânica do F22 (fala real conduz, prova 3D no momento citado, CTA escrito); cena 3D nova por pedido do usuário (cada corte com estilo novo) — documentado em format-plan.json',
       'verdict': 'pass (prévia)'}
(J / 'qa/format-fidelity.json').write_text(json.dumps(fid, ensure_ascii=False, indent=1))
print('ok', len(edges))
