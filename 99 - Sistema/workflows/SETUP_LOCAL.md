**v1.6:** A entrada principal agora é `workflows/ASSISTED_START.md`; use o instalador com prévia/backup, não apenas recomendações. O conteúdo abaixo continua como referência técnica de ambiente.

# Workflow — Setup Local

## Objective
Prepare a local editing environment without silently installing anything.

## Required check
Run:
```bash
python3 tools/doctor.py
```

## Suggested macOS installation
Only if the user chooses to install missing dependencies:
```bash
brew install ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-optional.txt
```

On Apple Silicon, `mlx-whisper` can be installed separately and is preferred by `tools/transcribe.py` when available.

## Windows/Linux
Install FFmpeg/FFprobe using the platform's package manager. Python virtual environment usage is the same conceptually.

## Model download note
Local Whisper backends may download model weights on first use. After models are cached, the transcription stage can run locally without sending media to Anthropic.

## Checks
- `ffmpeg` found;
- `ffprobe` found;
- Python supported;
- at least one optional transcription backend found if speech editing is required;
- enough free disk for proxies/renders.

## Optional motion (v1.3)
Run `python3 tools/doctor_motion.py`. Follow `motion/README.md` for the lightweight JS browser route; `motion/remotion/README.md` for advanced React scenes. No installs without permission. Copy the user's existing format/job folders separately when upgrading; do not overwrite them with template contexts.


## Memory activation and migration (v1.4)
Read `MEMORIA-COMO-USAR.md`. New folder has project hooks; existing config must be merged,
not overwritten. `tools/install_memory_hooks.py` previews; `--apply` requires user authorization.
No new package dependency for the memory store. Test one simulated save/recall separately from
real format data, then remove the fixture. A live-host test is distinct from our unit tests.
Never replace a user's format stores/jobs/patterns with templates during a skill update.
