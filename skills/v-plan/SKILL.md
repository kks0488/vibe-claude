---
name: v-plan
description: Strategic planning session with Prometheus (v-planner) - creates comprehensive implementation plans
---

# V-Plan Skill

Start a planning session for complex tasks.

## When to Use

- Multi-file changes
- New feature development
- Architecture decisions
- Unclear requirements

## Process

```
1. UNDERSTAND
   └─ v-planner analyzes the request
   └─ Identifies scope, dependencies, risks

2. RESEARCH
   └─ v-finder locates relevant code
   └─ v-researcher checks patterns/best practices

3. PLAN
   └─ Break into phases
   └─ Identify critical path
   └─ Define checkpoints

4. REVIEW
   └─ v-advisor checks for risks
   └─ User approves or refines

5. OUTPUT
   └─ Save to .vibe/plan-{timestamp}.md
```

## Plan Document Format

```markdown
# Plan: {task}

## Overview
{1-2 sentence summary}

## Phases

### Phase 1: {name}
- [ ] Task 1.1
- [ ] Task 1.2
Critical files: {list}
Risk: {low/medium/high}

### Phase 2: {name}
...

## Dependencies
- {External deps}
- {Internal deps}

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|

## Verification
- [ ] Tests to run
- [ ] Manual checks

## Estimated Complexity
{SIMPLE/MODERATE/COMPLEX}
```

## Activation

```
/v-plan <task description>
```

Claude will:
1. Spawn v-planner (opus) for strategic analysis
2. Use v-finder to locate relevant code
3. Present plan for approval
4. Save approved plan to `.vibe/`

## Integration

After planning:
- `/vibe` uses the plan automatically
- Plan becomes the work document blueprint
