# Changelog

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
