#!/usr/bin/env bash

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_DIR=$(mktemp -d)
trap 'rm -rf "${TMP_DIR}"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

run_stop() {
  printf '%s' "$1" | "${ROOT}/hooks/stop-guard.sh"
}

OUTPUT=$(run_stop '{"stop_hook_active":true,"last_assistant_message":"Done."}')
[[ -z "${OUTPUT}" ]] || fail "active Stop hook should allow without output"

OUTPUT=$(run_stop '{"stop_hook_active":false,"last_assistant_message":"The implementation is completed."}')
python3 -c 'import json,sys; data=json.load(sys.stdin); assert data["decision"] == "block"' <<<"${OUTPUT}" \
  || fail "completion claim without evidence should block"

OUTPUT=$(run_stop '{"stop_hook_active":false,"last_assistant_message":"Implementation completed. 12 tests passed."}')
[[ -z "${OUTPUT}" ]] || fail "completion claim with evidence should allow"

OUTPUT=$(run_stop '{"stop_hook_active":false,"last_assistant_message":"Here is an explanation of the design."}')
[[ -z "${OUTPUT}" ]] || fail "ordinary conversation should allow"

VALID_PY="${TMP_DIR}/it's-valid.py"
printf 'answer = 42\n' >"${VALID_PY}"
OUTPUT=$(python3 -c 'import json,sys; print(json.dumps({"tool_input":{"file_path":sys.argv[1]}}))' "${VALID_PY}" | "${ROOT}/hooks/post-edit.sh")
[[ -z "${OUTPUT}" ]] || fail "valid quoted path should pass"

INVALID_PY="${TMP_DIR}/invalid.py"
printf 'if True print("broken")\n' >"${INVALID_PY}"
OUTPUT=$(python3 -c 'import json,sys; print(json.dumps({"tool_input":{"file_path":sys.argv[1]}}))' "${INVALID_PY}" | "${ROOT}/hooks/post-edit.sh")
python3 -c 'import json,sys; data=json.load(sys.stdin); assert data["decision"] == "block" and "Syntax check failed" in data["reason"]' <<<"${OUTPUT}" \
  || fail "invalid Python should return structured feedback"

printf 'All hook tests passed.\n'
