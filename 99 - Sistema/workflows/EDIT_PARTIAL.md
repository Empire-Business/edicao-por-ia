**v1.6:** Registre `factory.py change` com o tipo exato. Reabra só as etapas dependentes. Consulte `workflows/RESUME_JOB.md`.

# Workflow — Edit Partial

## Format checkpoint (v1.4)
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


Use when the user asks to change one part of an existing job.

1. Identify the smallest source-of-truth artifact that controls the requested change.
2. Preserve approved EDL segments, captions and pattern behavior outside the requested scope.
3. Patch only the affected ranges/rules.
4. Re-render only the necessary output(s).
5. Re-run QA gates affected by the change.

Do not regenerate a full edit because one cut, caption or overlay needs correction.
