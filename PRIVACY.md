# Privacy

## No collection by the author

vibe-claude is a Claude Code plugin. It has no server, no account, no analytics and no telemetry. The author receives nothing.

## What stays on your computer

Everything the plugin records stays in `~/.vibe-claude` on your computer. You can change this location with the `VIBE_HOME` environment variable.

This folder contains:

- Backups of project files taken before each request and before risky commands.
- A log of shell commands Claude ran, including their exit codes and session IDs.
- Copies of deleted files so a delete can be undone.

Deleting that folder removes all of these records.

The plugin does not intentionally read or store names, email addresses or other personal data. Project files it backs up stay local.

## Package checks

When Claude tries to install a package, the plugin asks the public package registry, npm, PyPI or crates.io, whether the package name exists and how old it is. Only the package name is sent. Names from private registries are never sent.

## Optional second opinion

If you have the OpenAI Codex CLI installed and signed in, the plugin runs it to review each change. The diff goes to OpenAI through your own Codex CLI and account, under OpenAI's terms.

Files that usually hold secrets, such as `.env` files and private keys, are excluded. Values that look like API keys or tokens are masked before sending. Without Codex, this step does not run.

## Questions

Open an issue at https://github.com/kks0488/vibe-claude/issues.