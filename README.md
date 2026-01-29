# Vibe-Claude (Claude Code Plugin)

<p align="center">
  <img src="assets/vibe-claude.jpeg" alt="Vibe-Claude Logo" width="400">
</p>

Multi-agent orchestration for **Claude Code (Anthropic CLI)**:
- Faster navigation (specialists: finder/analyst/worker/tester/critic)
- **Evidence-based completion** (commands + output + file:line)
- **Context-efficient workflow** (handoffs, compression, resume)

## Quick Start (First-Time User)

```bash
# Install (recommended)
claude plugin install vibe-claude

# Restart Claude Code after install/update
```

Then run:
```
/vibe scan this repo and fix the first failing test
```

## What Makes This Useful (vs vanilla Claude Code)

- **Consistent orchestration**: `v-conductor` routes work instead of one generalist doing everything.
- **Specialization**: fast file-finding (`v-finder`), deep debugging (`v-analyst`), implementation (`v-worker`), verification (`v-tester` + `v-critic`).
- **Less “trust me”**: completion requires evidence (real command output, real file references).
- **Session durability**: `/v-compress` and `/v-continue` help when context runs low.

## Practical Prompt Examples

### Debug + Fix
```
/vibe fix the failing test in this repo. show the exact command output.
/vibe debug why this CLI command exits non-zero
/v-debug why authentication fails only in production
```

### Plan First (Complex Work)
```
/v-plan refactor auth to support refresh tokens (keep public API stable)
```

### Review / Quality Gate
```
/v-review review the last change for regressions and missing tests
```

### Documentation
```
/vibe update README with accurate setup steps and runnable examples
```

### Context / Resume
```
/v-compress
/v-continue
```

## How It Works (Short)

- **Routing**: work is classified and routed to the smallest effective path (see `DEFINITIONS.md`).
- **Handoffs**: agents request other specialists via `[HANDOFF REQUEST: ...]`; `v-conductor` routes them (see `agents/v-conductor.md`).
- **Verification**: tests + review gate completion.
- **Retry policy**: max 10 attempts by default (see `DEFINITIONS.md`).

## Edge-Case Behavior (Short)

- Agent/tool failure → retry once, then escalate tier; if still stuck, split the task.
- Unknown/missing handoff target → fallback to `v-analyst`.
- Circular handoffs → stop, re-analyze (`v-analyst`), then ask user to narrow scope if it repeats.

## Commands

| Command | Description |
|---------|-------------|
| `/vibe <task>` | Orchestrate end-to-end |
| `/v-turbo <task>` | Parallel execution mode |
| `/v-plan <task>` | Planning session |
| `/v-debug <issue>` | Systematic debugging |
| `/v-review` | Review / quality gate |
| `/v-continue` | Resume from last work doc |
| `/v-memory <cmd>` | Save/search knowledge (memU optional) |
| `/v-compress` | Compress context into files |
| `/cancel-vibe` | Stop current vibe session |

## V-Memory (Optional memU)

`/v-memory` works without memU (local markdown storage + grep fallback).  
If you run memU, set `MEMU_API` and it will sync.

## Repository Layout

```
vibe-claude/
├── .claude-plugin/
├── agents/
├── skills/
├── commands/
├── hooks/
├── scripts/
├── DEFINITIONS.md
├── CLAUDE.md
└── README.md
```

## License

MIT
