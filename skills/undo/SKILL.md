---
description: Go back to an earlier state of the project's files (before a request, before a risky command, or the last time checks passed). Use when the user says undo, go back, revert, restore, it worked before, or 되돌려/원래대로/이전으로.
argument-hint: "[what to undo, in plain words]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo *), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" trash *)
---

The user wants an earlier version of their files back. They may not read code, so talk about moments and effects, never about git.

1. List the saved moments:

   `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo list`

   Each line is `<id> <when> <kind> '<label>' [how it differs from now]`. Always refer to a moment by its id (first column), never by its position, because new moments are added while you talk. Kinds: "before request" (the label is what the user asked for), "before risky command", "checks passed" (a moment when tests or the build passed), "before an undo".

2. Pick the moment that matches what the user described: $ARGUMENTS
   If nothing was described, suggest the newest "before request" entry that is not marked "(start of the current request)" and does not say "same as now": that undoes the latest finished request. If unsure, show at most 3 options in plain words, for example "3분 전, '로그인 고쳐줘' 요청 직전 (파일 4개가 달라요)", and ask which one.

3. Optionally see which files would change: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo show <id>`

4. Restore after the user agrees: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo restore <id>`
   This only touches files in the project, never git history, and the current files are saved first, so the undo can itself be undone (the output names the id to restore). If it answers "Not restored", nothing was changed; explain the reason in plain words.

5. Tell the user in one or two plain sentences what is back, how to check it (for example reload the page), and that they can say "undo" again to return.

Snapshots skip git-ignored files, folders such as node_modules, and files over 5 MB. When a command deleted files the snapshots did not cover, a copy went to the trash (kept 7 days): list it with `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" trash` and bring files back with `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" trash restore <id>` (it never overwrites files that exist again). Databases and online services are not part of them; say so if the user expects those to come back.
