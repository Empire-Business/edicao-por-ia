# Research snapshot — 2026-09-25

This package was designed from current documentation available on 2026-09-25. Re-check model names/pricing before future financial decisions.

## Anthropic / Claude
- Claude Opus 5.5 overview: https://platform.claude.com/docs/en/models/opus-5-5/overview
- Claude Opus page / release: https://www.anthropic.com/claude/opus
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code feature/context overview: https://code.claude.com/docs/en/features-overview
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Thinking/cost steering: https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost
- Batch processing: https://platform.claude.com/docs/en/build-with-claude/batch-processing

Key finding: Opus 5.5 accepts text/images and returns text; a practical video workflow therefore uses local media tools and passes compact text/image evidence to the model rather than treating the model as a native video codec/editor.

## Local media / speech tools
- FFmpeg filters: https://ffmpeg.org/ffmpeg-filters.html
- FFprobe: https://ffmpeg.org/ffprobe-all.html
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Apple MLX Whisper: https://github.com/ml-explore/mlx-examples/tree/main/whisper
- WhisperX: https://github.com/m-bain/whisperX

Key findings:
- FFmpeg exposes silence detection/removal and trim/concat primitives.
- FFprobe can emit machine-readable JSON stream/format metadata.
- faster-whisper supports word timestamps and VAD.
- MLX Whisper supports word timestamps and is a useful Apple Silicon option.
- WhisperX adds forced alignment and diarization when higher timestamp precision is needed, at the cost of a heavier stack.
