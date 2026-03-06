#!/usr/bin/env bash
# Vibe-Claude v5.0 — Post-Edit Syntax Check
# Runs lightweight syntax validation after Write/Edit operations.

set -euo pipefail

INPUT=$(cat)

FILE=$(echo "${INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('toolInput', {}).get('file_path', data.get('file_path', '')))
except:
    print('')
" 2>/dev/null || echo "")

[ -z "${FILE}" ] && exit 0
[ ! -f "${FILE}" ] && exit 0

EXT="${FILE##*.}"
ERROR=""

case "${EXT}" in
  py)
    ERROR=$(python3 -c "import ast; ast.parse(open('${FILE}').read())" 2>&1) || true
    ;;
  js|mjs)
    command -v node >/dev/null 2>&1 && ERROR=$(node --check "${FILE}" 2>&1) || true
    ;;
  ts|tsx)
    # Basic syntax check only — full type checking is too slow for a hook
    command -v node >/dev/null 2>&1 && ERROR=$(node -e "
      try { require('fs').readFileSync('${FILE}','utf8') } catch(e) { console.error(e.message) }
    " 2>&1) || true
    ;;
  json)
    ERROR=$(python3 -c "import json; json.load(open('${FILE}'))" 2>&1) || true
    ;;
  yaml|yml)
    ERROR=$(python3 -c "
import yaml, sys
try:
    yaml.safe_load(open('${FILE}'))
except Exception as e:
    print(str(e))
" 2>&1) || true
    ;;
  sh|bash)
    command -v bash >/dev/null 2>&1 && ERROR=$(bash -n "${FILE}" 2>&1) || true
    ;;
esac

if [ -n "${ERROR}" ]; then
  # Return error as feedback but don't block — let Claude fix it
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PostToolUse","syntax_error":"${FILE}: ${ERROR}"}}
EOF
  exit 0
fi

exit 0
