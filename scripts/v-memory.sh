#!/bin/bash
# v-memory helper script - memU integration for vibe-claude
# Usage: v-memory-helper.sh <command> [args]
# Enhanced version with local file storage and fallback

set -euo pipefail
IFS=$'\n\t'

MEMU_API="${MEMU_API:-http://localhost:8100}"
MEMU_USER_ID="${MEMU_USER_ID:-vibe-claude}"
MEMORY_DIR="$HOME/.claude/.vibe/memory"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: Missing required dependency: ${cmd}${NC}" >&2
        exit 1
    fi
}

require_cmd curl

# Ensure directories exist
ensure_dirs() {
    mkdir -p "$MEMORY_DIR"/{lessons,patterns,decisions,context}
}

# JSON string escaping for safe request bodies
escape_for_json() {
    local input="$1"
    local output=""
    local i char
    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        case "$char" in
            $'\\') output+='\\' ;;
            '"') output+='\"' ;;
            $'\n') output+='\n' ;;
            $'\r') output+='\r' ;;
            $'\t') output+='\t' ;;
            $'\b') output+='\b' ;;
            $'\f') output+='\f' ;;
            *) output+="$char" ;;
        esac
    done
    printf '%s' "$output"
}

# Check if memU is available
is_memu_available() {
    curl -s --connect-timeout 2 "$MEMU_API/health" > /dev/null 2>&1 || return 1
}

# Save to local file
save_local() {
    local type="$1"
    local title="$2"
    local content="$3"
    local date=$(date +%Y-%m-%d)
    local slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')

    ensure_dirs
    [ -z "$slug" ] && slug="untitled"

    # Map type to directory
    local dir_type
    case "$type" in
        lesson) dir_type="lessons" ;;
        pattern) dir_type="patterns" ;;
        decision) dir_type="decisions" ;;
        context) dir_type="context" ;;
        *) dir_type="$type" ;;
    esac

    mkdir -p "$MEMORY_DIR/$dir_type"
    local filename="$MEMORY_DIR/$dir_type/${date}-${slug}.md"

    cat > "$filename" << EOF
# $title

**Date:** $date
**Type:** $type

---

$content
EOF

    echo "$filename"
}

# Functions
memorize() {
    local content="$1"
    local metadata="$2"

    curl -sS -X POST "$MEMU_API/memorize" \
        -H "Content-Type: application/json" \
        -d "{
            \"content\": \"$(escape_for_json "$content")\",
            \"user_id\": \"$(escape_for_json "$MEMU_USER_ID")\",
            \"metadata\": $metadata
        }"
}

retrieve() {
    local query="$1"
    local limit="${2:-5}"

    curl -sS -X POST "$MEMU_API/retrieve" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$(escape_for_json "$query")\",
            \"user_id\": \"$(escape_for_json "$MEMU_USER_ID")\",
            \"limit\": $limit
        }"
}

check_similar() {
    local content="$1"
    local threshold="${2:-0.85}"

    curl -sS -X POST "$MEMU_API/check-similar" \
        -H "Content-Type: application/json" \
        -d "{
            \"content\": \"$(escape_for_json "$content")\",
            \"user_id\": \"$(escape_for_json "$MEMU_USER_ID")\",
            \"threshold\": $threshold
        }"
}

list_items() {
    local type="$1"

    if [ -z "$type" ]; then
        curl -sS "$MEMU_API/items?user_id=$MEMU_USER_ID"
    else
        curl -sS "$MEMU_API/items?user_id=$MEMU_USER_ID&metadata.type=$type"
    fi
}

delete_item() {
    local id="$1"
    curl -sS -X DELETE "$MEMU_API/items/$id"
}

# Health check
health() {
    local response
    response=$(curl -sS --connect-timeout 2 "$MEMU_API/health" 2>/dev/null || true)
    if echo "$response" | grep -q "ok"; then
        echo -e "${GREEN}✓ memU is running at $MEMU_API${NC}"
        return 0
    else
        echo -e "${RED}✗ memU is not responding at $MEMU_API${NC}"
        return 1
    fi
}

# Save with dual storage (local + memU)
save() {
    local type="$1"
    local title="$2"
    local content="$3"

    if [ -z "$type" ] || [ -z "$title" ] || [ -z "$content" ]; then
        echo -e "${RED}Usage: $0 save <type> <title> <content>${NC}"
        echo "Types: lesson, pattern, decision, context"
        return 1
    fi

    # Always save locally first
    local filepath=$(save_local "$type" "$title" "$content")
    echo -e "${GREEN}✓ Saved to: $filepath${NC}"

    # Try to sync to memU
    if is_memu_available; then
        local metadata="{\"title\":\"$(escape_for_json "$title")\",\"type\":\"$(escape_for_json "$type")\",\"source\":\"vibe-claude\"}"
        local result=""
        if result=$(memorize "$content" "$metadata" 2>/dev/null); then
            :
        else
            echo -e "${YELLOW}⚠ memU request failed (local saved)${NC}" >&2
            return 0
        fi
        if echo "$result" | grep -q "\"success\""; then
            echo -e "${GREEN}✓ Synced to memU${NC}"
        else
            echo -e "${YELLOW}⚠ memU sync failed (local saved)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ memU unavailable (local saved only)${NC}"
    fi
}

# Search with fallback
search() {
    local query="$1"
    local limit="${2:-5}"

    if [ -z "$query" ]; then
        echo -e "${RED}Usage: $0 search <query> [limit]${NC}"
        return 1
    fi

    # Try memU first
    if is_memu_available; then
        echo -e "${BLUE}Searching memU...${NC}"
        retrieve "$query" "$limit"
    else
        # Fallback to local grep
        require_cmd grep
        require_cmd head
        echo -e "${YELLOW}memU unavailable, searching local files...${NC}"
        ensure_dirs
        echo ""
        local matches
        matches=$(grep -r -l -i "$query" "$MEMORY_DIR" 2>/dev/null || true)
        if [ -z "$matches" ]; then
            echo "No local matches."
            return 0
        fi
        while IFS= read -r file; do
            echo -e "${GREEN}Found: $file${NC}"
            echo "---"
            head -15 "$file"
            echo ""
        done <<< "$matches"
    fi
}

# List local memories
list_local() {
    local type="${1:-all}"
    ensure_dirs

    echo -e "${BLUE}=== Local Memories ===${NC}"
    echo ""

    if [ "$type" = "all" ]; then
        for dir in lessons patterns decisions context; do
            local count=$(ls -1 "$MEMORY_DIR/$dir/" 2>/dev/null | wc -l)
            echo -e "${GREEN}$dir${NC} ($count files)"
            ls -1 "$MEMORY_DIR/$dir/" 2>/dev/null | head -5
            [ "$count" -gt 5 ] && echo "  ... and $((count-5)) more"
            echo ""
        done
    else
        local count=$(ls -1 "$MEMORY_DIR/$type/" 2>/dev/null | wc -l)
        echo -e "${GREEN}$type${NC} ($count files)"
        ls -1 "$MEMORY_DIR/$type/" 2>/dev/null
    fi
}

# Main
case "$1" in
    save)
        save "$2" "$3" "$4"
        ;;
    memorize)
        if ! is_memu_available; then
            echo -e "${RED}ERROR: memU unavailable at $MEMU_API${NC}" >&2
            exit 1
        fi
        memorize "$2" "$3"
        ;;
    retrieve|search)
        search "$2" "$3"
        ;;
    check-similar)
        if ! is_memu_available; then
            echo -e "${RED}ERROR: memU unavailable at $MEMU_API${NC}" >&2
            exit 1
        fi
        check_similar "$2" "$3"
        ;;
    list)
        if [ "$2" = "--local" ] || [ "$2" = "-l" ]; then
            list_local "$3"
        else
            if is_memu_available; then
                list_items "$2"
            else
                echo -e "${YELLOW}memU unavailable, listing local memories instead...${NC}"
                list_local "${2:-all}"
            fi
        fi
        ;;
    list-local)
        list_local "$2"
        ;;
    delete)
        if ! is_memu_available; then
            echo -e "${RED}ERROR: memU unavailable at $MEMU_API${NC}" >&2
            exit 1
        fi
        delete_item "$2"
        ;;
    health)
        health
        ;;
    *)
        echo "v-memory-helper - memU integration for vibe-claude"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  save <type> <title> <content>       Save locally + sync to memU"
        echo "  memorize <content> <metadata_json>  Save to memU only"
        echo "  search <query> [limit]              Semantic search (fallback to local)"
        echo "  check-similar <content> [threshold] Check for duplicates"
        echo "  list [type]                         List memU memories"
        echo "  list-local [type]                   List local memories"
        echo "  delete <id>                         Delete memory from memU"
        echo "  health                              Check memU status"
        echo ""
        echo "Memory types: lesson, pattern, decision, context"
        echo ""
        echo "Environment variables:"
        echo "  MEMU_API     - memU API URL (default: http://localhost:8100)"
        echo "  MEMU_USER_ID - memU user ID (default: vibe-claude)"
        ;;
esac
