# Vibe-Claude

> **Don't think. Just vibe. Claude does the rest.**

A **self-evolving** multi-agent orchestration system for Claude Code.
The more you use it, the smarter it gets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude-Code-blueviolet)](https://claude.ai)

---

## Key Feature: Self-Evolution

**Vibe-Claude evolves itself.** When it encounters a task it can't handle well:

```
Capability gap detected
        ↓
Create new agent prompt or skill
        ↓
Save to ~/.claude/agents/ or ~/.claude/skills/
        ↓
Reference and use in future tasks
```

| Situation | What Happens |
|-----------|--------------|
| Repeated task pattern | Creates reusable prompt template |
| Specialized knowledge needed | Creates expert agent prompt |
| Better method discovered | Updates existing prompts |
| External tool needed | Creates integration skill |

### How Evolution Works

New agents are saved as prompt files. Claude reads and applies them when relevant:

```
User: "Test my API endpoints"
        ↓
Claude checks ~/.claude/agents/
        ↓
Finds v-api-tester.md
        ↓
Reads the prompt and becomes that specialist
```

**The system learns your project's patterns over time.**

---

## Who Is This For?

- "I don't know code" → **You don't need to**
- "Just make it work" → **It will**
- "I hate complexity" → **One command**
- "Money isn't the issue" → **We use Opus liberally**

---

## Quick Start

```bash
# Install
git clone https://github.com/kks0488/vibe-claude.git ~/.claude-vibe
cp -r ~/.claude-vibe/* ~/.claude/

# Use
/vibe make me a login page
```

That's it. Claude will:
- Analyze what's needed
- Plan the approach
- Build it
- Test it
- Fix any issues
- Repeat until perfect

---

## Usage Examples

```
/vibe create a blog with comments
/vibe fix this authentication bug
/vibe add dark mode to my app
/vibe make this look professional
/vibe refactor the entire API layer
```

Just describe what you want. In any language. However you want.

---

## Philosophy

> **"Vibe coding: where you describe, AI delivers."**

| Traditional Development | Vibe-Claude |
|------------------------|-------------|
| 1. Write requirements | 1. "Make this" |
| 2. Design architecture | 2. Done |
| 3. Write code | |
| 4. Write tests | |
| 5. Debug | |
| 6. Repeat... | |

### Why Does This Work?

**We throw money at it.**

Vibe-Claude uses Opus 4.5 without hesitation:
- Analysis? Opus
- Planning? Opus
- Review? Opus
- Anything complex? Opus

Expensive, but effective.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              VIBE-CLAUDE                     │
├─────────────────────────────────────────────┤
│                                              │
│  /vibe "your request"                        │
│         ↓                                    │
│  ┌─────────────────────────────────────┐    │
│  │         V-CONDUCTOR                  │    │
│  │    (Auto-routes to right agent)      │    │
│  └─────────────────────────────────────┘    │
│         ↓                                    │
│  ┌─────────────────────────────────────┐    │
│  │           AGENTS                     │    │
│  │                                      │    │
│  │  ┌──────────┐ ┌──────────┐          │    │
│  │  │v-analyst │ │v-planner │ ← Opus   │    │
│  │  │v-critic  │ │v-advisor │          │    │
│  │  │v-conductor│            │          │    │
│  │  └──────────┘ └──────────┘          │    │
│  │                                      │    │
│  │  ┌──────────┐ ┌──────────┐          │    │
│  │  │v-worker  │ │v-designer│ ← Sonnet │    │
│  │  │v-researcher│ │v-vision │          │    │
│  │  └──────────┘ └──────────┘          │    │
│  │                                      │    │
│  │  ┌──────────┐ ┌──────────┐          │    │
│  │  │v-finder  │ │v-writer  │ ← Haiku  │    │
│  │  └──────────┘ └──────────┘          │    │
│  └─────────────────────────────────────┘    │
│         ↓                                    │
│  ┌─────────────────────────────────────┐    │
│  │           SKILLS                     │    │
│  │  v-turbo  v-git  v-style  v-evolve  │    │
│  └─────────────────────────────────────┘    │
│         ↓                                    │
│      RESULT                                  │
│         ↓                                    │
│  Not perfect? → Retry automatically          │
│         ↓                                    │
│      DONE                                    │
└─────────────────────────────────────────────┘
```

---

## Agents

### Opus Tier (Heavy Lifting)

| Agent | Purpose |
|-------|---------|
| `v-analyst` | Deep debugging, root cause analysis |
| `v-planner` | Strategic planning, architecture design |
| `v-critic` | Ruthless code review, quality gates |
| `v-advisor` | Risk analysis, hidden requirements |
| `v-conductor` | Orchestration, agent routing |

### Sonnet Tier (Execution)

| Agent | Purpose |
|-------|---------|
| `v-worker` | Code implementation |
| `v-designer` | UI/UX, styling, components |
| `v-researcher` | Documentation, codebase analysis |
| `v-vision` | Screenshot/image analysis |

### Haiku Tier (Speed)

| Agent | Purpose |
|-------|---------|
| `v-finder` | Fast file/pattern search |
| `v-writer` | Documentation writing |

---

## Skills

| Skill | Purpose |
|-------|---------|
| `v-turbo` | Parallel execution, maximum speed |
| `v-git` | Clean commits, git mastery |
| `v-style` | Beautiful UI, design systems |
| `v-evolve` | Self-improvement, creates new capabilities |
| `v-continue` | Session restoration, resume work |
| `v-memory` | AI memory system with auto-recall & auto-save |

---

## How It Works

### The 5-Phase System

Every task follows this proven structure:

```
┌─────────────────────────────────────────────────┐
│              THE 5-PHASE SYSTEM                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Phase 1: RECON (Parallel)                      │
│  ├─ v-analyst: Analyze requirements             │
│  ├─ v-finder: Find related code                 │
│  ├─ v-researcher: Research best practices       │
│  └─ v-advisor: Identify risks                   │
│                                                 │
│  Phase 2: PLANNING                              │
│  └─ v-planner: Create comprehensive plan        │
│                                                 │
│  Phase 3: EXECUTION (Parallel)                  │
│  ├─ v-worker: Implement features                │
│  ├─ v-designer: Build UI components             │
│  └─ v-writer: Write documentation               │
│                                                 │
│  Phase 4: VERIFICATION TRIBUNAL                 │
│  ├─ v-critic: Quality review                    │
│  ├─ v-analyst: Logic verification               │
│  └─ Tests: Automated checks                     │
│  ALL THREE MUST APPROVE                         │
│                                                 │
│  Phase 5: POLISH (Optional)                     │
│  ├─ Refactor if needed                          │
│  ├─ Add docs/comments                           │
│  └─ Security/performance check                  │
│  SKIP if not needed                             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Work Document Tracking

Every `/vibe` task creates a tracking document:
```
.vibe/work-{timestamp}.md
```

This ensures **nothing is forgotten**. Each task is tracked with checkboxes and evidence.

### Evidence-Based Completion

**Nothing is "done" without proof:**
- Code must actually RUN (output shown)
- Tests must actually PASS (results pasted)
- Every feature verified with `file:line` references

**Forbidden phrases:**
- "Should work" → Must TEST it
- "I think it's done" → Must PROVE it
- "Looks correct" → Must RUN it

### Infinite Retry Engine

```
Attempt 1: Standard approach
Attempt 2: Alternative method
Attempt 3: Escalate to Opus
Attempt 4: v-analyst deep dive
Attempt 5: Create new agent
...continues until success
```

### Session Management (NEW)

Never lose progress when context runs out:

```
┌─────────────────────────────────────────────────┐
│  Context Warning System                         │
├─────────────────────────────────────────────────┤
│  25% remaining → Soft warning                   │
│  15% remaining → Show /v-continue command       │
│  5% remaining  → Final warning                  │
└─────────────────────────────────────────────────┘
```

**How it works:**
- Work file (`.vibe/work-*.md`) is updated in real-time
- No extra save needed = No wasted tokens
- `/v-continue` reads the latest work file

**Usage:**
```
# Previous session shows warning
[CONTEXT WARNING: 15% REMAINING]
To continue: /v-continue

# New session
User: /v-continue

# Claude reads work file and continues
[SESSION RESTORED]
Resuming from where we left off...
```

No more losing work when sessions end!

---

### Self-Evolution (The Secret Sauce)

This is what makes Vibe-Claude different. When Claude encounters something it can't handle well:

```
Day 1: "I need to optimize database queries"
       → Claude struggles a bit

Day 2: Claude creates v-db-optimizer agent
       → Saves to ~/.claude/agents/v-db-optimizer.md

Day 3+: All DB tasks routed to specialized agent
        → Fast, efficient, tailored to YOUR codebase
```

**Evolution is logged:**
```
~/.claude/evolution-log.md

## [2024-01-15] Created v-db-optimizer

### Reason
Repeated database optimization requests with suboptimal results

### Change
Created specialized agent with PostgreSQL expertise

### Effect
DB optimization tasks now 3x faster with better results
```

The more you use Vibe-Claude, the more it adapts to YOUR specific needs.

---

## Commands

| Command | Delegates To | Description |
|---------|--------------|-------------|
| `/vibe <task>` | Multi-agent | Maximum power mode - parallel + escalation + infinite retry |
| `/v-turbo <task>` | Parallel agents | Maximum speed with concurrent execution |
| `/v-plan <task>` | v-planner | Strategic planning session |
| `/v-review` | v-critic | Critical evaluation of code/plans |
| `/v-analyze <target>` | v-analyst | Root cause analysis, debugging |
| `/v-continue` | v-continue | Resume work from previous session |
| `/v-update` | - | Check for and install vibe-claude updates |
| `/v-cancel` | - | Stop current vibe session, save progress |
| `/v-memory <cmd>` | v-memory | Save, search, recall knowledge |

---

## V-Memory System (NEW)

AI가 자동으로 학습하고 기억하는 지식 시스템.

### How It Works

```
┌─────────────────────────────────────────────────┐
│              V-MEMORY SYSTEM                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  AUTO-RECALL (작업 시작 시)                       │
│  ├─ /vibe 실행 → 관련 메모리 자동 검색            │
│  ├─ 에러 발생 → 유사 해결 기록 검색               │
│  └─ 새 프로젝트 → 관련 지식 자동 로드             │
│                                                  │
│  AUTO-SAVE (작업 완료 시)                         │
│  ├─ 실패 → 해결 → lesson 자동 저장               │
│  ├─ 같은 패턴 3회+ → pattern 자동 저장           │
│  ├─ 기술 선택 → decision 자동 저장               │
│  └─ 새 도메인 → context 자동 저장                │
│                                                  │
│  DEDUP (저장 전)                                 │
│  └─ memU check-similar로 중복 방지              │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Memory Types

| Type | Purpose | Auto-Trigger |
|------|---------|--------------|
| `lessons` | 실패 → 해결 기록 | 2회+ 시도 후 성공 |
| `patterns` | 재사용 코드 패턴 | 같은 패턴 3회+ |
| `decisions` | 아키텍처 결정 | 기술 선택 논의 |
| `context` | 프로젝트 컨텍스트 | 새 도메인 학습 |

### Storage

```
~/.claude/.vibe/memory/
├── lessons/      # 실패 → 해결
├── patterns/     # 코드 패턴
├── decisions/    # 아키텍처 결정
└── context/      # 프로젝트 지식
```

### memU Integration

- **Semantic search**: 키워드가 아닌 의미로 검색
- **Deduplication**: 유사도 85%+ 중복 방지
- **Auto-sync**: 로컬 저장 시 memU에 동기화

**The more you use it, the smarter it gets.**

---

## File Structure

```
~/.claude/
├── CLAUDE.md          # Main system prompt
├── README.md          # This file
├── agents/            # 11 specialized agents
│   ├── v-analyst.md
│   ├── v-worker.md
│   ├── v-designer.md
│   └── ...
├── skills/            # 6 enhancement skills
│   ├── v-turbo/
│   ├── v-git/
│   ├── v-style/
│   ├── v-evolve/
│   ├── v-continue/
│   └── v-memory/      # AI memory system (NEW)
├── commands/          # Slash commands
│   ├── vibe.md
│   └── ...
├── scripts/           # Helper scripts
│   └── v-memory-helper.sh
└── .vibe/
    ├── memory/        # Knowledge storage (NEW)
    │   ├── lessons/
    │   ├── patterns/
    │   ├── decisions/
    │   └── context/
    └── work-*.md      # Work tracking documents
```

---

## FAQ

**Q: Do I need to know how to code?**
A: No.

**Q: What do I need to do?**
A: Type `/vibe` and describe what you want.

**Q: What if it doesn't work?**
A: Claude retries automatically. Until it works.

**Q: Is it expensive?**
A: Yes. But it works.

**Q: Can I customize the agents?**
A: Yes. Edit the markdown files in `~/.claude/agents/`.

---

## The Vibe Coder Manifesto

1. **Don't think, describe** - Say what you want, not how
2. **Trust the process** - Let Claude figure it out
3. **Money solves problems** - Opus is worth it
4. **Perfection is automatic** - Retries until right
5. **Evolution is constant** - System improves itself every day

---

## Contributing

Pull requests welcome. Keep it simple. Keep it vibe.

---

## Inspired By

This project draws inspiration from:

- [opencode](https://github.com/anomalyco/opencode) - Open-source AI coding assistant
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code) - Official Anthropic documentation for Claude Code
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-python) - Multi-agent patterns and best practices
- The open-source AI coding community

---

## License

MIT

---

## Author

Created with vibes by [@kks0488](https://github.com/kks0488)

---

**Don't think. Just vibe. Claude does the rest.**
