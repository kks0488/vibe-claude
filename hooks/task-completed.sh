#!/usr/bin/env bash
# TaskCompleted hook for vibe-claude v4.1.0
# Validates completion proof exists before allowing task to close

set -euo pipefail

INPUT=$(cat)

# Extract task output/context
TASK_OUTPUT=$(echo "${INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('output', data.get('taskOutput', '')))
except:
    print('')
" 2>/dev/null || echo "")

# Check for COMPLETION PROOF markers
HAS_PROOF=0
if echo "${TASK_OUTPUT}" | grep -qi "COMPLETION PROOF\|✓ Executed\|✓ Tests\|VERDICT.*APPROVED\|TRIBUNAL.*APPROVED"; then
  HAS_PROOF=1
fi

if [ "${HAS_PROOF}" -eq 1 ]; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "TaskCompleted",
    "validated": true,
    "reason": "Completion proof found in task output."
  }
}
EOF
  exit 0
else
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "TaskCompleted",
    "validated": false,
    "reason": "No COMPLETION PROOF found. Task must include evidence of execution, test results, or tribunal approval before completion."
  }
}
EOF
  exit 2  # exit 2 = reject completion, force continue
fi
