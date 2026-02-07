---
name: v-plan
description: Strategic planning with v-planner - creates comprehensive implementation plans
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

## Opus 4.6 Planning Power

### Effort: max Planning

Opus 4.6의 `max` effort로 계획 품질 극적 향상:
- 모든 의존성과 상호작용을 빠짐없이 분석
- 위험 요소의 2차, 3차 파급효과까지 고려
- 128K Output으로 COMPLEX 작업의 포괄적 5-Phase 계획 한 번에 생성

### Adaptive Thinking in Planning

```
요구사항 분석: effort auto-adjusts
  간단한 feature → medium thinking
  아키텍처 변경 → max thinking + interleaved reasoning

계획 생성: always effort: max
  → 가장 깊은 사고로 빈틈 없는 계획
  → 모든 Phase의 작업, 의존성, 위험 한 번에 도출
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
