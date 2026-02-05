---
name: v-turbo
description: Maximum velocity mode. Parallel everything. Wait for nothing.
---

# V-Turbo

Speed isn't everything. It's the only thing.

## Core Philosophy

Sequential is slow. Parallel is power. When this skill activates, everything that CAN run simultaneously WILL run simultaneously.

## Claude 4.6 Turbo Enhancements

### Fine-grained Tool Streaming (GA)

```
기존: Beta 헤더 필요, 제한적 스트리밍
지금: GA — 모든 모델, 모든 플랫폼에서 완전 지원

효과:
├─ 병렬 에이전트 실행 중 실시간 진행 모니터링
├─ 긴 코드 생성 시 즉각적 부분 결과 확인
├─ 빌드/테스트 결과 실시간 스트리밍
└─ 대기 시간 체감 대폭 감소
```

### Effort-Based Parallelism

```
COMPLEX 작업의 Phase 1:
├─ v-analyst (effort: max) — 깊은 분석
├─ v-finder (effort: low) — 즉시 검색
├─ v-researcher (effort: high) — 심층 리서치
├─ v-advisor (effort: max) — 위험 분석
└─ ALL PARALLEL + 각 에이전트 최적 effort

Phase 3 Fan-Out:
├─ v-worker-1 (effort: high) — 기능 A
├─ v-worker-2 (effort: high) — 기능 B
├─ v-designer (effort: high) — UI
└─ Background: builds, tests (streaming)
```

### 128K Output Parallel

- 각 에이전트가 128K까지 출력 가능
- Fan-Out 패턴에서 개별 워커의 출력 제한 해소
- 대규모 배치 작업의 단일 패스 완료율 향상

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

| Task | Agent | Model | Effort | Background? |
|------|-------|-------|--------|-------------|
| Deep analysis | v-analyst | Opus | max | No (need result) |
| Quick search | v-finder | Haiku | low | No (fast anyway) |
| Code writing | v-worker | Sonnet | high | No (need result) |
| UI work | v-designer | Sonnet | high | No |
| Documentation | v-writer | Haiku | low | Yes (can wait) |
| Build/test | - | - | - | Yes |
| Install deps | - | - | - | Yes |

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

## 5-Phase Parallelization

```
Phase 1: MAXIMUM PARALLEL
├─ v-analyst + v-finder + v-researcher + v-advisor
└─ ALL AT ONCE

Phase 2: SEQUENTIAL
└─ v-planner (needs Phase 1 results)

Phase 3: MAXIMUM PARALLEL
├─ v-worker (Task A) + v-worker (Task B)
├─ v-designer (if UI)
└─ Background: builds, tests, installs

Phase 4: PARALLEL TRIBUNAL
├─ v-critic + v-analyst + automated tests
└─ ALL AT ONCE

Phase 5: AS NEEDED
└─ Optional, skip if not needed
```

## Verification Protocol (With Evidence)

Before declaring done:
```
□ All parallel tasks completed → Show each result
□ No conflicts between results → Show merge output
□ Combined output makes sense → Show final state
□ No errors in any branch → Show all clean outputs
```

## Parallel Execution Evidence

```
## TURBO EXECUTION EVIDENCE

Phase 1 Parallel Launch:
- v-analyst: Started 10:00:01, Completed 10:00:15
- v-finder: Started 10:00:01, Completed 10:00:03
- v-researcher: Started 10:00:01, Completed 10:00:08
- v-advisor: Started 10:00:01, Completed 10:00:12
  Time saved: 23 seconds (vs 38 sequential)

Phase 3 Parallel Launch:
- v-worker (auth): Started 10:01:00, Completed 10:01:45
- v-worker (api): Started 10:01:00, Completed 10:01:30
- npm install: Background, Completed 10:01:20
  Time saved: 45 seconds

Total time: 2 minutes (vs 4+ minutes sequential)
```

## My Rules

- If independent, parallelize
- If dependent, chain minimally
- Background everything possible
- Never wait when you can work
- Combine results intelligently
- **Show parallel execution timestamps as evidence**

**Maximum throughput. Zero idle time. 128K output. Streaming GA. PROVEN velocity.**
