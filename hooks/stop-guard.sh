#!/usr/bin/env bash
# Vibe-Claude v5.1 — evidence-aware Stop guard.

set -euo pipefail

INPUT=$(cat)

STOP_HOOK_ACTIVE=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    data = {}
print("1" if data.get("stop_hook_active") else "0")
' <<<"${INPUT}")
BACKGROUND_TASKS=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    data = {}
print("1" if data.get("background_tasks") else "0")
' <<<"${INPUT}")
LAST_MSG=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    data = {}
print(str(data.get("last_assistant_message", ""))[:8000])
' <<<"${INPUT}")

# Never create a continuation loop, and do not interrupt a deliberate wait.
if [[ "${STOP_HOOK_ACTIVE}" == "1" || "${BACKGROUND_TASKS}" == "1" ]]; then
  exit 0
fi

# Ordinary conversation does not need execution evidence. Only completion claims do.
if ! grep -qiE '(completed|finished|fixed|implemented|updated|resolved|done|완료|수정했|구현했|업데이트했|해결했)' <<<"${LAST_MSG}"; then
  exit 0
fi

# Require concrete verification language, not a file:line reference by itself.
if grep -qiE '(exit (code|status)|tests? (passed|failed)|[0-9]+ (tests?|checks?) passed|build (passed|succeeded|failed)|lint(ed|ing)? (passed|clean|failed)|typecheck(ed|ing)? (passed|clean|failed)|verified by|검증.*(통과|실패)|테스트.*(통과|실패)|실행 결과)' <<<"${LAST_MSG}"; then
  exit 0
fi

python3 -c '
import json
print(json.dumps({
    "decision": "block",
    "reason": "You claimed completion without concrete execution evidence. Run the relevant test, build, lint, or check and report its result before stopping."
}))
'
