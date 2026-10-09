---
description: Go back to an earlier state of the project's files (before a request, before a risky command, or the last time checks passed). Use when the user says undo, go back, revert, restore, it worked before, or 되돌려/원래대로/이전으로.
argument-hint: "[what to undo, in plain words]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo *)
---

The user wants an earlier version of their files back. They may not read code, so talk about moments and effects, never about git.

1. List the saved moments:

   `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo list`

   Each line is `N. <when> <kind> '<label>' [how it differs from now]`. Kinds: "before request" (the label is what the user asked for), "before risky command", "checks passed" (a moment when tests or the build passed), "before an undo".

2. Pick the moment that matches what the user described: $ARGUMENTS
   If nothing was described, suggest the newest "before request" entry, which undoes the latest request. If unsure, show at most 3 options in plain words, for example "3분 전, '로그인 고쳐줘' 요청 직전 (파일 4개가 달라요)", and ask which one.

3. Optionally see which files would change: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo show N`

4. Restore after the user agrees: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/vibe.py" undo restore N`
   This only touches files in the project, never git history, and the current state is saved first, so the undo can itself be undone.

5. Tell the user in one or two plain sentences what is back, how to check it (for example reload the page), and that they can say "undo" again to return.

Snapshots skip ignored folders such as node_modules. Databases and online services are not part of them; say so if the user expects those to come back.
