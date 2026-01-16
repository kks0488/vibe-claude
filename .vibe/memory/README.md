# Vibe Memory System

AI가 학습하고 기억하는 지식 저장소.

---

## 폴더 구조

```
memory/
├── lessons/      # 실패 → 해결 기록 (무엇이 안 됐고, 어떻게 고쳤나)
├── patterns/     # 재사용 코드 패턴 (검증된 해결책)
├── decisions/    # 아키텍처 결정 (왜 이 방식을 선택했나)
└── context/      # 프로젝트별 컨텍스트 (도메인 지식)
```

---

## 메모리 타입별 용도

### lessons/
**"이건 안 됐고, 이렇게 해결했다"**

```markdown
# [날짜] 제목
- Task: 무엇을 시도했나
- Failure: 무엇이 실패했나
- Root Cause: 왜 실패했나
- Solution: 어떻게 해결했나
- Prevention: 다음에 어떻게 방지하나
```

### patterns/
**"이 문제는 이렇게 푼다"**

```markdown
# Pattern: 패턴명
- Problem: 어떤 문제를 해결하나
- Solution: 코드/접근법
- When to use: 언제 사용하나
- Example: 실제 사용 예시
```

### decisions/
**"이 방식을 선택한 이유"**

```markdown
# Decision: 결정 제목
- Context: 상황/배경
- Options: 고려한 대안들
- Decision: 선택한 방향
- Rationale: 선택 이유
- Consequences: 예상 결과/트레이드오프
```

### context/
**"이 프로젝트/도메인은 이렇게 작동한다"**

```markdown
# Context: 프로젝트/도메인명
- Overview: 개요
- Key Concepts: 핵심 개념
- Conventions: 관례/규칙
- Gotchas: 주의사항
```

---

## 사용법

### 저장
```bash
/v-memory save lesson "Task tool 커스텀 에이전트 제한"
/v-memory save pattern "FastAPI 에러 핸들링"
/v-memory save decision "PostgreSQL 선택 이유"
/v-memory save context "PlayAuto 도메인"
```

### 검색 (memU 시맨틱 검색)
```bash
/v-memory search "에러 핸들링"
/v-memory search "왜 실패했지?"
```

### 목록
```bash
/v-memory list
/v-memory list lessons
```

---

## memU 연동

- **API**: http://localhost:8100
- **user_id**: `vibe-claude`
- 저장 시 자동으로 memU에 동기화
- 검색 시 시맨틱 검색으로 관련 메모리 찾기
- 중복 체크로 같은 내용 반복 저장 방지

---

## 자동 저장 트리거

| 상황 | 저장 타입 |
|-----|----------|
| 실패 후 해결 | lessons |
| 새 패턴 발견 | patterns |
| 아키텍처 선택 | decisions |
| 프로젝트 학습 | context |

---

*v-memory 스킬로 관리됩니다.*
