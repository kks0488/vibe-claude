#!/usr/bin/env bash
# End-to-end simulation test for vibe-claude orchestration protocol.
#
# This does NOT run Claude Code. It validates that:
# - Commands map to existing skills (so /vibe works out of the box)
# - HANDOFF REQUEST blocks are parseable and routable
# - The canonical chain v-finder → v-analyst → v-worker → v-critic is supported
# - Edge cases (missing agent, malformed handoff, circular handoffs) are handled

set -euo pipefail
IFS=$'\n\t'

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
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

root = Path(os.environ["VIBE_ROOT"]).resolve()

agents_dir = root / "agents"
skills_dir = root / "skills"
commands_dir = root / "commands"

agent_files = sorted(agents_dir.glob("v-*.md"))
known_agents = {p.stem for p in agent_files}  # e.g. "v-worker"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_commands_map_to_skills() -> None:
    cmd_files = sorted(commands_dir.glob("*.md"))
    assert_true(bool(cmd_files), "No command definitions found in commands/")

    for cmd in cmd_files:
        text = read_text(cmd)
        m = re.search(r"Invoke the vibe-claude:([a-z0-9-]+) skill", text)
        assert_true(bool(m), f"{cmd}: missing 'Invoke the vibe-claude:<skill> skill' line")
        skill = m.group(1)
        skill_path = skills_dir / skill / "SKILL.md"
        assert_true(skill_path.exists(), f"{cmd}: refers to missing skill: skills/{skill}/SKILL.md")


HANDOFF_RE = re.compile(r"(?m)^\[HANDOFF REQUEST:\s*(v-[a-z0-9-]+)\]\s*$")
FROM_RE = re.compile(r"(?m)^From:\s*(v-[a-z0-9-]+)\s*$")
REASON_RE = re.compile(r"(?m)^Reason:\s*(.+?)\s*$")
SUGGESTED_RE = re.compile(r"(?m)^Suggested task:\s*(.+?)\s*$")


class Handoff:
    def __init__(self, target: str, sender: str, reason: str, suggested: str) -> None:
        self.target = target
        self.sender = sender
        self.reason = reason
        self.suggested = suggested


def parse_handoff(text: str) -> Handoff | None:
    m = HANDOFF_RE.search(text)
    if not m:
        return None
    target = m.group(1)

    sender_m = FROM_RE.search(text)
    reason_m = REASON_RE.search(text)
    suggested_m = SUGGESTED_RE.search(text)

    if not sender_m or not reason_m or not suggested_m:
        raise ValueError("Malformed HANDOFF REQUEST: missing From/Reason/Suggested task")

    return Handoff(
        target=target,
        sender=sender_m.group(1),
        reason=reason_m.group(1).strip(),
        suggested=suggested_m.group(1).strip(),
    )


def route_handoff(output: str, history: list[tuple[str, str, str]]) -> str | None:
    # v-critic tribunal outcomes:
    if re.search(r"(?m)^##\s+Verdict:\s+REVISE\b", output) or "VERDICT: REVISE" in output:
        return "v-worker"
    if re.search(r"(?m)^##\s+Verdict:\s+REJECT\b", output) or "VERDICT: REJECT" in output:
        return "v-planner"

    handoff = parse_handoff(output)
    if not handoff:
        return None

    key = (handoff.sender, handoff.target, handoff.reason)
    if key in history:
        raise RuntimeError(f"Circular handoff detected: {key}")
    history.append(key)

    # Missing target agent fallback: v-analyst (safe default)
    if handoff.target not in known_agents:
        return "v-analyst"

    return handoff.target


def test_happy_path_chain() -> None:
    outputs: dict[str, str] = {
        "v-finder": """## Found: 2 matches

[HANDOFF REQUEST: v-analyst]
From: v-finder
Reason: Found likely root-cause locations; needs analysis.
Context:
- Files: src/auth/login.ts:45, src/auth/session.ts:12
- Evidence: rg \"login|session\" → 2 files, 5 matches
Suggested task: Determine root cause and propose minimal fix.
""",
        "v-analyst": """## Investigation Summary
Root cause is in login validation flow.

[HANDOFF REQUEST: v-worker]
From: v-analyst
Reason: Root cause identified; needs implementation.
Context:
- File: src/auth/login.ts:45
- Evidence: Repro via unit test failure (see logs)
Suggested task: Implement minimal fix and keep behavior consistent.
""",
        "v-worker": """## Completed
Implemented fix.

[HANDOFF REQUEST: v-critic]
From: v-worker
Reason: Implementation complete; needs tribunal review.
Context:
- File: src/auth/login.ts:45
- Evidence: tests pass locally
Suggested task: Review for correctness, completeness, and consistency.
""",
        "v-critic": """## Review Summary
All criteria met.

## Verdict: APPROVED
""",
    }

    history: list[tuple[str, str, str]] = []

    nxt = route_handoff(outputs["v-finder"], history)
    assert_true(nxt == "v-analyst", f"Expected v-finder → v-analyst, got {nxt!r}")

    nxt = route_handoff(outputs["v-analyst"], history)
    assert_true(nxt == "v-worker", f"Expected v-analyst → v-worker, got {nxt!r}")

    nxt = route_handoff(outputs["v-worker"], history)
    assert_true(nxt == "v-critic", f"Expected v-worker → v-critic, got {nxt!r}")

    nxt = route_handoff(outputs["v-critic"], history)
    assert_true(nxt is None, f"Expected v-critic to end chain, got {nxt!r}")


def test_missing_target_agent_fallback() -> None:
    history: list[tuple[str, str, str]] = []
    out = """[HANDOFF REQUEST: v-does-not-exist]
From: v-worker
Reason: Need a specialist that doesn't exist.
Context:
- File: foo:1
- Evidence: n/a
Suggested task: do something.
"""
    nxt = route_handoff(out, history)
    assert_true(nxt == "v-analyst", f"Expected missing target → v-analyst fallback, got {nxt!r}")


def test_malformed_handoff_is_rejected() -> None:
    history: list[tuple[str, str, str]] = []
    out = """[HANDOFF REQUEST: v-analyst]
From: v-worker
Context:
- File: foo:1
Suggested task: missing Reason line.
"""
    try:
        route_handoff(out, history)
    except ValueError:
        return
    raise AssertionError("Expected malformed handoff to raise ValueError")


def test_circular_handoff_detection() -> None:
    history: list[tuple[str, str, str]] = []

    out1 = """[HANDOFF REQUEST: v-analyst]
From: v-worker
Reason: Blocked; need analysis.
Context:
- File: foo:1
- Evidence: n/a
Suggested task: Analyze the issue.
"""
    out2 = """[HANDOFF REQUEST: v-worker]
From: v-analyst
Reason: Needs implementation.
Context:
- File: foo:1
- Evidence: n/a
Suggested task: Implement the fix.
"""
    out3 = """[HANDOFF REQUEST: v-analyst]
From: v-worker
Reason: Blocked; need analysis.
Context:
- File: foo:1
- Evidence: n/a
Suggested task: Analyze the issue.
"""

    route_handoff(out1, history)
    route_handoff(out2, history)
    try:
        route_handoff(out3, history)
    except RuntimeError:
        return
    raise AssertionError("Expected circular handoff detection to raise RuntimeError")

def test_critic_verdict_routing() -> None:
    history: list[tuple[str, str, str]] = []

    revise_out = """## Review Summary
Issues found.

## Verdict: REVISE
"""
    nxt = route_handoff(revise_out, history)
    assert_true(nxt == "v-worker", f"Expected REVISE → v-worker, got {nxt!r}")

    reject_out = """## Review Summary
Fundamental issues.

VERDICT: REJECT
"""
    nxt = route_handoff(reject_out, history)
    assert_true(nxt == "v-planner", f"Expected REJECT → v-planner, got {nxt!r}")


def main() -> None:
    test_commands_map_to_skills()
    test_happy_path_chain()
    test_missing_target_agent_fallback()
    test_malformed_handoff_is_rejected()
    test_circular_handoff_detection()
    test_critic_verdict_routing()
    print("E2E WORKFLOW TEST OK")


if __name__ == "__main__":
    main()
PY
