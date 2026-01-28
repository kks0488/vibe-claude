#!/bin/bash

# Vibe-Claude Auto-Update Script
# Runs silently every 2 days to keep system updated

REPO="kks0488/vibe-claude"
INSTALL_DIR="$HOME/.claude"
VERSION_FILE="$INSTALL_DIR/.vibe-version.json"
LOG_FILE="$INSTALL_DIR/.vibe-update.log"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
}

log "=== Auto-update check started ==="

# Get versions
CURRENT_VERSION=$(cat "$VERSION_FILE" 2>/dev/null | grep '"version":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "unknown")
LATEST_VERSION=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "")

log "Current: $CURRENT_VERSION, Latest: $LATEST_VERSION"

# Check if update needed
if [ -z "$LATEST_VERSION" ]; then
    log "ERROR: Could not fetch latest version"
    exit 1
fi

if [ "$CURRENT_VERSION" == "$LATEST_VERSION" ]; then
    log "Already up to date"
    exit 0
fi

log "Update available! Updating..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Clone latest
if ! git clone --depth 1 "https://github.com/$REPO.git" "$TEMP_DIR/vibe-claude" 2>/dev/null; then
    log "ERROR: Failed to clone repository"
    exit 1
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
    [ -f "$INSTALL_DIR/$file" ] && cp "$INSTALL_DIR/$file" "$BACKUP_DIR/" 2>/dev/null
done

# Backup custom agents
if [ -d "$INSTALL_DIR/agents" ]; then
    mkdir -p "$BACKUP_DIR/agents"
    cp "$INSTALL_DIR/agents"/*.md "$BACKUP_DIR/agents/" 2>/dev/null
fi

# Copy new files
cp -r "$TEMP_DIR/vibe-claude/"* "$INSTALL_DIR/" 2>/dev/null
cp -r "$TEMP_DIR/vibe-claude/".* "$INSTALL_DIR/" 2>/dev/null

# Restore preserved files
for file in "${PRESERVE_FILES[@]}"; do
    [ -f "$BACKUP_DIR/$file" ] && cp "$BACKUP_DIR/$file" "$INSTALL_DIR/" 2>/dev/null
done

# Merge custom agents
if [ -d "$BACKUP_DIR/agents" ]; then
    for agent in "$BACKUP_DIR/agents"/*.md; do
        [ -f "$agent" ] && cp "$agent" "$INSTALL_DIR/agents/" 2>/dev/null
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

log "SUCCESS: Updated to $LATEST_VERSION"
log "=== Auto-update completed ==="
