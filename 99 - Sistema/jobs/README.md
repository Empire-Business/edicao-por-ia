# Jobs

One directory per intended final video.

Suggested structure:
```text
jobs/<job-id>/
  job.yaml
  analysis/
    media.json
    transcript.json
    silence.json
    edit_candidates.json
  edit/
    edl.json
    decision_log.md
  qa/
    qa.json
  renders/
```

Source files may remain outside the repository and be referenced by path. Large media is intentionally gitignored.

With a reference script, add `references/`, `analysis/script-candidates.json`, `analysis/script_alignment.json` and `analysis/script_coverage.md`. Preserve `edit/assembly-edl.json` before applying silence cleanup; save `edit/protected_ranges.json`, the final `edit/edl.json`, and `analysis/silence_edit_report.json`.

New-job examples:
```bash
python3 tools/make_job.py --source "/path/video.mp4" \
  --reference-script "/path/roteiro.md" --script-mode flexible \
  --silence-mode natural --pattern talking-head-clean-v2
```
Job files may be JSON-serialized with a `.yaml` extension (valid YAML) to quote arbitrary paths safely. Optional YAML loading uses PyYAML; local tools do not auto-install it.


## v1.4 personalization
`make_job.py` accepts --client, --project, --session, --anonymous and --root. It resolves a client's
preferences into a new effective manifest plus Markdown context/receipt/silence-settings. The source
job and approved patterns are not overwritten. Use the effective manifest throughout the workflow.
See `workflows/CLIENT_MEMORY.md` for per-turn capture and explicit override pins.
