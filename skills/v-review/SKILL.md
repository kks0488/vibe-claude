---
name: v-review
description: Code/plan review with Momus (v-critic) - ruthless quality gate
---

# V-Review Skill

Invoke the Verification Tribunal for quality review.

## When to Use

- Before committing changes
- After completing a phase
- When unsure about quality
- Before creating PR

## Review Types

### Code Review
```
/v-review code
```
- Logic errors
- Security vulnerabilities
- Performance issues
- Style violations
- Missing edge cases

### Plan Review
```
/v-review plan
```
- Completeness
- Feasibility
- Risk assessment
- Missing considerations

### Architecture Review
```
/v-review architecture
```
- Design patterns
- Scalability
- Maintainability
- SOLID principles

## Opus 4.6 Review Power

### Effort: max Reviews

v-critic이 Opus 4.6 effort: max로 리뷰:
- **Adaptive Thinking**: 코드 복잡도에 따라 자동으로 리뷰 깊이 조절
- **128K Output**: 대규모 PR 전체를 한 번에 리뷰, 파일 누락 없음
- **Interleaved Thinking**: 코드 읽기와 분석을 교차하며 깊은 통찰

### 강화된 Tribunal

```
기존 (4.5):
  v-critic + v-analyst + v-tester = Tribunal

지금 (Opus 4.6):
  v-critic (effort: max) + v-analyst (effort: max) + v-tester (effort: max)
  = Ultra Tribunal
  → 3개 에이전트 모두 최대 역량
  → 표면적 문제뿐 아니라 구조적 결함까지 탐지
  → 128K로 리뷰 결과를 상세하게 문서화
```

## Process

```
1. COLLECT
   └─ Gather changed files / plan document

2. ANALYZE
   └─ v-critic examines each item
   └─ v-analyst verifies logic

3. REPORT
   └─ Issues categorized by severity
   └─ Actionable feedback

4. ITERATE
   └─ Fix issues
   └─ Re-review if needed
```

## Output Format

```markdown
# Review: {subject}

## Summary
- Files reviewed: {n}
- Issues found: {n}
- Severity: {PASS/MINOR/MAJOR/CRITICAL}

## Issues

### CRITICAL
- [ ] {issue} @ {file:line}
  Reason: {explanation}
  Fix: {suggestion}

### MAJOR
...

### MINOR
...

## Approved: [YES/NO]
Reviewer: v-critic
```

## Severity Levels

| Level | Action Required |
|-------|-----------------|
| PASS | Good to go |
| MINOR | Fix if time permits |
| MAJOR | Must fix before merge |
| CRITICAL | Stop. Fix immediately. |

## The Critic's Standards

v-critic is ruthless:
- No "looks good to me"
- No handwaving
- Every issue must be specific
- Every fix must be actionable
