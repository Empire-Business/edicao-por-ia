# Reference and pauses — SIMULATION

## Context / objective
A person records from a script but speaks naturally and sometimes restarts. The edit should preserve the intended argument, not enforce identical wording.

## Equivalent wording
Reference: “Você não precisa publicar todos os dias.”
Recording: “Não é necessário postar diariamente.”
Expected decision: retain a fluent complete take. A lexical mismatch alone does not show an error.

## Actual abandoned attempt
Reference: “Vou mostrar três cuidados.”
Recording: “Vou mostrar dois... não, pera. Vou mostrar três cuidados.”
Expected decision: inspect the genuine correction and boundaries, then remove the abandoned attempt/marker if safe. The script is supporting evidence, not a way to synthesize 'três'.

## Different meaning
Reference: “Você não precisa publicar todos os dias.”
Recording: “Você precisa publicar todos os dias.”
Expected decision: verify the audio/ASR, flag the missing negation and check for an actual alternate take. Never remove/add words to manufacture a matching claim.

## Silence
A synthetic timeline has speech at 1–2 and 4–5 seconds; quiet at 0–1, 2–4 and 5–6. Automatic planning shortens the unprotected quiet and retains speech handles. If 2–4 is an intentional pause, adding it to protected ranges prevents its removal. This is a range-arithmetic test scenario, not a recording of human speech.

## Two final videos
Script A belongs to child A; script B to child B. Use original source times and child-scoped EDLs. Do not borrow an excellent sentence from B to fill a missing required idea in A without explicit authorization.

## Transferable / not transferable
Transfer: distinction between equivalent meaning, actual error, intentional pause and evidence-backed cuts. Do not copy example numbers or hypothetical timestamps into a real job.

## Status
Simulation. Semantic/audio acceptance needs a real script and recording; no model behavior is certified by this example.
