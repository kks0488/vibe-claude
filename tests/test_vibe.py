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
        self.home = Path(tempfile.mkdtemp(prefix="vibe-home-")).resolve()
        self.sid, self.pid = "s1", "p1"

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.bin, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def env(self):
        # A PATH without the real codex, so tests never call a real model.
        return dict(os.environ, CLAUDE_PROJECT_DIR=str(self.dir), PATH=f"{self.bin}:/usr/bin:/bin", LANG="en_US.UTF-8",
                    VIBE_HOME=str(self.home), VIBE_STOP_WAIT="5",
                    VIBE_TEMP_ROOTS="/tmp:/private/tmp")  # test projects live in the system temp folder

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

    def stop(self, msg="Done. Open http://localhost:3000 to see it.", active=False, background=()):
        self.last_stop = dict(last_assistant_message=msg, stop_hook_active=active, background_tasks=list(background))
        return self.hook("stop", last_assistant_message=msg, stop_hook_active=active, background_tasks=list(background))[0]

    def codex(self):
        return self.hook("codex", **self.last_stop)

    def snap_id(self, kind, label=""):
        for line in self.cli("undo", "list").stdout.splitlines():
            if kind in line and label in line:
                return line.split()[0]
        self.fail(f"no snapshot {kind!r} {label!r}")

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
        self.assertIn("hid its real result", self.stop()["reason"])

    def test_piped_check_is_not_trusted_even_with_clean_output(self):
        self.edit("app.py")
        self.ran("pytest 2>&1 | tail -3", stdout="==== 5 passed in 0.1s ====")
        self.assertIn("hid its real result", self.stop()["reason"])

    def test_pipefail_makes_a_piped_check_trustworthy(self):
        self.edit("app.py")
        self.ran("set -o pipefail; pytest 2>&1 | tail -3")
        self.assertIn("systemMessage", self.stop())

    def test_inline_code_counts_only_when_it_loads_project_code(self):
        self.edit("calc.py", "def add(a, b):\n    return a + b\n")
        self.ran('python3 -c "print(5)"')
        self.assertIn("nothing was run", self.stop()["reason"])
        self.ran('python3 -c "from calc import add; print(add(2, 3))"')
        self.assertIn("vibe ✓", self.stop()["systemMessage"])

    def test_block_points_at_the_projects_own_tests(self):
        self.write("tests/test_calc.py", "import unittest\n")
        self.write("package.json", '{"scripts": {"test": "vitest", "build": "vite build"}}')
        self.edit("app.py")
        reason = self.stop()["reason"]
        self.assertIn("npm test", reason)
        self.assertIn("python3 -m pytest", reason)

    def test_commands_that_only_mention_a_check_are_not_evidence(self):
        self.edit("app.py")
        for cmd in ("echo pytest", "pytest --help", "pytest --collect-only", "grep -r pytest ."):
            self.ran(cmd)
        self.assertIn("nothing was run", self.stop()["reason"])

    def test_results_hidden_by_later_commands_are_unclear(self):
        for i, cmd in enumerate(("pytest; echo finished", "pytest || echo recovered",
                                 "set +o pipefail; pytest | tail -1", "pytest &")):
            self.hook("prompt", prompt="again", prompt_id=f"h{i}")
            self.pid = f"h{i}"
            self.edit("app.py", f"x = {i}\n")
            self.ran(cmd)
            self.assertIn("hid its real result", self.stop()["reason"], cmd)

    def test_chained_checks_with_and_all_count(self):
        self.edit("app.js")
        self.ran("cd web && npm run lint && npm test")
        msg = self.stop()["systemMessage"]
        self.assertIn("npm run lint", msg)

    def test_changes_made_by_shell_commands_need_a_check_too(self):
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="change it with sed", prompt_id="sed")
        self.pid = "sed"
        self.write("app.py", "x = 2\n")  # changed by a Bash command, so no edit event
        self.assertIn("app.py", self.stop()["reason"])
        self.ran("python3 app.py")
        self.assertIn("vibe ✓", self.stop()["systemMessage"])

    def test_fixing_a_bad_option_clears_the_failure(self):
        self.edit("app.js")
        self.ran("npm test --wrong-flag", ok=False)
        self.ran("npm test")
        self.assertIn("vibe ✓", self.stop()["systemMessage"])

    def test_a_narrower_passing_run_does_not_hide_a_failure(self):
        self.edit("app.py")
        self.ran("pytest", ok=False, stdout="3 failed")
        self.ran("pytest tests/test_one.py")
        self.assertIn("failed", self.stop()["reason"])

    def test_app_errors_are_failures_not_missing_tools(self):
        self.edit("app.js")
        self.ran("npm test", ok=False, stdout="Error: Cannot find module './missing-app-file'")
        self.assertIn("failed", self.stop()["reason"])

    def test_a_check_that_may_not_have_run_is_unclear(self):
        self.edit("app.py")
        self.ran("true || pytest")
        self.assertIn("hid its real result", self.stop()["reason"])

    def test_success_in_one_folder_does_not_clear_a_failure_in_another(self):
        self.edit("api/app.js")
        self.ran("cd api && npm test", ok=False)
        self.ran("cd web && npm test")
        self.assertIn("failed", self.stop()["reason"])

    def test_a_missing_tool_inside_the_test_script_is_a_failure(self):
        self.edit("app.js")
        self.ran("npm test", ok=False, stdout="sh: vitest: command not found")
        self.assertIn("failed", self.stop()["reason"])

    def test_shell_change_after_the_check_needs_a_new_check(self):
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="change", prompt_id="m1")
        self.pid = "m1"
        self.write("app.py", "x = 2\n")
        self.ran("python3 app.py")
        time.sleep(1.1)
        self.write("app.py", "x = 3\n")  # changed by a later shell command
        self.assertIn("nothing was run", self.stop()["reason"])

    def test_checks_of_another_project_prove_nothing(self):
        self.edit("app.py")
        self.ran("cd ../some-other-project && pytest")
        self.ran("pytest /elsewhere/tests")
        self.assertIn("nothing was run", self.stop()["reason"])

    def test_skipping_the_failing_tests_does_not_hide_the_failure(self):
        self.edit("app.py")
        self.ran("pytest", ok=False, stdout="1 failed")
        self.ran("pytest --ignore=tests/test_broken.py")
        self.ran("pytest -k 'not broken'")
        self.assertIn("failed", self.stop()["reason"])

    def test_deleting_code_after_the_check_needs_a_new_check(self):
        self.write("helper.py", "x = 1\n")
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="clean up", prompt_id="d1")
        self.pid = "d1"
        self.write("app.py", "x = 2\n")
        self.ran("python3 app.py")
        time.sleep(0.05)
        (self.dir / "helper.py").unlink()
        self.hook("post-tool", tool_name="Bash", tool_input={"command": "rm helper.py"}, tool_response={"stdout": ""})
        self.assertEqual(self.stop()["decision"], "block")

    def test_receipt_reflects_a_ratchet_failure_after_shell_only_changes(self):
        self.write("tests/check.sh", "exit 0\n")
        self.ran("bash tests/check.sh")
        self.write("tests/check.sh", "exit 1\n")
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="sed it", prompt_id="r1")
        self.pid = "r1"
        self.write("app.py", "x = 2\n")
        self.ran("python3 app.py")
        self.assertIn("Regression", self.stop()["reason"])
        out = self.stop("Still failing; open localhost to see.", active=True)
        self.assertIn("vibe ✗", out["systemMessage"])

    def test_copy_that_keeps_the_old_file_time_still_needs_a_check(self):
        self.write("app.py", "x = 1\n")
        old = self.write("old.py", "x = 0\n")
        os.utime(old, (1, 1))
        self.hook("prompt", prompt="restore old", prompt_id="c1")
        self.pid = "c1"
        self.write("app.py", "x = 2\n")
        self.ran("python3 app.py")
        time.sleep(0.05)
        shutil.copy2(old, self.dir / "app.py")
        self.hook("post-tool", tool_name="Bash", tool_input={"command": "cp -p old.py app.py"}, tool_response={"stdout": ""})
        self.assertEqual(self.stop()["decision"], "block")

    def test_background_work_ends_honestly_without_blocking(self):
        self.edit("app.py")
        out = self.stop(background=[{"id": "dev-server"}])
        self.assertNotIn("decision", out)
        self.assertIn("NOT verified", out["systemMessage"])

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

    def test_ratchet_never_remembers_compound_commands(self):
        self.write("tests/check.sh", "exit 0\n")
        self.ran("bash tests/check.sh && touch deployed")
        self.ran("FOO=1 bash tests/check.sh")
        self.assertEqual(self.cli("checks").stdout.strip(), "No remembered checks.")

    def test_ratchet_never_remembers_deploys_or_extra_targets(self):
        for cmd in ("make test deploy", "npm run deploy:test", "gradle test publish"):
            self.ran(cmd)
        self.ran("make test")
        self.assertEqual(self.cli("checks").stdout.strip(), "make test")

    def test_project_folder_stays_clean(self):
        self.edit("app.py")
        self.ran("pytest")
        self.stop()
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["app.py"])


class GuardTests(Project):
    """The user is never asked. Files are kept recoverable; other irreversible steps stop Claude once."""

    def once(self, cmd):
        """First attempt is stopped with an explanation for Claude; the identical retry goes through."""
        out = self.pre("Bash", command=cmd)
        self.assertEqual(self.decision(out), "deny", cmd)
        self.assertIn("stopped this once", out["hookSpecificOutput"]["permissionDecisionReason"], cmd)
        self.assertIsNone(self.pre("Bash", command=cmd), cmd)
        return out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_no_hook_ever_asks_the_user(self):
        for cmd in ("rm -rf photos", "git reset --hard", "psql -c 'DROP TABLE users'", "git push -f", "rm tests/test_a.py",
                    "git clean -fdx", "rm -rf ../elsewhere", "find . -delete"):
            self.assertNotEqual(self.decision(self.pre("Bash", command=cmd)), "ask", cmd)

    def test_recoverable_delete_just_takes_a_backup(self):
        self.write("photos/a.jpg", "1")
        self.assertIsNone(self.pre("Bash", command="rm -rf photos"))
        self.assertIn("before risky command", self.cli("undo", "list").stdout)

    def test_files_the_backup_misses_go_to_the_trash_first(self):
        self.write(".gitignore", "*.raw\n")
        self.write("photos/a.raw", "precious")  # ignored, so snapshots do not cover it
        self.assertIsNone(self.pre("Bash", command="rm -rf photos"))
        shutil.rmtree(self.dir / "photos")
        listing = self.cli("trash").stdout
        self.assertIn("rm -rf photos", listing)
        r = self.cli("trash", "restore", listing.split()[0])
        self.assertIn("Restored 1", r.stdout)
        self.assertEqual((self.dir / "photos/a.raw").read_text(), "precious")

    def test_files_outside_the_project_are_kept_too(self):
        outside = Path(tempfile.mkdtemp(prefix="vibe-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        (outside / "notes.txt").write_text("keep")
        self.assertIsNone(self.pre("Bash", command=f"rm -rf {outside}"))
        shutil.rmtree(outside)
        self.cli("trash", "restore", self.cli("trash").stdout.split()[0])
        self.assertEqual((outside / "notes.txt").read_text(), "keep")

    def test_too_large_to_keep_stops_claude_once(self):
        os.environ["VIBE_HOME"], old = str(self.home), os.environ.get("VIBE_HOME")
        self.addCleanup(lambda: os.environ.pop("VIBE_HOME") if old is None else os.environ.update(VIBE_HOME=old))
        limit, vibe.TRASH_MAX = vibe.TRASH_MAX, 10
        self.addCleanup(setattr, vibe, "TRASH_MAX", limit)
        self.write(".gitignore", "*.raw\n")
        self.write("big/a.raw", "x" * 100)
        captured = []
        emit, vibe.emit = vibe.emit, captured.append
        self.addCleanup(setattr, vibe, "emit", emit)
        v = vibe.Vibe({"cwd": str(self.dir), "prompt_id": "big"})
        vibe.pre_bash(v, "rm -rf big", "en")
        self.assertIn("too large", captured[-1]["hookSpecificOutput"]["permissionDecisionReason"])
        n = len(captured)
        vibe.pre_bash(v, "rm -rf big", "en")
        self.assertEqual(len(captured), n)  # Claude decided to go ahead

    def test_folders_marked_disposable_are_not_copied(self):
        self.write(".gitignore", "qa/\n")
        self.write("qa/shots/a.png", "1")
        self.assertEqual(self.cli("allow-delete", "qa").returncode, 0)
        self.assertIsNone(self.pre("Bash", command="rm -rf qa/shots"))
        self.assertIn("empty", self.cli("trash").stdout)
        self.assertEqual(self.cli("allow-delete", "..").returncode, 1)

    def test_regenerable_folders_are_allowed(self):
        self.assertIsNone(self.pre("Bash", command="rm -rf node_modules dist .next"))

    def test_catastrophic_delete_is_always_denied(self):
        for cmd in ("rm -rf ~", "rm -rf /", "rm -rf .", "sudo rm -rf $HOME/", "env rm -rf /", "sudo -n rm -rf /",
                    "env FOO=1 rm -rf ~", "rm -rf ..", "rm -rf ./*", "rm -rf docs && rm -rf ~", "bash -c 'rm -rf /'",
                    "eval rm -rf ~", "cd .. && rm -rf *", "D=$HOME && rm -rf $D"):
            for _ in range(2):  # retrying does not help
                self.assertEqual(self.decision(self.pre("Bash", command=cmd)), "deny", cmd)

    def test_irreversible_steps_stop_claude_once(self):
        for cmd in ("git push -f origin main", "git -c core.x=1 push --force", "git clean -fdx",
                    "psql -c 'DROP TABLE users'", "supabase db reset", "python manage.py flush",
                    "echo 'DROP TABLE x;' | psql", "sqlite3 app.db 'DELETE FROM users;'", "git branch -D old"):
            reason = self.once(cmd)
            self.assertIn("cannot be undone", reason)
            self.assertIn("will not be asked", reason)

    def test_a_retry_counts_only_within_the_same_request(self):
        self.once("git push -f origin main")
        self.hook("prompt", prompt="next", prompt_id="p2")
        out = self.hook("pre-tool", tool_name="Bash", tool_input={"command": "git push -f origin main"}, prompt_id="p2")[0]
        self.assertEqual(self.decision(out), "deny")

    def test_receipt_tells_the_user_about_irreversible_steps(self):
        self.hook("prompt", prompt="DB 초기화해줘")
        self.once("supabase db reset")
        out = self.stop("데이터베이스를 초기화했어요. 앱을 새로고침해 보세요.")
        self.assertIn("되돌릴 수 없는 작업이 있었어요 — 데이터베이스를 통째로 비워요", out["systemMessage"])

    def test_reset_to_an_older_commit_keeps_files_the_backup_lacks(self):
        git = lambda *args: subprocess.run(["git", "-C", str(self.dir), "-c", "user.name=t", "-c", "user.email=t@t",
                                            *args], capture_output=True, check=True)
        git("init", "-q")
        self.write("a.py", "1")
        git("add", "-A")
        git("commit", "-qm", "one")
        self.write("video.bin", "x" * 6_000_000)  # too large for snapshots, small enough for the trash
        git("add", "-A")
        git("commit", "-qm", "two")
        self.assertIsNone(self.pre("Bash", command="git reset --hard HEAD~1"))
        self.assertIn("git reset --hard HEAD~1", self.cli("trash").stdout)
        self.assertIsNone(self.pre("Bash", command="git reset --hard"))

    def test_heredoc_text_and_known_variables_are_understood(self):
        cmd = "cat > notes.md <<'EOF'\nrm -rf ~\nDROP TABLE users;\nEOF\necho done"
        self.assertIsNone(self.pre("Bash", command=cmd))
        self.assertIsNone(self.pre("Bash", command="S=/tmp/shots && rm -rf $S/cut_*.png ${S}/old"))
        self.assertIsNone(self.pre("Bash", command="rm -rf ../elsewhere/src/__pycache__"))

    def test_searching_or_dry_runs_are_not_dangerous(self):
        for cmd in ("grep 'DROP TABLE' migration.sql", "git clean -ndf", "rg 'rm -rf' docs", "rm -rf /tmp/build-cache",
                    "echo 'DROP TABLE users;'"):
            self.assertIsNone(self.pre("Bash", command=cmd), cmd)

    def test_ordinary_commands_pass(self):
        for cmd in ("git status", "ls -la", "npm run build", "git push origin main", "rm notes.txt",
                    "sqlite3 app.db 'DELETE FROM users WHERE id=3;'", "git restore --staged ."):
            self.assertIsNone(self.pre("Bash", command=cmd), cmd)

    def test_deleting_a_project_test_stops_claude_once(self):
        self.write("tests/test_login.py", "def test_a():\n    assert True\n")
        self.assertIn("Deleting tests", self.once("rm tests/test_login.py"))

    def test_weakening_a_test_stops_claude_once(self):
        test = "def test_a():\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n"
        path = self.write("tests/test_math.py", test)
        for old, new in (("    assert add(0, 0) == 0\n", ""), ("def test_a", "@pytest.mark.skip\ndef test_a"),
                         ("== 3", "== 3\n    assert True")):
            out = self.pre("Edit", file_path=path, old_string=old, new_string=new)
            self.assertEqual(self.decision(out), "deny", new)
            self.assertIn("weakens a test", out["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertIsNone(self.pre("Edit", file_path=path, old_string=old, new_string=new))

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
                                          " && cargo add serde && pip install . && pip install --target vendor requests"
                                          " && python3 -m pip install -U httpx"))
        self.assertEqual([(e, n) for e, n, _ in found], [("npm", "@types/node"), ("npm", "react"), ("pypi", "flask"),
                                                         ("crates", "serde"), ("pypi", "requests"), ("pypi", "httpx")])
        self.assertTrue(all(p for _, _, p in vibe.install_targets("pip install --index-url https://corp/simple corp-lib")))
        self.assertTrue(all(p for _, _, p in vibe.install_targets("PIP_INDEX_URL=https://corp/simple pip install lib")))

    def test_private_registry_names_are_never_sent_out(self):
        self.write(".npmrc", "@corp:registry=https://npm.corp.example\n")
        self.assertTrue(vibe.private_registry("npm", "@corp/ui", self.dir))
        self.assertFalse(vibe.private_registry("npm", "react", self.dir))

    def test_package_reality_check(self):
        os.environ["VIBE_HOME"], old = str(self.home), os.environ.get("VIBE_HOME")
        self.addCleanup(lambda: os.environ.pop("VIBE_HOME") if old is None else os.environ.update(VIBE_HOME=old))
        original, emit = vibe.package_info, vibe.emit
        captured = []
        vibe.emit = captured.append
        try:
            v = vibe.Vibe({"cwd": str(self.dir), "prompt_id": "pk"})
            vibe.package_info = lambda eco, name: (False, None)
            for _ in range(2):  # a package that does not exist is always refused
                vibe.pre_bash(v, "npm install reqeusts-helperz", "en")
                self.assertEqual(captured[-1]["hookSpecificOutput"]["permissionDecision"], "deny")
            vibe.package_info = lambda eco, name: (True, 3)
            vibe.pre_bash(v, "pip install brand-new-thing", "en")
            self.assertIn("only 3 days old", captured[-1]["hookSpecificOutput"]["permissionDecisionReason"])
            n = len(captured)
            vibe.pre_bash(v, "pip install brand-new-thing", "en")  # Claude checked and went ahead
            vibe.package_info = lambda eco, name: (None, None)  # offline: fail open
            vibe.pre_bash(v, "pip install requests", "en")
            self.assertEqual(len(captured), n)
        finally:
            vibe.package_info, vibe.emit = original, emit


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
        r = self.cli("undo", "restore", self.snap_id("before request", "change version"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.dir / "app.py").read_text(), "version = 1\n")
        self.assertFalse((self.dir / "new.py").exists())
        self.assertTrue((self.dir / "node_modules/big.js").exists())
        self.assertFalse((self.dir / ".git").exists())
        # The undo itself can be undone: the newest snapshot is the state before the undo.
        self.cli("undo", "restore", self.snap_id("before an undo"))
        self.assertEqual((self.dir / "app.py").read_text(), "version = 2\n")
        self.assertTrue((self.dir / "new.py").exists())

    def test_risky_command_takes_a_snapshot_first(self):
        self.write("photos/a.txt", "1")
        self.pre("Bash", command="rm -rf photos")  # recoverable, so allowed after the snapshot
        self.assertIn("before risky command", self.cli("undo", "list").stdout)

    def test_restore_refuses_to_overwrite_an_ignored_file(self):
        self.write("config.json", "{}")
        self.hook("prompt", prompt="before")
        (self.dir / "config.json").unlink()
        self.hook("prompt", prompt="middle", prompt_id="p8")
        self.write(".gitignore", "config.json\n")
        self.write("config.json", '{"mine": true}')
        r = self.cli("undo", "restore", self.snap_id("before request", "'before'"))
        self.assertEqual(r.returncode, 1)
        self.assertEqual((self.dir / "config.json").read_text(), '{"mine": true}')

    def test_list_marks_the_current_request(self):
        self.write("a.py", "1")
        self.hook("prompt", prompt="first")
        self.write("a.py", "2")
        self.hook("prompt", prompt="undo please", prompt_id="p7")
        line = next(l for l in self.cli("undo", "list").stdout.splitlines() if "undo please" in l)
        self.assertIn("start of the current request", line)

    def in_process(self):
        old = os.environ.get("VIBE_HOME")
        os.environ["VIBE_HOME"] = str(self.home)
        self.addCleanup(lambda: os.environ.pop("VIBE_HOME") if old is None else os.environ.update(VIBE_HOME=old))
        return vibe.Vibe({"cwd": str(self.dir)})

    def test_pruning_keeps_recent_ids_valid(self):
        v = self.in_process()
        keep, vibe.KEEP_SNAPSHOTS = vibe.KEEP_SNAPSHOTS, 2
        self.addCleanup(setattr, vibe, "KEEP_SNAPSHOTS", keep)
        ids = []
        for i in range(25):
            self.write("a.py", str(i))
            ids.append(v.snapshot("turn", str(i)))
        v.prune()
        self.assertEqual(len(v.snapshots(100)), 2)
        self.assertEqual(v.resolve(ids[-1][:10]), ids[-1])
        self.assertIsNone(v.resolve(ids[0][:10]))

    def test_big_files_stay_out_of_every_snapshot(self):
        v = self.in_process()
        big, vibe.MAX_FILE = vibe.MAX_FILE, 100
        self.addCleanup(setattr, vibe, "MAX_FILE", big)
        self.write("video.bin", "x" * 500)
        self.write("a.py", "1")
        first = v.snapshot("turn", "1")
        self.write("a.py", "2")
        second = v.snapshot("turn", "2")
        self.assertNotIn("video.bin", v.files_in(first) | v.files_in(second))

    def test_unknown_ids_are_rejected(self):
        self.hook("prompt", prompt="hi")
        self.assertEqual(self.cli("undo", "restore", "deadbeef00").returncode, 1)
        self.assertEqual(self.cli("undo", "restore", "1").returncode, 1)

    def test_restore_never_follows_links_out_of_the_project(self):
        outside = Path(tempfile.mkdtemp(prefix="vibe-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        (outside / "a.txt").write_text("precious")
        (self.dir / "assets").symlink_to(outside)
        self.hook("prompt", prompt="before")
        (self.dir / "assets").unlink()
        self.write("assets/a.txt", "new")
        self.hook("prompt", prompt="after", prompt_id="p9")
        r = self.cli("undo", "restore", self.snap_id("before request", "'before'"))
        self.assertEqual((outside / "a.txt").read_text(), "precious")

    def test_restore_refuses_to_replace_a_folder_with_unsaved_files(self):
        self.write("notes", "a file")
        self.hook("prompt", prompt="before")
        (self.dir / "notes").unlink()
        self.write("notes/big.bin", "x")
        (self.dir / ".gitignore").write_text("*.bin\n")
        r = self.cli("undo", "restore", self.snap_id("before request", "'before'"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("no backup", r.stdout)
        self.assertTrue((self.dir / "notes/big.bin").exists())

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
        out, p = self.codex()
        self.assertEqual(p.returncode, 2)
        self.assertIn("independent reviewer", p.stderr)
        self.assertIn("total is wrong", p.stderr)
        prompt = (self.bin / "prompt").read_text()
        self.assertIn("Fix the total", prompt)
        self.assertIn("+x = 2", prompt)
        # The same change is never reviewed twice.
        self.assertEqual(self.codex()[1].returncode, 0)

    def test_secrets_never_reach_the_reviewer(self):
        self.fake_codex("LGTM")
        key = "sk-proj-" + "a" * 30
        self.write(".env", "OPENAI_API_KEY=old\n")
        self.hook("prompt", prompt="Use my key")
        self.write(".env", f"OPENAI_API_KEY={key}\n")
        self.write("app.py", f"KEY = '{key}'\n")
        self.ran("python3 app.py")
        self.stop()
        self.codex()
        prompt = (self.bin / "prompt").read_text()
        self.assertNotIn(key, prompt)
        self.assertNotIn(".env", prompt)
        self.assertIn("[redacted", prompt)

    def test_private_key_bodies_never_reach_the_reviewer(self):
        self.fake_codex("LGTM")
        body = "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2g"
        pem = f"-----BEGIN OPENSSH PRIVATE KEY-----\n{body}\n-----END OPENSSH PRIVATE KEY-----\n"
        self.hook("prompt", prompt="Add deploy key")
        self.write("deploy/id_ed25519", pem)
        self.write("deploy/notes.py", "KEY = " + repr(pem) + "\n")
        self.write("deploy/app.py", "print('deploying')\n")
        self.ran("python3 deploy/app.py")
        self.stop()
        self.codex()
        prompt = (self.bin / "prompt").read_text()
        self.assertIn("deploying", prompt)
        self.assertNotIn(body, prompt)
        self.assertNotIn("id_ed25519", prompt)
        self.assertNotIn("notes.py", prompt)

    def test_a_failed_review_is_retried(self):
        script = self.bin / "codex"
        script.write_text(f"#!/bin/bash\n[ \"$1\" = login ] && exit 0\necho run >> {self.bin}/calls\nexit 1\n")
        script.chmod(0o755)
        self.finish_a_verified_change()
        self.codex()
        self.stop("Done. Open http://localhost:3000 now.")
        self.codex()
        self.assertEqual((self.bin / "calls").read_text().count("run"), 2)

    def test_lgtm_stays_quiet(self):
        self.fake_codex("LGTM")
        self.finish_a_verified_change()
        out, p = self.codex()
        self.assertEqual((p.returncode, p.stderr), (0, ""))

    def test_without_codex_everything_still_works(self):
        out = self.finish_a_verified_change()
        self.assertNotIn("Codex", out["systemMessage"])
        started = time.time()
        self.assertEqual(self.codex()[1].returncode, 0)
        self.assertLess(time.time() - started, 10)

    def test_unverified_changes_are_reviewed_too(self):
        self.fake_codex("- app.py:1 — bug")
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="Fix")
        self.edit("app.py", "x = 2\n")
        self.assertIn("Codex review running", self.stop(active=True)["systemMessage"])
        self.assertEqual(self.codex()[1].returncode, 2)

    def test_codex_skips_when_stop_was_blocked(self):
        self.fake_codex("- bug")
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="Fix")
        self.edit("app.py", "x = 2\n")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertEqual(self.codex()[1].returncode, 0)


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
