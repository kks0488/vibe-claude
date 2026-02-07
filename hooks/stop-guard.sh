#!/usr/bin/env bash
# Stop hook for vibe-claude v4.1.0
# "NEVER STOP UNTIL PROVEN DONE" — enforced by hook
# If no completion proof is found in the conversation, prevents stop

set -euo pipefail

INPUT=$(cat)

# Extract the stop reason / last message context
STOP_CONTEXT=$(echo "${INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Get the last assistant message or stop reason
    messages = data.get('messages', [])
    if messages:
        last = messages[-1].get('content', '')
        print(last[:2000] if isinstance(last, str) else str(last)[:2000])
    else:
        print(data.get('reason', ''))
except:
    print('')
" 2>/dev/null || echo "")

# Check if completion proof exists
HAS_PROOF=0
if echo "${STOP_CONTEXT}" | grep -qi "COMPLETION PROOF\|✓ Executed.*Output\|✓ Tests.*Result\|VERDICT.*APPROVED\|all.*complete\|cancel-vibe\|CANCELLED"; then
  HAS_PROOF=1
fi

# Check if user explicitly cancelled
IS_CANCEL=0
if echo "${STOP_CONTEXT}" | grep -qi "cancel-vibe\|CANCELLED\|force.stop"; then
  IS_CANCEL=1
fi

if [ "${HAS_PROOF}" -eq 1 ] || [ "${IS_CANCEL}" -eq 1 ]; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "decision": "allow",
    "reason": "Completion proof found or user cancelled."
  }
}
EOF
  exit 0
else
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "decision": "block",
    "reason": "No COMPLETION PROOF found. Continue working until all tasks are proven complete. Forbidden: 'I think it's done', 'Should work', 'Looks correct'."
  }
}
EOF
  exit 2  # exit 2 = block stop, force continue
fi
