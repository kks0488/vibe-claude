#!/bin/bash

# Vibe-Claude Installer/Updater
# https://github.com/kks0488/vibe-claude

set -Eeuo pipefail
IFS=$'\n\t'

REPO="kks0488/vibe-claude"
INSTALL_DIR="$HOME/.claude"
TEMP_DIR="$(mktemp -d)"
VERSION_FILE="$INSTALL_DIR/.vibe-version.json"

echo "================================"
echo "  Vibe-Claude Installer"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: Missing required dependency: ${cmd}${NC}" >&2
        exit 1
    fi
}

die() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    exit 1
}

cleanup() {
    rm -rf "$TEMP_DIR" >/dev/null 2>&1 || true
}

ROLLBACK_READY=0
ROLLBACK_SNAPSHOT_DIR=""

rollback() {
    [ "${ROLLBACK_READY:-0}" -eq 1 ] || return 0
    [ -n "${ROLLBACK_SNAPSHOT_DIR:-}" ] || return 0

    echo -e "${YELLOW}Rolling back partial install...${NC}" >&2

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

    echo -e "${YELLOW}Rollback complete.${NC}" >&2
}

on_error() {
    local exit_code=$?
    set +e
    echo -e "${RED}Install failed (exit ${exit_code}).${NC}" >&2
    rollback || true
    exit "$exit_code"
}

trap cleanup EXIT
trap on_error ERR

require_cmd curl
require_cmd git
require_cmd mktemp
require_cmd grep
require_cmd sed
require_cmd cp
require_cmd rm

mkdir -p "$INSTALL_DIR"

normalize_version() {
    local v="$1"
    if [[ "$v" =~ ^v[0-9] ]]; then
        echo "${v#v}"
        return
    fi
    echo "$v"
}

# Get latest version from GitHub
get_latest_version_raw() {
    local tag=""
    tag="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' 2>/dev/null || true)"
    if [ -z "$tag" ]; then
        echo "main"
        return
    fi
    echo "$tag"
}

# Get current installed version
get_current_version_raw() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | grep '"version":' | sed -E 's/.*"([^"]+)".*/\1/' 2>/dev/null || echo "unknown"
    else
        echo "not-installed"
    fi
}

RAW_LATEST_VERSION="$(get_latest_version_raw)"
LATEST_VERSION="$(normalize_version "$RAW_LATEST_VERSION")"
RAW_CURRENT_VERSION="$(get_current_version_raw)"
CURRENT_VERSION="$(normalize_version "$RAW_CURRENT_VERSION")"

echo "Current version: $CURRENT_VERSION"
echo "Latest version:  $LATEST_VERSION"
echo ""

# Check if update needed
if [ "$CURRENT_VERSION" == "$LATEST_VERSION" ]; then
    echo -e "${GREEN}Already up to date!${NC}"
    exit 0
fi

echo -e "${YELLOW}Updating to $LATEST_VERSION...${NC}"
echo ""

# Clone repository
echo "Downloading..."
if ! git clone --depth 1 --branch "$RAW_LATEST_VERSION" --single-branch "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude"; then
    if ! git clone --depth 1 --branch "$LATEST_VERSION" --single-branch "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude"; then
        echo -e "${YELLOW}Tag clone failed; falling back to default branch...${NC}" >&2
        git clone --depth 1 "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" || die "Failed to clone repository"
    fi
fi

# Backup user files (if they exist)
echo "Backing up user files..."
BACKUP_DIR="$INSTALL_DIR/.backup-$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Files to preserve (user-specific)
PRESERVE_FILES=(
    "lessons-learned.md"
    "evolution-log.md"
    ".vibe-version.json"
    "settings.json"
    "settings.local.json"
)

for file in "${PRESERVE_FILES[@]}"; do
    if [ -f "$INSTALL_DIR/$file" ]; then
        cp "$INSTALL_DIR/$file" "$BACKUP_DIR/"
    fi
done

# Also backup custom agents created by user
if [ -d "$INSTALL_DIR/agents" ]; then
    mkdir -p "$BACKUP_DIR/agents"
    for agent in "$INSTALL_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            cp "$agent" "$BACKUP_DIR/agents/"
        fi
    done
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
echo "Installing new files..."
shopt -s nullglob
for item in "$TEMP_DIR/vibe-claude/"* "$TEMP_DIR/vibe-claude"/.[!.]* "$TEMP_DIR/vibe-claude"/..?*; do
    [ "$(basename "$item")" = ".git" ] && continue
    cp -R "$item" "$INSTALL_DIR/"
done
shopt -u nullglob

# Restore preserved files
echo "Restoring user files..."
for file in "${PRESERVE_FILES[@]}"; do
    if [ -f "$BACKUP_DIR/$file" ]; then
        cp "$BACKUP_DIR/$file" "$INSTALL_DIR/"
    fi
done

# Merge custom agents (keep both old and new)
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
  "installMethod": "script",
  "lastCheckAt": "$(date -Iseconds)"
}
EOF

ROLLBACK_READY=0

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Update Complete!${NC}"
echo -e "${GREEN}  Version: $LATEST_VERSION${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Restart Claude Code to apply changes."
