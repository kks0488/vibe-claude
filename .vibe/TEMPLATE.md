# VIBE Work Document Template

Copy this template for each new task.

---

## Task: {Describe the task}

**Started:** {YYYY-MM-DD HH:MM}
**Status:** IN_PROGRESS | COMPLETED

---

## Requirements

Break down the user's request into specific requirements:

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

---

## Execution Checklist

### Phase 1: Reconnaissance
- [ ] Analyze requirements
- [ ] Find related code
- [ ] Research best practices
- [ ] Identify risks

### Phase 2: Planning
- [ ] Create implementation plan
- [ ] Define acceptance criteria

### Phase 3: Execution
- [ ] Task A
- [ ] Task B
- [ ] Task C
(Add more as needed)

### Phase 4: Verification
- [ ] Run all tests
- [ ] Code review (v-critic)
- [ ] Logic verification (v-analyst)
- [ ] Build succeeds
- [ ] Lint passes
- [ ] Types check

---

## Progress Log

### [{timestamp}] Started
Initial analysis of the task.

### [{timestamp}] {Action taken}
{What was done}
{Evidence/output}
✓ Verified: {How it was verified}

### [{timestamp}] {Next action}
...

---

## Final Verification

- [ ] All requirements boxes checked
- [ ] All execution boxes checked
- [ ] All verification boxes checked
- [ ] Evidence provided for each
- [ ] v-critic APPROVED
- [ ] v-analyst VERIFIED

---

## Completion Proof

```
✓ Executed: {command}
  Output: {actual output}

✓ Tests: {test command}
  Result: {X passed, 0 failed}

✓ Requirements:
  - [Req 1]: file:line ✓
  - [Req 2]: file:line ✓

✓ Tribunal:
  - v-critic: APPROVED
  - v-analyst: VERIFIED
  - Build: SUCCESS
```

**COMPLETED:** {YYYY-MM-DD HH:MM}
