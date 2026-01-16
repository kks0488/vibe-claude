---
name: v-compress
description: Compress completed work to extend session context
---

# V-Compress Mode

Compress completed phases to extend session by 2-3x.

## Activation

```
/v-compress
```

## Behavior

When activated:
1. **Identify Completed Phases** - Find phases marked 100% complete
2. **Extract Key Information** - Decisions, changes, outcomes
3. **Create Summary** - Concise summary of completed work
4. **Save Detail** - Full detail to `.vibe/phase*-detail.md`
5. **Replace with Summary** - Keep only summary in conversation

## Compression Format

```markdown
## Phase N: [Name] ✓ COMPRESSED

### Summary
- [Key outcome 1]
- [Key outcome 2]

### Files Changed
- path/to/file.ts: [what changed]

### Decisions Made
- [Decision]: [Rationale]

Detail: .vibe/phase{N}-detail-{timestamp}.md
```

## When to Use

- After completing a major phase
- When context is getting long
- Before starting a new complex phase
- Every 3-4 phases in long tasks

## Integration

Works with:
- vibe: Compress between phases
- v-continue: Read compressed summaries
- v-memory: Save important details to memory
