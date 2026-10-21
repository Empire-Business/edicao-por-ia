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

## Hidden retakes — mandatory sweep (author, 20/10/2026)
"Eu cometi alguns erros de gravação que você não cortou" / "no vídeo do Felca eu cometi um erro perto de 1:17 e você
não tirou". A whole-file transcript is NOT proof of a clean take: Whisper swallows aborted attempts into one long word
("pessoas" lasting 2 s; "é" lasting 9.5 s over five false starts of "O fato é que a IA…") or simply skips them.
1. On the source voice, before choosing takes: `tools/find_hidden_retakes.py --audio <isolated voice> --transcript
   <transcript> --out analysis/hidden_retakes_source.json --retranscribe`. It flags words > 0.8 s, voiced gaps the
   transcript did not write, repeated 2–4-word phrases and adjacent duplicates, and re-transcribes each window alone
   with +8 dB gain. Use it to pick the LAST complete attempt of each idea.
2. After building the cut voice: transcribe the final voice and run the same tool on it
   (`analysis/hidden_retakes_final.json`). Zero long words, zero repeats and no stray syllables between takes
   (e.g. "durante a reunião criativa." = tail of an aborted take glued to the next one) are a delivery gate.
3. Trim each take to its voiced islands; when a retake starts right after an aborted one, start the cut at the
   retake's first voiced frame, not at the transcript's word start (which may belong to the aborted attempt).
4. Spoken direction to the editor ("é a frase mesmo?", "tem um finalzinho aí…", "putz") is always removed.

## Auto-cut threshold
Only `high` confidence + low semantic risk may be automatically included in an EDL without model escalation. Medium/low candidates need Sonnet or Opus review depending on ambiguity.

## Optional reference-script evidence
If a script exists, load `REFERENCE_SCRIPT_POLICY.md` and `MATCH_REFERENCE_SCRIPT.md`. Compare intent and complete ideas, not literal wording. The script helps identify abandoned starts, missing required ideas and the best actual take; it does not establish what was spoken or prove a divergent take wrong. Preserve paraphrases. Never use forced script alignment to hide recording errors.

Silence shortening is a separate automatic stage after semantic take selection; read `SILENCE_POLICY.md`. Quiet amplitude alone does not identify a speech mistake.
