# Vibe-Claude

<p align="center">
  <img src="assets/vibe-claude.jpeg" alt="Vibe-Claude Logo" width="400">
</p>

<h3 align="center">Don't think. Just vibe. Claude does the rest.</h3>

<p align="center">
  <strong>A self-evolving multi-agent orchestration system for Claude Code</strong><br>
  The more you use it, the smarter it gets.
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://claude.ai"><img src="https://img.shields.io/badge/Claude-Code-blueviolet" alt="Claude Code"></a>
  <a href="#"><img src="https://img.shields.io/badge/v3.0.0-Opus%204.6-orange" alt="v3.0.0"></a>
  <a href="#"><img src="https://img.shields.io/badge/Agents-13-blue" alt="13 Agents"></a>
  <a href="#"><img src="https://img.shields.io/badge/Skills-11-green" alt="11 Skills"></a>
  <a href="#"><img src="https://img.shields.io/badge/128K%20Output-Adaptive%20Thinking-brightgreen" alt="128K Output"></a>
</p>

---

## What Happens When You Type `/vibe`

```
You: "/vibe make me a login page with OAuth"

Vibe-Claude:
├─ 🔍 Analyzes your codebase (v-analyst)
├─ 📋 Plans the implementation (v-planner)
├─ 🏗️ Builds the feature (v-worker, v-designer)
├─ ✅ Tests everything (v-tester)
├─ 🔄 Fixes any issues (automatic retry)
└─ ✨ Done. Actually done. Proven done.

Time: You waited. It worked.
Cost: Opus 4.6-level. Worth it.
Power: 128K output. Adaptive thinking. Compaction.
```

---

## Powered by Opus 4.6

| Feature | What It Means |
|---------|---------------|
| **Adaptive Thinking** | 작업 복잡도에 따라 사고 깊이 자동 조절 |
| **Effort: max** | COMPLEX 작업에 최대 역량 투입 |
| **128K Output** | 64K → 128K, 대규모 기능 한 번에 생성 |
| **Compaction API** | 서버사이드 자동 컨텍스트 요약 → 무한 대화 |
| **Fine-grained Streaming** | 실시간 진행상황 모니터링 (GA) |

---

## The Difference

| Without Vibe-Claude | With Vibe-Claude |
|---------------------|------------------|
| "Build a login page" | "Build a login page" |
| ↓ | ↓ |
| Claude asks clarifying questions | Claude interviews you once |
| You answer | Plans everything |
| Claude writes some code | Builds in parallel |
| Error occurs | Tests automatically |
| You debug together | Retries on failure |
| More errors | Retries again |
| Context runs out | Compresses context |
| Start over | Keeps working |
| ... | ... |
| **Hours later**: Maybe done? | **Result**: Working, tested, verified |

---

## Quick Start (30 seconds)

```bash
# Plugin installation (recommended)
claude plugin install vibe-claude@vibe-claude-marketplace

# Or clone manually
git clone https://github.com/kks0488/vibe-claude.git ~/projects/vibe-claude
cd ~/projects/vibe-claude && claude plugin link .

# Use it
/vibe build me a todo app with dark mode
```

That's literally it. No config. Just results.

---

## Who Is This For?

| You say... | Vibe-Claude says... |
|------------|---------------------|
| "I don't know code" | You don't need to |
| "Just make it work" | It will |
| "I hate complexity" | One command: `/vibe` |
| "Money isn't the issue" | Perfect. We use Opus liberally |
| "I need it done right" | Verified. Tested. Proven. |

---

## Real Examples

```bash
# Simple
/vibe add a logout button

# Moderate
/vibe create a blog with comments and markdown support

# Complex
/vibe refactor the entire authentication system to use JWT

# Ambitious
/vibe build a real-time chat feature with typing indicators
```

**Any language. Any description. Any complexity.**

Claude figures out what you mean and makes it happen.

### Practical Prompt Examples (Copy/Paste)

```text
# Full orchestration (recommended)
/vibe add OAuth login, include tests, and prove it works

# Plan first, then execute
/v-plan design a migration plan for moving from REST to GraphQL
/vibe implement the approved plan step-by-step with verification

# Systematic debugging (root cause, not guessing)
/v-debug my tests started failing after the last change — find why and fix

# Quality gate / tribunal review
/v-review

# Speed mode (parallel swarm)
/v-turbo scan this repo for dead code and propose safe deletions (no code changes yet)

# Memory (save/search)
/v-memory search "auth token"
/v-memory save lesson "How we fixed flaky integration tests"
```

### Manual Install (Alternative): `git clone` + `scripts/install.sh`

If you prefer not to use `claude plugin install`, you can install/update using the included installer script:

```bash
git clone https://github.com/kks0488/vibe-claude.git ~/.claude-vibe
bash ~/.claude-vibe/scripts/install.sh
```

This script installs into `~/.claude/`, keeps backups, and is safe to re-run for updates.

### Edge-Case Behavior (What Happens When Things Go Wrong)

**Handoff edge cases (agent → v-conductor → agent):**
- **unknown target**: v-conductor does not crash; it selects a safe fallback agent (default: `v-analyst`) and asks for a corrected target.
- **malformed** handoff request: v-conductor requests a re-issue in the correct template (or escalates to `v-analyst` to reconstruct safely).
- **circular** handoff: v-conductor detects loops (A→B→A) and breaks the chain; escalates for root-cause analysis and/or re-planning.

**Verification Tribunal outcomes (Phase 4):**
- **APPROVED → continue**
- **REVISE → v-worker**
- **REJECT → v-planner**

---

## How It Actually Works

### The 13 Agents

Vibe-Claude isn't just one AI. It's a team:

```
┌──────────────────────────────────────────────────────────┐
│              AGENT HIERARCHY (Opus 4.6)                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  🧠 OPUS 4.6 TIER (effort: max) - 6 agents               │
│  ├─ v-analyst    → Deep debugging, root cause            │
│  ├─ v-planner    → Strategy, architecture                │
│  ├─ v-critic     → Ruthless code review                  │
│  ├─ v-advisor    → Risk analysis                         │
│  ├─ v-conductor  → Orchestration + effort routing        │
│  └─ v-tester     → Edge case verification                │
│  ★ Adaptive Thinking + 128K Output + Compaction          │
│                                                          │
│  ⚡ SONNET 4.5 TIER (effort: high) - 5 agents             │
│  ├─ v-worker     → Code implementation                   │
│  ├─ v-designer   → UI/UX, styling                        │
│  ├─ v-researcher → Codebase analysis                     │
│  ├─ v-vision     → Screenshot analysis                   │
│  └─ v-api-tester → API endpoint testing                  │
│  ★ Fine-grained Streaming GA                             │
│                                                          │
│  🚀 HAIKU 4.5 TIER (effort: low) - 2 agents              │
│  ├─ v-finder     → Fast file search                      │
│  └─ v-writer     → Documentation                         │
│  ★ Maximum speed, minimal overhead                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Effort-Based Routing (New in v3.0.0)

Smart task classification → optimal agent + effort level:

| Complexity | Effort | Agents | Thinking |
|------------|--------|--------|----------|
| TRIVIAL | `low` | Haiku | Minimal |
| SIMPLE | `medium` | Sonnet | Balanced |
| MODERATE | `high` | Sonnet/Opus | Deep |
| COMPLEX | `max` | Opus 4.6 | Maximum |

### The 11 Skills

| Skill | What It Does |
|-------|--------------|
| `vibe` | Maximum power mode - the full orchestra |
| `v-turbo` | Parallel execution for speed |
| `v-plan` | Strategic planning before coding |
| `v-review` | Quality gate - find every flaw |
| `v-debug` | Systematic debugging, not guessing |
| `v-git` | Clean commits, proper messages |
| `v-style` | Beautiful UI, design systems |
| `v-evolve` | Self-improvement, new capabilities |
| `v-continue` | Resume work across sessions |
| `v-memory` | Remember lessons, patterns, decisions |
| `v-compress` | Extend sessions, save context |

### The 5-Phase System

Every `/vibe` task follows this:

```
Phase 0.5: INTERVIEW (complex tasks only)
    └─ "What exactly do you need?"

Phase 1: RECON (parallel)
    ├─ v-analyst analyzes
    ├─ v-finder searches
    ├─ v-researcher studies
    └─ v-advisor warns

Phase 2: PLANNING (complex tasks only)
    └─ v-planner creates the battle plan

Phase 3: EXECUTION (parallel)
    ├─ v-worker builds
    ├─ v-designer styles
    └─ v-writer documents

Phase 4: ULTRA TRIBUNAL (all effort: max)
    ├─ v-critic reviews (Opus 4.6)
    ├─ v-analyst verifies (Opus 4.6)
    └─ v-tester tests (Opus 4.6)
    ALL THREE MUST APPROVE

Phase 5: POLISH (complex tasks only)
    └─ Refactor, document, optimize
```

---

## The Secret Sauce: Self-Evolution

**Vibe-Claude learns from every interaction.**

```
Week 1: "Optimize my database queries"
        → Claude struggles a bit

Week 2: Claude creates v-db-optimizer agent
        → Specialized for YOUR stack

Week 3+: All DB tasks → instant expertise
         → Tailored to YOUR codebase
```

Every struggle becomes a strength. Every solution gets remembered.

---

## Infinite Retry Engine

```
Attempt 1: Standard approach
    ↓ FAIL
Attempt 2: Alternative method
    ↓ FAIL
Attempt 3: Escalate to Opus 4.6 (effort: max) + v-analyst
    ↓ FAIL
Attempt 4: Decompose into smaller tasks
    ↓ FAIL
Attempt 5: Research external solutions
    ↓ FAIL
...
Attempt 10: Still trying

THE LOOP CONTINUES UNTIL SUCCESS (max 10 attempts)
(or you say /cancel-vibe)
```

**Same Error 3x Rule**: Same exact error 3 times? STOP. `/clear` + completely different approach.

### Anti-Patterns (NEW in 1.2.0)

Vibe-Claude now detects and avoids common failure patterns:

| Pattern | Trigger | Action |
|---------|---------|--------|
| Kitchen Sink | 2+ unrelated tasks | Split sessions |
| Death Spiral | 3+ failed fixes | /clear + root cause |
| Infinite Exploration | 5+ files no plan | Stop + subagent |
| Trust-Verify Gap | Claim without proof | Run verification |
| Subagent Bypass | Direct exploration | Delegate now |

### Batch Operations (NEW in 1.2.0)

For large-scale changes (5+ files):

```
Orchestrator (main Claude):
├─ Define transformation
├─ List target files
├─ Spawn workers (parallel)
│   ├─ v-worker-1: files 1-5
│   ├─ v-worker-2: files 6-10
│   └─ v-worker-3: files 11-15
├─ Collect results
└─ Verify all succeeded
```

**Writer/Reviewer Pattern**: For quality-critical batch ops, v-worker writes → v-critic reviews → fix issues → final verification.

### Session Management (Enhanced in 1.2.0)

Never lose progress when context runs out:

| Session Type | Strategy |
|--------------|----------|
| Single-task | Complete → /clear |
| Multi-task | Task → checkpoint → task |
| Exploration | Subagent-heavy, summarize often |
| Long-running | Aggressive checkpointing |

**Checkpoint Protocol:**
```markdown
# .vibe/checkpoint-{timestamp}.md

## Context
- Task: {description}
- Phase: {current phase}
- Progress: {completed items}

## State
- Modified files: {list}
- Pending tasks: {list}

## Resume Instructions
{Exact steps to continue}
```

**Session Handoff:**
1. Create checkpoint
2. `/v-compress` (save details to file)
3. Summary message to user
4. Next session: `/v-continue`

**Command Reference:**

| Command | When to Use | Effect |
|---------|-------------|--------|
| `/clear` | Fresh start needed | Clears all context |
| `/compact` | Context getting full | Summarizes conversation |
| `/v-compress` | Phase complete | Saves details, keeps summary |
| `/v-continue` | Resume previous work | Loads last checkpoint |

No more losing work when sessions end!

---

## Context Management (Compaction-Enhanced)

> **"Opus 4.6 + Compaction API = 컨텍스트 걱정은 과거의 일."**

```
100% ████████████████████ Fresh session
 80% ████████████████░░░░ Compaction API standby
 60% ████████████░░░░░░░░ Compaction 자동 요약 시작
 40% ████████░░░░░░░░░░░░ /v-compress 보조 + checkpoint
 20% ████░░░░░░░░░░░░░░░░ /v-continue 준비
```

**Two-Strike Rule**: Same failure twice? Evaluate context → compress or clear.

**Never lose work**: `/v-continue` resumes from last checkpoint.

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `/vibe <task>` | Maximum power mode |
| `/v-turbo <task>` | Parallel execution, max speed |
| `/v-plan <task>` | Strategic planning session |
| `/v-review` | Critical evaluation of code/plans |
| `/v-debug` | Systematic debugging session |
| `/v-continue` | Resume work from previous session |
| `/v-memory <cmd>` | Save, search, recall knowledge |
| `/v-compress` | Compress context, extend session |
| `/cancel-vibe` | Stop current vibe session |
| `/update` | Check for updates |

---

## Evidence-Based Completion

**Nothing is "done" without proof.**

```
## COMPLETION PROOF

✓ Executed: npm run dev
  Output: Server running on localhost:3000

✓ Tests: npm test
  Result: 47 passed, 0 failed

✓ Features verified:
  - Login page: src/pages/Login.tsx:42
  - OAuth flow: src/auth/oauth.ts:15
  - Error handling: src/utils/errors.ts:8

✓ Tribunal: APPROVED
```

**Forbidden phrases:**
- ~~"Should work"~~ → Must TEST it
- ~~"I think it's done"~~ → Must PROVE it
- ~~"Looks correct"~~ → Must RUN it

---

## V-Memory: AI That Remembers

```
┌────────────────────────────────────────────────┐
│              V-MEMORY SYSTEM                   │
├────────────────────────────────────────────────┤
│                                                │
│  AUTO-RECALL                                   │
│  ├─ New task → search related memories         │
│  ├─ Error occurs → find similar solutions      │
│  └─ New project → load relevant knowledge      │
│                                                │
│  AUTO-SAVE                                     │
│  ├─ Struggled then succeeded → save lesson     │
│  ├─ Same pattern 3x → save pattern             │
│  └─ Architecture decision → save decision      │
│                                                │
└────────────────────────────────────────────────┘
```

**The more you use it, the smarter it gets.**

---

## FAQ

<details>
<summary><strong>Do I need to know how to code?</strong></summary>

No. Describe what you want in plain language. Any language.

</details>

<details>
<summary><strong>What if it doesn't work the first time?</strong></summary>

It retries automatically. Up to 10 times. Different approaches each time.

</details>

<details>
<summary><strong>Is it expensive?</strong></summary>

Yes. We use Opus liberally because it works. If cost matters more than results, this isn't for you.

</details>

<details>
<summary><strong>How is this different from just using Claude Code?</strong></summary>

Claude Code is the engine. Vibe-Claude is the autopilot. Powered by Opus 4.6, we add:
- 13 specialized agents with effort-based routing
- Adaptive thinking (auto-adjusts depth per task)
- 128K output tokens (2x previous)
- Compaction API for infinite conversations
- Automatic retry on failure (up to 10x)
- Context management + server-side compaction
- Session persistence
- Self-evolution
- Evidence-based completion

</details>

<details>
<summary><strong>Can I customize the agents?</strong></summary>

Yes. They're just markdown files. Edit them in the plugin's `agents/` directory or create new ones.

</details>

<details>
<summary><strong>What happens when context runs out?</strong></summary>

Opus 4.6의 Compaction API가 서버사이드에서 자동으로 컨텍스트를 요약합니다. `/v-compress`는 상세 파일 백업용이고, `/v-continue`는 세션 간 복구에 사용됩니다.

</details>

<details>
<summary><strong>Can I stop it mid-task?</strong></summary>

Yes. `/cancel-vibe` stops the current session immediately.

</details>

<details>
<summary><strong>Does it work with my existing project?</strong></summary>

Yes. It reads your codebase, understands your patterns, and adapts.

</details>

---

## File Structure

```
vibe-claude/
├── .claude-plugin/    # Plugin metadata
├── agents/            # 13 specialized agents
├── skills/            # 11 enhancement skills
├── commands/          # Slash commands
│   ├── vibe.md
│   ├── v-turbo.md
│   ├── v-plan.md
│   ├── v-review.md
│   ├── v-debug.md
│   ├── v-continue.md
│   ├── v-memory.md
│   └── v-compress.md
├── hooks/             # Auto-execution hooks
├── scripts/           # Helper scripts
│   ├── install.sh
│   ├── auto-update.sh
│   ├── v-memory.sh
│   ├── v-compress.sh
│   ├── v-continue.sh
│   ├── validate-handoff.sh
│   ├── test-e2e-workflow.sh
│   └── test-v-memory.sh
├── assets/            # Images
├── CLAUDE.md          # Plugin instructions
└── README.md          # This file
```

### Update Plugin

```bash
claude plugin update vibe-claude
```

---

## The Vibe Coder Manifesto

1. **Don't think, describe** - Say what you want, not how
2. **Trust the process** - Let Claude figure it out
3. **Money solves problems** - Opus is worth it
4. **Perfection is automatic** - Retries (max 10) until right
5. **Evolution is constant** - System improves itself every day

---

## Architecture Diagram

```
┌───────────────────────────────────────────────────────┐
│              VIBE-CLAUDE (Opus 4.6)                   │
├───────────────────────────────────────────────────────┤
│                                                       │
│  /vibe "your request"                                 │
│         ↓                                             │
│  ┌───────────────────────────────────────────┐        │
│  │  EFFORT-BASED ROUTING (Phase 0)           │        │
│  │  TRIVIAL→low  SIMPLE→med  COMPLEX→max     │        │
│  └───────────────────────────────────────────┘        │
│         ↓                                             │
│  ┌───────────────────────────────────────────┐        │
│  │  AGENTS (13) + Adaptive Thinking          │        │
│  │  Opus 4.6(6) + Sonnet 4.5(5) + Haiku(2)  │        │
│  │  128K Output │ Compaction │ Streaming GA   │        │
│  └───────────────────────────────────────────┘        │
│         ↓                                             │
│  ┌───────────────────────────────────────────┐        │
│  │  SKILLS (11)                              │        │
│  │  vibe, v-turbo, v-plan, v-review...       │        │
│  └───────────────────────────────────────────┘        │
│         ↓                                             │
│      RESULT                                           │
│         ↓                                             │
│  Not perfect? → Retry (up to 10x)                     │
│         ↓                                             │
│      PROVEN DONE                                      │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## Contributing

Pull requests welcome. Keep it simple. Keep it vibe.

---

## Inspired By

- [opencode](https://github.com/anomalyco/opencode) - Open-source AI coding assistant
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) - Official Anthropic documentation
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-python) - Multi-agent patterns

---

## License

MIT

---

## Author

Created with vibes by [@kks0488](https://github.com/kks0488)

---

<p align="center">
  <strong>Don't think. Just vibe. Claude does the rest.</strong>
</p>
