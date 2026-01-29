#!/bin/bash

# Vibe-Claude Installer/Updater
# https://github.com/kks0488/vibe-claude

set -e

REPO="kks0488/vibe-claude"
INSTALL_DIR="$HOME/.claude"
TEMP_DIR=$(mktemp -d)
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

# Get latest version from GitHub
get_latest_version() {
    curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' 2>/dev/null || echo "main"
}

# Get current installed version
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | grep '"version":' | sed -E 's/.*"([^"]+)".*/\1/' 2>/dev/null || echo "unknown"
    else
        echo "not-installed"
    fi
}

LATEST_VERSION=$(get_latest_version)
CURRENT_VERSION=$(get_current_version)

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
if ! git clone --depth 1 --branch "$LATEST_VERSION" --single-branch "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" 2>/dev/null; then
    git clone --depth 1 "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" 2>/dev/null
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
        cp "$INSTALL_DIR/$file" "$BACKUP_DIR/" 2>/dev/null || true
    fi
done

# Also backup custom agents created by user
if [ -d "$INSTALL_DIR/agents" ]; then
    mkdir -p "$BACKUP_DIR/agents"
    for agent in "$INSTALL_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            cp "$agent" "$BACKUP_DIR/agents/" 2>/dev/null || true
        fi
    done
fi

# Copy new files
echo "Installing new files..."
cp -r "$TEMP_DIR/vibe-claude/"* "$INSTALL_DIR/" 2>/dev/null || true
shopt -s nullglob
for item in "$TEMP_DIR/vibe-claude"/.[!.]* "$TEMP_DIR/vibe-claude"/..?*; do
    [ "$(basename "$item")" = ".git" ] && continue
    cp -r "$item" "$INSTALL_DIR/" 2>/dev/null || true
done
shopt -u nullglob

# Restore preserved files
echo "Restoring user files..."
for file in "${PRESERVE_FILES[@]}"; do
    if [ -f "$BACKUP_DIR/$file" ]; then
        cp "$BACKUP_DIR/$file" "$INSTALL_DIR/" 2>/dev/null || true
    fi
done

# Merge custom agents (keep both old and new)
if [ -d "$BACKUP_DIR/agents" ]; then
    for agent in "$BACKUP_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            AGENT_NAME=$(basename "$agent")
            # Only restore if it was a custom agent (not overwritten by update)
            if [ ! -f "$INSTALL_DIR/agents/$AGENT_NAME" ]; then
                cp "$agent" "$INSTALL_DIR/agents/" 2>/dev/null || true
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

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Update Complete!${NC}"
echo -e "${GREEN}  Version: $LATEST_VERSION${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Restart Claude Code to apply changes."
