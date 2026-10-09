"""Behavior tests for hooks/vibe.py. Run: python3 -m unittest discover -s tests -v"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIBE = ROOT / "hooks" / "vibe.py"
spec = importlib.util.spec_from_file_location("vibe", VIBE)
vibe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vibe)


class Project(unittest.TestCase):
    """A throwaway project folder plus helpers that feed hook events to vibe.py."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="vibe-test-")).resolve()
        self.bin = Path(tempfile.mkdtemp(prefix="vibe-bin-")).resolve()
        self.sid, self.pid = "s1", "p1"

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.bin, ignore_errors=True)

    def env(self):
        # A PATH without the real codex, so tests never call a real model.
        return dict(os.environ, CLAUDE_PROJECT_DIR=str(self.dir), PATH=f"{self.bin}:/usr/bin:/bin", LANG="en_US.UTF-8")

    def hook(self, event, **data):
        data.setdefault("session_id", self.sid)
        data.setdefault("prompt_id", self.pid)
        data.setdefault("cwd", str(self.dir))
        p = subprocess.run([sys.executable, str(VIBE), event], input=json.dumps(data), capture_output=True,
                           text=True, env=self.env(), cwd=self.dir, timeout=120)
        out = json.loads(p.stdout) if p.stdout.strip() else None
        return out, p

    def cli(self, *args):
        return subprocess.run([sys.executable, str(VIBE), *args], capture_output=True, text=True,
                              env=self.env(), cwd=self.dir, timeout=60)

    def write(self, rel, text):
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return str(path)

    def edit(self, rel, text="x = 1\n"):
        path = self.write(rel, text)
        return self.hook("post-tool", tool_name="Write", tool_input={"file_path": path, "content": text})[0]

    def ran(self, cmd, ok=True, stdout=""):
        if ok:
            return self.hook("post-tool", tool_name="Bash", tool_input={"command": cmd},
                             tool_response={"stdout": stdout, "stderr": ""})[0]
        return self.hook("post-tool-fail", tool_name="Bash", tool_input={"command": cmd},
                         error=f"Exit code 1\n{stdout}")[0]

    def stop(self, msg="Done. Open http://localhost:3000 to see it.", active=False):
        return self.hook("stop", last_assistant_message=msg, stop_hook_active=active, background_tasks=[])[0]

    def pre(self, tool, **tool_input):
        return self.hook("pre-tool", tool_name=tool, tool_input=tool_input)[0]

    def decision(self, out):
        return (out or {}).get("hookSpecificOutput", {}).get("permissionDecision")


class ProofTests(Project):
    def setUp(self):
        super().setUp()
        self.hook("prompt", prompt="Make the button blue")

    def test_conversation_without_edits_is_not_blocked(self):
        self.assertIsNone(self.stop("Here is how the design works."))

    def test_code_change_without_any_check_blocks(self):
        self.edit("app.py")
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("nothing was run", out["reason"])

    def test_words_alone_are_not_evidence(self):
        self.edit("app.py")
        self.assertEqual(self.stop("Done. 12 tests passed. Open localhost:3000.")["decision"], "block")

    def test_passing_check_after_edit_allows_with_receipt(self):
        self.edit("app.py")
        self.ran("python3 -m pytest -q")
        out = self.stop()
        self.assertNotIn("decision", out)
        self.assertIn("vibe ✓ 1 file(s) changed", out["systemMessage"])
        self.assertIn("pytest", out["systemMessage"])

    def test_check_before_last_edit_does_not_count(self):
        self.ran("npm test")
        self.edit("app.js")
        self.assertEqual(self.stop()["decision"], "block")

    def test_failed_check_blocks(self):
        self.edit("app.py")
        out = self.ran("npm test", ok=False)
        self.assertIsNone(out)
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("failed", out["reason"])

    def test_missing_tool_is_not_a_failed_check(self):
        self.edit("app.py")
        self.ran("python3 -m pytest -q", ok=False, stdout="/usr/bin/python3: No module named pytest")
        self.ran("python3 -m unittest")
        self.assertIn("vibe ✓", self.stop()["systemMessage"])

    def test_piped_check_uses_tool_output_not_exit_code(self):
        self.edit("app.py")
        self.ran("pytest 2>&1 | tail -3", stdout="==== 2 failed, 3 passed ====")
        self.assertIn("failed", self.stop()["reason"])

    def test_piped_check_with_clean_output_passes(self):
        self.edit("app.py")
        self.ran("pytest 2>&1 | tail -3", stdout="==== 5 passed in 0.1s ====")
        self.assertIn("systemMessage", self.stop())

    def test_swallowed_errors_are_unclear(self):
        self.edit("app.py")
        self.ran("npm test || true")
        self.assertIn("hid its real result", self.stop()["reason"])

    def test_docs_only_change_needs_no_check(self):
        self.edit("README.md", "# hi\n")
        self.assertIsNone(self.stop())

    def test_second_stop_never_loops_and_reports_honestly(self):
        self.edit("app.py")
        out = self.stop(active=True)
        self.assertNotIn("decision", out)
        self.assertIn("nothing was run", out["systemMessage"])

    def test_requires_a_way_for_the_user_to_see_it(self):
        self.edit("app.py")
        self.ran("pytest")
        out = self.stop("I made the change.")
        self.assertEqual(out["decision"], "block")
        self.assertIn("see the result themselves", out["reason"])

    def test_running_the_edited_program_counts(self):
        self.edit("script.py", "print('hi')\n")
        self.ran("python3 script.py", stdout="hi")
        self.assertIn("systemMessage", self.stop())

    def test_korean_prompt_gets_korean_receipt(self):
        self.hook("prompt", prompt="버튼 파랗게 해줘", prompt_id="p2")
        self.pid = "p2"
        self.edit("app.py")
        self.ran("pytest")
        self.assertIn("파일 1개 변경", self.stop("완료했어요. `python3 app.py`로 확인하세요.")["systemMessage"])

    def test_ratchet_blocks_when_an_earlier_passing_check_breaks(self):
        self.write("tests/check.sh", "exit 0\n")
        self.ran("bash tests/check.sh")  # remembered as green
        self.write("tests/check.sh", "echo broken; exit 1\n")
        self.edit("app.py")
        self.ran("python3 app.py")
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("Regression: `bash tests/check.sh`", out["reason"])
        self.assertIn("broken", out["reason"])
        self.assertIn("bash tests/check.sh", self.cli("checks").stdout)
        self.cli("checks", "forget", "bash tests/check.sh")
        self.assertNotIn("check.sh", self.cli("checks").stdout)

    def test_ratchet_passes_when_earlier_checks_still_pass(self):
        self.write("tests/check.sh", "exit 0\n")
        self.ran("bash tests/check.sh")
        self.edit("app.py")
        self.ran("python3 app.py")
        out = self.stop()
        self.assertIn("bash tests/check.sh", out["systemMessage"])


class GuardTests(Project):
    def test_recursive_delete_asks_in_plain_words(self):
        out = self.pre("Bash", command="rm -rf photos")
        self.assertEqual(self.decision(out), "ask")
        self.assertIn("photos", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_regenerable_folders_are_allowed(self):
        self.assertIsNone(self.pre("Bash", command="rm -rf node_modules dist .next"))

    def test_catastrophic_delete_is_denied(self):
        for cmd in ("rm -rf ~", "rm -rf /", "rm -rf .", "sudo rm -rf $HOME/"):
            self.assertEqual(self.decision(self.pre("Bash", command=cmd)), "deny", cmd)

    def test_dangerous_commands_ask(self):
        for cmd in ("git reset --hard HEAD~1", "git push -f origin main", "git clean -fdx",
                    "psql -c 'DROP TABLE users'", "supabase db reset", "find . -name '*.py' -delete",
                    "git checkout -- .", "sqlite3 app.db 'DELETE FROM users;'"):
            self.assertEqual(self.decision(self.pre("Bash", command=cmd)), "ask", cmd)

    def test_ordinary_commands_pass(self):
        for cmd in ("git status", "ls -la", "npm run build", "git push origin main", "rm notes.txt",
                    "sqlite3 app.db 'DELETE FROM users WHERE id=3;'", "git restore --staged ."):
            self.assertIsNone(self.pre("Bash", command=cmd), cmd)

    def test_korean_users_get_korean_questions(self):
        self.hook("prompt", prompt="사진 폴더 정리해줘")
        out = self.pre("Bash", command="git reset --hard")
        self.assertIn("저장하지 않은 코드 변경", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_deleting_a_test_file_asks(self):
        self.assertEqual(self.decision(self.pre("Bash", command="rm tests/test_login.py")), "ask")

    def test_weakening_a_test_asks(self):
        test = "def test_a():\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n"
        path = self.write("tests/test_math.py", test)
        out = self.pre("Edit", file_path=path, old_string="    assert add(0, 0) == 0\n", new_string="")
        self.assertEqual(self.decision(out), "ask")
        self.assertIn("checks 2→1", out["hookSpecificOutput"]["permissionDecisionReason"])
        out = self.pre("Edit", file_path=path, old_string="def test_a", new_string="@pytest.mark.skip\ndef test_a")
        self.assertEqual(self.decision(out), "ask")
        out = self.pre("Edit", file_path=path, old_string="== 3", new_string="== 3\n    assert True")
        self.assertEqual(self.decision(out), "ask")

    def test_strengthening_a_test_passes(self):
        path = self.write("src/math.test.ts", "it('adds', () => { expect(add(1, 2)).toBe(3) })\n")
        out = self.pre("Edit", file_path=path, old_string="toBe(3) })", new_string="toBe(3); expect(add(2, 2)).toBe(4) })")
        self.assertIsNone(out)

    def test_secret_in_code_is_denied_but_env_file_is_fine(self):
        key = "AKIA" + "ABCDEFGHIJKLMNOP"
        out = self.pre("Write", file_path=str(self.dir / "config.js"), content=f"const key = '{key}'\n")
        self.assertEqual(self.decision(out), "deny")
        self.assertIsNone(self.pre("Write", file_path=str(self.dir / ".env"), content=f"AWS_KEY={key}\n"))

    def test_install_command_parsing(self):
        found = list(vibe.install_targets("npm i -D @types/node@20 react && pip install 'flask[async]==3.0' -r req.txt"
                                          " && cargo add serde && pip install ."))
        self.assertEqual(found, [("npm", "@types/node"), ("npm", "react"), ("pypi", "flask"), ("crates", "serde")])

    def test_package_reality_check(self):
        original = vibe.package_info
        captured = []
        vibe.emit = captured.append
        try:
            v = vibe.Vibe({"cwd": str(self.dir)})
            vibe.package_info = lambda eco, name: (False, None)
            vibe.pre_bash(v, "npm install reqeusts-helperz", "en")
            self.assertEqual(captured[-1]["hookSpecificOutput"]["permissionDecision"], "deny")
            vibe.package_info = lambda eco, name: (True, 3)
            vibe.pre_bash(v, "pip install brand-new-thing", "en")
            self.assertEqual(captured[-1]["hookSpecificOutput"]["permissionDecision"], "ask")
            vibe.package_info = lambda eco, name: (None, None)  # offline: fail open
            n = len(captured)
            vibe.pre_bash(v, "pip install requests", "en")
            self.assertEqual(len(captured), n)
        finally:
            vibe.package_info = original
            vibe.emit = lambda obj: print(json.dumps(obj, ensure_ascii=False))


class SyntaxTests(Project):
    def check(self, rel, text):
        return self.edit(rel, text)

    def test_valid_files_pass(self):
        self.assertIsNone(self.check("it's ok.py", "answer = 42\n"))
        self.assertIsNone(self.check("a.json", '{"a": 1}'))
        self.assertIsNone(self.check("a.sh", "echo hi\n"))

    def test_broken_files_block_with_details(self):
        for rel, text in (("bad.py", "if True print('x')\n"), ("bad.json", "{"), ("bad.sh", "if then\n"),
                          ("bad.toml", "a = = 1\n")):
            out = self.check(rel, text)
            self.assertEqual(out["decision"], "block", rel)
            self.assertIn("Syntax check failed", out["reason"])

    def test_notebook_cells_are_checked(self):
        nb = {"cells": [{"cell_type": "code", "source": ["%pip install x\n", "x = 1\n"]},
                        {"cell_type": "code", "source": "def broken(:\n"}]}
        path = self.write("a.ipynb", json.dumps(nb))
        out = self.hook("post-tool", tool_name="NotebookEdit", tool_input={"notebook_path": path})[0]
        self.assertIn("cell 2", out["reason"])


class SnapshotTests(Project):
    def test_undo_restores_files_without_touching_user_git(self):
        self.write("app.py", "version = 1\n")
        self.write("node_modules/big.js", "x")
        self.hook("prompt", prompt="change version")
        self.write("app.py", "version = 2\n")
        self.write("new.py", "extra = True\n")
        listing = self.cli("undo", "list").stdout
        self.assertIn("before request", listing)
        self.assertIn("change version", listing)
        r = self.cli("undo", "restore", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.dir / "app.py").read_text(), "version = 1\n")
        self.assertFalse((self.dir / "new.py").exists())
        self.assertTrue((self.dir / "node_modules/big.js").exists())
        self.assertFalse((self.dir / ".git").exists())
        # The undo itself can be undone: the newest snapshot is the state before the undo.
        self.assertIn("before an undo", self.cli("undo", "list").stdout)
        self.cli("undo", "restore", "1")
        self.assertEqual((self.dir / "app.py").read_text(), "version = 2\n")
        self.assertTrue((self.dir / "new.py").exists())

    def test_risky_command_takes_a_snapshot_first(self):
        self.write("photos/a.txt", "1")
        self.pre("Bash", command="rm -rf photos")
        self.assertIn("before risky command", self.cli("undo", "list").stdout)

    def test_state_folder_hides_itself_from_git(self):
        self.hook("prompt", prompt="hi")
        self.assertEqual((self.dir / ".vibe/.gitignore").read_text(), "*\n")

    def test_home_folder_is_never_snapshotted(self):
        v = vibe.Vibe({"cwd": str(Path.home())})
        self.assertFalse(v.enabled)


class CodexTests(Project):
    def fake_codex(self, verdict):
        script = self.bin / "codex"
        script.write_text(f"""#!/bin/bash
if [ "$1" = login ]; then exit 0; fi
out=""
while [ $# -gt 0 ]; do [ "$1" = -o ] && out="$2"; shift; done
cat > "{self.bin}/prompt"
printf '%s\\n' {json.dumps(verdict)} > "$out"
""")
        script.chmod(0o755)

    def finish_a_verified_change(self):
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="Fix the total")
        self.edit("app.py", "x = 2\n")
        self.ran("pytest")
        return self.stop()

    def test_findings_wake_claude_with_exit_2(self):
        self.fake_codex("- app.py:1 — total is wrong — the user sees a bad price")
        self.assertIn("Codex review running", self.finish_a_verified_change()["systemMessage"])
        out, p = self.hook("codex", background_tasks=[])
        self.assertEqual(p.returncode, 2)
        self.assertIn("independent reviewer", p.stderr)
        self.assertIn("total is wrong", p.stderr)
        prompt = (self.bin / "prompt").read_text()
        self.assertIn("Fix the total", prompt)
        self.assertIn("+x = 2", prompt)
        # The same change is never reviewed twice.
        self.assertEqual(self.hook("codex", background_tasks=[])[1].returncode, 0)

    def test_lgtm_stays_quiet(self):
        self.fake_codex("LGTM")
        self.finish_a_verified_change()
        out, p = self.hook("codex", background_tasks=[])
        self.assertEqual((p.returncode, p.stderr), (0, ""))

    def test_without_codex_everything_still_works(self):
        out = self.finish_a_verified_change()
        self.assertNotIn("Codex", out["systemMessage"])
        started = time.time()
        self.assertEqual(self.hook("codex", background_tasks=[])[1].returncode, 0)
        self.assertLess(time.time() - started, 10)

    def test_codex_skips_when_stop_was_blocked(self):
        self.fake_codex("- bug")
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="Fix")
        self.edit("app.py", "x = 2\n")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertEqual(self.hook("codex", background_tasks=[])[1].returncode, 0)


class SessionTests(Project):
    def test_rules_are_injected_at_session_start(self):
        out = self.hook("session-start", source="startup")[0]
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Prove it", ctx)
        self.assertLess(len(ctx), 1500)

    def test_internal_errors_fail_open(self):
        out, p = self.hook("stop", last_assistant_message=None, stop_hook_active="weird", background_tasks=None)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
