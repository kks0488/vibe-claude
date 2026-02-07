#!/usr/bin/env bash
# Setup hook for vibe-claude v4.1.0
# Runs once when the plugin is loaded

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Ensure .vibe/ directory structure exists
VIBE_DIR="${PLUGIN_ROOT}/.vibe"
mkdir -p "${VIBE_DIR}/memory/lessons" \
         "${VIBE_DIR}/memory/patterns" \
         "${VIBE_DIR}/memory/decisions" \
         "${VIBE_DIR}/memory/context" \
         "${VIBE_DIR}/plans" \
         "${VIBE_DIR}/drafts" \
         "${VIBE_DIR}/notepads" 2>/dev/null || true

# Validate critical files exist
MISSING=""
for f in CLAUDE.md DEFINITIONS.md agents/v-conductor.md skills/vibe/SKILL.md; do
  if [ ! -f "${PLUGIN_ROOT}/${f}" ]; then
    MISSING="${MISSING} ${f}"
  fi
done

# Detect previous session (most recent work document)
LAST_SESSION=""
if ls "${VIBE_DIR}"/work-*.md 1>/dev/null 2>&1; then
  LAST_SESSION=$(ls -t "${VIBE_DIR}"/work-*.md 2>/dev/null | head -1)
fi

# Build setup message
SETUP_MSG="Vibe-Claude v4.1.0 initialized. All 13 agents running Opus 4.6 with project memory."

if [ -n "${MISSING}" ]; then
  SETUP_MSG="${SETUP_MSG} WARNING: Missing files:${MISSING}"
fi

if [ -n "${LAST_SESSION}" ]; then
  SETUP_MSG="${SETUP_MSG} Previous session detected: $(basename "${LAST_SESSION}"). Use /v-continue to resume."
fi

echo "<vibe-setup>${SETUP_MSG}</vibe-setup>"

exit 0
