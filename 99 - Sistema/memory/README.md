# Portable local format memory — v1.4

The earlier winners/failures/decisions folders were only a filing convention. They are preserved
as legacy material, but memories are stored per format at
`context/clients/<format-id>/memory.sqlite3` with project/pattern/job scopes, history and receipts.
The `clients` folder name is retained for compatibility; a format is a named editing profile,
separate from output proportions such as 9:16. No personal format database is shipped in this package.

Start: `workflows/FORMAT_MEMORY.md`. Rules: `method/FORMAT_MEMORY_POLICY.md`.
Schema: `RECORD_SCHEMA.json`; minimal simulated payload: `CAPTURE_EXAMPLE.json`.
Operator guide and migration: `../MEMORIA-COMO-USAR.md`.
Store operations and settings resolution are local; semantic classification is done by the agent.
Legacy `client` fields and commands remain supported. Do not use a blanket host MEMORY.md as the
only source of format identity or preferences.
