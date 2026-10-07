# Workflow — Split One Recording into Multiple Videos

1. Probe/transcribe source once at parent level.
2. Collect boundary signals: long silences, explicit spoken markers, hook resets, topic resets, visual transitions.
3. Produce `analysis/boundaries.json` with timestamp, confidence and evidence.
4. If expected output count is known, use it as a constraint, not as permission to invent boundaries.
5. High-confidence boundaries may create child jobs automatically.
6. Medium/low confidence: ask one question containing the proposed split timestamps and brief labels.
7. Child jobs reference the same immutable source and parent transcript cache.
8. Each child applies its own pattern and QA independently.

Never concatenate neighboring child-video context into one model prompt after boundaries are accepted.

Before editing children, assign each reference script/block subset and source-time scope. Do not infer association solely from upload order. Apply silence cuts to each child assembly, never to the entire source as a replacement for the child EDL.
