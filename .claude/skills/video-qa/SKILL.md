---
name: video-qa
description: Run deterministic and editorial QA on a draft or final video job.
disable-model-invocation: true
---

QA `$ARGUMENTS` using `workflows/QA.md` and `method/QUALITY_BAR.md`. Run local QA tools first, then delegate interpretation to `video-qa`. Escalate to `video-director` only when the failure is editorially ambiguous or meaning-sensitive.
