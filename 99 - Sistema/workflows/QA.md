# Workflow — QA

## Mechanical
Run:
```bash
python3 tools/qa_media.py renders/draft.mp4 --output qa/qa.json
```
Review:
- decodability;
- streams;
- duration;
- resolution/fps;
- black segments;
- long silence;
- audio peak/mean when available.

## Editorial
Check the required gates in `method/QUALITY_BAR.md` against the pattern and decision log.

For cut-heavy speech edits, review short windows around cuts rather than replaying the entire source by default.

## Result
- PASS: all required gates `ATENDIDO` or `NÃO SE APLICA`.
- FIX: any required gate `PRECISA DE AJUSTE`.

Never state that playback/listening occurred unless the agent actually had a playback-capable path and used it.

For script-guided work, verify retained idea coverage and critical wording against actual source evidence. For silence cleanup, inspect the cut report and protected pauses; mechanical tests do not establish natural speech or audible cut quality.

## Motion-specific QA
If animation is present, apply the motion gates in QUALITY_BAR and save `qa/motion-qa.json`. State which playback checks were actually watched versus only programmatically tested. Template tests are synthetic; they do not approve a customer's semantic placement or brand fit. Inspect entry/settled/exit plus surrounding master frames and confirm the master audio stream is unchanged.

## Comparação obrigatória com a referência do formato
Para trabalhos novos com format_contract, inspecionar referência real e preencher analysis/format-plan.json antes da montagem. Após renderizar, preencher qa/format-fidelity.json com critérios do contrato, decisões, cenas de referência e frames do render com hashes. O controlador bloqueia montagem/QA/entrega sem comparação válida. Usar tools/format_fidelity.py --prepare para estrutura pendente; isso não aprova nada. Referência, UID/geração, receita e render devem corresponder ao trabalho. Não afirmar semelhança artística só por validação mecânica. Exceção atual deve constar em format_deviations do trabalho e coincidir com user_instruction no relatório; não altera o modelo consolidado.
