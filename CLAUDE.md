# Vibe-Claude (Claude Code Plugin)

**SSOT**: `DEFINITIONS.md` (phases, routing, retry policy)

## Use

| Command | When to use |
|---------|-------------|
| `/vibe <task>` | Default: orchestrate end-to-end with evidence |
| `/v-turbo <task>` | Speed: parallel execution |
| `/v-plan <task>` | Planning only (complex work) |
| `/v-debug <issue>` | Systematic debugging |
| `/v-review` | Tribunal review / quality gate |
| `/v-continue` | Resume from last work doc |
| `/v-memory <cmd>` | Save/search knowledge (memU optional) |
| `/v-compress` | Compress context into files |
| `/cancel-vibe` | Stop current vibe session |

## Rules (Keep It Tight)

- Delegate work to agents; don’t do everything yourself.
- **Evidence before claims**: commands + output + `file:line`.
- Context: ~60% → `/v-compress`, ~20% → `/clear`.
- Retry: max 10 attempts, then ask user for guidance.

## Quick Routing

- Find files/patterns → `v-finder`
- Root cause / logic → `v-analyst`
- Implement changes → `v-worker`
- Run tests → `v-tester`
- Review → `v-critic`
- Docs → `v-writer`

## Handoff

Agents emit `[HANDOFF REQUEST: v-...]`. `v-conductor` routes them. See `agents/v-conductor.md`.

