# Quality Bar

Use `ATENDIDO`, `PRECISA DE AJUSTE`, or `NÃO SE APLICA` for each gate.

## Required gates
- Requested final video(s) are all accounted for.
- Original media remains untouched.
- Correct pattern ID/version is recorded.
- EDL references valid source files and valid time ranges.
- No obvious speech mistake remains when cleanup was requested.
- No meaning-changing removal lacks a documented decision.
- No cut truncates a required word/sentence.
- Audio/video duration drift is within tolerance.
- Export resolution/aspect/fps match the pattern or explicit request.
- No unintended black frames at cuts/start/end.
- No abnormal long silence created by the edit.
- Output file is decodable by ffprobe.

## Editorial gates
- Opening is intentional and not accidental pre-roll.
- Pacing matches the named pattern rather than generic “fast editing”.
- Visual effects are motivated; no gratuitous zooms/captions/B-roll.
- Filler removal does not make the speaker robotic.
- Multi-video jobs do not leak content from neighboring child videos.
- Captions, if used, preserve wording and timing closely enough for the chosen style.

## Optional gates
Only assess if the pattern/job uses them:
- B-roll quality.
- Motion graphics.
- Music ducking.
- Speaker diarization.
- Brand typography/colors.

Never fail a job because an optional feature is absent when it does not apply.

## Script and silence gates (when applicable)
- Each required script idea is mapped to actual retained footage or explicitly flagged as missing.
- Equivalent paraphrases are not rejected just for different words; no semantic contradiction is concealed by a cut.
- No script text was fabricated as audio or caption text; captions match actual retained words.
- Wrong-version references and child-video cross-contamination are absent.
- Automatic silence cleanup ran, was explicitly disabled, or has a documented reason not to apply. Detection-only is not completed removal.
- Word handles and annotated intentional pauses survived; low-volume speech is not removed solely for its amplitude.
- The final EDL combines approved retake cuts and silence cuts without restoring discarded attempts.
- The same source-time cuts drive both audio and picture, followed by caption retiming.
- Residual intentional pauses are excluded from “unmotivated silence” failures.
- Auditory/perceptual QA not actually performed is marked PENDING, never ATENDIDO.

## Motion gates (only when used)
- Required: semantic cue and matching active child; current master/EDL hashes; exact final-frame timeline.
- Required: voice preserved, no duration truncation, no covered required captions/face/proof, readable text at intended display size.
- Required: actual rendered animation inspected for entrance/hold/exit, alpha, clipping, flicker and natural pace. Keyframe-only checks do not establish full playback quality.
- Required: no fabricated evidence or data, no cross-format asset reuse, no unexpected downloads/overwrites.
- Optional Remotion/3D absent: NÃO SE APLICA if not requested; PRECISA DE AJUSTE if it is required but not run.


## Format personalization gate (v1.4)
When format context is active, require the effective job's memory receipt and
`qa/personalization.json`. Check current overrides, scoped feedback, later rejections, stale
context and actual editorial application. A file existing does not prove the edit obeyed it.


## Direção visual (v1.5)
Quando aplicável, usar `visual/VISUAL_QA.md`. O mapa de cena precisa registrar frames realmente
inspecionados. Validação geométrica usa caixas declaradas; não certifica rastreamento ou gosto.
Não entregar como final uma rota de imagem/VFX ainda sem ferramenta ou com revisão pendente.

## Comparação obrigatória com a referência do formato
Para trabalhos novos com format_contract, inspecionar referência real e preencher analysis/format-plan.json antes da montagem. Após renderizar, preencher qa/format-fidelity.json com critérios do contrato, decisões, cenas de referência e frames do render com hashes. O controlador bloqueia montagem/QA/entrega sem comparação válida. Usar tools/format_fidelity.py --prepare para estrutura pendente; isso não aprova nada. Referência, UID/geração, receita e render devem corresponder ao trabalho. Não afirmar semelhança artística só por validação mecânica. Exceção atual deve constar em format_deviations do trabalho e coincidir com user_instruction no relatório; não altera o modelo consolidado.
