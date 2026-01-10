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

## Verification Protocol

Before declaring done:
```
□ All parallel tasks completed
□ No conflicts between results
□ Combined output makes sense
□ No errors in any branch
```

## My Rules

- If independent, parallelize
- If dependent, chain minimally
- Background everything possible
- Never wait when you can work
- Combine results intelligently

**Maximum throughput. Zero idle time.**
