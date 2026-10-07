# Edge-Case Tests

1. Source with no audio.
2. Source with variable frame rate.
3. Transcript contains “não, pera, vou repetir” and then a complete sentence.
4. Two complete takes differ semantically.
5. One 30-minute recording contains three independent short videos.
6. User says there are two videos but automatic signals suggest three.
7. Pattern is missing.
8. Pattern requests portrait output from landscape source.
9. Output path already exists.
10. Source becomes unavailable after analysis cache was created.
11. Client context contradicts old memory.
12. Caption request exists but transcript timing is low confidence.
13. Music makes silence detection unreliable.
14. Final render contains a black frame at a cut.
15. Optional transcription backend is absent.

16. Reference script has paraphrases, stage directions, required CTA and repeated takes.
17. Wrong reference version or scripts swapped between child videos.
18. A silent interval contains a low-volume negation omitted by ASR.
19. Multi-track dialogue with one empty track; ensure all speakers are protected.
20. Entirely silent audio, nonzero time origin or stale source hash.
21. A script cue requests an intentional long pause; it must acquire source timestamps.
22. Existing assembly removes a take; silence cleanup must not restore it.

## Motion-specific edge cases
Fractional fps; VFR input; a cue deleted by silence/retake editing; an effect extending beyond the child; altered PNG/cache hash; preview frames used as a full layer; two overlapping captions; a face below the assumed safe zone; cropped proof/number; long text; missing font; no audio track; stale master with same duration; transparent layer accidentally flattened to black; a remote image URL; SVG/script injection; unavailable npm registry; already existing output; cache from a different client. Tool-guard cases are tested where listed in results; semantic and brand cases remain acceptance scenarios.

## Memory / client scope additions
Unknown client; stale ACTIVE.md; two parallel clients; one-file/two-video child-job exception;
contradictory feedback; later rejection of an approved version; unsupported setting; expired note;
retry after a crash between client commit and host receipt; symlinked storage; unavailable write
permission; live hooks disabled; no actual new preference; user requests forgetting a key;
old exports/backups still containing it; new session with no configured owner; budget omissions.
