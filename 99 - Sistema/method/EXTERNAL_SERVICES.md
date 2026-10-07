# External services — what we learned (2026-10-01)

## Simple local configuration
The user opens **CHAVES DAS INTEGRAÇÕES.txt** in the visible project root, pastes each key
following `SCRAPECREATORS_API_KEY=` / `ELEVENLABS_API_KEY=` and saves. No terminal, hidden files
or shell sourcing. Setup creates this empty file only if absent, never overwrites an existing
file. It is private, ignored by Git and must not be included when sharing the factory.
`tools/service_keys.py` loads credentials only when executing an authorized service operation:
visible file first, then environment, legacy root/engine `.env`, then the old ScrapeCreators local
JSON. It parses assignments as text, never executes them. Do not inspect real secret files during
setup/review, print keys, copy them to chat/memory/jobs, or place them in subprocess arguments.
Tests use fake credentials. The user need not migrate old keys for existing operations to work.

The factory is generic. Require a registered format identified by the user before editing;
Bruno and historical test colors are never global defaults. These services consume credits;
record authorized use in the job decision log. A request to use TikTok/YouTube scenes authorizes
ScrapeCreators research and retrieval for that job; accept it without asking for duplicate consent.

## ElevenLabs — Audio Isolation (noisy camera voice)
- MANDATORY (user rule, 2026-10-02: "isso tem q ser uma regra inviolavel em todos os videos"): every video's voice goes
  through Audio Isolation before the first preview, for every format/job. Standing authorization for this endpoint only;
  music depends on the format/job; a TikTok/YouTube scene request authorizes ScrapeCreators.
- Tool: `python3 tools/el_isolate_voice.py jobs/<id> --base-video renders/X.mp4 --out renders/Y.mp4`
- ORDER MATTERS. Isolate the FULL source audio (mono, peak-normalized to −2 dBFS) and only then
  apply the EDL cuts. Isolating the already-cut, quiet, stereo voice removed only 3–6 dB of noise
  and the user rejected it; the right order removed ~15 dB between words and was approved.
- Endpoint: `POST /v1/audio-isolation`, multipart field `audio`. Returns mp3 44.1 kHz mono. Only audio is uploaded.
- After isolation keep the plain voice chain: HPF 70 Hz + gain to ≈ −16.7 LUFS + peak limiter.
- Evidence to report: noise in the source's real pauses before/after, sync offset, loudness; a
  spectrogram pair (`showspectrumpic`) shows whether gaps between words went black.
- The current key cannot read the account (no `user_read`), so credit balance is unknown.

## ElevenLabs — Music (original, royalty-free beds)
- Endpoint: `POST /v1/music?output_format=mp3_44100_192`, JSON `{prompt, music_length_ms, model_id:"music_v1", force_instrumental:true}`.
- Describe instruments, mood, tempo and structure; do NOT name artists or songs in the prompt
  (a reference the user gives is translated into a description).
- Ask for ~10 s more than the longest video; the track brings its own ending.
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
- `composition_plan` with per-section durations did not work for this: durations were not respected and the
  dynamics stayed flat. Generate separate acts with plain prompts and edit them instead.
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
