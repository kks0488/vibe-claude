#!/usr/bin/env bash
# E2E workflow simulation test for vibe-claude.
#
# Validates:
#   - Phase routing (TRIVIAL/SIMPLE/MODERATE/COMPLEX)
#   - Handoff chain (agent A -> v-conductor -> agent B)
#   - Command-to-skill mapping (/vibe, /v-plan, /v-debug, ...)
#   - Edge cases: unknown target, malformed request, circular handoff

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
NC=$'\033[0m'

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "${RED}ERROR:${NC} Missing required dependency: ${cmd}" >&2
    exit 1
  fi
}

pass() { echo "${GREEN}PASS${NC} $*"; }
fail() { echo "${RED}FAIL${NC} $*" >&2; }
note() { echo "${YELLOW}==>${NC} $*"; }

run_test() {
  local name="$1"
  shift

  note "$name"

  set +e
  "$@"
  local status=$?
  set -e

  if [ "$status" -eq 0 ]; then
    pass "$name"
    return 0
  fi

  fail "$name"
  return 1
}

test_phase_routing() {
  VIBE_ROOT="$ROOT_DIR" python3 - <<'PY'
import os
import re
import sys
from pathlib import Path

root = Path(os.environ["VIBE_ROOT"]).resolve()

definitions = root / "DEFINITIONS.md"
conductor = root / "agents" / "v-conductor.md"
readme = root / "README.md"
claude_md = root / "CLAUDE.md"
vibe_skill = root / "skills" / "vibe" / "SKILL.md"

expected = {
    "TRIVIAL": "P3 only",
    "SIMPLE": "P1→P3→P4",
    "MODERATE": "P1→P3→P4",
    "COMPLEX": "P0.5→P1→P2→P3→P4→P5",
}

errors: list[str] = []

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{path}: failed to read ({e})")
        return ""

def parse_definitions_complexity_routes(text: str) -> dict[str, str]:
    routes: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## Complexity Routing":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        m = re.match(r"^\|\s*(TRIVIAL|SIMPLE|MODERATE|COMPLEX)\s*\|\s*[^|]*\|\s*([^|]+?)\s*\|\s*$", line)
        if m:
            routes[m.group(1)] = m.group(2).strip()
    return routes

definitions_text = read_text(definitions)
routes = parse_definitions_complexity_routes(definitions_text)

missing = [k for k in expected.keys() if k not in routes]
if missing:
    errors.append(f"{definitions}: missing routing rows for: {', '.join(missing)}")
else:
    for k, v in expected.items():
        if routes.get(k) != v:
            errors.append(f"{definitions}: {k} route mismatch (expected '{v}', got '{routes.get(k)}')")

def assert_file_contains_routes(path: Path, text: str) -> None:
    for level, route in expected.items():
        ok = any(level in line and route in line for line in text.splitlines())
        if not ok:
            errors.append(f"{path}: missing '{level}' routing line containing '{route}'")

assert_file_contains_routes(conductor, read_text(conductor))
assert_file_contains_routes(readme, read_text(readme))
assert_file_contains_routes(claude_md, read_text(claude_md))
assert_file_contains_routes(vibe_skill, read_text(vibe_skill))

if errors:
    print("PHASE ROUTING VALIDATION FAILED:\n", file=sys.stderr)
    for e in errors:
        print(f"- {e}", file=sys.stderr)
    sys.exit(1)

print("PHASE ROUTING OK")
PY
}

test_command_skill_mapping() {
  VIBE_ROOT="$ROOT_DIR" python3 - <<'PY'
import os
import re
import sys
from pathlib import Path

root = Path(os.environ["VIBE_ROOT"]).resolve()
commands_dir = root / "commands"
skills_dir = root / "skills"
session_start = root / "hooks" / "session-start.sh"
claude_md = root / "CLAUDE.md"

errors: list[str] = []

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{path}: failed to read ({e})")
        return ""

session_start_text = read_text(session_start)
claude_md_text = read_text(claude_md)

command_files = sorted(commands_dir.glob("*.md"))
if not command_files:
    errors.append(f"{commands_dir}: no command files found")

for cmd_path in command_files:
    cmd_name = cmd_path.stem  # e.g. "v-plan"
    cmd_text = read_text(cmd_path)

    if "disable-model-invocation: true" not in cmd_text:
        errors.append(f"{cmd_path}: missing frontmatter 'disable-model-invocation: true'")

    m = re.search(r"Invoke the vibe-claude:([a-z0-9-]+) skill", cmd_text)
    if not m:
        errors.append(f"{cmd_path}: missing mapping line 'Invoke the vibe-claude:<skill> skill'")
        continue

    skill_name = m.group(1)
    if skill_name != cmd_name:
        errors.append(f"{cmd_path}: command '{cmd_name}' maps to skill '{skill_name}' (expected same name)")

    skill_path = skills_dir / skill_name / "SKILL.md"
    if not skill_path.exists():
        errors.append(f"{cmd_path}: mapped skill missing: {skill_path}")
        continue

    skill_text = read_text(skill_path)
    name_match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", skill_text)
    if not name_match:
        errors.append(f"{skill_path}: missing frontmatter 'name: ...'")
    elif name_match.group(1) != skill_name:
        errors.append(f"{skill_path}: frontmatter name mismatch (expected '{skill_name}', got '{name_match.group(1)}')")

    slash = f"/{cmd_name}"
    if slash not in session_start_text:
        errors.append(f"{session_start}: missing '{slash}' in SessionStart quick reference/context")
    if slash not in claude_md_text:
        errors.append(f"{claude_md}: missing '{slash}' in Slash Commands table")

if errors:
    print("COMMAND/SKILL MAPPING VALIDATION FAILED:\n", file=sys.stderr)
    for e in errors:
        print(f"- {e}", file=sys.stderr)
    sys.exit(1)

print("COMMAND/SKILL MAPPING OK")
PY
}

test_handoff_chain_and_edge_cases() {
  VIBE_ROOT="$ROOT_DIR" python3 - <<'PY'
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple
from pathlib import Path

root = Path(os.environ["VIBE_ROOT"]).resolve()
agents_dir = root / "agents"
conductor_path = agents_dir / "v-conductor.md"

agent_a = "v-analyst"
agent_b = "v-worker"

known_agents: Set[str] = {p.stem for p in agents_dir.glob("v-*.md")}

errors: List[str] = []

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{path}: failed to read ({e})")
        return ""

conductor_text = read_text(conductor_path)

if "HANDOFF REQUEST" not in conductor_text:
    errors.append(f"{conductor_path}: missing 'HANDOFF REQUEST' reference")
if "Task(" not in conductor_text:
    errors.append(f"{conductor_path}: missing Task(...) usage (needed for orchestration)")

# Ensure v-conductor explicitly documents required edge cases + tribunal routing (E2E contract).
required_doc_snippets = [
    "Handoff Edge Cases",
    "circular",
    "malformed",
    "unknown target",
    "Tribunal",
    "APPROVED",
    "REVISE",
    "REJECT",
    "v-worker",
    "v-planner",
]
for snippet in required_doc_snippets:
    if snippet not in conductor_text:
        errors.append(f"{conductor_path}: missing required snippet '{snippet}' (E2E contract)")

agent_a_path = agents_dir / f"{agent_a}.md"
agent_b_path = agents_dir / f"{agent_b}.md"

if not agent_a_path.exists():
    errors.append(f"missing agent A file: {agent_a_path}")
if not agent_b_path.exists():
    errors.append(f"missing agent B file: {agent_b_path}")

agent_a_text = read_text(agent_a_path)
if f"From: {agent_a}" not in agent_a_text:
    errors.append(f"{agent_a_path}: missing handoff template line 'From: {agent_a}'")
if re.search(r"(?m)^Typical handoffs:\s*$", agent_a_text) is None:
    errors.append(f"{agent_a_path}: missing 'Typical handoffs:' list")
if re.search(r"(?m)^-\s+`?v-worker`?\s+—", agent_a_text) is None:
    errors.append(f"{agent_a_path}: missing typical handoff recipient 'v-worker'")

@dataclass(frozen=True)
class ParsedHandoff:
    target: str
    sender: Optional[str]

def parse_handoff(text: str) -> Optional[ParsedHandoff]:
    m_target = re.search(r"(?m)^\[HANDOFF REQUEST:\s*(v-[a-z0-9-]+)\s*\]\s*$", text)
    if not m_target:
        return None
    m_sender = re.search(r"(?m)^From:\s*(v-[a-z0-9-]+)\s*$", text)
    sender = m_sender.group(1) if m_sender else None
    return ParsedHandoff(target=m_target.group(1), sender=sender)

def choose_fallback_agent(payload: str) -> str:
    lowered = payload.lower()
    if any(k in lowered for k in ["ui", "ux", "style", "layout", "css"]):
        return "v-designer"
    if any(k in lowered for k in ["find", "locate", "search", "grep"]):
        return "v-finder"
    if any(k in lowered for k in ["plan", "architecture", "strategy"]):
        return "v-planner"
    if any(k in lowered for k in ["review", "critique", "quality"]):
        return "v-critic"
    if any(k in lowered for k in ["test", "pytest", "jest", "vitest"]):
        return "v-tester"
    if any(k in lowered for k in ["implement", "code", "fix", "build"]):
        return "v-worker"
    return "v-analyst"

def simulate_conductor_decision(handoff_text: str, chain: List[Tuple[str, str]]) -> Tuple[str, str]:
    parsed = parse_handoff(handoff_text)
    if not parsed:
        return ("MALFORMED", "v-analyst")

    sender = parsed.sender
    if sender is None or sender not in known_agents:
        return ("UNKNOWN_SENDER", "v-analyst")

    target = parsed.target
    if target not in known_agents:
        return ("UNKNOWN_TARGET", choose_fallback_agent(handoff_text))

    # Circular detection:
    visited = set()
    for a, b in chain:
        visited.add(a)
        visited.add(b)
    if target in visited or (sender, target) in chain or sender == target:
        return ("CIRCULAR", "v-analyst")

    return ("DELEGATE", target)

# 1) Happy-path chain: v-analyst -> v-conductor -> v-worker
happy = f"""[HANDOFF REQUEST: {agent_b}]
From: {agent_a}
Reason: blocked on implementation details
Context:
- File: scripts/validate-handoff.sh:1
- Evidence: n/a
Suggested task: implement the required fix
"""

status, delegate = simulate_conductor_decision(happy, chain=[])
if status != "DELEGATE" or delegate != agent_b:
    errors.append(f"E2E happy-path handoff: expected DELEGATE->{agent_b}, got {status}->{delegate}")

# 2) Unknown target should not crash; must fallback deterministically to a real agent.
unknown_target = """[HANDOFF REQUEST: v-ghost]
From: v-analyst
Reason: UI rendering issue
Context:
- File: README.md:1
Suggested task: adjust UI styling
"""
status, delegate = simulate_conductor_decision(unknown_target, chain=[])
if status != "UNKNOWN_TARGET":
    errors.append(f"E2E unknown-target: expected status UNKNOWN_TARGET, got {status}")
if delegate not in known_agents:
    errors.append(f"E2E unknown-target: fallback agent '{delegate}' is not a known agent")

# 3) Malformed handoff must be detected.
malformed = """HANDOFF REQUEST: v-worker
From v-analyst
Reason: missing brackets and colon
"""
status, delegate = simulate_conductor_decision(malformed, chain=[])
if status != "MALFORMED":
    errors.append(f"E2E malformed: expected status MALFORMED, got {status}")
if delegate != "v-analyst":
    errors.append(f"E2E malformed: expected fallback 'v-analyst', got '{delegate}'")

# 4) Circular handoff must be detected and broken.
circular = """[HANDOFF REQUEST: v-analyst]
From: v-worker
Reason: needs analysis again
Context:
- File: agents/v-worker.md:1
Suggested task: analyze why I'm blocked
"""
chain = [("v-analyst", "v-worker")]
status, delegate = simulate_conductor_decision(circular, chain=chain)
if status != "CIRCULAR":
    errors.append(f"E2E circular: expected status CIRCULAR, got {status}")
if delegate != "v-analyst":
    errors.append(f"E2E circular: expected escalation 'v-analyst', got '{delegate}'")

if errors:
    print("HANDOFF E2E VALIDATION FAILED:\n", file=sys.stderr)
    for e in errors:
        print(f"- {e}", file=sys.stderr)
    sys.exit(1)

print("HANDOFF E2E OK")
PY
}

main() {
  require_cmd python3

  local failures=0

  if ! run_test "Phase routing" test_phase_routing; then failures=$((failures+1)); fi
  if ! run_test "Command-to-skill mapping" test_command_skill_mapping; then failures=$((failures+1)); fi
  if ! run_test "Handoff workflow + edge cases" test_handoff_chain_and_edge_cases; then failures=$((failures+1)); fi

  echo ""
  if [ "$failures" -ne 0 ]; then
    echo "${RED}E2E WORKFLOW TEST FAILED${NC} (${failures} failing section(s))" >&2
    exit 1
  fi

  echo "${GREEN}E2E WORKFLOW TEST OK${NC}"
}

main "$@"
