---
name: v-debug
description: Systematic debugging with v-analyst - find root cause, not symptoms
---

# V-Debug Skill

Systematic approach to debugging. No guessing.

## When to Use

- Unexpected behavior
- Test failures
- Runtime errors
- Performance issues

## Philosophy

```
DON'T: Randomly change things hoping it works
DO: Understand the system, find root cause, fix once
```

## Opus 4.6 Debugging Power

### Effort: max for Debugging

디버깅은 항상 최대 역량이 필요한 작업:
```
v-analyst (effort: max) → Five Whys 이상의 깊은 분석
Adaptive Thinking → 문제 복잡도에 따라 자동으로 사고 깊이 조절
128K Output → 복잡한 스택 트레이스와 로그 전체를 한 번에 분석
```

### Compaction for Long Debug Sessions

```
긴 디버깅 세션:
  기존: Context 소진 → 디버깅 포기
  지금: Compaction API가 이전 시도 자동 요약
    → 실패한 가설 기억
    → 새 가설에 집중
    → 사실상 무한 디버깅 가능
```

## Process

```
1. REPRODUCE
   └─ Confirm the bug exists
   └─ Document exact steps
   └─ Capture error output

2. ISOLATE
   └─ Identify affected components
   └─ Find minimal reproduction
   └─ Rule out unrelated code

3. HYPOTHESIZE
   └─ Form theories about cause
   └─ Rank by likelihood
   └─ Design tests for each

4. VERIFY
   └─ Test each hypothesis
   └─ Gather evidence
   └─ Find root cause

5. FIX
   └─ Minimal change
   └─ Don't break other things
   └─ Add regression test

6. CONFIRM
   └─ Original bug gone
   └─ No new bugs introduced
   └─ Tests pass
```

## Debug Document

```markdown
# Debug: {issue description}

## Reproduction
Steps:
1. {step}
2. {step}

Expected: {what should happen}
Actual: {what happens}
Error: {if any}

## Isolation
Affected files: {list}
Related systems: {list}
Recent changes: {list}

## Hypotheses
| # | Theory | Likelihood | Test |
|---|--------|------------|------|
| 1 | {theory} | HIGH | {how to test} |
| 2 | {theory} | MEDIUM | {how to test} |

## Investigation Log
### [timestamp] Tested hypothesis #1
Result: {confirmed/rejected}
Evidence: {what we found}

## Root Cause
{Explanation of actual cause}

## Fix
File: {path}
Change: {description}

## Verification
- [ ] Original bug fixed
- [ ] Regression test added
- [ ] Related tests pass
```

## Anti-Patterns

| Bad | Good |
|-----|------|
| "Let me try this..." | "My hypothesis is..." |
| Random print statements | Strategic logging |
| Changing multiple things | One change at a time |
| "It works now" | "Here's why it works" |

## Integration

v-debug automatically uses:
- v-analyst for deep analysis
- v-finder to locate related code
- v-tester to verify fixes
