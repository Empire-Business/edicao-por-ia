# Workflow — Match a reference script

## Objective
Use a script to recognize intended ideas, probable recording mistakes and the best complete takes, without requiring a verbatim performance.

## Inputs
Active job, correct reference version, original-source timestamped transcript, child-video scope if any, and `method/REFERENCE_SCRIPT_POLICY.md`.

## Process
1. Associate reference(s) with one final video. Save pasted material in `references/`. Normalize attachments, preserving the original; record hash/version.
2. Transcribe the recording independently. Keep its original words, times and source path.
3. Divide the reference into idea blocks. Mark directions versus spoken content, required clauses, CTA, critical names/numbers/negations. Use `jobs/REFERENCE_SCRIPT_TEMPLATE.json` as an optional structured format; natural text is sufficient input.
4. Retrieve compact candidates locally:
   ```bash
   python3 tools/prepare_script_comparison.py \
     --script jobs/example/references/roteiro.md \
     --transcript jobs/example/analysis/transcript.json \
     --output jobs/example/analysis/script-candidates.json
   ```
   For a child job, also pass `--start` and `--end` in ORIGINAL source seconds. Assign only its reference blocks. Windows crossing the boundary are omitted, so inspect/segment a straddling utterance rather than silently calling it missing.
5. Send the active block outline + candidate windows to the normal semantic editor. The candidate packet is a retrieval aid, not an answer. Resolve synonyms and paraphrases by meaning, and look beyond the top candidates where needed.
6. Compare neighboring takes and preserve a complete fluent version of each intended idea. Identify actual mistakes, useful improvisation, divergences, missing required content and out-of-order ideas.
7. Write `analysis/script_alignment.json` and a readable `analysis/script_coverage.md`. Every required block has an evidence-backed status. Do not use a lexical score as a correctness percentage.
8. Translate intentional pauses/breaths/demonstrations into `edit/protected_ranges.json`, with original source times. Include speech that must be preserved.
9. Write `edit/assembly-edl.json` for approved retained takes. Log each semantic removal and any allowed reordering. Do not apply silence cuts yet.
10. Run `workflows/REMOVE_SILENCE.md` against this assembly EDL; it must never restore an abandoned take.
11. Review final retained transcript against the reference by idea coverage, meaning and order. Retimed captions reflect speech actually retained.

## Outputs
Versioned reference, compact retrieval packet, semantic alignment/coverage, decision log, protected ranges, assembly EDL; a re-recording list only if needed.

## Stop conditions
Do not finalize a video with an unresolved required idea, contradictory critical claim, missing/incorrect reference assignment, unreliable word boundaries, or unreadable reference. Continue reversible work on the rest and ask one essential question when necessary.

## Common errors
Literal matching; biased transcription; always keeping the last take; copying script text into captions; confusing directions with speech; reordering words to invent claims; borrowing a neighboring video's line; saying a line is absent because retrieval did not find it.
