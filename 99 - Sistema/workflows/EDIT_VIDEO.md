**v1.6:** Para trabalhos novos, use `factory.py intake/resume`, depois siga `workflows/RESUME_JOB.md` para registrar as etapas. Antes de renderizar, use `validate-edl` contra o escopo. Leia o job efetivo mais recente. Orçamento/modelos: `method/EXECUTION_AND_COSTS.md`.

# Workflow — Edit Video

## Format checkpoint (v1.4)
Before editing, require both the F format and the ID visual explicitly selected by the user. Verify both registrations and use the v2 effective manifest. No format:
ask “Qual formato devo usar neste vídeo?”; do not start the edit or borrow Bruno/another profile.
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


## 1. Preflight
Load job and named pattern. Confirm source files/hash/streams, one versus multiple outputs, and reference-script assignment. Normalize unusual timestamps before making a source-time plan. Read `INPUT_CONTRACT.md`.

## 2. Original evidence
Probe/transcribe the actual recording independently and detect silence before cutting. Use `tools/transcribe.py` and `tools/detect_silence.py`; cache by source/settings hash. Generate sparse frames only as needed. Do not substitute script wording into transcription.

## 3. Script comparison, if provided
Run `MATCH_REFERENCE_SCRIPT.md`. Default is flexible/semantic, not verbatim. Map each required idea to real source timestamps; distinguish fluent paraphrases, mistakes, retakes, directions and missing material. No script: proceed normally.

## 4. Editorial assembly
Haiku screens likely error/restart candidates; Sonnet resolves ordinary editorial choices and script alignment. Escalate only unresolved high-impact windows to the director. Write `analysis/edit_candidates.json`, `edit/decision_log.md` and `edit/assembly-edl.json`. Mark intentional pauses/nonverbal moments as source-time protected ranges.

## 4b. Insertion assets, if supplied
Run `USE_INSERTION_ASSETS.md`. Match user-provided images/videos to semantically appropriate moments using transcript meaning, reference-script blocks, cue phrases, and pattern expectations. Create a provisional `analysis/insertion_plan.json`; finalize placement after step 5 using the retimed transcript. Use only high-confidence placements automatically; otherwise skip or ask one targeted question if a required asset cannot be placed safely.

## 4c. Requested TikTok/YouTube scenes
Accept the request and use only ScrapeCreators for search, metadata and media URL resolution,
through `tools/broll_research.py`. The request is authorization for those calls; never add a
second generic approval step. Use the visible keys file described in `method/EXTERNAL_SERVICES.md`.
Record source/author and API failures, inspect actual downloaded frames and then run
`USE_INSERTION_ASSETS.md`. If the API cannot expose the selected media, report that precise
limitation and research alternatives through the same provider. No yt-dlp/browser/provider fallback.

## 5. Automatic silence cleanup
Enabled by default for speech jobs. Run `REMOVE_SILENCE.md` against the assembly EDL, with the active pattern, timestamped speech and protected ranges. Respect job overrides. The result is `edit/edl.json` and `analysis/silence_edit_report.json`. Do not stop at merely detecting silence. If disabled, preserve the assembly as the final EDL and record the choice.

## 6. Draft render
Choose the human-readable video name from `job.yaml` (or the source filename on an older job),
resolve its format profile ID and output proportion, then get a unique preview path with
`python3 tools/output_naming.py --name <video-name> --proportion 9:16 --format <format-id> --kind preview --directory jobs/<job-id>/renders`.
Pass the returned path to `python3 tools/render_edl.py jobs/<job-id>/edit/edl.json --output <returned-path>`.
For a final, use `--kind final` and the same version as the approved preview. Always use a new path;
original media and earlier versions are never overwritten.

## 7. Captions
Use `tools/retime_transcript.py` with the actual retained transcript and final EDL. Never use unspoken script lines as captions. For multiple media sources, use a source-specific transcript mapping and verify source identities.

## 7b. Final visual insertions and JavaScript motion
With the clean master and retimed transcript available, finalize insertion timing. When the user asks for rich illustrations, speech-to-visual direction or scene-aware composition, run `DIRECT_VISUALS.md` first; inspect real frames, map space and plan semantic beats. Every retained idea receives a decision, not necessarily an effect. Consider a meaningful reusable animation unless disabled. Follow `CREATE_JS_ANIMATIONS.md` for code-based motion. Hash the clean master and EDL, then anchor every layer to integer clean-master frames. Use the motion compositor to keep narrator audio intact. Do not turn silent motion/B-roll into a spoken EDL segment. Caption-safe areas remain reserved; advanced overlapping captions/media need explicit composition order.

For visual planning in step 7b, use `method/EDITORIAL_REASONING.md` within the existing plan:
identify the information relationship, select a mechanism allowed by the pinned recipe, and
tie it to retained speech and actual evidence. This does not change the recipe, add effect
quotas, move speech, or require a new artifact for old/non-visual jobs. A justified `keep`
remains complete coverage.

## 8. QA and delivery
Run mechanical QA and `workflows/QA.md`. Verify script idea coverage when applicable, retained pauses/words, natural rhythm and A/V sync. Mechanical success alone is not auditory/editorial approval. Fix/version EDLs, not sources. Render final only after applicable required gates are actually satisfied.

## Comparação obrigatória com a referência do formato
Para trabalhos novos com format_contract, inspecionar referência real e preencher analysis/format-plan.json antes da montagem. Após renderizar, preencher qa/format-fidelity.json com critérios do contrato, decisões, cenas de referência e frames do render com hashes. O controlador bloqueia montagem/QA/entrega sem comparação válida. Usar tools/format_fidelity.py --prepare para estrutura pendente; isso não aprova nada. Referência, UID/geração, receita e render devem corresponder ao trabalho. Não afirmar semelhança artística só por validação mecânica. Exceção atual deve constar em format_deviations do trabalho e coincidir com user_instruction no relatório; não altera o modelo consolidado.

No preflight do formato, usar method/FORMAT_EXECUTION_CHECKLIST.md e as recipe_rules do contrato. Verificar a rota real de execução e os insumos; recipe status draft não é certificação artística. A comparação exige restrições/identidade e regras específicas de visual, motion, áudio, legenda, pesquisa e layouts, além da sequência de cenas.
