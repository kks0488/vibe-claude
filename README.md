<p align="center">
  <img src="assets/banner.png" alt="vibe-claude: build with AI without reading code, and still know it works" width="100%">
</p>

<p align="center">
  <b>English</b> · <a href="README.ko.md"><b>한국어</b></a>
</p>

<h2 align="center">Your AI says “Done!”<br>vibe-claude makes sure it really is.</h2>

<p align="center">
  For people who build apps with Claude Code but can't read code.<br>
  <b>Install once. Nothing to learn. No questions asked.</b>
</p>

<table>
<tr>
<td width="50%" valign="top">

### ✅ No more fake “done”
Claude can't say it's finished until your app was **actually run and worked**. Just saying “it works” is not enough.

</td>
<td width="50%" valign="top">

### ↩️ Nothing is ever lost
Every change is saved automatically. Something broke, or got deleted? Just say **“undo”**.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 👀 A second AI double-checks
A different AI (OpenAI Codex) looks over each change and sends Claude back to fix real problems. *Optional: only if you have Codex.*

</td>
<td width="50%" valign="top">

### 🤫 No technical questions
It never asks you things you can't judge. It decides safely, then tells you what happened **in one plain line**.

</td>
</tr>
</table>

<h3 align="center">Install: paste these two lines into Claude Code</h3>

```text
/plugin marketplace add kks0488/vibe-claude
/plugin install vibe-claude@vibe-claude
```

<p align="center"><b>Claude Code alone is enough.</b> No Codex subscription? Everything works except the second-AI review, which is simply skipped.</p>

<p align="center">
  <img src="assets/demo.gif" alt="Claude is stopped until tests pass, deleted files come back with undo, a second AI reviews the change" width="100%">
</p>

## What you'll notice

At the end of every change, one line tells you the truth:

| You see | It means |
| --- | --- |
| 🟢 `vibe ✓ 2 files changed · checked: npm test` | It was really tested after the last change, and it passed. |
| 🟡 `vibe ⚠ … NOT verified` | Nothing could be tested. Be careful with this change. |
| 🔴 `vibe ✗ … check FAILED` | It's still broken, and Claude knows. |
| ⚪ `… could not be undone — …` | Claude did something permanent (like resetting a database), and here is what. |

Changed your mind? Say **“undo”** or **“go back to before the login change.”** That's all.

## See it in action

**Proof.** Claude says it's done, gets stopped, runs the tests, and the receipt shows what really happened.

<p align="center"><img src="assets/demo-proof.svg" alt="Terminal demo: Claude is stopped until it actually tests the change" width="100%"></p>

**Safety and undo.** Deleted files are kept, a permanent step makes Claude stop and think, and “undo” brings everything back.

<p align="center"><img src="assets/demo-guard.svg" alt="Terminal demo: files are kept before deleting, and undo restores them" width="100%"></p>

## Tested on real work

- Tuned by replaying **16 days of real sessions (about 22,000 commands)**.
- **87 automated tests**, plus runs with real Claude and real Codex.
- Reviewed four times by Codex before release.
- Costs about **1% more** AI usage.

---

<details>
<summary><b>🔧 Under the hood (for the curious)</b></summary>

<br>

| Part | What happens |
| --- | --- |
| **Proof gate** | Every shell command and its real exit code is logged. After a code change, Claude can't stop until a test, build or run of the program passes *after the last edit*. Words in the reply don't count; neither does a result hidden by a pipe, `;` or `\|\| true`. |
| **Regression ratchet** | Single check commands that passed before in the project are re-run at the end of a change. |
| **Second opinion** | With [Codex CLI](https://github.com/openai/codex) installed and logged in, `codex exec` reviews the diff read-only in the background (secrets redacted) and wakes Claude via `asyncRewake` on findings. |
| **Receipt** | A `systemMessage` built from the log, never from the model. |
| **Snapshots + undo** | A private git store in `~/.vibe-claude/` (outside the project) saves your files at every request and before risky commands, git project or not. `/vibe-claude:undo` restores by snapshot id and can itself be undone. |
| **Trash** | Files a delete would remove that snapshots don't cover (git-ignored, over 5 MB, outside the project; up to 300 MB) are copied to a 7-day trash first. |
| **Guard** | Irreversible steps (database resets, force pushes, cloud deletes, branch deletes) are denied once with a reason so Claude decides from the conversation; the identical retry goes through and the receipt reports it. Deleting the project, home folder or disk is always refused. |
| **Test guard** | Edits that remove assertions, add `skip`/`xfail`/`.only` or always-true checks, and deletions of committed tests, are stopped once. |
| **Package check** | `npm`/`pip`/`uv`/`cargo` installs are checked against the public registry: names that don't exist are refused, packages under 14 days old are stopped once. Private registries are never queried. |
| **Secret check** | Writing real-looking API keys or private keys into code is refused; `.env` files are allowed. |
| **Syntax check** | Python, JS, TS (with the project's own `typescript`), JSON, YAML, TOML, shell and notebooks. |

**Requirements:** `python3` and `git`. Codex is optional.

**Settings:** optional `.vibe/config.json` in your project:

```json
{ "codex": "auto", "ratchet": true, "snapshots": true, "packages": true, "lang": null, "safe_to_delete": [] }
```

`"codex": "off"` turns the second opinion off. `lang` is `"en"` or `"ko"` (default: the language you write in). `python3 <plugin>/hooks/vibe.py status` shows what is active.

**How a request flows:**

```mermaid
flowchart LR
    A([You ask]) --> B[Snapshot<br/>your files]
    B --> C[Claude works]
    C -->|risky command| G{Guard}
    G -->|files| T[Back up or<br/>copy to trash] --> C
    G -->|irreversible| S[Stop Claude once<br/>to decide] --> C
    C -->|wants to stop| P{Proof gate}
    P -->|no passing check<br/>after last edit| C
    P -->|verified| R[Receipt] --> X([Codex review<br/>in background])
    X -->|real problem| C
```

**What it deliberately doesn't do:** Claude Code already has plan mode, memory, subagents, `/rewind`, `/code-review` and `/goal`; superpowers, spec-kit and claude-mem cover methodology, specs and memory. vibe-claude only adds what those leave open: proof a model can't fake, a reviewer that isn't the same model, and an undo that also covers shell commands. The whole plugin is one standard-library Python file, [`hooks/vibe.py`](hooks/vibe.py), and one skill.

**FAQ.** *Slower?* An unchecked change gets one extra round of testing; snapshots take under a second on typical projects. *Need Codex?* No; the review step is skipped without it. *Windows?* Not tested yet. *Where did the 13 agents go?* See [docs/HISTORY.md](docs/HISTORY.md).

</details>

<p align="center">
  <a href="https://github.com/kks0488/vibe-claude/actions/workflows/ci.yml"><img src="https://github.com/kks0488/vibe-claude/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/kks0488/vibe-claude/releases"><img src="https://img.shields.io/github/v/release/kks0488/vibe-claude?color=d97757&label=release" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3fb950" alt="MIT license"></a>
  <br>
  <a href="CHANGELOG.md">Changelog</a> · <a href="docs/HISTORY.md">History</a> · MIT © Kyoungsoo Kim and contributors
</p>
