# Vibe-Claude

Multi-agent orchestration system for Claude Code with infinite retry, context management, and proven completion.

## Features

- **13 Specialized Agents**: v-analyst, v-worker, v-designer, v-planner, v-critic, v-tester, v-researcher, v-finder, v-writer, v-conductor, v-advisor, v-vision, v-api-tester
- **8 Powerful Skills**: vibe, v-turbo, v-git, v-style, v-memory, v-compress, v-continue, v-evolve
- **Context Management**: Two-Strike Rule, automatic compression, session handoff
- **Infinite Retry**: Up to 10 attempts with intelligent fallback strategies
- **Proven Completion**: Evidence-based verification, no "should work" claims

## Installation

### From Marketplace (Recommended)

```bash
claude plugin install vibe-claude
```

### From Source

```bash
# Clone the repository
git clone https://github.com/kkaemo/vibe-claude.git

# Add as local marketplace
claude plugin add-marketplace ./vibe-claude

# Install
claude plugin install vibe-claude
```

## Quick Start

```bash
# Maximum power mode
/vibe <task description>

# Parallel execution
/v-turbo <task description>

# Continue previous session
/v-continue

# Save knowledge
/v-memory save lesson "What I learned"
```

## Agent Tiers

| Tier | Agents | Use Case |
|------|--------|----------|
| **Opus** | v-analyst, v-planner, v-critic, v-advisor, v-conductor, v-tester | Heavy analysis, planning, review |
| **Sonnet** | v-worker, v-designer, v-researcher, v-vision, v-api-tester | Execution, implementation |
| **Haiku** | v-finder, v-writer | Fast search, documentation |

## Skills Overview

| Skill | Description |
|-------|-------------|
| `vibe` | Maximum power mode with todo tracking, agent delegation, verification |
| `v-turbo` | Parallel agent orchestration, background execution |
| `v-git` | Atomic commits, style detection, clean history |
| `v-style` | UI/UX design excellence |
| `v-memory` | AI memory system with memU integration |
| `v-compress` | Context compression for longer sessions |
| `v-continue` | Session recovery and progress restoration |
| `v-evolve` | Self-improvement, new capability creation |

## The Vibe Promise

```
YOU SAY IT.
WE THROW AGENTS AT IT.
WE RETRY UP TO 10 TIMES.
WE PROVE IT WORKS.
WE PROTECT OUR CONTEXT.
WE NEVER LOSE WORK.

UNTIL IT'S DONE.
ACTUALLY DONE.
PROVEN DONE.
```

## License

MIT
