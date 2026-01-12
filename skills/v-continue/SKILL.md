---
name: v-continue
description: Resume work from previous session - reads session state and continues automatically
---

# V-Continue Skill

Resume work from where the previous session left off.

## Activation

```
/vibe continue
```

## How It Works

1. **Find Session State**
   - Check for `.vibe/session-state.md` in current project
   - If not found, check for most recent `.vibe/work-*.md` file

2. **Read and Analyze**
   - Parse the session state file
   - Identify completed tasks, in-progress work, and pending items
   - Understand the current state and next steps

3. **Resume Work**
   - Display summary of previous progress
   - Automatically continue from where left off
   - Activate appropriate skills (vibe, v-turbo, etc.) as needed

## Protocol

```
/vibe continue
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

1. `.vibe/session-state.md` (primary - auto-saved state)
2. `.vibe/work-*.md` (most recent by timestamp)
3. Any `*-IMPLEMENTATION-PLAN.md` in `.vibe/`

## Example Usage

**Previous session ended at 15% context:**
```
Session state saved to: .vibe/session-state.md
To continue: /vibe continue
```

**New session:**
```
User: /vibe continue

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
