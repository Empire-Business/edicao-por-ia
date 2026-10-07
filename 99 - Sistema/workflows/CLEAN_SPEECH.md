# Workflow — Clean Speech

1. Ensure independent transcription of the actual recording and usable timestamps.
2. If a reference script was supplied, run `MATCH_REFERENCE_SCRIPT.md`; never require verbatim wording in flexible mode.
3. Split long transcripts into overlapping chunks. Haiku marks likely mistakes using `SPEECH_ERROR_POLICY.md`; a lexical mismatch alone is not an error.
4. Merge candidate windows. Auto-accept only high-confidence, low-risk abandoned takes. Sonnet resolves normal semantic choices; the director receives only unresolved high-impact cases.
5. Write retained spans to `edit/assembly-edl.json` and log source-time decisions. Mark intentional pauses/breaths/nonverbal actions in `edit/protected_ranges.json`.
6. Run `REMOVE_SILENCE.md` unless disabled: convert quiet ranges into a synchronized A/V EDL while protecting speech and prior decisions. Never reintroduce discarded takes.
7. Render a new draft; retime transcript/captions from the final EDL.
8. Review around every cut. If playback/listening is unavailable, provide short review clips and mark auditory QA pending instead of claiming it passed.
9. Optional fresh ASR of the final is supplementary evidence, not a substitute for listening or a license to rewrite speech to match the reference.

Do not remove every hesitation or breathing pause by default.


## Hidden repeats (learned 2026-10-01)
Whisper merges a false start into the following take ("Antes de sair... antes de sair aceitando" came back as one clean sentence). After assembling, scan the retimed words for short function words lasting > 0.6 s or gaps > 0.5 s inside a sentence, re-transcribe that slice in sub-slices, and cut the first attempt. A word that lasts far longer than it should is the tell.
