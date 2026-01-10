---
name: v-turbo
description: Maximum velocity mode. Parallel everything. Wait for nothing.
---

# V-Turbo

Speed isn't everything. It's the only thing.

## Core Philosophy

Sequential is slow. Parallel is power. When this skill activates, everything that CAN run simultaneously WILL run simultaneously.

## Activation Triggers

- Multiple independent tasks detected
- User mentions "fast", "quick", "parallel"
- Complex task with separable components
- Time-sensitive work

## Parallel Patterns

### 1. Fan-Out

```
Single Request
      ↓
┌─────┼─────┐
↓     ↓     ↓
Agent Agent Agent
↓     ↓     ↓
└─────┼─────┘
      ↓
Combined Result
```

### 2. Pipeline with Parallelism

```
[A + B parallel] → [C depends on both] → [D + E parallel]
```

### 3. Speculative Execution

```
Uncertain which approach?
→ Try both simultaneously
→ Use whichever succeeds first
→ Cancel the other
```

## Agent Dispatch Matrix

| Task | Agent | Model | Background? |
|------|-------|-------|-------------|
| Deep analysis | v-analyst | Opus | No (need result) |
| Quick search | v-finder | Haiku | No (fast anyway) |
| Code writing | v-worker | Sonnet | No (need result) |
| UI work | v-designer | Sonnet | No |
| Documentation | v-writer | Haiku | Yes (can wait) |
| Build/test | - | - | Yes |
| Install deps | - | - | Yes |

## Background Execution Rules

**Always Background:**
```bash
npm install, yarn, pip install
npm run build, make, cargo build
npm test, pytest, jest
docker build, docker pull
git clone (large repos)
```

**Never Background:**
```bash
git status, git diff
ls, pwd, cat
Simple edits
Quick checks
```

## 5-Phase Parallelization

```
Phase 1: MAXIMUM PARALLEL
├─ v-analyst + v-finder + v-researcher + v-advisor
└─ ALL AT ONCE

Phase 2: SEQUENTIAL
└─ v-planner (needs Phase 1 results)

Phase 3: MAXIMUM PARALLEL
├─ v-worker (Task A) + v-worker (Task B)
├─ v-designer (if UI)
└─ Background: builds, tests, installs

Phase 4: PARALLEL TRIBUNAL
├─ v-critic + v-analyst + automated tests
└─ ALL AT ONCE

Phase 5: AS NEEDED
└─ Optional, skip if not needed
```

## Verification Protocol (With Evidence)

Before declaring done:
```
□ All parallel tasks completed → Show each result
□ No conflicts between results → Show merge output
□ Combined output makes sense → Show final state
□ No errors in any branch → Show all clean outputs
```

## Parallel Execution Evidence

```
## TURBO EXECUTION EVIDENCE

Phase 1 Parallel Launch:
- v-analyst: Started 10:00:01, Completed 10:00:15
- v-finder: Started 10:00:01, Completed 10:00:03
- v-researcher: Started 10:00:01, Completed 10:00:08
- v-advisor: Started 10:00:01, Completed 10:00:12
  Time saved: 23 seconds (vs 38 sequential)

Phase 3 Parallel Launch:
- v-worker (auth): Started 10:01:00, Completed 10:01:45
- v-worker (api): Started 10:01:00, Completed 10:01:30
- npm install: Background, Completed 10:01:20
  Time saved: 45 seconds

Total time: 2 minutes (vs 4+ minutes sequential)
```

## My Rules

- If independent, parallelize
- If dependent, chain minimally
- Background everything possible
- Never wait when you can work
- Combine results intelligently
- **Show parallel execution timestamps as evidence**

**Maximum throughput. Zero idle time. PROVEN velocity.**
