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
