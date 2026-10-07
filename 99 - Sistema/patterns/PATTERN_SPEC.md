# Pattern Specification

A pattern is a versioned editing contract. It is not merely a look-and-feel note.

## Required sections
- `id`, `version`, `status`, `purpose`;
- target output geometry/fps;
- editorial pacing;
- speech cleanup policy;
- visual reframing rules;
- caption policy;
- audio policy;
- allowed/forbidden effects;
- render engine;
- QA tolerances.

## Important distinction
Pattern rules should describe **mechanisms**:
- maximum silence before tightening;
- when a punch-in is justified;
- maximum caption lines;
- filler aggressiveness;
- crop behavior;
- whether B-roll is optional/required/forbidden.
- insertion asset policy (none / optional / encouraged / proof-heavy).
- default insert density and typical insert duration range.

Avoid vague instructions such as “make it viral” or “make it dynamic”.

## Versioning
Changing a rule that can alter an existing job's output requires a new version. Cosmetic documentation fixes that do not affect output can keep the version.

## Automatic silence fields
`editorial.silence_removal`: `enabled`, `minimum_silence_seconds`, `keep_pause_seconds`, `word_handle_seconds`, `minimum_cut_seconds`, `trim_edges`. All time fields use seconds, all thresholds are configurable starting points. Speech/protected-range evidence outranks aggressive style settings. See `method/SILENCE_POLICY.md`.

## Motion add-ons (v1.3)
Versioned `patterns/motion/` entries describe animation separately from clean-cut pacing. Keep original v1/v2 video presets unchanged; add an explicitly approved per-job or per-client motion override. Store animation intensity, allowed primitives, safe regions, color/type references, reading-time rules and reusable component IDs.


## Extensão opcional visual_direction
Um padrão novo pode definir densidade/intenção visual, preservação do cenário, áreas protegidas,
estilo/refs e rotas autorizadas. Não alterar silenciosamente padrões existentes. Exceções do job
prevalecem sobre herança. Um limite de densidade é parâmetro de estilo, não regra do método.
