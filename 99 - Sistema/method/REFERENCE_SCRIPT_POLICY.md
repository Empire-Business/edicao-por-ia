# Reference script policy

## Purpose and default
A supplied script is an **optional editorial reference**, not a verbatim transcript and not proof of what was actually recorded. Default: `reference_script.mode: flexible`.
Aim for the closest faithful version of the intended message, structure and CTA that the recorded material supports. Preserve fluent paraphrases, contractions, synonyms and useful improvisation when they convey the same idea. A word-for-word difference alone is never a speech error.

Without a script, continue the existing speech-cleanup workflow; do not invent a reference or demand one.

## Intake and isolation
Record reference path(s), version/hash, mode and associated child-video ID in the job. Accept pasted text by saving a UTF-8 reference file. Preserve the original file and normalize supported attachments to TXT/MD or structured JSON using available authorized tools; do not pretend to read an inaccessible document. `prepare_script_comparison.py` accepts TXT, MD and JSON, not PDF/DOCX directly.
For two videos in one recording, explicitly map each script or block subset to the right child job and source-time range. Do not combine scripts or infer their association merely from upload order. Ask one concise question only when association is genuinely ambiguous.

## Never bias evidence to match the reference
1. Transcribe the **actual recording independently** before comparing it to the script.
2. Do not replace ASR text with the script, force-align unspoken script lines, or assume a script word was uttered.
3. Treat ASR as fallible. Suspected numbers, names, negation and low-confidence words require targeted audio review. Without playback/listening capability, mark the review pending and provide the excerpt.
4. Subtitles must follow the retained recorded speech, not the reference's unspoken wording.
5. No synthetic voice, fabricated sentence, dubbed replacement or patched claim without a separate explicit request.

## Compare idea units, not string differences
For each spoken block, create `analysis/script_alignment.json` with:
- block ID, reference text and required/optional status;
- actual transcript excerpts + immutable source path and timestamps;
- semantic status: `equivalent`, `partial`, `repeated_take`, `meaning_divergence`, `missing_after_review`, or `uncertain`;
- candidate/selected take, rejected take and reason when applicable;
- confidence and evidence, protected words/clauses, unresolved issue;
- final action: keep, trim abandoned take, review, or request re-recording.

Directions, headings and stage cues are `direction_not_spoken`, not missing speech. Map a direction such as '[pause]' to a **protected source-time range** before automatic silence cleanup; a label without timestamps cannot protect media mechanically.

`prepare_script_comparison.py` only retrieves compact lexical candidates. Its score is NOT semantic confidence, not exhaustive search, and never a cut authorization. A fluent paraphrase can have low lexical overlap. Sonnet must check surrounding context and search broader transcript sections when candidates are weak. Every required idea must be accounted for before finalization.

## Cut decision rules
- **Same idea, different wording:** keep a fluent take. Do not cut just to increase literal similarity.
- **Clear abandoned take then a complete correction:** prefer the complete, intentional take when context confirms it; the reference provides extra evidence.
- **Two complete alternatives:** compare intended meaning, fluency, full-clause integrity, sound and visual continuity. Do not always select the last take or the most literal one.
- **Different price, number, name, negation, promise or condition:** the script highlights a conflict but is not permission to delete a negation or fabricate agreement. Verify the recording. Use a genuine matching take if available; otherwise flag and ask only the essential question.
- **Useful ad-lib:** preserve when it supports the reference. Remove unrelated digressions only when the user's requested fidelity/pacing warrants it and the remaining argument stays complete.
- **Required line never recorded:** report it as a recording gap, with suggested re-record text clearly labeled as a suggestion. Never pretend it exists in the source.
- **Different idea order:** default preserves source order. `reorder_policy: match_reference_safe` permits moving complete coherent blocks to the reference order, with a decision log and continuity QA. Never splice isolated words to invent a new statement.
- **Wrong/outdated script suspected:** show the concrete mismatch and confirm the version; do not declare the entire performance incorrect.

## Modes
`flexible` is standard. `strict` increases attention to exact required wording only when explicitly requested. Even strict mode cannot manufacture words, falsify captions or reinterpret every stylistic variation as a mistake. `off` disables comparison without disabling silence cleanup.

## Tokens and review
Use local hashing/retrieval first. Haiku can tag candidate restarts; Sonnet is the normal semantic editor. Escalate only unresolved high-impact windows to the configured director model. Reuse the transcript; a new script invalidates alignment/decisions, not transcription. Load only the active reference and child-job scope.
