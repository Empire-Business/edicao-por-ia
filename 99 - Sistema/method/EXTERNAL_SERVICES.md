# External services — what we learned (2026-10-01, revised 2026-11-09)

## Simple local configuration
The user opens **CHAVES DAS INTEGRAÇÕES.txt** in the visible project root, pastes each key
following `OPENROUTER_API_KEY=` / `ELEVENLABS_API_KEY=` / `SCRAPECREATORS_API_KEY=` / `APIFY_API_TOKEN=` and saves. No terminal, hidden files
or shell sourcing. Lay guides: `03 - Ajuda/COMO CONFIGURAR O OPENROUTER.html` (recommended: AI music,
narration and covers) and `03 - Ajuda/COMO CONFIGURAR O ELEVENLABS.html` (optional, noise only). Teach one
step at a time (see the didactics rule in AGENTS.md); never ask for a key in the chat. Setup creates this empty file only if absent, never overwrites an existing
file. It is private, ignored by Git and must not be included when sharing the factory.
`tools/service_keys.py` loads credentials only when executing an authorized service operation:
visible file first, then environment, legacy root/engine `.env`, then the old ScrapeCreators local
JSON. It parses assignments as text, never executes them. Do not inspect real secret files during
setup/review, print keys, copy them to chat/memory/jobs, or place them in subprocess arguments.
Tests use fake credentials. The user need not migrate old keys for existing operations to work.
A keys file created before a service existed lacks its line: the user adds `OPENROUTER_API_KEY=`
at the end and saves; setup never rewrites an existing file. Since 2.11.0 the update migration
(`post_update.py` → `service_keys.annotate_services`) appends, once, plain-language notes about the
current service map and an empty `OPENROUTER_API_KEY=` line when that name is absent. Append-only:
existing bytes/values/permissions are kept and nothing about the values is returned or logged.

The factory is generic. Require a registered format identified by the user before editing;
Bruno and historical test colors are never global defaults. These services consume credits;
record authorized use in the job decision log. A request to use TikTok/YouTube scenes authorizes
ScrapeCreators research and retrieval for that job; accept it without asking for duplicate consent.

## Áudio: limpeza local; música e narração pelo OpenRouter (ordens do autor, 22/10 e 09/11/2026)

22/10/2026: limpar a fala continua parte da edição e a rota padrão é local. 09/11/2026: **música com IA
e narração passam para o OpenRouter** (música: Google Lyria 3; narração: TTS do OpenRouter, provedor
padrão). **O ElevenLabs fica só para tratar ruído** (Voice Isolator opcional e pago); não gera mais música
nem narração. ELEVENLABS_API_KEY e APIFY_API_TOKEN são opcionais e podem ficar vazios. Toda chamada paga
exige o sim atual da pessoa, com o custo estimado mostrado antes (`--accept-paid`); ter a chave não
autoriza gasto. Não alternar para nuvem em uma falha local. Se o OpenRouter falhar, a alternativa
oferecida é a biblioteca local de trilhas (música) ou a voz local (narração), nunca o ElevenLabs.

### Limpeza da voz
- `tools/audio_local.py INPUT --out OUTPUT.wav` trata uma fonte inteira. Auto usa o executável
  DeepFilterNet se preparado; caso contrário usa FFmpeg básico e identifica essa limitação no recibo.
- `tools/el_isolate_voice.py JOB --base-video renders/X.mp4 --out renders/Y.mp4` preserva o fluxo
  existente: fonte inteira → limpeza local → cortes da EDL → loudness/limiter → vídeo novo.
  `--provider deepfilter` exige esse runtime; `--provider ffmpeg` seleciona a alternativa básica.
- `tools/prepare_local_audio.py` mostra a preparação; `--apply` só após autorização de instalação.
  Runtime oficial v0.5.6, hash fixado em `config/audio-runtimes.json`; por enquanto o download revisado
  cobre Mac Apple Silicon. Outros sistemas usam FFmpeg ou um deep-filter oficial previamente preparado.
  Nenhuma instalação altera Gatekeeper, assinatura, permissões globais ou o Python existente.
- O cache considera hash da fonte, provedor e runtime. Não reutilizar limpeza paga antiga como evidência
  de execução local. Originais e versões anteriores não são sobrescritos.
- DeepFilterNet recebe padding e compensação de atraso; a saída volta à duração original. FFmpeg reduz
  ruído básico; não prometer que remove eco ou que equivale ao ElevenLabs. Medir pausas, conferir sincronismo
  e ouvir antes de aprovar. Os recibos `.audio.json` mantêm a avaliação auditiva pendente.
- ElevenLabs (só ruído) permanece disponível somente com `--provider elevenlabs --accept-paid`, após o sim atual
  para aquele áudio. Apenas áudio é enviado, sem retries automáticos. A autorização permanente anterior
  de isolamento pago foi substituída. O alinhamento do resultado pago ainda exige conferência.

### Narração (OpenRouter por padrão) e alinhamento
- Padrão: `tools/narrate.py speak --text-file F --out X.wav --accept-paid` usa o TTS do OpenRouter
  (`POST https://openrouter.ai/api/v1/audio/speech`, JSON `{model, input, voice, instructions?, response_format, speed?}`).
  A resposta é o áudio cru (não JSON), com `Content-Type` (ex.: `audio/pcm;rate=24000;channels=1`) e `X-Generation-Id`.
- Modelo padrão verificado em 09/11/2026: `google/gemini-3.8-flash-tts`, voz `Kore`, `instructions` em português
  ("Fale em português do Brasil, tom natural, claro e próximo."; trocar com `--instructions`). O Gemini só devolve
  `pcm` (24 kHz, 16 bits, mono): a ferramenta converte com FFmpeg (`-f s16le -ar 24000 -ac 1`). Uma frase de
  46 caracteres virou 3,16 s de fala. Preço: frações de centavo (por token, na lista de modelos); a resposta não
  traz o custo, então o recibo grava `generation_id` para conferir em https://openrouter.ai/activity.
- Outros modelos com `--model` (ex.: `fish-audio/s2.1-pro`, `microsoft/mai-voice-2.1`,
  `elevenlabs/eleven-multilingual-v2`; este exige `--voice` explícita, senão HTTP 400). Modelos fora do Google
  recebem `response_format: mp3`. O id `openai/gpt-4o-mini-tts-2025-12-15` não existe (400).
- Sem `--accept-paid` a ferramenta para antes de ler a chave e mostra o custo estimado. Sem repetição
  automática. 401 = chave recusada; 402 = sem créditos; 429/5xx = instável.
- Saída e recibo como nos demais provedores: não sobrescreve, `.audio.json` com provider, model, voice,
  instructions, generation_id, `paid_request: true`, `alignment: pending_local_transcription`,
  `quality_review: pending_listening`. O TTS do OpenRouter não dá tempos de palavras: usar `align` (abaixo).
- `--provider elevenlabs` deixou de ser aceito (mensagem aponta para `openrouter`). `el_tts.py` é só uma ponte
  para `narrate.py`.

Vozes locais (sem custo, alternativa explícita):
- `tools/narrate.py voices --provider cortez-voz` consulta Cortez Voz local em `http://127.0.0.1:3930`.
  `speak --provider cortez-voz --voice ID --model ENGINE --text-file F --out X.wav` usa um engine local escolhido explicitamente.
- Cortez Voz é a cópia AGPL controlada em `Empire-Business/cortez-voz`, derivada de VoiceStudio.
  O setup aplicado inclui sua instalação a partir de commit e SHA-256 fixos em `config/cortez-voice.json`.
  Não seguir main/latest do autor original; não remover quarentena, refazer assinatura ou instalar globalmente.
  Ferramentas e dependências ficam isoladas. Prévia informa os downloads; a preparação pode consumir vários GB.
- O setup não inicia banco, migrations, servidor ou modelos. Primeiro início requer pedido explícito de
  inicialização do banco local no ambiente/diretório escolhido. `tools/prepare_cortez_voice.py --start
  --initialize-data` direciona somente `.factory/cortez-voz-data`. Não executar isso como validação automática.
- Mac Apple Silicon, Windows x64 e Linux x64/glibc possuem caminho de instalação. Somente as plataformas
  com recibo real podem ser declaradas testadas. Mac Intel/ARM Windows/Linux permanecem pendentes.
- Sem Cortez Voz preparado e aberto, informar a pendência. No Mac pode-se escolher
  explicitamente `--provider macos --voice NOME` entre as vozes instaladas listadas por `voices --provider macos`.
  São vozes de sistema: não prometer clonagem ou naturalidade equivalente. Sem downloads automáticos de vozes.
- A API local só aceita loopback literal; proxies e redirects ficam bloqueados. O provedor `cortez-voz` verifica a identidade
  Empire-Business/cortez-voz. O provedor legado `voicestudio` requer URL explícita da instalação externa.
  Aliases como `tts-1` e `omnivoice` não são aceitos porque podem escolher outro backend ativo.
- Esta edição do aplicativo inclui engines OmniVoice, MLX Audio e KittenTTS; engines extras não são instalados
  pelo app. Os pesos exigem escolha e revisão de licença próprias; não presumir uso comercial dos pesos OmniVoice.
- Voz clonada exige pedido explícito para a pessoa. Conferir licença do engine/pesos e autorização da voz.

Alinhamento (qualquer provedor):
- Após gerar, usar `tools/narrate.py align AUDIO --backend mlx --model MODELO_LOCAL`
  (ou backend faster) para transcrever com pesos já em cache, em modo offline. Gera `.words.json` e
  `.alignment.json` com hash do áudio, tempos reais e origem. Não distribui tempos pelo roteiro.
  O recibo da geração registra a pendência original; o recibo de alinhamento comprova sua conclusão.
  Se o modelo não estiver preparado, informar a falta; não baixar pesos nem usar nuvem automaticamente.

### Música: biblioteca local e geração pelo OpenRouter
- `tools/music_library.py list` lista as trilhas privadas. `add SOURCE --id ID --title TITULO
  --license ORIGEM_OU_LICENCA --rights-confirmed` importa uma cópia de material já dentro da fábrica.
  Só confirmar direitos com declaração real do usuário; não inventar licença nem importar trilhas de outro cliente.
- Biblioteca em `context/audio-library/`, fora da distribuição de código. Cada faixa guarda origem/licença
  e hash. `prepare --track ID --seconds N --out X.wav` prepara duração, volume e fade sem pagar API.
- Biblioteca vazia: pedir uma faixa autorizada ou uma geração paga específica. Não instalar músicas,
  escolher mídia privada histórica ou fabricar uma licença. Reutilizar somente quando combinar com o trecho.
- Mistura por `mix_voice_music.py` / `score_two_act.py` continua com ducking e variação por capítulo/virada.
- Música com IA: `tools/or_music.py --prompt "..." --seconds N --out X.mp3 --accept-paid`, somente com o sim
  atual para aquela geração. A preferência de um formato por música não autoriza gerar música paga.
  `tools/el_music.py` foi aposentado: só mostra o aviso com o comando novo e sai com erro, sem chamar nada.
- `tools/or_music.py --check-key` confere a chave sem gerar nada (`GET /api/v1/key`) e mostra só limite/uso,
  nunca a chave nem o rótulo dela. Endpoint documentado pela OpenRouter, ainda não verificado com chamada real
  no Cortez: se responder algo inesperado, explicar e não insistir.

## Composição quando uma geração paga for escolhida (OpenRouter, Google Lyria 3, verificado 09/11/2026)
- `POST https://openrouter.ai/api/v1/chat/completions`, `Authorization: Bearer <OPENROUTER_API_KEY>`, JSON
  `{model, stream: true, modalities: ["text","audio"], audio: {format: "mp3"}, messages: [{role: "user", content: PROMPT}]}`.
  Resposta em SSE (`data: {...}` por linha, fim em `data: [DONE]`); o áudio vem em base64, em pedaços, em
  `choices[0].delta.audio.data` (juntar e decodificar); `delta.content` traz texto curto (ex.: `<instrumental>`);
  o último evento traz `usage.cost` (US$), gravado no recibo como custo real.
- `google/lyria-3-clip-preview`: trecho de ~30 s (veio 30,77 s), MP3 44,1 kHz estéreo, US$ 0,04, ~9 s.
  `google/lyria-3-pro-preview`: música completa, US$ 0,08, ~30 s. A ferramenta escolhe clip até 30 s e pro acima;
  limite 3 a 240 s (mais que isso: gerar partes e juntar na mixagem).
- **A duração NÃO é respeitada** (pedido "60 s" → 75,8 s). A ferramenta pede a duração no texto e depois corta
  com FFmpeg no tamanho pedido com fade-out (padrão 2 s; `--fade`). Se vier mais curta, avisa e NÃO estica
  (`shorter_than_requested` no recibo). Se o corte local falhar depois da cobrança, o original fica salvo como
  `<nome>-sem-corte.mp3`.
- Instrumental: a ferramenta acrescenta "Instrumental only, no vocals." ao prompt.
- Describe instruments, mood, tempo (BPM) and structure; do NOT name artists or songs in the prompt
  (a reference the user gives is translated into a description).
- Erros: 402 = sem créditos; 401 = chave errada; 429/5xx = serviço instável (o endpoint do Lyria Pro estava com
  ~42% de disponibilidade em 09/11/2026). Nenhuma repetição automática que gaste duas vezes; mensagem clara e
  sugestão da biblioteca local. Nunca trocar para ElevenLabs.
- Recibo `.audio.json`: provider `openrouter`, model, `cost_usd` (do `usage.cost`), custo estimado, generation_id,
  prompt, duração pedida/bruta/final, corte e fade, sha256, `quality_review: pending_listening`.
- Mix: `python3 tools/mix_voice_music.py jobs/<id> --voice … --music … --base-video … --out … --music-db -6`
  → bed ≈ 11 LU under the voice with sidechain ducking, 2.5 s fade-out, picture stream-copied.
  `--music-db -11` gives a discreet bed (≈ 16 LU under).
- A single generic track laid under the whole video was REJECTED ("não combina com os vídeos"). Fit the music to the
  speech: `tools/score_two_act.py` — act 1 (tension) until the turn where the solution is presented, act 2
  (resolution) from the turn, act-1 drop on the end of the hook, act-2 real ending on the last frame. Read the
  retimed transcript to pick `--turn` and `--drop-at`.
- Ducking: a plain sidechain follows the voice LEVEL, so softly spoken words barely duck and the music covers them
  (user: "tem horas que a música fica alta demais"). `score_two_act.py` boosts+limits the sidechain so any speech ducks
  equally, compresses music peaks and dips 2.5 kHz. Check the reported `music_minus_voice_db` (aim median ≈ −16, worst ≤ −5).
- Per-section durations inside one prompt are not reliable: generate separate acts with plain prompts and edit them.
- Measure what the model returned (real end, where the bass enters) before editing; requested length ≠ real length.
- Generated tracks are stored per format: `context/clients/<format>/assets/music/`. The historical
  `clients` folder name remains for compatibility.
- Whether a format wants music at all is a FORMAT/JOB preference — check memory first.

## ScrapeCreators — requested TikTok/YouTube scenes
- Whenever the user requests scenes from TikTok and/or YouTube, accept and operate exclusively
  through ScrapeCreators. Search/metadata/media URL resolution use its API; download only explicit
  media URLs returned by it (CDN transport is part of that retrieval). No yt-dlp, browser scraping,
  other extractor/provider or silent substitution. The request is the authorization; do not ask again.
- Tool: `python3 tools/broll_research.py search|get|sheet jobs/<id> …`. A format must be set first.
  `search` saves responses in `assets/viral/search/`; `get` accepts ID=name or URL=name, logs
  provider/source/author/status in `assets/viral/sources.json`; `sheet` provides frames for inspection.
- API client: `tools/scrapecreators.py`, keys loaded through `tools/service_keys.py`.
  Endpoints: `/v1/tiktok/search/keyword`, `/v2/tiktok/video`, `/v1/youtube/search`, `/v1/youtube/video`.
  Costs vary by endpoint; consult the current documentation rather than claiming every call is 1 credit.
- Downloads are staged and verified with ffprobe before becoming an asset. HTTP error pages are
  never successful videos. Expired cached TikTok URLs can be refreshed once through the same API.
- Missing key: direct the user to the visible file. Invalid key, exhausted credits, restricted media
  or unavailable API: report the precise blocker, retain progress and sources, and resume when resolved.
- YouTube metadata is not a guarantee of downloadable media. Official schema checked 2026-10-06:
  [ScrapeCreators OpenAPI](https://docs.scrapecreators.com/openapi.json), `/v1/youtube/video`, returns
  video details/caption tracks; its current example has no `downloadOptions`. If an API response does
  expose explicit video formats, the tool uses them. Otherwise record `media_unavailable` and research
  alternative candidates through ScrapeCreators within the authorized budget. Do not fabricate a
  download endpoint, claim the scene was obtained or switch providers to force success.
- Pick clips by what they show at the retained spoken moment. Inspect real frames, burned-in
  captions/watermarks, quality, crop and sync; then follow `method/INSERTION_ASSETS_POLICY.md`.
  Preserve source/author; third-party rights are not transferred by the API.
- Historical all-format B-roll research instructions do not make Bruno's assets, colors or identity
  defaults. Use only the selected format/job's actual requirements and authorized budget.

## OpenRouter — outfit/scenery swap (generative video edit, validated 2026-10-12)
- What it is: a video-edit model redraws a short range of ONE take with another outfit and/or
  another scenery, keeping the person's motion. Available in any format. Flow, consent and QA:
  `workflows/SWAP_OUTFIT_SCENERY.md`. Tool: `tools/gen_video_edit.py` (`models`, `run`, `patch`).
- The assistant does not produce these pixels; the video model does. Report the model used.
- NO standing authorization. Each clip needs the user's yes for (a) the spend and (b) how the range
  reaches the provider. The API takes the input only as a public HTTPS link: a `data:` URL returns
  400 “Only HTTPS URLs are allowed”, and OpenRouter's Files endpoint does not accept video. So either
  the user hosts the range (`--source-url`) or agrees to a temporary public link (`--temp-public-link`,
  Litterbox, 1 hour). Never pick the public link silently.
- API: `POST https://openrouter.ai/api/v1/videos` with `{model, prompt, input_references:[{type:
  "video_url", video_url:{url}}]}` → 202 with `id` and `polling_url`; poll until `completed`;
  download from `unsigned_urls[0]` or `/videos/<id>/content?index=0`. `usage.cost` is the real charge.
  Live models and prices need no key: `GET /api/v1/videos/models` (`pricing_skus`); which ones take a
  video as input: `GET /api/v1/models?output_modalities=video` (`architecture.input_modalities`).
- Default model `black-forest-labs/flux-video-edit`: US$ 0.03 per output second (5 s = US$ 0.15,
  charged exactly that in three runs). Sent 720×1280 at 30 fps; it returned 704×1248 at 24 fps, about
  40 ms longer. The tool conforms the result to the recording's size, frame rate and duration and
  keeps the ORIGINAL audio; never use the model's audio track.
- Observed quality on a vertical talking head with hands and a handheld microphone: outfit and
  scenery stayed stable for 5 s, hands and ring preserved, no background bleeding into the gestures.
  The face is slightly redrawn (smoother skin, small tone shift) and more so when outfit and scenery
  change together. A night scenery kept the daylight on the person: ask for a scenery that matches
  the recording's light.
- Listed but NOT tested here: `runway/aleph-2` (US$ 0.28/s, minimum US$ 0.56 per generation) and the
  ByteDance Seedance models (priced by volume, unknown before running; minimum 4 s). The tool blocks
  volume-priced models unless `--accept-unknown-cost` is passed after the user agrees.
- Missing key → point to the visible keys file. 401 invalid key, 402 no credits, a failed/expired
  job or an invalid download are reported as concrete blockers; no other provider is tried.

## Apify — YouTube download when ScrapeCreators has no file (author order, 2026-10-13)
- ScrapeCreators `/v1/youtube/video` often returns metadata, chapters, captions and `most_replayed` but
  `downloadOptions.formats: []`. Then, and only then, use `tools/apify_youtube.py URL OUT.mp4`
  (actor `streamers/youtube-video-downloader`, `storeInKVStore: true`, `preferredQuality: 1080p`).
- Long videos exceed the 300 s synchronous endpoint (HTTP 408). The tool starts the run, polls it and
  reads the dataset; after an interruption resume with `--run-id` so the same download is not paid twice.
- The file is the dataset's `downloadedFileUrl` (KV store, deleted after ~3 days); HLS manifest URLs are not files.
  The result must match the requested video id and pass ffprobe with video before becoming a source.
- Measured 2026-10-13: 12:36 video at 1920×1080 with audio, about 4 min, US$ 1.03. Record run id and cost.
- Transcript without paying Apify: ScrapeCreators `/v1/youtube/video/transcript?url=…&language=pt`.

## OpenRouter — cover/thumbnail options (F18, 2026-10-13)
- `tools/gen_thumbnails.py models` lists the live `openai/gpt-image*` models; `run JOB --brief …` uses the
  newest non-mini one by default ("sempre o mais recente"), 16:9, with job-local reference images
  (real presenter frames + author cover references). Receipt in `thumbs/receipt.json` with model and cost.
- Each option is one paid call; the F18 request authorizes the 3 covers of that job. The author may instead
  generate them in his own Codex/ChatGPT; record which path was used. Not yet run in a real job.

## Vimeo — referências públicas do Cortez

Por solicitação atual do autor, `tools/vimeo_publish.py` envia somente as referências públicas selecionadas em `web/modelos-edicao/publication.json` para a pasta **Cortez** da conta autenticada. `VIMEO_ACCESS_TOKEN` é privado; também é aceito em `.factory/secrets/vimeo-access-token`, com acesso local restrito. Nunca incluir chave, client secret, link TUS ou recibo privado em Git, logs, painel ou prompts. Não se precisa do client secret para usar o token autenticado.

Prévia não lê credenciais nem envia arquivos. Upload exige pedido explícito do autor e checagem da cota disponível; não contratar plano. O recibo permite retomar blocos e conciliar um upload antes de repetir. O painel recebe somente o ID e o hash de exibição de vídeos já processados. As instalações dos usuários não recebem a chave do autor: a edição usa o cache local verificado do GitHub, conforme `workflows/CACHE_FORMAT_REFERENCES.md`. Não carregar mídia privada de trabalhos nem reorganizar vídeos alheios à seleção Cortez.
