**v1.6:** `factory.py intake` cria jobs filhos com o mesmo batch_id e saldo compartilhado. Consulte `workflows/RESUME_JOB.md`; nunca abrir orçamento por filho nem resetar consumo ao retomar.

# Workflow — Batch Factory

## Format checkpoint (v1.4)
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


## Goal
Process many independent videos without making Opus the default worker.

## Pipeline
1. Deterministic ingest/probe for all sources in parallel.
2. Local ASR in bounded parallelism appropriate to machine resources.
3. Haiku screening per job/chunk.
4. Sonnet editorial pass per job.
5. Opus queue only for escalations.
6. Draft renders in parallel only within CPU/GPU limits.
7. Mechanical QA for every output.
8. Editorial QA based on exception sampling + all flagged jobs.

## Isolation
Each job gets its own directory. Shared caches are read-only and keyed by source hash.

## Cost log
Record model role, task type and estimated tokens when the execution environment exposes them. Never fabricate usage numbers.
