#!/usr/bin/env bash
# PostToolUse hook for vibe-claude v4.1.0
# Runs after Write|Edit to perform basic syntax/lint checks

set -euo pipefail

INPUT=$(cat)

# Extract the file path from the tool use
FILE_PATH=$(echo "${INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Try multiple possible field names
    path = data.get('file_path', data.get('filePath', data.get('path', '')))
    print(path)
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "${FILE_PATH}" ] || [ ! -f "${FILE_PATH}" ]; then
  # No file or file doesn't exist, skip check
  exit 0
fi

# Determine file type and run appropriate check
EXT="${FILE_PATH##*.}"
ERRORS=""

case "${EXT}" in
  ts|tsx)
    # TypeScript syntax check (if npx available)
    if command -v npx &>/dev/null; then
      ERRORS=$(npx --yes tsc --noEmit --pretty "${FILE_PATH}" 2>&1 | head -20) || true
    fi
    ;;
  js|jsx|mjs)
    # JavaScript syntax check with node
    if command -v node &>/dev/null; then
      ERRORS=$(node --check "${FILE_PATH}" 2>&1) || true
    fi
    ;;
  py)
    # Python syntax check
    if command -v python3 &>/dev/null; then
      ERRORS=$(python3 -m py_compile "${FILE_PATH}" 2>&1) || true
    fi
    ;;
  json)
    # JSON validity
    if command -v python3 &>/dev/null; then
      ERRORS=$(python3 -c "import json; json.load(open('${FILE_PATH}'))" 2>&1) || true
    fi
    ;;
  sh|bash)
    # Shell script syntax
    if command -v bash &>/dev/null; then
      ERRORS=$(bash -n "${FILE_PATH}" 2>&1) || true
    fi
    ;;
  *)
    # No check for unknown extensions
    exit 0
    ;;
esac

if [ -n "${ERRORS}" ] && [ "${ERRORS}" != "" ]; then
  # Escape for JSON
  ESCAPED_ERRORS=$(echo "${ERRORS}" | head -10 | tr '\n' ' ' | sed 's/"/\\"/g')
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "<vibe-lint-warning>Syntax issues detected in ${FILE_PATH}: ${ESCAPED_ERRORS}</vibe-lint-warning>"
  }
}
EOF
else
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "<vibe-lint-ok>${FILE_PATH} syntax check passed.</vibe-lint-ok>"
  }
}
EOF
fi

exit 0
