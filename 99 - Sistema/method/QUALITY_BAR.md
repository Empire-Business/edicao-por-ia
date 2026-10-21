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

## Lessons gates (author corrections, 20/10/2026)
Each item below was a real defect in a delivered or near-delivered preview. Check them on the rendered file.
- **Hook frame 0**: the first frame already shows the hook media and text — no fade-in from opacity 0, no empty ID
  background ("é pra começar direto mostrando o Felca"). Inspect frames 0 / 0.1 / 0.25 / 0.5 s of the final MP4.
  In GSAP, `fromTo` renders its FROM state at creation: a `fromTo` on a shared overlay (flash, vignette) left a 55 %
  white veil over everything before its start time — use `immediateRender: false` for shared overlays.
- **Presenter quality**: compare a face close-up of the render with the original; an outfit swap must follow
  `workflows/SWAP_OUTFIT_SCENERY.md` → "Quality" (crop sent, original head composited). Never upscale the face.
- **Silence and retakes**: final voice passes `tools/find_hidden_retakes.py` (no long words, repeats or stray
  syllables) and has no retained pause > 0.18 s without a documented reason (`method/SILENCE_POLICY.md`).
- **Third-party media**: no commentator faces/insets from reaction videos (crop to the media area), no burned
  captions in another language, no sensitive segments of the source video. A full-screen crop must be re-checked:
  an inset hidden behind the presenter in one layout shows up in another.
- **B-roll in-points**: open the first 1 s of every clip at its in-point — transitions in the source (grey/black
  frames, "content warning" cards) must not appear; move the in-point instead.
- **Comparisons (COM IA × ORIGINAL, before/after)**: verify frame by frame that each half shows what its label says
  from its first frame (a source that alternates versions can start on the wrong one).
- **Timing anchors**: when the same word repeats in the narration ("essa loira **aqui**… **Aqui** ela aparece…"),
  anchor to the intended occurrence (search after a time), and re-check every label/tag that hides on that anchor.
- **Generic B-roll**: when the speech describes the author's own product/solution and no product motion exists,
  build one in the ID instead of a generic third-party clip ("você botou um B-roll muito genérico").
- **Render environment**: point `TMPDIR` to the job's `tmp/` folder on the work disk; HyperFrames temp files can fill
  the system disk and abort a render ("Low disk space").

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
