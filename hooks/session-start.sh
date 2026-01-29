#!/usr/bin/env bash
# SessionStart hook for vibe-claude plugin

set -euo pipefail

# Read core skill content
vibe_intro=$(cat <<'INTRO'
vibe-claude is active.

Use:
- `/vibe <task>` (default orchestration)
- `/v-plan`, `/v-debug`, `/v-review`
- `/v-compress` (save context), `/v-continue` (resume), `/cancel-vibe` (stop)

Rules:
- Delegate; don’t brute-force in the main context.
- Evidence before “done” (commands + output + file:line).
- Retry up to 10 attempts, then ask for guidance.
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
