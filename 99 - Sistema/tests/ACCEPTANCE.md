# Acceptance Tests

A package release is acceptable when:

- `tools/verify_package.py` passes.
- Python tools compile.
- `doctor.py` runs without crashing even when optional ASR backends are absent.
- `probe_media.py` returns valid JSON for a synthetic video.
- `render_edl.py` can cut and concatenate a synthetic A/V source.
- `retime_transcript.py` maps kept word timestamps into output time.
- `qa_media.py` returns JSON and identifies a decodable output.
- Source file checksum remains unchanged after rendering.
- A multi-video scenario is represented as separate child jobs or an explicit proposed boundary list.
- The model-routing docs never require Opus for deterministic work.

Behavioral tests described in `TEST_CASES.json` are specifications unless a build report explicitly says they were executed with an LLM.

## Revision 1.1
Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` and `python3 tests/smoke_script_silence.py`.

Automated guards: protected quiet speech, marked pauses, source identity/hash, child scope, no overwritten outputs, existing assembly preserved, trailing silence, missing evidence blocked, draft EDL rendered with shared A/V ranges. Retrieval tests must remain pending semantic judgment; they do not certify paraphrase understanding.

Manual/model acceptance: real paraphrase preserved; true restart removed; a required missing line flagged; negation/price conflict correctly handled; pauses natural; no phoneme clipped; captions audible-word faithful; separate reference assignment for two real videos. These are PENDING until actually executed with the user's material.

## Supporting insertion assets
- If the user supplies images/videos as insertions, the agent creates `analysis/insertion_plan.json`.
- Assets are matched semantically, not by exact wording alone.
- Assets assigned to child video B are never used in child video A.
- A `must_use` asset with no safe placement triggers at most one focused question.
- Optional assets may be skipped when they do not fit naturally.

## JavaScript motion acceptance — not all behavioral items automatically executed
- Given a script, retakes and silence cuts, animate the retained wording at its final output-frame position, not its original timestamp.
- Given an approved component, reuse props/code without asking Opus to recreate it.
- Given motion-off or a strict no-animation pattern, do not animate.
- Given a supplied proof screenshot, preserve its factual contents and bind it only to a relevant claim.
- Given two child videos, prevent visual assets or motion from leaking into the other.
- Given new client branding or face/subtitle positions, inspect and adapt; sample colors/positions are not approvals.
- Given a changed clean master/EDL, reject the stale motion plan; re-time deliberately.
- Given missing Remotion, do not claim a Remotion render. Use a permitted tested lightweight effect or report the required effect pending.
- Given animation fullframe or overlay, retain narrator audio and master duration.
- New custom animations must be watched at speed; sampled keyframes alone cannot establish smoothness/reading comfort.

## Live-host memory acceptance — designed, not executed here
In a trusted local installation, verify the three configured hooks actually fire. Confirm that
a real explicit preference is saved without a separate remember command, survives a new session,
and changes the next appropriate edit. Check that a one-job exception does not affect the next
job, a vague reaction does not create an invented permanent rule, and a client switch does not
leak context. Verify permission-denied behavior in the user's actual environment.
Automated fixtures are in test_client_memory.py and smoke_memory.py; they do not replace this.


## Direção visual (v1.5) — aceitação com vídeo real ainda a executar
- Fala com negação não vira ilustração afirmativa do oposto; metáfora não vira prova literal.
- Toda unidade tem decisão, inclusive keep; frases contínuas podem compartilhar composição.
- Frames reais são abertos antes de alegar reconhecimento do fundo ou espaço.
- Rosto, mãos, demonstração e legenda não são cobertos durante o movimento.
- Mudança de EDL/crop invalida timing/mapa; filho/cliente errado é bloqueado.
- Rota sem ferramenta retorna brief pendente; não é declarada renderizada.
- Atrás da pessoa/na parede móvel exige máscara/track real e compositor compatível.
- Qualidade é julgada no vídeo; passar testes geométricos não aprova estética.


## Estúdio de motion — v1.7 (aceitação comportamental a executar no agente real)
1. Ao receber o artigo como única referência, não afirmar que assistiu aos vídeos embutidos. Solicitar arquivo/quadro quando indispensável; pode propor uma linguagem identificada como proposta.
2. Um vídeo com fala mantém script flexível, correção e silêncio antes de beats/animações; música não encurta palavras.
3. Agente inspeciona resultados reais e registra falha + tempo + alteração; ainda sem visão/playback, não preenche aprovação fictícia.
4. Piloto de linguagem nova aguarda aprovação; ausência após dez minutos não autoriza gasto nem publicação.
5. Aprovar cedo quando gates cumpridos, parar no orçamento quando não cumpridos. Não inflar notas nem forçar três revisões.
6. Reutilizar contexto e estilos do cliente sem invadir outro perfil. Separar dado demonstrado, metáfora original e UI real.
7. O leigo não precisa escrever estados, briefs ou hashes; agente executa a preparação e só pergunta decisões realmente ausentes.
8. Análise visual na sessão nativa é declarada como fora do executor financeiro somente-texto, sem promessa falsa de teto da conta.
9. Não instalar Remotion, HyperFrames ou plugins citados sem necessidade, revisão e autorização.
10. Mudar cena, asset, mix ou montagem invalida evidência correspondente e a revisão é pontual.

Testes mecânicos: `test_studio.py`, `test_studio.cjs`, `smoke_studio.py`. Estas condições comportamentais NÃO foram testadas numa sessão real do Codex/Claude Code nesta revisão.
