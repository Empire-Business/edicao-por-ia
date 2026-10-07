# Input Contract

The user may speak naturally. Do not require a form when the request already contains enough information.

## Natural-language examples
- “Edit `/Videos/aula.mov` with `talking-head-clean-v1`, cut my speech mistakes and keep pauses natural.”
- “This file contains 2 separate Reels. Split them, edit both with `reels-dynamic-v1`, and give me two outputs.”
- “These 3 camera files are one video. Combine them into a single long-form edit.”
- “Use the same pattern as format X, but captions off for this job only.”

## Mandatory choices for a new edit
The user must select an editing code F and a separate visual code ID. Neither comes from a session,
owner, output proportion or historical brand. All formats accept any palette/typeface through ID.
Only missing choices are asked. Current editions have stable E codes; output revisions keep V codes.
New editing formats require an example URL; existing explicitly waived entries can lack one.

## Fields the agent should extract when present
- source file(s);
- intended relationship: `one-output`, `one-source-many-outputs`, `many-sources-one-output`, or `batch-independent`;
- expected number of final videos, if known;
- pattern ID/version;
- speech cleanup preference;
- filler aggressiveness override;
- captions override;
- must-keep/must-remove phrases or ranges;
- target platform/proportion override;
- output destination;
- format/project context.

## Portable materials
All persistent material inputs must be inside the copied factory folder. External attachments
are import sources only: the coordinator copies/verifies them inside before intake. Source video,
script, supporting media and reference files outside the workspace (including symlinks escaping
it) are rejected. Saved file references use relative internal paths/`workspace://`; the reader
resolves them from the current folder, so another user's machine does not need the original path.

## Defaults
If a field is absent and the pattern defines it, use the pattern. Do not ask the user to restate pattern defaults.

## One-question rule
Ask only when an answer changes the structure or meaning of the result and no safe reversible default exists. Ask one question at a time.

Good blocking question:
> “I found likely boundaries at 02:14 and 05:48, which would create 3 videos, but you said there are 2. Should the first two sections stay together or should the last two?”

Avoid generic briefing questions such as “what style do you want?” when a pattern was already named.

## Structured input option
For automation, use `jobs/<job-id>/job.yaml`. Natural-language instructions always take precedence over stale manifest fields and should update the manifest when they change the job.

## Reference script and silence (v1.1)
Extract optional `reference_script.paths`, `reference_script.mode` (default `flexible`), reference version, and assignment to each child video. A script may be pasted or attached; normalize a working text copy while preserving the original. Do not require it for unscripted video.

Also extract `silence_removal.enabled` (default true), mode (`pattern_default`, `natural`, `tight`, `relaxed`, `off`), protected phrases/time ranges, and explicit pause/pace preferences. A named pattern already answers routine pacing questions.

Examples:
- “Use este roteiro como referência. Eu falei com minhas palavras. Corte os erros e os silêncios sem deixar a fala artificial.”
- “Há dois vídeos nesta gravação. O roteiro A corresponde ao primeiro e o B ao segundo. Edite os dois.”
- “Mantenha a pausa antes de revelar o resultado, mas tire o restante do tempo morto.”
- “Use `talking-head-clean-v2`, roteiro flexível e remoção de silêncios no modo natural.”

When critical: “Este trecho gravado diz 30 dias, mas o roteiro diz 60. Qual informação deve permanecer?” Never ask the user to approve each routine silence cut.

## Supporting insertion assets (v1.2)
The user may attach images and/or videos to be used as supporting inserts. Extract when present:
- `supporting_assets[].path`
- `supporting_assets[].type` (`image`, `video`, `screen_recording`, `logo`, `graphic`)
- `supporting_assets[].role` (`b_roll`, `proof`, `demo`, `cutaway`, `overlay`, `end_card`)
- `supporting_assets[].notes`
- `supporting_assets[].cue_phrases` and/or `supporting_assets[].script_block_ids`
- `supporting_assets[].child_id` when the source file will become multiple outputs
- `supporting_assets[].priority` (`must_use`, `optional`, `fallback`, `do_not_use`)
- `supporting_assets[].preferred_duration_s` or `max_duration_s`, if specified
- `supporting_assets[].placement_mode` (`auto_semantic`, `manual_window`, `safe_generic`)

Examples:
- “These 4 screenshots are supporting inserts. Put each one at the moment I talk about that result.”
- “Use this product demo video as B-roll when I explain the setup step.”
- “This recording will become 2 videos. The screenshots with child_id `video-2` belong only to the second one.”
- “You can use these assets freely, but only where they make semantic sense.”

## JavaScript animations (v1.3)
Extract optional `motion.enabled` (`auto`, `on`, `off`), `motion.preset`, `motion.engine` (`auto`, `javascript-svg`, `remotion`), `motion.intensity`, `motion.max_new_design_iterations`, required/prohibited effects and safe areas. No long briefing when the named style answers these. Auto means consider selectively, not force decorations.

Example: “Use animações em JavaScript para explicar as ideias importantes. Reaproveite os padrões aprovados, preserve minha voz e sincronize tudo depois de cortar os erros e silêncios.”


## Format profile and preference pins (v1.4)
A format is a named editing profile with its own context; output proportions such as 9:16 and 16:9
are separate delivery settings. Extract format/project from the current request or identified job.
Do not ask again when already explicit. A registered format identified by the user is mandatory
before editing. No owner/default/session fallback and no anonymous edit. Ask which format to use
or register the format requested by the user through the memory workflow, with receipt. Capture relevant format facts and feedback as part of the turn, even if no new
video is requested.
`explicit_fields` lists current job overrides as dotted paths. The resolver merges allowlisted
preferences only into unpinned fields; legacy jobs with no list retain existing fields as pinned.
The public manifest key is `format`; existing `client` fields and `--client` options remain
accepted as compatibility aliases. Do not strip pins to force a preference. An unknown format is
not an invitation to borrow another profile.


## Direção visual por fala e cenário (v1.5)
Extrair `visual_direction.mode` (off/auto/storyboard), referências, restrições, autonomia,
`allow_background_change`, `allow_external_generation` e orçamento autorizado. Sem valores:
planejar/reaproveitar localmente, manter cenário, não fazer uploads/gerações pagas.
“Cada fala como prompt” significa examinar todas as ideias, não gerar uma cena por frase.
Pedido suficiente: “Interprete as falas, crie ilustrações que expliquem as ideias, examine o
cenário e use os espaços sem cobrir meu rosto nem as legendas. Mantenha meu estilo.”
