# Workflow — Analyze Video Reference

## Goal
Extract reusable editing mechanisms from a reference without copying incidental surface details.

## Portable reference
Before analysis/registration, import the supplied external file into this factory and verify its
hash. Analyze the internal copy. Store reference/metadata/frame manifests with relative internal
paths or `workspace://`; never retain the temporary source location as a file dependency.

## Evidence
Use a sparse contact sheet, metadata, transcript if speech is relevant, and targeted frames around notable edits. Do not exhaustively sample every frame unless there is a specific reason.

## Extract
- pace and average shot/cut behavior;
- speech cleanup aggressiveness;
- framing/reframing logic;
- caption mechanism;
- use of punch-ins, B-roll, overlays, music and transitions;
- opening/closing structure;
- what is consistent enough to become a rule;
- what looks like a one-off example.

## Output
Write an annotated reference note with:
- context;
- mechanism;
- transferable rules;
- non-transferable surface details;
- uncertainty;
- status (`reference`, `example`, `rejected`, `unknown`).

Only convert it into a pattern rule after the user approves or multiple references support it.

## Reference-driven studio extension (v1.7)
For supplied visual references, bespoke scenes, state lists or a showreel, route through `workflows/MOTION_STUDIO.md`. It adds a style guide, state list, reusable seek renderer, paginated evidence and bounded review. Do not skip locked speech timing, format context or costs.
