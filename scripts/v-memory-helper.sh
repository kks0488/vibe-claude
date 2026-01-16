#!/bin/bash
# v-memory helper script - memU integration for vibe-claude
# Usage: v-memory-helper.sh <command> [args]

MEMU_API="http://localhost:8100"
MEMU_USER_ID="vibe-claude"
MEMORY_DIR="$HOME/.claude/.vibe/memory"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
memorize() {
    local content="$1"
    local metadata="$2"

    curl -s -X POST "$MEMU_API/memorize" \
        -H "Content-Type: application/json" \
        -d "{
            \"content\": \"$content\",
            \"user_id\": \"$MEMU_USER_ID\",
            \"metadata\": $metadata
        }"
}

retrieve() {
    local query="$1"
    local limit="${2:-5}"

    curl -s -X POST "$MEMU_API/retrieve" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"user_id\": \"$MEMU_USER_ID\",
            \"limit\": $limit
        }"
}

check_similar() {
    local content="$1"
    local threshold="${2:-0.85}"

    curl -s -X POST "$MEMU_API/check-similar" \
        -H "Content-Type: application/json" \
        -d "{
            \"content\": \"$content\",
            \"user_id\": \"$MEMU_USER_ID\",
            \"threshold\": $threshold
        }"
}

list_items() {
    local type="$1"

    if [ -z "$type" ]; then
        curl -s "$MEMU_API/items?user_id=$MEMU_USER_ID"
    else
        curl -s "$MEMU_API/items?user_id=$MEMU_USER_ID&metadata.type=$type"
    fi
}

delete_item() {
    local id="$1"
    curl -s -X DELETE "$MEMU_API/items/$id"
}

# Health check
health() {
    local response=$(curl -s "$MEMU_API/health" 2>/dev/null)
    if echo "$response" | grep -q "ok"; then
        echo -e "${GREEN}✓ memU is running${NC}"
        return 0
    else
        echo -e "${RED}✗ memU is not responding${NC}"
        return 1
    fi
}

# Main
case "$1" in
    memorize)
        memorize "$2" "$3"
        ;;
    retrieve|search)
        retrieve "$2" "$3"
        ;;
    check-similar)
        check_similar "$2" "$3"
        ;;
    list)
        list_items "$2"
        ;;
    delete)
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
        echo "  memorize <content> <metadata_json>  Save to memU"
        echo "  search <query> [limit]              Semantic search"
        echo "  check-similar <content> [threshold] Check for duplicates"
        echo "  list [type]                         List memories"
        echo "  delete <id>                         Delete memory"
        echo "  health                              Check memU status"
        ;;
esac
