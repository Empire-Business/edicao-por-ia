# Claude Video Factory

## v1.4 — proactive client memory
Start with `MEMORIA-COMO-USAR.md`. Save/retrieve real client facts and feedback through
`workflows/CLIENT_MEMORY.md`; don't wait for a special remember command. Client stores are
isolated; new jobs inherit supported preferences while current job overrides remain stronger.
New folders include Claude Code command hooks. Existing installations must merge settings and
preserve clients/jobs/patterns. No user database is included in this generic ZIP.


Portable local skill for building a repeatable AI-assisted video editing workflow around Claude Code, Codex or similar agents.

The key idea is simple: Claude is the **editorial brain**, not the media codec. Media mechanics stay local with FFmpeg/FFprobe and local speech-to-text. The model sees compact representations: metadata, transcripts, candidate cuts, selected frames and QA summaries.

## Atualização 1.1 — roteiro de referência e silêncios

- Aceita roteiro opcional como referência de sentido, sem exigir fala idêntica.
- Orienta a comparação semântica, escolha de tomadas reais, registro de erros e identificação de partes não gravadas.
- Cria cortes automáticos de tempo morto a partir da detecção de silêncio, protegendo fala e pausas marcadas; a mesma EDL controla áudio e vídeo.
- Inclui ferramentas locais testáveis e mantém os padrões v1. Novos starters v2 tornam a política de silêncio explícita.
- Comparação semântica é feita pelo agente usando o workflow; o utilitário de busca local não entende a fala nem decide sozinho qual tomada está correta.

Leia `REVISION_REPORT.md` para o que faltava, o que foi alterado, testes e limitações. Comece por `START-HERE.md`.

## What it does

- Creates named/versioned video patterns so you can say “use `reels-dynamic-v1`”.
- Detects likely speech mistakes, false starts and retakes from timestamped transcripts.
- Handles one source file containing multiple independent videos.
- Handles batches of many videos without mixing their context.
- Produces a non-destructive edit decision list (EDL) before rendering.
- Routes cheap work to Haiku, normal editorial work to Sonnet and only escalates hard judgment to Opus 5.5.
- Reuses local caches and avoids sending full media into model context.
- Supports FFmpeg-first rendering and an optional hybrid/Remotion path for elaborate motion graphics.
- Includes structural verification and deterministic media QA tools.

## Minimum runtime

Required:
- Python 3.10+
- FFmpeg + FFprobe

Recommended transcription backend:
- Apple Silicon: `mlx-whisper`
- Cross-platform/CUDA/CPU: `faster-whisper`

Optional precision alignment:
- WhisperX

Optional complex motion-graphics layer:
- Node.js + Remotion (not required for clean cuts, reframing, audio, subtitles or simple overlays)

## First run

1. Read `START-HERE.md`.
2. Run `python3 tools/doctor.py`.
3. Create a job with `python3 tools/make_job.py --source /path/video.mp4 --pattern talking-head-clean-v2`.
4. Transcribe/probe according to `workflows/EDIT_VIDEO.md`.
5. In Claude Code, invoke `/video-factory <job-id>` or simply ask the agent to edit the job using a named pattern.

## Safety

No source file is modified in place. Rendering always writes to a new output path. Installation commands in the docs are suggestions for the user to run; the skill does not auto-install software.

## Supporting insertion assets (v1.2)
You may provide images and/or videos to be used as supporting inserts. The factory can interpret them as B-roll, proof, demos, cutaways, overlays, or end-cards and place them at semantically appropriate moments. Prefer adding notes or cue phrases when possible, but they are optional.

## v1.3 — Animações em JavaScript
Agora há um fluxo específico para criar animações por código e encaixá-las na gravação: `workflows/CREATE_JS_ANIMATIONS.md`. Inclui quatro componentes JS, render local para frames transparentes, composição com voz preservada, regras de economia e um adapter opcional React/Remotion. Consulte `motion/README.md`.

Pedido de exemplo: “Edite com o padrão aprovado, corte os erros e silêncios e use animações JavaScript discretas nos trechos que precisam de explicação. Use meus prints sem alterar dados. Reutilize os componentes existentes; use Opus para criar uma animação nova só quando necessário.”

As animações entram depois dos cortes, para não perder o sincronismo com a fala. Nenhum padrão anterior foi renomeado ou alterado nesta revisão. Extraia a atualização em outra pasta e migre os seus jobs/contextos sem sobrescrevê-los.


## v1.5 — Direção visual a partir da fala e do cenário
Peça: “Ative a direção visual: interprete minhas falas, crie visuais úteis e use o espaço do
cenário sem cobrir rosto, mãos importantes ou legendas.” `DIRECAO-VISUAL-COMO-USAR.md` explica
os limites sem configuração manual. O novo fluxo examina sentido e frames reais, produz
storyboard/briefs e exporta specs para os quatro componentes JS existentes. Geração neural,
máscaras, tracking e VFX avançado dependem de ferramentas adicionais. Não há garantia estética.
