#!/usr/bin/env bash
# Vibe-Claude v5.1 — lightweight PostToolUse syntax check.

set -euo pipefail

INPUT=$(cat)
FILE=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    data = {}
tool_input = data.get("tool_input", data.get("toolInput", {}))
print(tool_input.get("file_path", data.get("file_path", "")))
' <<<"${INPUT}")

[[ -z "${FILE}" || ! -f "${FILE}" ]] && exit 0

EXT=${FILE##*.}
STATUS=0
ERROR=""

set +e
case "${EXT}" in
  py)
    ERROR=$(python3 -c 'import ast, pathlib, sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' "${FILE}" 2>&1)
    STATUS=$?
    ;;
  js|mjs|cjs)
    if command -v node >/dev/null 2>&1; then
      ERROR=$(node --check "${FILE}" 2>&1)
      STATUS=$?
    fi
    ;;
  json)
    ERROR=$(python3 -c 'import json, pathlib, sys; json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' "${FILE}" 2>&1)
    STATUS=$?
    ;;
  yaml|yml)
    if python3 -c 'import yaml' >/dev/null 2>&1; then
      ERROR=$(python3 -c 'import pathlib, sys, yaml; yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' "${FILE}" 2>&1)
      STATUS=$?
    fi
    ;;
  sh|bash)
    ERROR=$(bash -n "${FILE}" 2>&1)
    STATUS=$?
    ;;
esac
set -e

if [[ "${STATUS}" -ne 0 ]]; then
  [[ -n "${ERROR}" ]] || ERROR="syntax checker exited with status ${STATUS}"
  python3 -c '
import json, sys
print(json.dumps({
    "decision": "block",
    "reason": f"Syntax check failed for {sys.argv[1]}:\n{sys.argv[2][:4000]}"
}))
' "${FILE}" "${ERROR}"
fi
