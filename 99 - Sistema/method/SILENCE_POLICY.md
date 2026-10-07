# Automatic silence cleanup policy

## Default
Automatic cleanup is enabled for speech-editing jobs. It shortens **unmotivated quiet gaps**, including dead space at the beginning/end, while preserving intelligibility and appropriate pacing. The user should not have to request every individual pause cut.
This is not permission to remove every breath, dramatic pause, demonstration, listening beat, or moment of intentional silence.

## Implemented path
`detect_silence.py` detects quiet ranges; `plan_silence_cuts.py` intersects those ranges with the current assembly, protects timestamped speech and explicitly marked pauses, and writes a new EDL + audit report. `render_edl.py` applies that EDL to both picture and sound.
Do NOT shorten only the audio with `silenceremove` while leaving the video timeline unchanged. Same source intervals must be removed from both tracks, followed by caption retiming.

## Starter settings, not universal truth
Three modes: `natural` (0.8 s trigger; ~0.30 s retained pause), `tight` (0.5 s; ~0.18 s), `relaxed` (1.5 s; ~0.50 s). Word handles add protection and may make retained gaps longer. These are configurable starting values, not claims of an optimal pace.
Version-1 patterns keep their existing `max_unmotivated_silence_seconds` thresholds. Version-2 starters explicitly opt into these new settings. Never silently mutate an approved pattern. Job overrides take precedence.

## Required sequence
1. Analyze the original, before removing pauses: they help identify restarts and independent videos.
2. Select the actual dialogue track(s); do not rely on an empty channel, soundtrack, or a muted microphone. In multi-track dialogue, protect speech across **all relevant speakers**, or compute the intersection of per-track quiet regions. The single-track detector alone is insufficient for unexamined multi-track material.
3. Detect quiet locally with configurable threshold and minimum duration. Inspect an excerpt to calibrate noisy/soft recordings instead of increasing the threshold until speech disappears.
4. Transcription or VAD provides speech protection. Low volume is not proof of no speech; no ASR word is not proof of silence. Timestamped low-confidence words remain protected too. If word timestamps are absent, the tool conservatively protects the entire text-bearing segment.
5. The editor marks intentional pauses, breaths and nonverbal actions in `edit/protected_ranges.json`. Unknown intent is not inferable from amplitude alone; preserve ambiguous moments or flag a review excerpt.
6. Select error/retake removals first, then apply silence cleanup to the resulting assembly EDL. Intersect each cut with existing retained source ranges; never merge away meaningful source/audio content between distinct quiet intervals.
7. Keep configurable handles around words, plus a short pause according to mode. Avoid micro-cuts and tiny retained fragments. Do not change playback speed to conceal a bad cut.
8. Render to a new file; do not overwrite media or a prior render. Retimed captions use the final EDL.
9. Check residual unmotivated gaps, complete words, cut clicks, natural cadence, protected pauses and A/V synchronization. A protected long pause is not a failed QA gate merely because it is long.

## Tool guards and limitations
- Missing/empty speech evidence blocks automatic speech cleanup; do not bypass the guard to claim success.
- No audio means not applicable, NOT delete the entire image sequence.
- An entirely silent recording blocks cleanup pending track/threshold/microphone review.
- Nonzero stream origins need a normalized working copy with source-time mapping first.
- Stale source hashes, mismatched sources, invalid timestamps, empty EDLs and overwrites are rejected.
- A music/noise bed can hide quiet gaps. The energy-only detector may leave pauses; report that limitation instead of pretending all gaps were removed. Use a dialogue stem or additional local speech analysis when authorized.
- Mechanical guards do not understand rhetorical intent, do not guarantee perfect ASR boundaries, and do not replace audio/editorial QA.
- These tools output a draft EDL. Neither an EDL nor a decodable MP4 alone proves editorial quality.

## Report
Save `analysis/silence_edit_report.json`: settings, source/evidence hashes, original-time cut ranges, protected ranges count, removed seconds and before/after timeline duration. Document deliberately retained pauses in the decision log.

## Source
FFmpeg filter documentation: https://ffmpeg.org/ffmpeg-filters.html#silencedetect and the `trim`, `atrim`, `setpts`, `asetpts` and `concat` sections; consulted in this revision. Detection logs quiet ranges; trimming is a separate operation.
