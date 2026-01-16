---
name: v-memory
description: AI memory system - save, search, and recall knowledge
---

# V-Memory System

Save, search, and recall knowledge across sessions.

## Commands

```
/v-memory save <type> "<title>"   # Save new memory
/v-memory search "<query>"        # Semantic search
/v-memory list [type]             # List memories
```

## Memory Types

| Type | Purpose | Location |
|------|---------|----------|
| lesson | Failure → Solution | ~/.claude/.vibe/memory/lessons/ |
| pattern | Reusable code | ~/.claude/.vibe/memory/patterns/ |
| decision | Architecture choices | ~/.claude/.vibe/memory/decisions/ |
| context | Domain knowledge | ~/.claude/.vibe/memory/context/ |

## Save Protocol

When saving a memory:
1. Determine appropriate type
2. Create file with timestamp: `{type}-{YYYYMMDD}-{title}.md`
3. Use template from `~/.claude/skills/v-memory/templates/`
4. Fill in required fields
5. Save to appropriate directory

## Search Protocol

When searching:
1. Read all files in memory directories
2. Match against query (title, content, tags)
3. Return relevant results with snippets

## Auto-Save Triggers

- 2+ retry attempts → save as lesson
- Architecture discussion → save as decision
- Reusable solution found → save as pattern

## Integration

Works with:
- vibe: Auto-recall at start, auto-save at end
- v-continue: Load relevant context when resuming
