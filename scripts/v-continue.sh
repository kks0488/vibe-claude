#!/bin/bash
# v-continue.sh - 세션 복구 스크립트

VIBE_DIR="$HOME/.claude/.vibe"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

find_latest_work() {
    local latest=$(ls -t "$VIBE_DIR"/work-*.md 2>/dev/null | head -1)
    
    if [[ -z "$latest" ]]; then
        echo -e "${RED}No work document found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Latest work document: $latest${NC}"
    echo ""
    
    # 진행 상황 표시
    echo -e "${YELLOW}=== Progress Status ===${NC}"
    echo ""
    
    # Task 추출
    grep "^## Task:" "$latest" || grep "^## " "$latest" | head -1
    echo ""
    
    # 완료/미완료 항목 카운트
    local total=$(grep -c "^\- \[" "$latest" 2>/dev/null || echo 0)
    local done=$(grep -c "^\- \[x\]" "$latest" 2>/dev/null || echo 0)
    local pending=$((total - done))
    
    echo "Progress: $done / $total completed ($pending remaining)"
    echo ""
    
    # 미완료 항목 표시
    echo -e "${YELLOW}=== Pending Items ===${NC}"
    grep "^\- \[ \]" "$latest" | head -10
    
    # 마지막 로그
    echo ""
    echo -e "${YELLOW}=== Last Activity ===${NC}"
    grep "^### \[" "$latest" | tail -3
    
    echo ""
    echo -e "${GREEN}Ready to continue. Pass this file to Claude.${NC}"
    echo "File: $latest"
}

# 메인
case "$1" in
    status|"")
        find_latest_work
        ;;
    *)
        echo "v-continue - Session Recovery"
        echo ""
        echo "Commands:"
        echo "  status    Show latest work status (default)"
        ;;
esac
