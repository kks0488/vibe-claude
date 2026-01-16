# Lessons Learned

A record of failures and their solutions. Check this before starting similar tasks.

---

## [2026-01-10] 다음 작업자에게 전달

### 현재 시스템 상태
- **Version**: v1.2.0
- **5-Phase System**: 완전 구현됨
- **모든 에이전트/스킬**: Phase awareness 및 evidence requirements 추가됨
- **Auto-update**: 2일마다 4am에 실행 (cron)

### 남은 작업 / 개선 아이디어

1. **GitHub 릴리즈**: 오늘 변경사항을 v1.3.0으로 릴리즈 필요
2. **테스트**: 새 5-phase 시스템 실제 프로젝트에서 테스트 필요
3. **문서화**: 한국어 README도 있으면 좋을 수 있음
4. **MCP 서버**: GitHub MCP가 Docker로 설정되어 있음 (`ghcr.io/github/github-mcp-server`)

### 주의사항

- `/vibe` 실행시 반드시 `.vibe/work-*.md` 문서가 생성되어야 함
- 모든 완료 보고는 실제 출력/증거 포함 필수
- Phase 5는 선택적 - 필요없으면 N/A로 표시

### 파일 위치

| 파일 | 역할 |
|-----|-----|
| `CLAUDE.md` | 메인 시스템 프롬프트 |
| `commands/vibe.md` | VIBE MODE 전체 프로토콜 |
| `.vibe/TEMPLATE.md` | 작업 문서 템플릿 |
| `scripts/auto-update.sh` | 자동 업데이트 스크립트 |

---

## [2026-01-10] Task tool subagent_type limitation

- **Task**: Tried to call custom agent via Task tool
- **Failure**: `subagent_type="v-api-tester"` not recognized
- **Root Cause**: Task tool has hardcoded subagent types, custom agents work via auto-delegation
- **Solution**: Custom agents in `~/.claude/agents/` are auto-discovered and delegated based on description matching
- **Prevention**: Use description-based matching, not direct subagent_type calls for custom agents

---
