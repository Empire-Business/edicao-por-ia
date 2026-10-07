# Workflow — Ingest

1. Create or open the job directory.
2. Do not copy massive media unless the user wants a self-contained project; referencing an absolute/local source path is allowed.
3. Run `tools/probe_media.py` on every source.
4. Compute source hashes when cache reuse matters.
5. Record expected number of outputs if supplied.
6. If speech exists, transcribe once and cache by source hash/settings.
7. Generate a sparse contact sheet only if visual reasoning is needed.

Output: `analysis/media.json` plus source metadata in the job manifest.
