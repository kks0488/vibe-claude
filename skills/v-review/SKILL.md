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
