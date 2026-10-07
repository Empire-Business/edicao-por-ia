# Primary-source notes — consulted for v1.4 (2026-09-25 conversation date)

## Anthropic: how Claude remembers a project
https://code.claude.com/docs/en/memory
Official documentation distinguishes authored instructions from auto memory. Both are contextual,
not guaranteed enforcement. Native auto memory is local and repository-scoped; that is not enough
by itself to isolate several video clients in one factory or make a portable generic ZIP carry
personal data. v1.4 uses an explicit per-client local store instead; it does not disable native memory.

## Anthropic: hooks reference
https://code.claude.com/docs/en/hooks
Command handlers receive JSON on stdin. SessionStart/UserPromptSubmit can provide additionalContext.
Stop can request continuation with a block/reason; stop_hook_active must prevent unbounded loops.
Project hooks live in .claude/settings.json. Managed policy/trust/permissions may affect execution.
The included hook implements only these documented stable event shapes; no SDK/API calls.

## Anthropic: automate actions with hooks
https://code.claude.com/docs/en/hooks-guide
Used to check configuration/lifecycle expectations. Installation in a user's live host remains
an acceptance test; simulated protocol tests are not a live Claude Code session.

All memory semantics, schema, resolver precedence and tests in v1.4 are implementation decisions,
not a claim that Anthropic promises the same behaviors or that a model has been fine-tuned.
