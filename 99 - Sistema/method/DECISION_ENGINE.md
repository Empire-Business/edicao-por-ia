# Decision Engine

## Classify the request

1. **Setup** — environment/tooling is missing or unknown.
2. **Pattern definition** — user wants a reusable editing style.
3. **Single edit** — one final video.
4. **Split + edit** — one source contains multiple final videos.
5. **Multi-source edit** — several files combine into one final video.
6. **Batch factory** — multiple independent jobs.
7. **Review/repair** — an existing render or EDL needs changes.
8. **QA only** — verify a render.

## Minimum context by task

### Single edit
Load:
- job manifest;
- requested pattern;
- `EDIT_VIDEO.md`;
- `MODEL_ROUTING.md`;
- `QUALITY_BAR.md`.

Add `SPEECH_ERROR_POLICY.md` only if speech cleanup is relevant.
If a reference script is supplied, add `REFERENCE_SCRIPT_POLICY.md` + `MATCH_REFERENCE_SCRIPT.md` before take selection.
For enabled silence cleanup, add `SILENCE_POLICY.md` + `REMOVE_SILENCE.md` after assembly decisions.
No script is not a blocker; ambiguous script-to-child association can be.

### Split + edit
Add `MULTI_VIDEO_POLICY.md` and `SPLIT_MULTI_VIDEO.md`.

### Pattern definition
Load only the chosen references, `PATTERN_SPEC.md`, `DEFINE_PATTERN.md`, and relevant brand/format context.

## Ask vs decide

Proceed without asking when:
- the pattern gives an explicit default;
- the choice is reversible in the EDL;
- confidence is high and intent is preserved;
- a safe fallback exists.

Ask one essential question when:
- two plausible cuts materially change meaning;
- expected number of final videos cannot be inferred with useful confidence;
- a required brand asset is missing and no neutral fallback is allowed;
- a destructive or irreversible operation is requested without a destination.

Never run a long briefing interview by default.

## Stop conditions
Stop finalization if any REQUIRED QA gate fails. Do not silently downgrade a final into a draft.

## Motion branch (v1.3)
- User mentions animations, motion, animated charts, kinetic text or JavaScript: load CREATE_JS_ANIMATIONS + MOTION_POLICY.
- User only edits speech: briefly consider visual needs, skip animation when unnecessary/off; do not load all motion examples.
- New complex component: Opus design is justified. Existing component: local or Sonnet. Do not force Haiku into visual art direction.
- The animation workflow runs after locked clean-master timing; never schedule against a pre-silence-cut timeline.


## Memory branch (v1.4, always evaluated)
Current turn contains format info, style preference, correction, approval/rejection or results:
run FORMAT_MEMORY now, not only after publication. Clear durable preference → save/apply in its
scope. One-video override → job. Vague criticism → candidate or focused question; no invented rule.
Identify the format before retrieval. Use session binding only when not contradicted by the current job.
Format context is not a reason to send complete history to Opus.
