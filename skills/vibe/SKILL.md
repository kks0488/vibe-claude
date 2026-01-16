---
name: vibe
description: Maximum power mode. Todo tracking, agent delegation, verification, infinite retry.
---

# Vibe Skill

The core skill that powers `/vibe` mode. Maximum power, infinite retry, proven completion.

## Core Philosophy

```
DOCUMENT FIRST.
MONEY IS NO OBJECT.
OPUS FOR EVERYTHING.
PARALLEL EVERYTHING.
RETRY INFINITELY.
NEVER. GIVE. UP.
NEVER. FORGET.
```

## Activation

```
/vibe <task description>
```

## What Happens When Activated

### 1. Work Document Creation
Creates `.vibe/work-{timestamp}.md` with:
- Task requirements (checkbox format)
- 5-phase structure
- Progress log

### 2. 5-Phase Execution

```
Phase 0: ROUTING (Dynamic)
└─ Classify task complexity → Choose optimal path

Phase 1: RECON (Parallel)
├─ v-analyst: Analyze requirements
├─ v-finder: Find related code
├─ v-researcher: Research best practices
├─ v-advisor: Identify risks
└─ v-memory: Search related memories

Phase 2: PLANNING
└─ v-planner: Create comprehensive plan

Phase 3: EXECUTION (Parallel)
├─ v-worker: Implement features
├─ v-designer: Build UI components
└─ v-writer: Write documentation

Phase 4: VERIFICATION (Tribunal)
├─ v-critic: Quality review
├─ v-analyst: Logic verification
└─ v-tester: Test execution

Phase 5: POLISH (Optional)
├─ Refactoring
├─ Documentation
└─ v-memory: Save lessons/patterns
```

### 3. Dynamic Routing

Not all tasks need all phases:

| Complexity | Route | Example |
|------------|-------|---------|
| TRIVIAL | Phase 3 only | "Fix typo in README" |
| SIMPLE | P1→P3→P4 | "Add error handling to function" |
| MODERATE | P1→P3→P4 | "Implement login page" |
| COMPLEX | P1→P2→P3→P4→P5 | "Refactor auth system" |

### 4. Retry Policy (최대 10회)

```
Attempt 1: Standard approach
    ↓ FAIL
Attempt 2: Alternative method
    ↓ FAIL
Attempt 3: Escalate to Opus
    ↓ FAIL
Attempt 4: v-analyst deep dive
    ↓ FAIL
Attempt 5-10: 다양한 접근법 시도
    ↓ FAIL
Attempt 10 이후: 사용자에게 guidance 요청
```

**탈출 조건** (DEFINITIONS.md 참조):
- 최대 10회 재시도
- 30분 타임아웃
- 사용자가 `/cancel-vibe` 입력
- 명확히 불가능한 작업 → 사용자에게 보고

### 5. Evidence Requirements

**NEVER claim done without proof:**
```
✓ Code runs: [actual output]
✓ Tests pass: [actual results]
✓ Features verified: [file:line references]
✓ Tribunal approved
```

## Skill Combinations

Vibe automatically activates complementary skills:

| Task Signal | Additional Skills |
|-------------|-------------------|
| "with commits" | + v-git |
| "with UI" | + v-style |
| "fast" | + v-turbo |
| "continue" | + v-continue |

## Work Document Template

```markdown
# .vibe/work-{timestamp}.md

## Task: {user request}
Started: {datetime}

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Phase 1: Recon
- [ ] Analyze  - [ ] Find  - [ ] Research

## Phase 3: Execution
- [ ] Task A  - [ ] Task B

## Phase 4: Verification
- [ ] Tests  - [ ] Review  - [ ] Build

## Phase 5: Polish (COMPLEX만)
- [ ] Refactoring  - [ ] Documentation  - [ ] Lessons saved

## Progress Log
### [timestamp] {action} - {result} ✓
```

## Exit Conditions

The ONLY ways to exit vibe mode:

1. ✓ ALL work document boxes checked
2. ✓ ALL requirements proven complete
3. ✓ ALL tests passing (shown, not claimed)
4. ✓ Tribunal approved
5. OR: User says `/cancel-vibe`

## Integration with Other Skills

### v-turbo
When activated together:
- Phase 1: ALL agents launch simultaneously
- Phase 3: Multiple workers in parallel
- Background: builds, tests, installs

### v-git
When activated together:
- Atomic commits during Phase 3
- Style detection and matching
- Clean history guaranteed

### v-memory
When activated together:
- Auto-recall related knowledge at start
- Auto-save lessons after completion
- Pattern detection for reuse

### v-style
When activated together:
- Bold design choices
- Consistent design system
- Accessibility checks

## Forbidden Phrases

If Claude says these, vibe mode has FAILED:
- "I think it's done"
- "Should work"
- "Looks correct"
- "Probably"
- "Most likely"

**CERTAINTY REQUIRED. PROOF REQUIRED.**

## The Vibe Promise

```
YOU SAY IT.
WE THROW MONEY AT IT.
WE THROW AGENTS AT IT.
WE RETRY UP TO 10 TIMES.
WE PROVE IT WORKS.

UNTIL IT'S DONE.
ACTUALLY DONE.
PROVEN DONE.
```
