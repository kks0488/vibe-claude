---
description: Activate maximum performance mode with parallel agent orchestration
---

[ULTRAWORK MODE ACTIVATED]

$ARGUMENTS

## Enhanced Execution Instructions
- Use PARALLEL agent execution for all independent subtasks
- Delegate aggressively to specialized subagents:
  - 'v-analyst' for complex debugging and architecture decisions
  - 'v-researcher' for documentation and codebase research
  - 'v-finder' for quick pattern matching and file searches
  - 'v-designer' for UI/UX work
  - 'v-writer' for documentation tasks
  - 'v-vision' for analyzing images/screenshots
- Maximize throughput by running multiple operations concurrently
- Continue until ALL tasks are 100% complete - verify before stopping
- Use background execution for long-running operations:
  - For Bash: set `run_in_background: true` for npm install, builds, tests
  - For Task: set `run_in_background: true` for long-running subagent tasks
  - Use `TaskOutput` to check results later
  - Maximum 5 concurrent background tasks
- Report progress frequently

CRITICAL: Do NOT stop until every task is verified complete.
