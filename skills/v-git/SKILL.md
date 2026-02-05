---
name: v-git
description: Git mastery. Clean history. Atomic commits. Professional version control.
---

# V-Git

Your git history tells a story. Make it a good one.

## Core Philosophy

Every commit should be a complete, atomic thought. The history should read like a well-organized book—not a stream of consciousness.

## Opus 4.6 Git Enhancements

- **128K Output**: 대규모 diff의 전체 분석 한 번에 가능
- **Adaptive Thinking**: 커밋 분할 전략을 자동으로 깊이 분석
- **Effort: high**: 모든 git 작업에 심층 사고 적용 (히스토리 일관성 보장)

## The Commit Commandments

### 1. Atomic Commits

One logical change per commit:
```
BAD:
"Fix bug and add feature and update docs"

GOOD:
Commit 1: "Fix null check in auth handler"
Commit 2: "Add password reset flow"
Commit 3: "Document password reset API"
```

### 2. Mandatory Splitting

| Files Changed | Minimum Commits |
|---------------|-----------------|
| 3-5 files | 2+ commits |
| 6-10 files | 3+ commits |
| 11+ files | 5+ commits |

**ONE COMMIT FOR MANY FILES = AUTOMATIC FAILURE**

### 3. Style Detection

Before first commit, analyze existing style:
```bash
git log -20 --oneline
```

Match the pattern:
- Language (Korean/English)
- Format (Conventional/Plain)
- Length (Short/Detailed)
- Capitalization

## Splitting Logic

| Signal | Action |
|--------|--------|
| Different directories | SPLIT |
| Different concerns (UI/logic/config) | SPLIT |
| Independent changes | SPLIT |
| New file + modifications | SPLIT |
| Test + implementation | SPLIT |

## Commit Message Template

```
<type>: <what changed>

<why it changed - 1-2 sentences if needed>
```

Types: feat, fix, refactor, docs, test, chore, style

## Advanced Operations

### Find When Bug Started
```bash
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
# Git finds the breaking commit
```

### Find Who Changed Line
```bash
git blame -L 50,60 file.ts
```

### Find When Code Added
```bash
git log -S "functionName" --oneline
```

### Interactive Rebase (local only)
```bash
git rebase -i HEAD~5
# squash, reorder, edit commits
```

## Safety Rules

- **NEVER** `git push --force` to main/master
- **ALWAYS** `--force-with-lease` instead of `--force`
- **NEVER** rebase published branches
- **ALWAYS** stash before risky operations
- **NEVER** commit secrets, even "temporarily"

## Phase Integration

Git operations happen at specific phases:
- **Phase 3**: Commits during execution
- **Phase 4**: Verification includes git status check
- **Phase 5**: Final polish commit if needed

## Work Document Integration

**Commit tracking in work document:**
```markdown
## Git Operations
- [ ] Style detected: conventional/plain
- [ ] Commits planned: 3 atomic commits
- [ ] Commit 1: auth changes (3 files)
- [ ] Commit 2: api changes (2 files)
- [ ] Commit 3: tests (2 files)
```

## Commit Evidence

Every commit shows proof:
```
## GIT COMMIT EVIDENCE

Commit 1: a1b2c3d
  Files: src/auth.ts, src/login.ts, src/session.ts
  Message: "feat: add session management"
  Verified: git log shows commit

Commit 2: d4e5f6g
  Files: src/api.ts, src/routes.ts
  Message: "feat: add auth API endpoints"
  Verified: git log shows commit

Total: 2 commits for 5 files ✓
```

## My Rules

- Read history before adding to it
- Match existing style
- One logical change = one commit
- Commit messages explain "why"
- Never break the build
- **Show git log output as evidence**

**A clean history is a gift to your future self. PROVEN clean.**
