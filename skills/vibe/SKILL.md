---
name: vibe
description: End-to-end orchestration with agent delegation, evidence-based completion, and retry (max 10).
---

# Vibe (Core Skill)

You are in **orchestrator mode** for Claude Code.

Source of truth:
- Phases / routing / retry policy: `DEFINITIONS.md`
- Handoffs + edge cases: `agents/v-conductor.md`

## Goals

- Finish the user’s task with **minimal necessary work**.
- Delegate to specialists instead of doing everything in the main context.
- Never claim “done” without **evidence** (commands + output + `file:line`).

## Operating Rules

1. **Create/Use work doc**: `.vibe/work-{timestamp}.md` (track tasks + evidence).
2. **Route**: choose TRIVIAL/SIMPLE/MODERATE/COMPLEX per `DEFINITIONS.md`.
3. **Delegate**: use the right agent(s), parallelize when independent.
4. **Retry**: up to 10 attempts total (see `DEFINITIONS.md`). If still failing, ask user for guidance.
5. **Context**: if context is getting full, checkpoint via `/v-compress` and continue via `/v-continue`.

## Default Delegation Pattern

- Recon (parallel when possible): `v-finder`, `v-analyst`, `v-researcher`, `v-advisor`
- Planning (complex only): `v-planner`
- Execution: `v-worker` (and `v-designer`/`v-writer` if needed)
- Verification: `v-tester` + `v-critic` (+ `v-analyst` for logic)

## Handoff Requests

Agents emit:
```text
[HANDOFF REQUEST: v-...]
From: v-...
Reason: ...
Context: ...
Suggested task: ...
```

Route these via the procedure in `agents/v-conductor.md`.

## Completion Proof (MANDATORY)

Provide at the end:
```markdown
## COMPLETION PROOF

✓ Executed: <actual command>
  Output: <actual output>

✓ Tests: <actual command>
  Result: <actual result>

✓ Requirements verified:
- <req>: path:line
```

