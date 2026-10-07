# Workflow — Define Pattern

## Format checkpoint (v1.4)
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


## Inputs
- user intent;
- one or more approved references when available;
- target platforms/proportions;
- brand constraints;
- elements that must never occur.

## Process
1. Read `patterns/PATTERN_SPEC.md`.
2. Extract mechanisms, not surface copying.
3. Separate hard rules from adjustable defaults.
4. Use Opus 5.5 only if reference interpretation is complex; otherwise Sonnet is enough.
5. Create a new versioned YAML file. Never edit an existing pattern in place when the change would alter prior job reproducibility.
6. Add the pattern to `patterns/INDEX.md`.
7. Test with at least one representative job before calling it approved.
8. For a newly registered author format, follow `PUBLISH_FORMAT_GALLERY.md`. Publish its guide, real example and search descriptors in the visual gallery before reporting creation complete. A recipe's draft/approved status remains honest and separate from gallery publication.

## Output
A pattern file with explicit status: `draft`, `approved`, or `deprecated`.
