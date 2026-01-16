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
/v-memory save context "제목"    # 프로젝트 컨텍스트
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

### recall - 관련 메모리 자동 로드

```bash
/v-memory recall            # 현재 작업 관련 메모리 검색
```

## How It Works

### Save Flow

```
/v-memory save lesson "제목"
        ↓
┌─────────────────────────────────────┐
│  1. 템플릿 로드                      │
│  2. 사용자 입력 수집                  │
│  3. .vibe/memory/{type}/ 에 저장     │
│  4. memU에 동기화 (시맨틱 검색용)     │
│  5. 중복 체크 (check-similar)        │
└─────────────────────────────────────┘
```

### Search Flow

```
/v-memory search "쿼리"
        ↓
┌─────────────────────────────────────┐
│  1. memU /retrieve 호출              │
│  2. 시맨틱 유사도로 검색              │
│  3. 관련 메모리 파일 경로 반환        │
│  4. 상위 결과 내용 표시               │
└─────────────────────────────────────┘
```

## memU Integration

**API Endpoints:**

| 동작 | memU API | 용도 |
|-----|----------|------|
| 저장 | `POST /memorize` | 메모리 저장 + 임베딩 |
| 검색 | `POST /retrieve` | 시맨틱 검색 |
| 중복체크 | `POST /check-similar` | 저장 전 중복 확인 |
| 삭제 | `DELETE /items/{id}` | 메모리 삭제 |

**Configuration:**

```bash
MEMU_API=http://localhost:8100
MEMU_USER_ID=vibe-claude
```

## Auto-Save Triggers

작업 중 자동으로 메모리 저장을 제안:

| 상황 | 저장 타입 | 트리거 |
|-----|----------|--------|
| 실패 후 해결 | lesson | "이 문제 해결됐다" |
| 새 패턴 발견 | pattern | 같은 코드 3회 이상 |
| 아키텍처 선택 | decision | "왜 이걸 선택?" |
| 프로젝트 학습 | context | 새 도메인 진입 |

## Memory Location

```
~/.claude/.vibe/memory/
├── lessons/      # 실패 → 해결
├── patterns/     # 코드 패턴
├── decisions/    # 아키텍처 결정
└── context/      # 프로젝트 컨텍스트
```

## Protocol

### Save Memory

```
/v-memory save lesson "Task tool 제한사항"
        ↓
┌─────────────────────────────────────────────────┐
│  [V-MEMORY: SAVE LESSON]                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  Title: Task tool 제한사항                       │
│                                                 │
│  Collecting information...                      │
│  - Task: 무엇을 시도했나?                        │
│  - Failure: 무엇이 실패했나?                     │
│  - Root Cause: 왜?                              │
│  - Solution: 어떻게 해결?                        │
│  - Prevention: 다음에 어떻게 방지?               │
│                                                 │
│  ✓ Saved to: .vibe/memory/lessons/2026-01-17-*.md│
│  ✓ Synced to memU (id: xxx)                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Search Memory

```
/v-memory search "에러 핸들링"
        ↓
┌─────────────────────────────────────────────────┐
│  [V-MEMORY: SEARCH]                             │
├─────────────────────────────────────────────────┤
│                                                 │
│  Query: "에러 핸들링"                            │
│  Found: 3 related memories                      │
│                                                 │
│  1. [pattern] api-error-handling.md (0.92)      │
│     → FastAPI 글로벌 에러 핸들러                 │
│                                                 │
│  2. [lesson] 2026-01-15-retry-logic.md (0.85)   │
│     → Retry 로직 실패 해결                       │
│                                                 │
│  3. [decision] error-boundary.md (0.78)         │
│     → React Error Boundary 도입 결정            │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Rules

- 저장 전 항상 memU check-similar로 중복 확인
- 파일명 형식: `{date}-{slug}.md` 또는 `{slug}.md`
- memU user_id는 항상 `vibe-claude`
- 검색 결과 없으면 로컬 파일도 grep으로 검색
