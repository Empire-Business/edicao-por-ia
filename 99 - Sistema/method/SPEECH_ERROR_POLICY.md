# Speech Error Policy

## Goal
Remove obvious mistakes and retakes without changing the speaker's intended meaning or making speech unnaturally robotic.

## Evidence hierarchy
1. explicit self-correction markers in speech;
2. repeated/restarted phrase followed by a complete take;
3. incomplete syntax followed immediately by a cleaner restatement;
4. long pause + restart pattern;
5. transcript confidence/timing plus audio/visual evidence;
6. editorial inference alone — lowest authority.

## Candidate classes

### A. Explicit mistake — high confidence
Examples: “errei”, “de novo”, “pera”, “não, volta”, “vou repetir”.
Default: remove the abandoned attempt and marker when the resulting sentence is natural.

### B. False start / restart — usually high confidence
A phrase starts, breaks, and is repeated more completely within a short window.
Default: keep the complete take.

### C. Duplicate complete take — medium confidence
Two complete versions of the same line exist.
Choose using completeness, fluency, continuity, visual quality and pattern pace. Escalate if wording meaningfully differs.

### D. Filler — pattern-controlled
“é…”, “ahn…”, repeated connectors, breath pauses.
Never assume all fillers are mistakes. Follow the active pattern's aggressiveness.

### E. Stutter / natural hesitation — conservative by default
Do not over-clean to the point of changing personality or cadence.

### F. Contradiction / semantic correction — requires judgment
If two takes express different claims, never auto-delete one only because it appears later. Escalate with both transcript windows.

## Cut boundary rules
- Prefer word-level timestamps.
- Keep configurable handles around retained words.
- Never cut inside a phoneme when a nearby word boundary exists.
- Avoid visible jump cuts during blinks/large mouth movement when a nearby boundary is available; inspect frames around the cut when needed.
- Use tiny audio edge fades to reduce clicks without changing segment duration.

## Candidate JSON
Each suggested removal should record:
- source time range;
- class;
- confidence (`high|medium|low`);
- evidence;
- proposed retained alternative;
- semantic risk;
- whether visual review is required.

## Auto-cut threshold
Only `high` confidence + low semantic risk may be automatically included in an EDL without model escalation. Medium/low candidates need Sonnet or Opus review depending on ambiguity.

## Optional reference-script evidence
If a script exists, load `REFERENCE_SCRIPT_POLICY.md` and `MATCH_REFERENCE_SCRIPT.md`. Compare intent and complete ideas, not literal wording. The script helps identify abandoned starts, missing required ideas and the best actual take; it does not establish what was spoken or prove a divergent take wrong. Preserve paraphrases. Never use forced script alignment to hide recording errors.

Silence shortening is a separate automatic stage after semantic take selection; read `SILENCE_POLICY.md`. Quiet amplitude alone does not identify a speech mistake.
