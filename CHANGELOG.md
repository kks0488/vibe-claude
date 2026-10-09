# Changelog

## v6.0.0 — 2026-10-09

v6 is built for people who don't read code. Proof is now based on what actually ran, not on what the model wrote.

### Added

- **Evidence log and proof gate**: commands are parsed as shell, and a check only counts when its exit code really decides the command's result (`;`, `||`, `&` or a pipe without `pipefail` after it make it "unclear"). Changes are found by comparing snapshots, so edits made by shell commands count too. After a change, Claude can't finish until a check passes after the last edit.
- **Regression ratchet**: single check commands that passed before are re-run, without a shell, at the end of a change. Compound commands are never remembered.
- **Codex second opinion**: if `codex` is installed and logged in, it reviews each verified change read-only in the background and wakes Claude when it finds problems (`asyncRewake`). Without Codex this step is skipped.
- **Receipt**: a one-line `systemMessage` built from the log, never from the model.
- **Guard**: never asks the user. A backup before every destructive command; files the backup misses are copied to a 7-day trash (`vibe.py trash`); steps no backup can undo stop Claude once so it decides from the conversation, and the receipt reports them; refusal of catastrophic deletes; test-weakening detection; non-existent and brand-new package detection; secret detection. Here-document text is not read as commands, simple variables are expanded, and folders marked disposable (`vibe.py allow-delete`) stop asking. Tuned by replaying 16 days of real sessions (about 22,000 shell commands).
- **Snapshots and `/vibe-claude:undo`**: a private shadow git repository in `~/.vibe-claude/` (outside the project) saves the files at every request and before risky commands, including non-git projects. Restores are chosen by fixed snapshot id, never follow symlinks out of the project, refuse to overwrite anything without a backup, and can themselves be undone.
- Syntax checks for TypeScript (via the project's own `typescript`), TOML, and notebooks. `MultiEdit` and `NotebookEdit` are now covered.
- Rules are injected at `SessionStart`, because plugins don't load `CLAUDE.md`.

### Changed

- Replaced `stop-guard.sh` and `post-edit.sh` with one Python script, `hooks/vibe.py`.
- The Stop gate no longer pattern-matches words like "done" in the final message, which caused false blocks (for example "abandoned").
- README rewritten around what the plugin does; the v1–v5 story moved to `docs/HISTORY.md`.
- CI runs the unit tests and `claude plugin validate --strict`, and checks that version numbers match.

## v5.1.0 — 2026-08-14

This release turns the lessons from several months of day-to-day use into tested behavior.

### Fixed

- Read the current `last_assistant_message`, `stop_hook_active`, and `tool_input` hook fields.
- Avoid Stop-hook continuation loops and allow ordinary conversation without demanding test output.
- Require real verification language for completion claims instead of treating a `file:line` reference as proof.
- Return current top-level `decision: block` feedback with exit status 0.
- Pass edited paths as arguments, fixing failures and code injection risks for quotes and other special characters.
- Stop pretending that merely reading TypeScript is a syntax check.
- Remove the global `opus` model override so users keep control of model selection.

### Added

- A native Claude Code plugin manifest and self-hosted marketplace entry.
- Hook regression tests and GitHub Actions CI.
- Community health files and a concise research note.

## v5.0.0 — 2026-03-06

- Removed the orchestration layers that duplicated native Claude Code capabilities.
- Kept two small runtime guardrails: completion evidence and post-edit syntax checks.
