# Lessons Learned

A record of failures and their solutions. Check this before starting similar tasks.

---

## [2026-01-10] Task tool subagent_type limitation

- **Task**: Tried to call custom agent via Task tool
- **Failure**: `subagent_type="v-api-tester"` not recognized
- **Root Cause**: Task tool has hardcoded subagent types, custom agents work via auto-delegation
- **Solution**: Custom agents in `~/.claude/agents/` are auto-discovered and delegated based on description matching
- **Prevention**: Use description-based matching, not direct subagent_type calls for custom agents

---
