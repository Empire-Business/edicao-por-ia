# Insertion Assets Policy

## Purpose
Allow the editor to use user-supplied images and video clips as supporting visual insertions (B-roll, cutaways, proof, screenshots, product shots, examples, overlays, or visual context) at the right moment in the timeline.

## Core rule
Insertion assets are optional supporting evidence, not decorations by default.
Use them when they clarify, illustrate, prove, smooth a cut, or match a named pattern. Do not add them gratuitously.

## Accepted asset types
- image
- video
- screen recording
- logo/brand asset
- graphic/exported slide

## What “right time” means
A placement is high-confidence when one or more are true:
1. the transcript or reference script mentions the thing shown by the asset;
2. the user gave cue words, cue phrases, or a target section/block;
3. the asset clearly resolves a hard jump, supports a claim, or visually demonstrates the current spoken idea;
4. the named pattern explicitly expects B-roll or proof overlays.

If confidence is low, either:
- skip the asset;
- place it only in a clearly safe generic context if the user asked for broad freedom; or
- ask one targeted question when a required asset cannot be placed safely.

## Semantics over literal wording
Compare the spoken content and the asset meaning, not only exact words.
Example:
- Speech: “you don’t need to post every day”
- Asset note: “consistency > volume slide”
This is a plausible match.

## User intent and permissions
Only use assets supplied or explicitly authorized by the user.
Do not assume rights to third-party assets.
Do not infer or fabricate missing brand assets.

## Allowed uses
- B-roll/cutaway over spoken audio.
- Visual proof while the speaker mentions a result, page, chart, screenshot, message, or product.
- Bridging a visibly awkward jump cut.
- Short illustrative inserts for named pattern pacing.
- End-card or CTA support when the job/pattern allows it.

## Default limits
Unless the job or pattern says otherwise:
- prefer short inserts over long takeovers;
- do not cover the speaker continuously;
- do not hide important spoken moments that benefit from face visibility;
- keep the insertion density proportional to the pattern.

## Images versus videos
- Videos can be inserted directly as timeline segments or cutaways.
- Images should be converted to simple timed visual clips when needed.
- Motion on images is optional and conservative unless the pattern explicitly calls for it.

## Timing guidance
Choose entry/exit around semantic boundaries:
- start shortly before or at the first relevant spoken cue;
- leave before the next unrelated point;
- avoid mid-word insertions unless needed to hide a cut;
- prefer natural phrase boundaries.

## Required metadata when available
Use any of the following if provided:
- note/description
- cue words or cue phrases
- target script block IDs
- target child video ID
- priority
- must_use / optional / fallback / forbidden
- max_duration_s / preferred_duration_s

Missing metadata is allowed. The editor should infer cautiously.

## Failure conditions
Do not place an asset if:
- it contradicts the spoken meaning;
- it introduces a false claim or unverified proof;
- it confuses which format/project is active;
- it would create visual clutter against the chosen pattern;
- the user explicitly forbids inserts/B-roll.

## Output
When assets are supplied, create `analysis/insertion_plan.json` documenting:
- assets considered
- whether each was used
- why it was used or skipped
- planned timing windows
- confidence level
