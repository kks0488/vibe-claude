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

## Rules

- Default language: **Korean (한국어)**
- Delegate work to agents; don't do everything yourself.
- **Evidence before claims**: commands + output + `file:line`.
- Context: ~60% → `/v-compress`, ~40% → checkpoint, ~20% → `/clear`.
- **Two-Strike Rule**: 동일 실패 2회 → 컨텍스트 잔량 확인 후 >60% v-analyst, 40-60% /v-compress, <40% /clear.
- Retry: max 10 attempts, then ask user for guidance.
- Work document: `.vibe/work-{timestamp}.md` (template in `DEFINITIONS.md`).

## Agents

| Tier | Agents |
|------|--------|
| **Opus** | `v-analyst`, `v-planner`, `v-critic`, `v-advisor`, `v-conductor`, `v-tester` |
| **Sonnet** | `v-worker`, `v-designer`, `v-researcher`, `v-vision`, `v-api-tester` |
| **Haiku** | `v-finder`, `v-writer` |

### Quick Routing

- Find files/patterns → `v-finder`
- Root cause / logic → `v-analyst`
- Implement changes → `v-worker`
- UI / styling → `v-designer`
- Plan / strategy → `v-planner`
- Run tests → `v-tester`
- Review → `v-critic`
- Risk / edge cases → `v-advisor`
- Research → `v-researcher`
- Screenshot / image → `v-vision`
- API validation → `v-api-tester`
- Docs → `v-writer`

## Handoff

Agents emit `[HANDOFF REQUEST: v-...]`. `v-conductor` routes them. See `agents/v-conductor.md`.

