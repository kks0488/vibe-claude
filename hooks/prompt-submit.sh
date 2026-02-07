#!/usr/bin/env bash
# UserPromptSubmit hook for vibe-claude plugin
# Lightweight context reminder on each prompt

set -euo pipefail

# Simple reminder (kept minimal to avoid context bloat)
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "<vibe-reminder>Remember: Evidence before claims. Delegate exploration to subagents.</vibe-reminder>"
  }
}
EOF

exit 0
