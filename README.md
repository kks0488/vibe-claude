# vibe-claude

Performance-first guardrails for Claude Code. Amplifies vanilla Claude Code without replacing it.

> Just say what you want. Claude handles the rest.

## Quick Start

```bash
# Install
claude plugin install vibe-claude

# Use - just describe what you want
/vibe Add login page with Google OAuth
```

Done. vibe-claude delegates to agents, manages context, retries on failure, and proves completion.

## Commands

| Command | What it does |
|---------|--------------|
| `/vibe <task>` | Full power mode - delegates, retries, verifies |
| `/v-turbo <task>` | Parallel execution for speed |
| `/v-plan <task>` | Planning before implementation |
| `/v-debug <issue>` | Systematic root cause analysis |
| `/v-review` | Quality review before commit |
| `/v-continue` | Resume previous session |
| `/v-compress` | Extend session by compressing context |

## How it works

```
You say what you want
        ↓
vibe-claude picks the right agents
        ↓
Manages context (40% warning, 20% danger)
        ↓
Retries up to 10x if something fails
        ↓
Only finishes when PROVEN done
```

## Agents

| Tier | Agents | For |
|------|--------|-----|
| **Opus** | v-analyst, v-planner, v-critic, v-advisor, v-conductor, v-tester | Analysis, planning, review |
| **Sonnet** | v-worker, v-designer, v-researcher, v-vision, v-api-tester | Implementation |
| **Haiku** | v-finder, v-writer | Search, docs |

## Core Rules

- **Two-Strike Rule** - Same failure twice → stop and reassess
- **Evidence Required** - No "should work" - show actual output
- **Context is Precious** - Compress at 60%, checkpoint at 40%

## Why vibe-claude?

- Works WITH Claude Code, not against it
- As Claude Code improves, vibe-claude benefits automatically
- Minimal overhead - just guardrails, no bloat
- Zero learning curve - just describe what you want

## License

MIT
