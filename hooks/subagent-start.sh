#!/usr/bin/env bash
# SubagentStart hook for vibe-claude v4.1.0
# Injects project context when a subagent starts

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
VIBE_DIR="${PLUGIN_ROOT}/.vibe"

# Build context injection
CONTEXT_PARTS=""

# Inject latest work document summary if exists
if ls "${VIBE_DIR}"/work-*.md 1>/dev/null 2>&1; then
  LATEST_WORK=$(ls -t "${VIBE_DIR}"/work-*.md 2>/dev/null | head -1)
  if [ -f "${LATEST_WORK}" ]; then
    # Extract first 20 lines as context summary
    WORK_SUMMARY=$(head -20 "${LATEST_WORK}" | tr '\n' ' ' | tr '"' "'" | tr '\\' '/')
    CONTEXT_PARTS="Current work: ${WORK_SUMMARY}"
  fi
fi

# Inject project DEFINITIONS.md reference
if [ -f "${PLUGIN_ROOT}/DEFINITIONS.md" ]; then
  CONTEXT_PARTS="${CONTEXT_PARTS} SSOT: ${PLUGIN_ROOT}/DEFINITIONS.md"
fi

# Escape for JSON output
ESCAPED_CONTEXT=$(echo "${CONTEXT_PARTS}" | sed 's/"/\\"/g' | tr '\n' ' ')

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "<vibe-agent-context>${ESCAPED_CONTEXT}</vibe-agent-context>"
  }
}
EOF

exit 0
