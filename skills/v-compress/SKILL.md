---
name: v-compress
description: 컨텍스트 자동 압축 - 완료된 Phase 요약으로 세션 2-3배 연장
---

# V-Compress Skill

세션 컨텍스트를 효율적으로 관리해서 더 오래 작업.

## 핵심 원리

```
Claude 4.6 Compaction API (서버사이드):
  → 컨텍스트 한계 접근 시 서버가 자동 요약
  → 이전 대화 내용 자동 압축
  → 사실상 무한 대화 가능

/v-compress (클라이언트사이드 보조):
  → 완료된 Phase 상세 내용 → 파일로 저장
  → 요약만 대화에 유지
  → Compaction API와 병행하여 이중 안전망
```

## 사용 시점

- Compaction API가 자동 관리하지만, 상세 기록이 필요할 때 수동 실행
- Phase 전환 시 이전 Phase의 상세 파일 저장
- 긴 세션에서 파일 기반 백업이 필요할 때
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

## Compaction API Integration (Claude 4.6)

### 자동 vs 수동 압축

| 방식 | 주체 | 시점 | 효과 |
|------|------|------|------|
| Compaction API | 서버 (자동) | 컨텍스트 한계 접근 시 | 이전 대화 자동 요약 |
| /v-compress | 클라이언트 (수동) | Phase 전환 시 | 상세 내용 파일 저장 |

### 하이브리드 전략

```
Context 100-60%:
  → Compaction API standby
  → 정상 작업

Context 60-40%:
  → Compaction API 자동 요약 시작
  → /v-compress로 Phase 상세 파일 저장

Context 40-20%:
  → Compaction + /v-compress 병행
  → Checkpoint 생성

Context 20%:
  → /v-continue 준비
  → 세션 핸드오프
```

### Context Budget (Compaction-Enhanced)

```
기존 (4.5):
100% ████████████████████ Fresh
 60% → Manual compress needed
 40% → WARNING
 20% → DANGER

지금 (4.6 + Compaction):
100% ████████████████████ Fresh
 80% → Compaction standby
 60% → Compaction 자동 요약
 40% → /v-compress 보조
 20% → /v-continue 준비
```

> **Compaction API가 대부분의 컨텍스트 관리를 자동화. /v-compress는 파일 기반 상세 백업.**

## Rules

- 현재 Phase는 압축 안함
- 핵심 결정/요구사항은 항상 유지
- 압축 전 상세 내용 파일로 저장
