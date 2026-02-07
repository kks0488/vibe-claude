#!/usr/bin/env bash
# SessionStart hook for vibe-claude plugin

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Read core skill content
vibe_intro=$(cat <<'INTRO'
You are enhanced with **vibe-claude** multi-agent orchestration system.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/vibe <task>` | Maximum power mode - retry (max 10), proven completion |
| `/v-turbo <task>` | Parallel agents, background execution |
| `/v-plan <task>` | Planning session |
| `/v-review` | Quality review |
| `/v-debug` | Systematic debugging |
| `/v-continue` | Resume previous session |
| `/v-memory save/search` | Knowledge persistence |
| `/v-compress` | Save context, extend session |
| `/cancel-vibe` | Emergency stop |

## Core Rules

1. **Context is precious** - 40% → compress, 20% → clear
2. **Two-Strike Rule** - Same failure 2x → stop and reassess
3. **Evidence Required** - Never claim done without proof
4. **Delegate exploration** - Use subagents for file reading

## Available Agents

**All 13 agents**: Opus 4.6 (v-analyst, v-planner, v-critic, v-advisor, v-conductor, v-tester, v-worker, v-designer, v-researcher, v-vision, v-api-tester, v-finder, v-writer)

For complex tasks, invoke `/vibe` to activate full orchestration.
INTRO
)

# Escape for JSON
escape_for_json() {
    local input="$1"
    local output=""
    local i char
    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        case "$char" in
            $'\\') output+='\\' ;;
            '"') output+='\"' ;;
            $'\n') output+='\n' ;;
            $'\r') output+='\r' ;;
            $'\t') output+='\t' ;;
            *) output+="$char" ;;
        esac
    done
    printf '%s' "$output"
}

vibe_escaped=$(escape_for_json "$vibe_intro")

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<vibe-claude-context>\n${vibe_escaped}\n</vibe-claude-context>"
  }
}
EOF

exit 0
