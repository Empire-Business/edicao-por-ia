# Output Rules

## v2 public codes
New exports use `<E>_<video>_<proportion>_<F>_<ID>_PREVIEW_V<n>.mp4` or the final without PREVIEW.
Example: `E01_demo_9x16_F01_ID03_PREVIEW_V1.mp4`. F, ID and E are stable; V is the revision.
Pass the manifest's codes to output_naming. Existing export filenames stay readable and are not renamed.

## Legacy naming
Every user-facing preview and final includes the video name, output proportion, format profile ID,
and version. Use this short pattern (the version is always the last part before the extension):

- Preview: `<video>_<proportion>_<format>_PREVIEW_V<n>.mp4`
- Final: `<video>_<proportion>_<format>_V<n>.mp4`

Examples: `aula-intro_9x16_omnx-sdrai_PREVIEW_V4.mp4` and
`aula-intro_16x9_omnx-sdrai_V4.mp4`. Use `9x16`, `16x9`, `1x1` and similar forms so filenames
work on Windows and macOS. The format is the short format profile ID (`format` in a new manifest),
not the proportion. Legacy filenames using `sem-formato` remain readable; new edits require a registered format. For multiple child videos,
include the child name/ID in `<video>`.

Use the job's human-readable `name`; if it is absent on an older job, use the original source
filename without its extension. Normalize names to lowercase slugs capped at 40 characters and
format IDs at 20 characters. Keep the same version number across proportion variants of one edit.
Increment it for a new editorial revision; a final may use the preview's version number. Optional
variant labels are capped at 16 characters and go before `PREVIEW` or `V<n>`.

Get an unused name with `python3 tools/output_naming.py --name aula-intro --proportion 9:16
--format omnx-sdrai --kind preview --directory jobs/<job-id>/renders`. The helper returns the next
available version for that video, format and preview/final kind. Internal masters, voice tracks,
raw renders and scene chunks keep their technical names; this rule applies to files shown or sent as
video previews/finals.

## Job evidence
Prefer JSON/YAML for machine-readable decisions and Markdown for human rationale.

## Non-destructive rule
EDLs reference source timestamps. Never replace a source file with an edited render.

## Final response from an agent
Report briefly:
- what was produced;
- pattern used;
- important editorial decisions;
- QA status;
- any unresolved ambiguity;
- exact output paths.

Do not dump raw FFmpeg logs unless requested.


## Persistence receipt (v1.4)
After useful feedback, state what was actually saved and whether it applies to this job,
project/pattern or future work for the format. Mention candidates separately. No repeated verbose
memory report. Denied/failed write → say it was NOT saved. A final edit must not claim a learned
preference was applied without checking the effective job and actual draft.
