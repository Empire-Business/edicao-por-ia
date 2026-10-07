**v1.6:** Economia operacional e teto financeiro são distintos. Consulte `method/EXECUTION_AND_COSTS.md`; trabalho local não torna gratuita a conversa principal.

# Token Economy

## Highest-impact rule
Never represent a video to the LLM as “all frames + full raw transcript + all logs”. Build compact, reusable evidence locally.

## Progressive disclosure
Always load:
- one job manifest;
- one active pattern;
- one relevant workflow;
- quality rules.

Load on demand:
- transcript windows around candidates;
- selected frames;
- format/brand context actually needed;
- prior decisions relevant to the same pattern/job.

Never load by default:
- all jobs;
- all formats;
- all patterns;
- all memory;
- all source research.

## Reuse by hash
Cache by:
- SHA-256 of source file;
- transcription backend + model + language + VAD settings;
- frame extraction settings;
- pattern version for pattern-dependent analysis.

Changing only export bitrate must not trigger transcription or editorial analysis again.

## Chunking
For long speech transcripts:
- target ~5–10 minute chunks;
- overlap ~8 seconds so restarts at boundaries are visible;
- run cheap screening per chunk;
- persist compact results to `analysis/chunks/`;
- send only flagged windows to Sonnet/Opus.

## Visual sampling
Default contact sheet: one frame every ~20 seconds plus scene/cut candidates. Extract denser frames only around:
- speech cuts;
- reframing questions;
- visual mistakes;
- suspected video boundaries.

## Claude Code context savings
- Action skills use `disable-model-invocation: true`, so they do not occupy context before manual invocation.
- Use subagents for transcript screening and large exploration; only their summaries return to the main context.
- Keep `AGENTS.md` and `CLAUDE.md` short and permanent.

## API-specific savings
If building an API orchestrator instead of interactive Claude Code:
- keep stable prompt prefixes to benefit from prompt caching;
- do not change effort level every turn just to save a few tokens, because configuration changes can invalidate cache prefixes;
- consider Message Batches for non-urgent large-scale analysis; Anthropic documents a 50% batch discount;
- avoid Opus fast mode unless latency is worth the premium.

## No-model alternatives first
Before calling any Claude model, ask:
1. Can FFmpeg/ffprobe answer this?
2. Can the local transcript answer this?
3. Can a small deterministic script answer this?
4. Can Haiku answer it safely?
5. Only then: Sonnet or Opus.

## Script / silence additions
- Hash and normalize only the active reference. Local candidate retrieval is a cheap index, not a semantic judge.
- Send the reference outline and relevant transcript windows to Sonnet; expand only ambiguous matches. A lexical low score is never enough to delete speech.
- Include reference hash/mode, active child scope, silence settings, transcript hash and protected-range hash in relevant cache keys.
- A script revision invalidates its alignment and dependent cuts, not unchanged ASR/probe evidence.
- Silence detection, range arithmetic and synchronized rendering are local tools with no LLM calls. Models only decide intentional pauses and semantic ambiguities.

## Motion economics (v1.3)
- Reuse reviewed JS components + small JSON props. Never resend all reference videos or generate code per frame.
- Cache within the active format/project by component hash, props hash, local asset/font hashes, dimensions, fps, duration, renderer/browser version. Do not share private assets across formats.
- Check a few keyframes, then a short preview; send only changed props, frame evidence and concise defects for fixes.
- Default to at most two new-design refinement rounds before reporting unresolved issues. A user-approved budget can change that. Do not lower quality silently to satisfy a token target.
- A caption-color change does not invalidate speech transcription. A changed EDL invalidates animation placement, not unchanged component code. Render reuse is a local operation, not an Opus invocation.
- Rendering uses CPU/GPU/disk, even when it consumes no LLM tokens. Avoid rendering every frame of an hour-long video when only a two-second overlay changes; re-render the affected layer and re-composite as needed.


## Memory budget (v1.4)
No model call for SQLite writes, idempotency, receipts, lookup or settings merge. The current
coordinator extracts 1..40 small records from useful user feedback; usually far fewer.
Do not spawn Opus just to save facts. Haiku may propose a schema on a large batch only when worth
it; the coordinator validates scope/meaning. Format context defaults to 7500 characters, with
explicit omitted IDs. Retrieve missing relevant constraints, never silently truncate them.
No full transcript/format-library reread per turn, and no embeddings service is required.
