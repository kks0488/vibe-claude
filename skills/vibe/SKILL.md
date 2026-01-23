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
CONTEXT IS PRECIOUS.
```

---

## Context Management (CRITICAL)

> **"컨텍스트 윈도우는 가장 중요한 자원이다."**

### Context Budget Visualization

```
100% ████████████████████ Fresh session
 80% ████████████████░░░░ Healthy
 60% ████████████░░░░░░░░ Caution - consider /v-compress
 40% ████████░░░░░░░░░░░░ WARNING - compress or checkpoint
 20% ████░░░░░░░░░░░░░░░░ DANGER ZONE - /clear recommended
```

### Context Preservation Rules

| Action | Context Cost | Alternative |
|--------|--------------|-------------|
| Read entire file | HIGH | Use subagent exploration |
| Grep large codebase | HIGH | Delegate to v-finder |
| Multiple retries | CUMULATIVE | Two-Strike Rule |
| Long error traces | HIGH | Summarize, save to file |
| Exploration without goal | VERY HIGH | Define scope first |

### Subagent-First Exploration Principle

```
WRONG: Claude reads 10 files directly → Context exhausted
RIGHT: v-finder/v-researcher explores → Returns summary only
```

**Rule**: 탐색 작업은 항상 서브에이전트에게 위임. 메인 컨텍스트는 의사결정과 조정에만 사용.

### Two-Strike Rule

```
Strike 1: First failure → Analyze, try alternative
Strike 2: Same failure → STOP
    ↓
Evaluate context:
├─ Context > 40%: /v-compress → Retry with fresh approach
└─ Context < 40%: /clear → New session with learned approach
```

---

## Activation

```
/vibe <task description>
```

## What Happens When Activated

### 1. Work Document Creation
Creates `.vibe/work-{timestamp}.md` with:
- Task requirements (checkbox format)
- Complexity classification
- Chosen route
- Context tracking
- Progress log

### 2. 5-Phase Execution (+ Phase 0.5)

```
Phase 0: ROUTING (Dynamic)
└─ Classify task complexity → Choose optimal path

Phase 0.5: INTERVIEW (COMPLEX only)
└─ Ask clarifying questions → Save to interview log

Phase 1: RECON (Parallel)
├─ v-analyst: Analyze requirements
├─ v-finder: Find related code
├─ v-researcher: Research best practices
├─ v-advisor: Identify risks
└─ v-memory: Search related memories

Phase 2: PLANNING (COMPLEX only)
└─ v-planner: Create comprehensive plan

Phase 3: EXECUTION (Parallel)
├─ v-worker: Implement features
├─ v-designer: Build UI components
└─ v-writer: Write documentation

Phase 4: VERIFICATION (Tribunal)
├─ v-critic: Quality review
├─ v-analyst: Logic verification
└─ v-tester: Test execution

Phase 5: POLISH (COMPLEX only)
├─ Refactoring
├─ Documentation
└─ v-memory: Save lessons/patterns
```

### 3. Dynamic Routing

| Complexity | Route | Interview? | Planning? | Example |
|------------|-------|------------|-----------|---------|
| TRIVIAL | P3 only | No | No | "Fix typo in README" |
| SIMPLE | P1→P3→P4 | No | No | "Add error handling to function" |
| MODERATE | P1→P3→P4 | Optional | No | "Implement login page" |
| COMPLEX | P0.5→P1→P2→P3→P4→P5 | **YES** | **YES** | "Refactor auth system" |

**COMPLEX 기준** (하나라도 해당시):
- 3개 이상의 서비스/모듈에 영향
- 새로운 아키텍처 패턴 도입
- 데이터 모델 변경
- 사용자가 명시적으로 계획 요청
- 불명확하거나 모호한 요구사항

---

## Phase 0.5: Interview Protocol (COMPLEX only)

> **"큰 기능은 Claude가 먼저 인터뷰하게 하라"**

### Interview Categories

```
1. SCOPE
   - What's included?
   - What's explicitly NOT included?
   - What are the boundaries?

2. TECHNICAL
   - Existing patterns to follow?
   - Dependencies or constraints?
   - Performance requirements?

3. EDGE CASES
   - Error scenarios?
   - Empty/null states?
   - Concurrent access?

4. VERIFICATION
   - How will success be measured?
   - Required test coverage?
   - Acceptance criteria?
```

### Interview Execution

```
Claude asks (max 5 questions per category, prioritized)
    ↓
User answers
    ↓
Claude summarizes understanding
    ↓
User confirms OR clarifies
    ↓
Save to .vibe/interview-{timestamp}.md
    ↓
Proceed to Phase 1
```

### Interview Exit Conditions

- User says "proceed" / "그냥 진행해"
- All critical questions answered
- Claude has enough context to avoid major rework

### Interview Document Template

```markdown
# .vibe/interview-{timestamp}.md

## Task: {task description}
## Interview Date: {datetime}

### Scope
Q: {question}
A: {answer}

### Technical
Q: {question}
A: {answer}

### Edge Cases
Q: {question}
A: {answer}

### Verification
Q: {question}
A: {answer}

### Summary
{Claude's understanding of requirements}

### Confirmed: [YES/NO]
```

---

### 4. Retry Policy (Context-Aware)

```
Attempt 1: Standard approach
    ↓ FAIL
Attempt 2: Alternative method
    ↓ FAIL (Two-Strike triggered)

Context Check:
├─ Context > 60%: Continue with v-analyst deep dive
├─ Context 40-60%: /v-compress first, then retry
└─ Context < 40%: /clear + new session with lessons

Attempt 3-10: Various approaches (if context allows)
    ↓ FAIL
After 10: Request user guidance
```

**Same Error 3x Rule**:
```
Same exact error 3 times?
    ↓
STOP. /clear + completely different approach
Don't throw good context after bad.
```

**탈출 조건** (DEFINITIONS.md 참조):
- 최대 10회 재시도
- 30분 타임아웃
- 사용자가 `/cancel-vibe` 입력
- 명확히 불가능한 작업 → 사용자에게 보고
- 컨텍스트 20% 미만 + 해결 불가

### 5. Evidence Requirements

**NEVER claim done without proof:**
```
✓ Code runs: [actual output]
✓ Tests pass: [actual results]
✓ Features verified: [file:line references]
✓ Tribunal approved
```

---

## Anti-Patterns (AVOID THESE)

### 1. Kitchen Sink Session
```
WRONG:
├─ Fix bug in auth
├─ Add new feature to dashboard
├─ Refactor database layer
└─ Update documentation
All in ONE session → Context exhausted, nothing done well
```

**Recognition**: Multiple unrelated tasks accumulating
**Recovery**: Complete one task, `/clear`, start next

### 2. Correction Death Spiral
```
WRONG:
Fix → Breaks something → Fix that → Breaks another → Fix...
Each "fix" makes it worse
```

**Recognition**: 3+ corrections without progress
**Recovery**: `/clear`, start fresh with root cause analysis

### 3. Infinite Exploration
```
WRONG:
"Let me check this file... and this one... and maybe this..."
Reading without clear goal
```

**Recognition**: 5+ files read without concrete action plan
**Recovery**: Stop, define specific questions, use subagent

### 4. Trust-Then-Verify Gap
```
WRONG:
Claude: "Done! Should work."
(No actual verification)
```

**Recognition**: Completion claim without evidence
**Recovery**: Run actual tests, show actual output

### 5. Subagent Bypass
```
WRONG:
Claude directly reads 20 files instead of delegating
Main context now 80% exploration, 20% actual work
```

**Recognition**: Direct exploration consuming context
**Recovery**: Delegate to v-finder, v-researcher, v-analyst

### Anti-Pattern Response Table

| Pattern | Trigger | Action |
|---------|---------|--------|
| Kitchen Sink | 2+ unrelated tasks | Split sessions |
| Death Spiral | 3+ failed fixes | /clear + root cause |
| Infinite Exploration | 5+ files no plan | Stop + subagent |
| Trust-Verify Gap | Claim without proof | Run verification |
| Subagent Bypass | Direct exploration | Delegate now |

---

## Session Management

### Session Types & Strategies

| Type | Duration | Strategy |
|------|----------|----------|
| Single-task | Short | Complete → /clear |
| Multi-task | Medium | Task → checkpoint → task |
| Exploration | Variable | Subagent-heavy, summarize often |
| Long-running | Extended | Aggressive checkpointing |

### Checkpoint Protocol

**When to Checkpoint**:
- Phase completion
- Before risky operation
- Context hits 60%
- After successful milestone

**Checkpoint Format**:
```markdown
# .vibe/checkpoint-{timestamp}.md

## Context
- Task: {description}
- Phase: {current phase}
- Progress: {completed items}

## State
- Modified files: {list}
- Pending tasks: {list}
- Blockers: {if any}

## Resume Instructions
{Exact steps to continue}
```

### Session Handoff Protocol

When context is low or session ending:

```
1. Create checkpoint
2. /v-compress (save details to file)
3. Summary message to user
4. Next session: /v-continue
```

### Command Reference

| Command | When to Use | Effect |
|---------|-------------|--------|
| `/clear` | Fresh start needed | Clears all context |
| `/compact` | Context getting full | Summarizes conversation |
| `/v-compress` | Phase complete | Saves details, keeps summary |
| `/v-continue` | Resume previous work | Loads last checkpoint |
| `/cancel-vibe` | Emergency stop | Exit vibe mode |

### Context Budget Tracking (Work Document)

```markdown
## Context Status
- Current: ~{X}%
- Threshold: 40% (compress), 20% (clear)
- Last checkpoint: {timestamp}
- Subagent delegations: {count}
```

---

## Batch Operations

### When to Use Fan-Out

```
Use Fan-Out when:
├─ 5+ files need similar changes
├─ Changes are independent (no shared state)
├─ Transformation is well-defined
└─ Order doesn't matter
```

### Fan-Out Protocol

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

### Writer/Reviewer Pattern

For quality-critical batch operations:

```
Phase 1: v-worker writes all changes
    ↓
Phase 2: v-critic reviews each change
    ↓
Phase 3: Fix any issues found
    ↓
Phase 4: Final verification
```

### Batch Evidence Format

```markdown
## Batch Operation: {description}

### Files Modified (15/15)
| File | Status | Reviewer |
|------|--------|----------|
| file1.ts | ✓ Done | v-critic approved |
| file2.ts | ✓ Done | v-critic approved |
...

### Summary
- Total files: 15
- Successful: 15
- Failed: 0
- Review: All passed
```

---

## Skill Combinations

Vibe automatically activates complementary skills:

| Task Signal | Additional Skills |
|-------------|-------------------|
| "with commits" | + v-git |
| "with UI" | + v-style |
| "fast" | + v-turbo |
| "continue" | + v-continue |
| "remember" | + v-memory |

---

## Work Document Template (Updated)

```markdown
# .vibe/work-{timestamp}.md

## Task: {user request}
Started: {datetime}
Complexity: {TRIVIAL|SIMPLE|MODERATE|COMPLEX}
Route: {chosen phase sequence}

## Context Status
- Current: ~100%
- Threshold: 40% (compress), 20% (clear)
- Last checkpoint: -
- Subagent delegations: 0

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Phase 0.5: Interview (COMPLEX only)
- [ ] Scope questions asked
- [ ] Technical questions asked
- [ ] Edge cases discussed
- [ ] Verification criteria defined
- [ ] Interview saved to .vibe/interview-{timestamp}.md

## Phase 1: Recon
- [ ] Analyze  - [ ] Find  - [ ] Research

## Phase 2: Planning (COMPLEX only)
- [ ] Plan created
- [ ] Plan approved

## Phase 3: Execution
- [ ] Task A  - [ ] Task B

## Phase 4: Verification
- [ ] Tests  - [ ] Review  - [ ] Build

## Phase 5: Polish (COMPLEX only)
- [ ] Refactoring  - [ ] Documentation  - [ ] Lessons saved

## Checkpoints
| Timestamp | Phase | Context | Notes |
|-----------|-------|---------|-------|
| {time} | {phase} | {%} | {notes} |

## Progress Log
### [timestamp] {action} - {result} ✓
```

---

## Exit Conditions

The ONLY ways to exit vibe mode:

1. ✓ ALL work document boxes checked
2. ✓ ALL requirements proven complete
3. ✓ ALL tests passing (shown, not claimed)
4. ✓ Tribunal approved
5. OR: User says `/cancel-vibe`
6. OR: Context < 20% AND no viable path forward

---

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

### v-compress
When activated together:
- Auto-compress at phase completion
- Details saved to files
- Context preserved for longer sessions

### v-continue
When activated together:
- Seamless session handoff
- Automatic checkpoint loading
- Progress restoration

---

## Forbidden Phrases

If Claude says these, vibe mode has FAILED:
- "I think it's done"
- "Should work"
- "Looks correct"
- "Probably"
- "Most likely"
- "Let me check a few more files..." (without clear goal)
- "Almost done" (without evidence)

**CERTAINTY REQUIRED. PROOF REQUIRED.**

---

## The Vibe Promise

```
YOU SAY IT.
WE THROW MONEY AT IT.
WE THROW AGENTS AT IT.
WE RETRY UP TO 10 TIMES.
WE PROVE IT WORKS.
WE PROTECT OUR CONTEXT.
WE CHECKPOINT PROGRESS.
WE NEVER LOSE WORK.

UNTIL IT'S DONE.
ACTUALLY DONE.
PROVEN DONE.
```
