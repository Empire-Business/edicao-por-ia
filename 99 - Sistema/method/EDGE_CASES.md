# Edge Cases

## Variable frame rate
FFmpeg re-encode from the EDL rather than assuming frame-number math. Store decisions in seconds.

## Missing audio
Allow visual-only edits. Do not run transcript workflow. Renderer must synthesize silence only when a downstream mux requires audio.

## Multiple speakers
Do not delete overlaps by default. If speaker separation matters, use optional diarization and record uncertainty.

## Music under speech
VAD/silence detection may be unreliable. Prefer ASR and do not equate “non-silent” with speech.

## Very long files
Probe once, transcribe once, chunk the transcript, and share read-only caches across child jobs.

## Screen recordings / slides
Scene changes may be rare or abrupt. Use transcript/topic boundaries more heavily.

## Tiny retakes
If two takes overlap semantically within a few seconds, compare both. Do not keep a fragment merely because it came last.

## Hard visual jump at speech cut
Try a nearby word boundary, a punch-in defined by the pattern, or approved B-roll. Do not add random transitions by default.

## User says “cut all pauses”
Interpret through pattern minimums and naturalness. Do not remove every micro-pause unless explicitly requested.

## Corrupt source / unsupported codec
Stop before editorial work, preserve the source, and create a diagnostic/proxy rather than rewriting the original.

## Portrait source to landscape output (or reverse)
Follow pattern fit mode (`cover`, `contain`, or explicit crop). Never silently stretch.
