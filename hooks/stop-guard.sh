#!/usr/bin/env bash
# Vibe-Claude v5.0 — Stop Guard
# Blocks agent from stopping without execution evidence.

set -euo pipefail

INPUT=$(cat)

LAST_MSG=$(echo "${INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    msgs = data.get('messages', [])
    if msgs:
        c = msgs[-1].get('content', '')
        print(c[:3000] if isinstance(c, str) else str(c)[:3000])
except:
    print('')
" 2>/dev/null || echo "")

ALLOW=0

# User cancelled or just chatting
echo "${LAST_MSG}" | grep -qiE "cancel|force.stop" && ALLOW=1

# Actual execution evidence
echo "${LAST_MSG}" | grep -qiE "(exit code|passed|failed.*0|PASS|Result:|Output:)" && ALLOW=1

# File:line references (proof of specific work)
echo "${LAST_MSG}" | grep -qiE "[a-zA-Z_/]+\.[a-z]+:[0-9]+" && ALLOW=1

if [ "${ALLOW}" -eq 1 ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"allow","reason":"Evidence found."}}'
  exit 0
else
  echo '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"No execution evidence. Run the code, show the output, then stop."}}'
  exit 2
fi
