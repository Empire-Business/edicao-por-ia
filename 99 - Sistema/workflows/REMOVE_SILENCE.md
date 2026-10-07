# Workflow — Automatically remove unmotivated silence

## Objective / inputs
Shorten dead space without losing words or disconnecting sound and picture. Inputs: source, timestamped transcript/VAD, active pattern, approved assembly EDL and protected source-time ranges. Read `method/SILENCE_POLICY.md`.

## Process
1. Work from the original evidence (probe, transcript, silence map). Reference-script comparison and retake selection happen before destructive-looking edits to a preview; originals remain immutable.
2. Select/calibrate the dialogue track. Detect quiet if the source hash/settings are not already cached:
   ```bash
   python3 tools/detect_silence.py "/absolute/source.mp4" \
     --noise=-40dB --duration 0.15 --audio-stream 0 \
     --output jobs/example/analysis/silence.json
   ```
3. Create `jobs/example/edit/protected_ranges.json` using `jobs/PROTECTED_RANGES_TEMPLATE.json`. An empty list is valid only after considering intentional pauses/nonverbal content. It is not proof that none exist.
4. Generate synchronized source-time cuts from the assembly:
   ```bash
   python3 tools/plan_silence_cuts.py \
     --source "/absolute/source.mp4" \
     --silence jobs/example/analysis/silence.json \
     --transcript jobs/example/analysis/transcript.json \
     --protected jobs/example/edit/protected_ranges.json \
     --base-edl jobs/example/edit/assembly-edl.json \
     --pattern patterns/talking-head-clean-v2.yaml \
     --output jobs/example/edit/edl.json \
     --report jobs/example/analysis/silence_edit_report.json
   ```
   YAML needs optional PyYAML. Without it, use a JSON pattern or `--mode natural`; explicitly preserve the requested output geometry/settings in the base EDL. Do not install packages without authorization.
   Pass explicit job-mode overrides with `--mode tight|natural|relaxed|off`. Detailed overrides go in a JSON object via `--settings`. Honor `silence_removal.enabled: false` by skipping or using `--mode off`.
   Without `--base-edl`, the tool uses the whole source. This is only correct for a job with no prior cut decisions, never a partially edited or split child video. For multiple sources, apply one source map at a time against versioned EDLs; other source segments are preserved unchanged.
5. Inspect the report. Source hashes, clip bounds and protected ranges must match. A missing transcript cannot be treated as an all-silent timeline. Create/review evidence instead.
6. Render the EDL using `render_edl.py`, then retime the transcript/SRT from that exact EDL. For multi-source jobs, use source-associated transcript mapping, never one source's words for every clip.
7. Run mechanical and editorial QA. Listen around each cut, or mark auditory review pending when listening is unavailable. Check intentional silences against the decision log. If cuts feel breathless, increase retained pause/handles and rerender a new version.

## Outputs
New `edit/edl.json`, silence audit JSON, retimed speech/captions, draft media and QA notes. Rendering/analysis do not consume language-model tokens themselves.

## Stop / common failures
Stop finalization on truncated words, A/V drift, unsafe evidence, overwritten assets, unexplained missing phrases or overly aggressive pace. Avoid audio-only shortening, stale timestamps, unprotected quiet speech, cutting an intentionally silent demonstration, and rendering from the unedited original after a script/retake decision.


## Format feedback and actual parameters (v1.4)
Use `job.effective*.silence-settings.json` from `resolve_format_context.py` with `--settings`.
This incorporates saved supported pause preferences without editing the pattern. Rhetorical
pause preferences still require source-specific protected ranges from the editor. Never reuse
old source timestamps. The user can override this one video's pacing through explicit_fields.
