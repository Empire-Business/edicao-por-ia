# Workflow — Review Existing Edit

## Format checkpoint (v1.4)
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


1. Identify whether the request targets the EDL, pattern, captions, audio, or final render.
2. Preserve approved portions; do not regenerate the whole edit for a local fix.
3. Probe the existing output.
4. Compare against job manifest + pattern + decision log.
5. Edit the smallest source-of-truth artifact possible, usually the EDL or caption data.
6. Re-render affected output and rerun relevant QA gates.
