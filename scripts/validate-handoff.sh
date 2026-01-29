#!/usr/bin/env bash
# Validate HANDOFF REQUEST protocol consistency across agents.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: Missing required dependency: $cmd" >&2
    exit 1
  fi
}

require_cmd python3

VIBE_ROOT="$ROOT_DIR" python3 - <<'PY'
import os
import re
import sys
from pathlib import Path

root = Path(os.environ["VIBE_ROOT"]).resolve()
agents_dir = root / "agents"

agent_files = sorted(agents_dir.glob("v-*.md"))
known_agents = {p.stem for p in agent_files}  # e.g. "v-worker"

errors: list[str] = []

def fail(msg: str) -> None:
    errors.append(msg)

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"{path}: not valid UTF-8")
        return ""

for path in agent_files:
    text = read_text(path)
    if not text:
        continue

    name_match = re.search(r"(?m)^name:\s*(v-[a-z0-9-]+)\s*$", text)
    if not name_match:
        fail(f"{path}: missing frontmatter 'name: v-...'")
        continue
    agent_name = name_match.group(1)

    if agent_name == "v-conductor":
        if "[HANDOFF REQUEST:" not in text:
            fail(f"{path}: missing HANDOFF REQUEST reference")
        if "Task(" not in text:
            fail(f"{path}: missing Task(...) usage for routing")
        if "핸드오프 라우팅 절차" not in text and "Handoff" not in text:
            fail(f"{path}: missing explicit handoff routing procedure")
        continue

    if "## 🔴 Handoff Requests" not in text:
        fail(f"{path}: missing '## 🔴 Handoff Requests' section")
        continue

    expected_from = f"From: {agent_name}"
    if expected_from not in text:
        fail(f"{path}: missing handoff template line '{expected_from}'")

    typ_idx = text.find("Typical handoffs:")
    if typ_idx == -1:
        fail(f"{path}: missing 'Typical handoffs:' list")
        continue

    recipients: list[str] = []
    after_lines = text[typ_idx:].splitlines()[1:]
    for line in after_lines:
        if not line.strip():
            break
        if line.startswith("## "):
            break
        m = re.match(r"-\s+`?(v-[a-z0-9-]+)`?\s+—", line)
        if m:
            recipients.append(m.group(1))

    if not recipients:
        fail(f"{path}: could not parse any recipients under 'Typical handoffs:'")
        continue

    for recipient in recipients:
        if recipient not in known_agents:
            fail(f"{path}: Typical handoff recipient '{recipient}' has no matching file in agents/")

if errors:
    print("HANDOFF VALIDATION FAILED:\n", file=sys.stderr)
    for e in errors:
        print(f"- {e}", file=sys.stderr)
    sys.exit(1)

print("HANDOFF VALIDATION OK")
PY
