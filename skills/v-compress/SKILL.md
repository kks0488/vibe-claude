---
name: v-compress
description: 컨텍스트 자동 압축 - 완료된 Phase 요약으로 세션 2-3배 연장
---

# V-Compress Skill

세션 컨텍스트를 효율적으로 관리해서 더 오래 작업.

## 핵심 원리

```
완료된 Phase → 상세 파일 저장 + 요약만 대화에 유지
현재 Phase → 전체 컨텍스트 유지
```

## 사용 시점

- Phase 전환 시 이전 Phase 요약
- 대화가 길어져서 정리 필요할 때
- `/v-compress` 명령으로 수동 실행

## 압축 대상

| 대상 | 처리 |
|------|------|
| 완료된 Phase | 핵심 발견만 요약 |
| 검색 결과 | 파일 목록만 유지 |
| 에러 해결 과정 | 최종 해결책만 |

## 유지 (압축 안함)

- 현재 작업 중인 Phase
- 핵심 결정 사항
- 파일:라인 참조
- 사용자 요구사항

## 압축 형식

### Phase 요약

```markdown
## Phase 1 [COMPRESSED]
**요약**: 12개 파일 발견, 핵심 의존성 jwt/bcrypt
**핵심 파일**: auth.ts:42, user.ts:89
**상세**: .vibe/phase1-detail.md
```

### 검색 결과

```markdown
## 검색 [COMPRESSED]
상위 5개: login.ts, session.ts, auth.ts, user.ts, token.ts
**전체**: .vibe/search-results.md
```

## 명령어

```bash
/v-compress              # 현재 세션 압축
/v-compress phase 1      # 특정 Phase만 압축
```

## 작동 방식

```
/v-compress
    ↓
1. 완료된 Phase 식별
2. 상세 내용 → .vibe/phase*-detail.md 저장
3. 요약만 대화에 출력
```

## 압축 후 알림

```
[V-COMPRESS]
Phase 1 압축됨
상세: .vibe/phase1-detail.md
```

## Rules

- 현재 Phase는 압축 안함
- 핵심 결정/요구사항은 항상 유지
- 압축 전 상세 내용 파일로 저장
