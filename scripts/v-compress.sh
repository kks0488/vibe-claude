#!/bin/bash
# v-compress.sh - 컨텍스트 압축 스크립트
# 완료된 Phase를 요약하여 저장

VIBE_DIR="$HOME/.claude/.vibe"
WORK_DIR="$VIBE_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

compress_phase() {
    local work_file="$1"
    local phase_num="$2"
    
    if [[ -z "$work_file" ]]; then
        # 최신 work 파일 찾기
        work_file=$(ls -t "$WORK_DIR"/work-*.md 2>/dev/null | head -1)
    fi
    
    if [[ ! -f "$work_file" ]]; then
        echo "No work document found"
        exit 1
    fi
    
    local timestamp=$(date '+%Y%m%d-%H%M%S')
    local detail_file="$VIBE_DIR/phase${phase_num}-detail-${timestamp}.md"
    
    echo -e "${YELLOW}Compressing Phase $phase_num from $work_file${NC}"
    
    # Phase 내용 추출 및 저장
    awk "/## Phase $phase_num/,/## Phase [0-9]|## Progress|## Requirements|$/" "$work_file" > "$detail_file"
    
    echo -e "${GREEN}✓ Detail saved: $detail_file${NC}"
    echo ""
    echo "Summary to keep in conversation:"
    echo "---"
    echo "## Phase $phase_num ✓ COMPRESSED"
    echo ""
    echo "### Summary"
    grep -E "^\- \[x\]" "$detail_file" | head -5 | sed 's/- \[x\]/- /'
    echo ""
    echo "Detail: $detail_file"
    echo "---"
}

list_compressed() {
    echo -e "${YELLOW}=== Compressed Phases ===${NC}"
    ls -la "$VIBE_DIR"/phase*-detail-*.md 2>/dev/null || echo "No compressed phases found"
}

# 메인
case "$1" in
    phase)
        compress_phase "$3" "$2"
        ;;
    list)
        list_compressed
        ;;
    *)
        echo "v-compress - Context Compression"
        echo ""
        echo "Commands:"
        echo "  phase <num> [work_file]   Compress a specific phase"
        echo "  list                       List compressed phases"
        echo ""
        echo "Example: v-compress.sh phase 1"
        ;;
esac
