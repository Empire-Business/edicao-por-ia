# Workflow — Use Insertion Assets

## Format checkpoint (v1.4)
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


## Goal
Use user-provided images and/or videos as semantically appropriate supporting inserts.

## Inputs
- current job manifest
- transcript and/or reference-script alignment when available
- supporting assets supplied by the user
- named pattern

## Process
1. Read `method/INSERTION_ASSETS_POLICY.md`.
2. Inspect each asset mechanically: path, media type, duration (for videos), dimensions, and child-video assignment.
3. Normalize asset notes/cues into a working manifest.
4. Match assets to likely spoken windows using:
   - transcript meaning;
   - reference script block IDs;
   - cue phrases;
   - safe editorial needs (e.g., hide a hard jump).
5. Produce `analysis/insertion_plan.json` with one entry per asset.
6. Use only high-confidence placements automatically.
7. If an asset is `must_use` but lacks a safe placement, ask one targeted question.
8. If an image is selected, prepare it as a simple timed visual clip if required by the render path.
9. Add chosen insertions to the EDL or edit plan.

## Checks
- Insertions do not contradict speech.
- Insertions respect child-video boundaries.
- Proof assets are not used to support unrelated claims.
- Visual clutter is compatible with the pattern.
- Speaker visibility is preserved when the emotional/credibility moment depends on face presence.

## Output
- `analysis/insertion_plan.json`
- prepared still-image clips when needed
- updated `edit/edl.json` or equivalent edit plan

## Common errors
- Forcing every asset into the cut.
- Matching by exact words only.
- Using an asset from video 2 inside video 1.
- Covering a key emotional statement with irrelevant B-roll.

## v1.3 timing and animated assets
Asset selection can happen early; final placement waits until silence cuts and transcript retiming are complete. Animate supplied screenshots through the proof-frame template when useful; preserve all original facts/numbers. For moving-video insertions/complex layered scenes use a verified advanced compositor, not the image-only template. Load CREATE_JS_ANIMATIONS only when animation helps.
