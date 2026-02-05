---
name: v-memory
description: AI memory system - save, search, and recall knowledge with memU integration
---

# V-Memory Skill

지식을 저장하고 검색하는 AI 메모리 시스템.

## Activation

```
/v-memory <command> [args]
```

## Commands

### save - 메모리 저장

```bash
/v-memory save lesson "제목"     # 실패→해결 기록
/v-memory save pattern "제목"    # 코드 패턴
/v-memory save decision "제목"   # 아키텍처 결정
```

### search - 시맨틱 검색 (memU)

```bash
/v-memory search "에러 핸들링"
/v-memory search "왜 PostgreSQL?"
```

### list - 메모리 목록

```bash
/v-memory list              # 전체
/v-memory list lessons      # 특정 타입만
```

## memU Integration

| 동작 | memU API | 용도 |
|-----|----------|------|
| 저장 | `POST /memorize` | 메모리 저장 + 임베딩 |
| 검색 | `POST /retrieve` | 시맨틱 검색 |
| 중복체크 | `POST /check-similar` | 저장 전 중복 확인 |

```bash
MEMU_API=http://localhost:8100
MEMU_USER_ID=vibe-claude
```

## Opus 4.6 Memory Enhancements

### Compaction + Memory 시너지

```
Compaction API가 컨텍스트 요약 시:
  → 핵심 lesson/pattern 자동 감지
  → /v-memory save 자동 트리거 제안
  → 중요 정보 손실 방지

128K Output:
  → 더 포괄적인 메모리 검색 결과 반환
  → 관련 메모리 간 연결 관계까지 분석
```

### 향상된 자동 저장

| 상황 | 기존 (4.5) | 지금 (Opus 4.6) |
|------|-----------|-----------------|
| 실패 → 해결 | 2회 재시도 후 저장 | Adaptive thinking으로 실패 패턴 깊이 분석 후 저장 |
| 아키텍처 결정 | 수동 저장 | Effort: max로 결정 근거까지 자동 문서화 |
| Compaction 발생 | N/A | 요약 전 핵심 정보 메모리에 자동 백업 |

## 저장 위치

```
~/.claude/.vibe/memory/
├── lessons/      # 실패 → 해결
├── patterns/     # 코드 패턴
└── decisions/    # 아키텍처 결정
```

## Save Flow

```
/v-memory save lesson "제목"
    ↓
1. 내용 수집 (문제, 해결책, 예방법)
2. .vibe/memory/lessons/ 에 저장
3. memU에 동기화 (시맨틱 검색용)
4. 중복 체크 (check-similar)
```

## Search Flow

```
/v-memory search "쿼리"
    ↓
1. memU /retrieve 호출
2. 시맨틱 유사도로 검색
3. 상위 결과 표시
```

## 자동 저장 (작업 중)

| 상황 | 저장 타입 | 조건 |
|-----|----------|------|
| 실패 후 해결 | lesson | 2회+ 재시도 후 성공 |
| 아키텍처 선택 | decision | "왜 이걸 선택?" 논의 |

```
[V-MEMORY AUTO-SAVE]
Lesson saved: API timeout retry pattern
Synced to memU: ✓
```

## Protocol Examples

### Save Lesson

```
/v-memory save lesson "Task tool 제한사항"
    ↓
[V-MEMORY: SAVE LESSON]
Title: Task tool 제한사항

Saved to: .vibe/memory/lessons/2026-01-17-task-tool.md
Synced to memU ✓
```

### Search

```
/v-memory search "에러 핸들링"
    ↓
[V-MEMORY: SEARCH]
Query: "에러 핸들링"
Found: 3 related memories

1. [pattern] api-error-handling.md (0.92)
2. [lesson] retry-logic.md (0.85)
3. [decision] error-boundary.md (0.78)
```

## Rules

- 저장 전 memU check-similar로 중복 확인
- 파일명: `{date}-{slug}.md` 또는 `{slug}.md`
- memU user_id: `vibe-claude`
- 검색 결과 없으면 로컬 grep 대체
