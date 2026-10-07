# Workflow — Personalization QA

## Inputs
Current request, source/effective job, scoped context/receipt, relevant feedback and actual edit.

## Gates (ATENDIDO / PRECISA DE AJUSTE / NÃO SE APLICA)
- Format and project are correct; no neighbor child video's assets/preferences were imported.
- New useful facts/feedback have a verified capture receipt, or a justified no-save review.
- Current job overrides win and one-video exceptions have not become format-wide rules.
- Mechanical settings reflect the effective manifest; run `resolve_format_context.py --check`.
- No known rejected artifact/effect is reused under another name without explicit reinstatement.
- “Pause too abrupt”, “don't crop the product” etc. became actual timing/framing decisions,
  not merely notes. Check the actual draft at relevant cuts, inserts and animation frames.
- Approved phrases, takes, assets and unaffected time ranges remain unchanged on partial edits.
- Approval is not a performance claim. Missing measurements are reported as missing.
- Budget omissions/conflicts/stale snapshots are reviewed before final export.

## Logo gate
New edits/format templates contain no automatic logo, wordmark, monogram, watermark or branded
closing/cover. `branding.logos_enabled` defaults to false. A logo is allowed only when the current
job explicitly requests it. Existing assets/reference screenshots do not grant that permission.
Check actual frames, including recreated interface headers and covers; a memory setting alone
is not proof that an already-built SVG/HTML overlay was removed.

## Output
`qa/personalization.json`: format, job/revision, relevant memory IDs, what was applied,
what was explicitly overridden, what is still a candidate, and gate states with reasons.
A mechanical pass does NOT prove an editor listened to the feedback or inspected the video.
If feedback is only “ruim”, retain the reaction to the known artifact and ask a targeted question
when needed to fix it; never invent a diagnosis or a universal ban.


## Direção visual
Conferir preferência de cenário, ilustração, densidade de movimento e referências aprovadas.
Salvar feedback explícito com o mecanismo existente; não registrar proposta da IA como aprovação.
Preferências novas fora das chaves mecânicas do resolvedor continuam decisões editoriais a aplicar
explicitamente no storyboard e verificar na saída, não parâmetros magicamente executados.
