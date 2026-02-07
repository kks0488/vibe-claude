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

## Two-Strike Rule (Context-Aware Escalation)

**정의**: 동일한 실패(같은 에러 시그니처/같은 막힘)가 2회 반복되면, 더 이상 “그대로 재시도”하지 않고 즉시 전술을 바꾼다.

```
Strike 1: 첫 실패 → 원인 가설 + 대안 시도
Strike 2: 같은 실패 반복 → STOP → 컨텍스트 레벨 확인 → 에스컬레이션/압축/리셋
```

### “같은 실패” 판정 기준 (최소 요건)

- 동일(또는 실질적으로 동일)한 에러 메시지/스택
- 동일한 테스트/커맨드에서 재현
- 동일한 설계/가정에 근거한 접근이 반복됨

### Context Level 기반 조치

| Context Level (체감) | 액션 | 에스컬레이션 |
|----------------------|------|--------------|
| > 60% | 계속 진행 가능 | v-analyst로 root cause 재분석 |
| 40–60% | `/v-compress`로 체크포인트 후 재시도 | 필요 시 haiku→sonnet→opus 업그레이드 |
| < 40% | `/clear`로 새 세션 + 학습 요약 파일로 재시작 | v-planner로 인터뷰/계획 재수립 |

> 핵심: “두 번 같은 데서 미끄러지면, 방법을 바꿔라.” (증거/가정/컨텍스트를 재점검)

---

## Work Document (Minimal Template)

`.vibe/work-{timestamp}.md` 는 최소한 아래 구조를 포함한다 (추가 섹션은 자유):

```markdown
# Task: {task}
Started: {datetime}
Status: in_progress

## Routing
- Complexity: {TRIVIAL|SIMPLE|MODERATE|COMPLEX}
- Path: {P3 only | P1→P3→P4 | P0.5→P1→P2→P3→P4→P5}

## Phases
- [ ] Phase 0: Routing
- [ ] Phase 0.5: Interview (COMPLEX only)
- [ ] Phase 1: Recon
- [ ] Phase 2: Planning (COMPLEX only)
- [ ] Phase 3: Execution
- [ ] Phase 4: Verification (Tribunal)
- [ ] Phase 5: Polish (Optional)

## Delegation Log
| Time | From → To | Summary | Link/Evidence |
|------|-----------|---------|---------------|

## Error Log
| # | What Failed | Evidence | Fix Attempt | Result |
|---|------------|----------|-------------|--------|

## Completion Evidence
## COMPLETION PROOF
✓ Executed: [actual command]
  Output: [actual output]

✓ Tests: [test command]
  Result: [X passed, 0 failed]
```

---

## Memory Types

| Type | Purpose | Auto-save Trigger |
|------|---------|-------------------|
| lesson | 실패 → 해결 | 2+ 재시도 후 성공 |
| pattern | 재사용 가능한 코드 | 수동 저장 |
| decision | 아키텍처 결정 | 중요 논의 후 |
| context | 도메인 지식 | 수동 저장 |

---

## Hook Events (v4.1.0)

| Event | Hook Script | Trigger | Action |
|-------|-------------|---------|--------|
| Setup | `setup.sh` | Plugin 로드 시 | `.vibe/` 디렉토리 생성, 설정 검증, 이전 세션 감지 |
| SessionStart | `session-start.sh` | 세션 시작/재개 | 에이전트 목록 + 핵심 규칙 주입 |
| UserPromptSubmit | `prompt-submit.sh` | 매 프롬프트 | "Evidence before claims" 리마인더 |
| SubagentStart | `subagent-start.sh` | 서브에이전트 시작 | 현재 work document 컨텍스트 주입 |
| TeammateIdle | `teammate-idle.sh` | teammate idle 전 | 미완료 작업 체크 → exit 2 계속 강제 |
| TaskCompleted | `task-completed.sh` | 태스크 완료 전 | COMPLETION PROOF 존재 확인 |
| Stop | `stop-guard.sh` | 에이전트 정지 시 | COMPLETION PROOF 없으면 exit 2 계속 강제 |
| PostToolUse | `post-edit-check.sh` | Write\|Edit 후 | 파일 syntax/lint 자동 체크 |

---

## Agent Configuration (v4.1.0)

| Agent | permissionMode | maxTurns | Special |
|-------|---------------|----------|---------|
| v-conductor | default | 50 | Task(agent allowlist) |
| v-worker | acceptEdits | 30 | skills: v-git, hooks: PostToolUse |
| v-designer | acceptEdits | 30 | skills: v-style, hooks: PostToolUse |
| v-tester | acceptEdits | 25 | - |
| v-writer | acceptEdits | 20 | - |
| v-analyst | default | 25 | - |
| v-finder | default | 10 | - |
| v-researcher | default | 25 | - |
| v-vision | default | 10 | - |
| v-critic | default | 25 | - |
| v-advisor | default | 15 | - |
| v-planner | default | 25 | - |
| v-api-tester | default | 20 | - |

---

*다른 파일에서는 이 정의를 참조합니다. 여기서만 수정하세요.*
