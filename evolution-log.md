# Vibe-Claude Evolution Log

시스템 자기 개선 기록.

---

## 2026-01-17: 문서 일관성 및 SSOT 개선

### 수정된 항목
- **Retry Policy 통일**: vibe/SKILL.md의 "무한 재시도"를 "최대 10회"로 수정 (DEFINITIONS.md와 일치)
- **lessons-learned.md 생성**: v-evolve 스킬이 참조하는 파일 신규 생성
- **/cancel-vibe 명령어 추가**: Slash Command 테이블에 누락된 명령어 추가
- **Work Document Template 개선**: Phase 5 섹션 추가 (CLAUDE.md, vibe/SKILL.md)
- **메모리 스크립트 통합**: v-memory-helper.sh를 v-memory.sh로 통합 (중복 제거)
- **v-conductor 도구 정리**: 불필요한 Bash, Edit, Write 도구 제거 (역할 분리 원칙)
- **메모리 디렉토리 구조 문서화**: long-term, short-term, working, meta, .archive 추가
- **Phase 0 일관성 확보**: Dynamic Routing 테이블에 P0 명시

### 영향받는 파일
- `~/.claude/CLAUDE.md`
- `~/.claude/skills/vibe/SKILL.md`
- `~/.claude/agents/v-conductor.md`
- `~/.claude/lessons-learned.md` (신규)
- `~/.claude/scripts/v-memory.sh` (통합)

---

## 2026-01-17: 시스템 문제점 수정

### 수정된 항목
- **명령어 4개 추가**: v-turbo, v-continue, v-memory, v-compress
- **에이전트 도구 수정**: WebFetch → WebSearch (v-researcher, v-vision, v-api-tester)
- **v-analyst 권한 조정**: Edit 도구 제거 (역할 분리 원칙)
- **CLAUDE.md 개선**:
  - Auto Routing: v-continue를 스킬로 명시
  - Infinite Retry: 탈출 조건 추가 (최대 10회, 30분)
  - Language: Korean으로 수정
  - Phase 2: 사용 기준 명확화

### 새로 추가된 자동화 스크립트
- `~/.claude/scripts/v-memory.sh` - memU 통합, 메모리 저장/검색
- `~/.claude/scripts/v-compress.sh` - 컨텍스트 압축
- `~/.claude/scripts/v-continue.sh` - 세션 복구

---

## Evolution Guidelines

새 기능 추가 시:
1. 이 로그에 날짜와 함께 기록
2. 영향받는 파일 목록 명시
3. 변경 이유 설명

