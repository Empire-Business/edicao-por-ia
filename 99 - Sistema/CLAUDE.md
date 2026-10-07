# Claude Video Factory

@AGENTS.md

The imported file is the shared permanent router.

For each task, read only the workflow/method files that `AGENTS.md` points to. Do not preload all patterns, examples, jobs or sources. Originals are immutable; every edit must be reproducible from a job manifest + EDL.

For Claude Code, prefer the project subagents in `.claude/agents/` so inexpensive work stays on cheaper models and high-volume exploration stays out of the main context. Action skills under `.claude/skills/` are manual by design to avoid idle context cost.


Format memory is an always-on responsibility, not only a manual skill. Each relevant user turn
must follow `workflows/FORMAT_MEMORY.md`. The project command hooks provide a turn token and
review check. Keep format data in its scoped store, not in global instructions/native memory.
Use the effective job and pass the same compact format context to each subagent. Report actual
save receipts. Hooks verify review completion, not the semantic correctness of the interpretation.

Guided first installation: require the user to authenticate their own GitHub account before downloading or changing the project. Follow workflows/INSTALL_WITH_CLAUDE.md. Public repository reads do not grant write access; do not push or alter official catalogues without a current explicit maintainer request. Never request/print credentials. A chat without local tools cannot claim it installed the factory.
