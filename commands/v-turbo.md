---
name: v-turbo
description: Maximum velocity mode with parallel agent orchestration
---

# V-Turbo Mode

Maximum velocity execution with parallel everything.

## Activation

This command activates v-turbo mode for the given task.

## Behavior

When activated:
1. **Parallel Agent Dispatch** - All independent agents launch simultaneously
2. **Background Execution** - Builds, tests, installs run in background
3. **Speculative Execution** - Start likely-needed work before confirmation
4. **Fan-out Patterns** - Multiple workers for large tasks

## Usage

```
/v-turbo <task description>
```

## Integration

Combines with:
- vibe: Full power mode with parallelism
- v-git: Parallel branch operations
- v-style: Multiple component creation

## Rules

- Never wait when you can parallelize
- Background all long-running operations
- Speculate on likely next steps
- Maximum concurrent agents
