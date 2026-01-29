#!/bin/bash

# Vibe-Claude Auto-Update Script
# Runs silently every 2 days to keep system updated

set -Eeuo pipefail
IFS=$'\n\t'

REPO="kks0488/vibe-claude"
INSTALL_DIR="$HOME/.claude"
VERSION_FILE="$INSTALL_DIR/.vibe-version.json"
LOG_FILE="$INSTALL_DIR/.vibe-update.log"

log() {
    mkdir -p "$INSTALL_DIR" >/dev/null 2>&1 || true
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE" 2>/dev/null || echo "[$(date -Iseconds)] $1" >&2
}

log "=== Auto-update check started ==="

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log "ERROR: Missing required dependency: $cmd"
        exit 1
    fi
}

require_cmd curl
require_cmd git
require_cmd mktemp
require_cmd grep
require_cmd sed
require_cmd cp
require_cmd rm

normalize_version() {
    local v="$1"
    if [[ "$v" =~ ^v[0-9] ]]; then
        echo "${v#v}"
        return
    fi
    echo "$v"
}

get_current_version_raw() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" 2>/dev/null | grep '"version":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "unknown"
    else
        echo "not-installed"
    fi
}

get_latest_version_raw() {
    local tag=""
    tag="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || true)"
    echo "$tag"
}

ROLLBACK_READY=0
ROLLBACK_SNAPSHOT_DIR=""
BACKUP_DIR=""

rollback() {
    [ "${ROLLBACK_READY:-0}" -eq 1 ] || return 0
    [ -n "${ROLLBACK_SNAPSHOT_DIR:-}" ] || return 0

    log "Rolling back partial update..."

    local items=(
        ".claude-plugin"
        "agents"
        "skills"
        "commands"
        "hooks"
        "scripts"
        "assets"
        "CLAUDE.md"
        "DEFINITIONS.md"
        "README.md"
        "LICENSE"
        ".vibe-version.json"
    )

    for item in "${items[@]}"; do
        rm -rf "$INSTALL_DIR/$item" >/dev/null 2>&1 || true
        if [ -e "$ROLLBACK_SNAPSHOT_DIR/$item" ]; then
            cp -R "$ROLLBACK_SNAPSHOT_DIR/$item" "$INSTALL_DIR/" >/dev/null 2>&1 || true
        fi
    done

    log "Rollback complete."
}

on_error() {
    local exit_code=$?
    set +e
    log "ERROR: Update failed (exit ${exit_code})"
    rollback || true
    exit "$exit_code"
}

trap on_error ERR

# Get versions
RAW_CURRENT_VERSION="$(get_current_version_raw)"
CURRENT_VERSION="$(normalize_version "$RAW_CURRENT_VERSION")"
RAW_LATEST_VERSION="$(get_latest_version_raw)"
LATEST_VERSION="$(normalize_version "$RAW_LATEST_VERSION")"

log "Current: $CURRENT_VERSION, Latest: $LATEST_VERSION"

# Check if update needed
if [ -z "$RAW_LATEST_VERSION" ]; then
    log "ERROR: Could not fetch latest version"
    exit 1
fi

if [ "$CURRENT_VERSION" == "$LATEST_VERSION" ]; then
    log "Already up to date"
    exit 0
fi

log "Update available! Updating..."

# Create temp directory
TEMP_DIR="$(mktemp -d)"
trap "rm -rf \"$TEMP_DIR\"" EXIT

# Clone latest
if ! git clone --depth 1 --branch "$RAW_LATEST_VERSION" --single-branch "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" >> "$LOG_FILE" 2>&1; then
    if ! git clone --depth 1 --branch "$LATEST_VERSION" --single-branch "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" >> "$LOG_FILE" 2>&1; then
        log "Tag clone failed; falling back to default branch..."
        git clone --depth 1 "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" >> "$LOG_FILE" 2>&1 || (log "ERROR: Failed to clone repository" && exit 1)
    fi
fi

# Backup user files
BACKUP_DIR="$INSTALL_DIR/.backup-$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"

PRESERVE_FILES=(
    "lessons-learned.md"
    "evolution-log.md"
    ".vibe-version.json"
    "settings.json"
    "settings.local.json"
    ".claude.json"
)

for file in "${PRESERVE_FILES[@]}"; do
    [ -f "$INSTALL_DIR/$file" ] && cp "$INSTALL_DIR/$file" "$BACKUP_DIR/"
done

# Backup custom agents
if [ -d "$INSTALL_DIR/agents" ]; then
    mkdir -p "$BACKUP_DIR/agents"
    cp "$INSTALL_DIR/agents"/*.md "$BACKUP_DIR/agents/" 2>/dev/null || true
fi

# Snapshot current install for rollback (only known vibe-claude items)
ROLLBACK_SNAPSHOT_DIR="$BACKUP_DIR/rollback-snapshot"
mkdir -p "$ROLLBACK_SNAPSHOT_DIR"
for item in .claude-plugin agents skills commands hooks scripts assets CLAUDE.md DEFINITIONS.md README.md LICENSE .vibe-version.json; do
    if [ -e "$INSTALL_DIR/$item" ]; then
        cp -R "$INSTALL_DIR/$item" "$ROLLBACK_SNAPSHOT_DIR/"
    fi
done
ROLLBACK_READY=1

# Copy new files
shopt -s nullglob
for item in "$TEMP_DIR/vibe-claude/"* "$TEMP_DIR/vibe-claude"/.[!.]* "$TEMP_DIR/vibe-claude"/..?*; do
    [ "$(basename "$item")" = ".git" ] && continue
    cp -R "$item" "$INSTALL_DIR/"
done
shopt -u nullglob

# Restore preserved files
for file in "${PRESERVE_FILES[@]}"; do
    [ -f "$BACKUP_DIR/$file" ] && cp "$BACKUP_DIR/$file" "$INSTALL_DIR/"
done

# Merge custom agents
if [ -d "$BACKUP_DIR/agents" ]; then
    for agent in "$BACKUP_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            AGENT_NAME=$(basename "$agent")
            # Only restore if it was a custom agent (not overwritten by update)
            if [ ! -f "$INSTALL_DIR/agents/$AGENT_NAME" ]; then
                cp "$agent" "$INSTALL_DIR/agents/"
            fi
        fi
    done
fi

# Update version file
cat > "$VERSION_FILE" << EOF
{
  "version": "$LATEST_VERSION",
  "installedAt": "$(date -Iseconds)",
  "installMethod": "auto-update",
  "lastCheckAt": "$(date -Iseconds)"
}
EOF

ROLLBACK_READY=0

log "SUCCESS: Updated to $LATEST_VERSION"
log "=== Auto-update completed ==="
