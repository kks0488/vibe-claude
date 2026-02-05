---
name: v-continue
description: Resume work from previous session - reads session state and continues automatically
---

# V-Continue Skill

Resume work from where the previous session left off.

## Activation

```
/v-continue
```

## How It Works

1. **Find Work File**
   - Find most recent `.vibe/work-*.md` file (already updated in real-time)
   - No separate session-state.md needed

2. **Read and Analyze**
   - Parse the work file
   - Identify checked (✓) and unchecked ([ ]) items
   - Find the next pending task

3. **Resume Work**
   - Display summary of previous progress
   - Automatically continue from where left off
   - Activate vibe mode for remaining tasks

## Protocol

```
/v-continue
    ↓
┌─────────────────────────────────────────────────┐
│  [SESSION RESTORED]                             │
├─────────────────────────────────────────────────┤
│                                                 │
│  Previous Task: {task description}              │
│                                                 │
│  Progress:                                      │
│  ✓ {completed items}                            │
│  → {current/in-progress item}                   │
│  ○ {pending items}                              │
│                                                 │
│  Resuming from: {current state}                 │
│                                                 │
└─────────────────────────────────────────────────┘
    ↓
Continue working automatically
```

## Opus 4.6 + Compaction 시너지

### Compaction-Aware Resume

```
기존 (4.5):
  Session end → checkpoint 파일 저장 → /v-continue로 파일 읽기

지금 (Opus 4.6 + Compaction):
  Session end → Compaction API가 자동으로 컨텍스트 보존
  + checkpoint 파일 = 이중 안전망
  → /v-continue 시 Compaction 요약 + 파일 기반 상세 복구
```

### 향상된 복구 품질

- **128K Output**: 복구 시 더 포괄적인 상태 요약 가능
- **Adaptive Thinking**: 복구 우선순위 자동 판단 (어디부터 재개할지)
- **Compaction**: 이전 세션의 핵심 컨텍스트가 서버에 자동 보존

## File Search Order

1. `.vibe/work-*.md` (most recent by timestamp)
2. Any `*-IMPLEMENTATION-PLAN.md` in `.vibe/`

## Example Usage

**Previous session showed warning:**
```
[CONTEXT WARNING: 15% REMAINING]
To continue: /v-continue
```

**New session:**
```
User: /v-continue

Claude:
[SESSION RESTORED]

Previous Task: Implement user authentication system

Progress:
✓ Created auth middleware
✓ Added JWT token generation
→ Implementing password reset flow (60% complete)
○ Add email verification
○ Write tests

Resuming password reset implementation...
```

## Rules

- ALWAYS check for session state files first
- Display clear summary before resuming
- Activate /vibe mode automatically for complex remaining tasks
- If no session state found, inform user and ask what to work on
