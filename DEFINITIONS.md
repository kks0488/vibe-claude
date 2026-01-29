# Vibe-Claude Definitions (SSOT)

이 파일은 시스템 전체에서 참조되는 핵심 정의의 Single Source of Truth입니다.

---

## 5-Phase Structure (+ Phase 0.5)

| Phase | Name | Purpose | Agents |
|-------|------|---------|--------|
| 0 | Routing | 복잡도 분류, 경로 선택 | Claude (자동) |
| 0.5 | Interview | (COMPLEX만) 요구사항 명확화, 제약/성공 기준 수집 | Claude (자동) |
| 1 | Recon | 분석, 탐색, 리서치 | v-analyst, v-finder, v-researcher, v-advisor |
| 2 | Planning | 전략 수립 (COMPLEX만) | v-planner |
| 3 | Execution | 구현, 코드 작성 | v-worker, v-designer, v-writer |
| 4 | Verification | 검증, 테스트, 리뷰 | v-critic, v-analyst, v-tester |
| 5 | Polish | 리팩토링, 문서화 (선택) | v-worker, v-writer |

---

## Complexity Routing

| Level | Criteria | Route |
|-------|----------|-------|
| TRIVIAL | 단일 줄 수정, 타이포 | P3 only |
| SIMPLE | 단일 파일, 명확한 요구사항 | P1→P3→P4 |
| MODERATE | 다중 파일, 명확한 요구사항 | P1→P3→P4 |
| COMPLEX | 아키텍처 변경, 3+ 모듈 영향 | P0.5→P1→P2→P3→P4→P5 |

---

## Completion Proof Template

```markdown
## COMPLETION PROOF

✓ Executed: [actual command]
  Output: [actual output]

✓ Tests: [test command]
  Result: [X passed, 0 failed]

✓ Requirements verified:
  - [Requirement]: file.ts:line
```

---

## Retry Policy

- **최대 재시도**: 10회
- **타임아웃**: 30분
- **탈출 조건**:
  - 사용자 `/cancel-vibe`
  - 명확히 불가능한 작업
  - 10회 실패 후 → 사용자에게 guidance 요청

---

## Handoff Request Protocol (Agents → v-conductor)

Agents cannot invoke other agents. They emit a handoff request; `v-conductor` routes it.

```text
[HANDOFF REQUEST: v-<agent>]
From: v-<agent>
Reason: <why>
Context:
- File/Endpoint/Image: path:line (as applicable)
- Evidence: <command output / repro>
Suggested task: <what to do>
```

Edge-case rules:
- Missing/unknown target agent → fallback to `v-analyst` + log `unknown handoff target`
- Malformed handoff (missing From/Reason/Suggested task) → ask re-emit once; then fallback to `v-analyst`
- Circular handoff (same `From → Target` and `Reason` repeats) → stop and root-cause analyze (`v-analyst`); if repeated, ask user to narrow scope/provide missing info

---

## Memory Types

| Type | Purpose | Auto-save Trigger |
|------|---------|-------------------|
| lesson | 실패 → 해결 | 2+ 재시도 후 성공 |
| pattern | 재사용 가능한 코드 | 수동 저장 |
| decision | 아키텍처 결정 | 중요 논의 후 |
| context | 도메인 지식 | 수동 저장 |

---

*다른 파일에서는 이 정의를 참조합니다. 여기서만 수정하세요.*
