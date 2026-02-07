#!/usr/bin/env bash
# TeammateIdle hook for vibe-claude v4.1.0
# Prevents teammate from going idle with incomplete work

set -euo pipefail

# Read the hook input from stdin
INPUT=$(cat)

# Extract agent name if available
AGENT_NAME=$(echo "${INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('agentName', 'unknown'))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")

# Check for incomplete work documents
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
VIBE_DIR="${PLUGIN_ROOT}/.vibe"

INCOMPLETE=0
if ls "${VIBE_DIR}"/work-*.md 1>/dev/null 2>&1; then
  LATEST_WORK=$(ls -t "${VIBE_DIR}"/work-*.md 2>/dev/null | head -1)
  if [ -f "${LATEST_WORK}" ]; then
    # Check for unchecked boxes
    UNCHECKED=$(grep -c '^\- \[ \]' "${LATEST_WORK}" 2>/dev/null || echo "0")
    if [ "${UNCHECKED}" -gt 0 ]; then
      INCOMPLETE=1
    fi
  fi
fi

if [ "${INCOMPLETE}" -eq 1 ]; then
  # Output decision to continue work
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "TeammateIdle",
    "decision": "continue",
    "reason": "Agent ${AGENT_NAME} has ${UNCHECKED} incomplete tasks in work document. Continue working."
  }
}
EOF
  exit 2  # exit 2 = force continue
else
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "TeammateIdle",
    "decision": "allow_idle",
    "reason": "No incomplete work detected for ${AGENT_NAME}."
  }
}
EOF
  exit 0
fi
