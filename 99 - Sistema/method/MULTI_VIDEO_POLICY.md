# Multi-Video Policy

## Two different problems

### Multiple files, one final video
Treat all files as sources for one job.

### One file, multiple final videos
Create one parent ingest record, then separate child jobs. Each child gets its own EDL, pattern, render and QA.

## Boundary evidence
Potential boundaries can come from:
- explicit user timestamps/expected count;
- long silence or recording stop behavior;
- spoken markers (“próximo vídeo”, “agora outro…”);
- repeated hook/introduction structure;
- slate/clap/repositioning;
- strong visual scene transition;
- topic reset in transcript.

No single weak signal is enough by itself.

## Confidence
- **High**: explicit marker or multiple independent signals agree.
- **Medium**: likely topic/recording reset but no explicit marker.
- **Low**: purely semantic guess.

Split automatically only at high confidence unless the user supplied the expected segmentation. For medium/low confidence, ask one compact question with proposed timestamps.

## Parallelism
Independent child jobs may be analyzed/rendered in parallel, but never share mutable edit state. Reusable source transcript/probe caches may be shared read-only by source hash.

## Per-video reference scripts
Associate script paths/block IDs with each child job before comparison. Shared read-only source evidence is allowed; semantic alignment, protected ranges and EDLs remain isolated. Feed the silence planner each child's base EDL, not the complete parent recording. Keep original source seconds throughout; do not confuse child-local timestamps with parent time.
