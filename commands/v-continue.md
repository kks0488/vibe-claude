---
name: v-continue
description: Resume work from previous session
---

# V-Continue Mode

Resume work from where you left off.

## Activation

```
/v-continue
```

## Behavior

When activated:
1. **Find Latest Work** - Scan `.vibe/work-*.md` for most recent
2. **Parse State** - Read progress log and checkbox status
3. **Identify Incomplete** - Find unchecked requirements
4. **Resume Execution** - Continue from last completed step

## Protocol

```
1. List all .vibe/work-*.md files
2. Sort by timestamp (newest first)
3. Read the latest work document
4. Check which requirements are incomplete
5. Resume from the first incomplete item
6. Update progress log with "[timestamp] Resumed from previous session"
```

## Integration

Works with:
- vibe: Continue vibe mode tasks
- v-compress: Read compressed summaries
- v-memory: Recall related context

## Notes

- If no work document found, inform user
- If all tasks complete, report completion
- Always update the work document when resuming
