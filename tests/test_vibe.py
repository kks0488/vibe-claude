"""Behavior tests for hooks/vibe.py. Run: python3 -m unittest discover -s tests -v"""

import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
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
        self.tmproot = Path(tempfile.mkdtemp(prefix="vibe-tmproot-")).resolve()  # stands in for /tmp
        self.sid, self.pid = "s1", "p1"

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.bin, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.tmproot, ignore_errors=True)

    def env(self):
        # A PATH without the real codex, so tests never call a real model.
        return dict(os.environ, CLAUDE_PROJECT_DIR=str(self.dir), PATH=f"{self.bin}:/usr/bin:/bin", LANG="en_US.UTF-8",
                    VIBE_HOME=str(self.home), VIBE_STOP_WAIT="5",
                    VIBE_TEMP_ROOTS=str(self.tmproot))  # test projects themselves live in the real temp folder

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

    def write(self, rel, text, shell=True):
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if shell:
            # These writes stand in for this session's shell commands. Feed the same hook evidence
            # as a real Bash tool; a bare folder difference could belong to another session.
            self.ran("cat > " + shlex.quote(str(path)))
        return str(path)

    def edit(self, rel, text="x = 1\n"):
        path = self.write(rel, text, shell=False)
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


class UvProofTests(Project):
    def setUp(self):
        super().setUp()
        self.hook("prompt", prompt="Check the change")

    def test_uv_value_options_find_the_actual_pytest(self):
        for options in ("--no-project --python /usr/bin/python3 --with 'pytest<9'",
                        "--python=/usr/bin/python3 --with=pytest --with 'pytest-cov'",
                        "-p /usr/bin/python3 -w pytest --with pytest-cov", "--"):
            cmd = "uv run " + options + " python -m pytest -q"
            checks = vibe.checks_in(cmd, self.dir, self.dir)
            self.assertEqual(len(checks), 1, cmd)
            self.assertEqual(checks[0]["kind"], "test")
            self.assertTrue(checks[0]["trusted"])

    def test_uv_unknown_or_missing_options_are_not_proof(self):
        for cmd in ("uv run --mystery pytest", "uv run --mystery=x pytest", "uv run --python",
                    "uv run --python= pytest", "uv run --python --with pytest pytest",
                    "uv run --directory elsewhere pytest", "uv run --package other pytest"):
            self.assertEqual(vibe.checks_in(cmd, self.dir, self.dir), [], cmd)

    def test_uv_actual_command_passes_at_stop(self):
        self.edit("app.py")
        self.ran("uv run --no-project --python /usr/bin/python3 --with 'pytest<9' python -m pytest -q")
        self.assertIn("vibe ✓", self.stop()["systemMessage"])

    def test_uv_failed_pytest_still_blocks(self):
        self.edit("app.py")
        self.ran("uv run --python=python3 --with pytest --with pytest-cov python -m pytest", ok=False)
        self.assertIn("failed", self.stop()["reason"])

    def test_uv_pipe_without_pipefail_is_still_unclear(self):
        self.edit("app.py")
        self.ran("uv run --python python3 --with pytest python -m pytest | tail -3")
        self.assertIn("hid its real result", self.stop()["reason"])

    def test_uv_pipefail_preserves_exit_evidence(self):
        self.edit("app.py")
        self.ran("set -o pipefail; uv run --python python3 --with pytest python -m pytest | tail -3")
        self.assertIn("vibe ✓", self.stop()["systemMessage"])


class SessionChangeTests(Project):
    def setUp(self):
        super().setUp()
        self.hook("prompt", prompt="Read the documentation")

    def no_snapshots(self):
        with patch.dict(os.environ, self.env()):
            vibe.Vibe({"session_id": self.sid}).save("config.json", {"snapshots": False})
        self.pid = "without-snapshot"
        self.hook("prompt", prompt="Write a brief")

    def foreign_edit(self, path="b.py"):
        target = self.dir / path
        target.write_text("x = 2\n")  # deliberately no own shell event
        self.hook("post-tool", session_id="s2", tool_name="Write", tool_input={"file_path": str(target)})

    def test_other_sessions_code_does_not_block_a_document_reader(self):
        self.ran("cat README.md")
        self.foreign_edit()
        out = self.stop("Here is the documentation.")
        self.assertNotIn("decision", out)
        self.assertIn("NOT verified", out["systemMessage"])
        self.assertIn("b.py", out["systemMessage"])
        self.assertNotIn("vibe ✓", out["systemMessage"])

    def test_unlogged_external_diff_is_not_assigned_to_this_session(self):
        (self.dir / "b.py").write_text("x = 2\n")
        out = self.stop()
        self.assertNotIn("decision", out)
        self.assertIn("b.py", out["systemMessage"])

    def test_own_shell_target_still_requires_a_check(self):
        self.write("a.py", "x = 1\n")
        self.foreign_edit()
        reason = self.stop()["reason"]
        self.assertIn("a.py", reason)
        self.assertNotIn("b.py", reason)
        self.ran("pytest")
        message = self.stop(active=True)["systemMessage"]
        self.assertIn("1 file(s) changed", message)
        self.assertIn("b.py", message)
        self.assertNotIn("vibe ✓", message)

    def test_concurrent_same_file_stays_unverified_after_a_check(self):
        self.edit("a.py")
        self.foreign_edit("a.py")
        self.ran("pytest")
        out = self.stop()
        self.assertNotIn("decision", out)
        self.assertIn("NOT verified", out["systemMessage"])
        self.assertNotIn("vibe ✓", out["systemMessage"])

    def test_bash_edit_diff_alone_does_not_prove_authorship(self):
        (self.dir / "b.py").write_text("x = 2\n")
        self.hook("post-tool", tool_name="Bash", tool_input={"command": "cat README.md"},
                  tool_response={"bashEditDiff": [{"filePath": str(self.dir / "b.py")}], "stdout": ""})
        self.assertNotIn("decision", self.stop())

    def test_unlogged_overwrite_after_own_edit_is_unverified(self):
        self.edit("a.py")
        (self.dir / "a.py").write_text("x = 99\n")
        self.ran("pytest")
        message = self.stop()["systemMessage"]
        self.assertIn("NOT verified", message)
        self.assertNotIn("vibe ✓", message)

    def test_external_edit_after_own_pass_does_not_require_another_test(self):
        self.edit("a.py")
        self.ran("pytest")
        self.foreign_edit("a.py")
        out = self.stop()
        self.assertNotIn("decision", out)
        self.assertIn("NOT verified", out["systemMessage"])
        self.assertNotIn("vibe ✓", out["systemMessage"])

    def test_no_snapshot_document_redirect_needs_no_code_test(self):
        self.no_snapshots()
        self.write("brief.md", "A short brief.\n")
        self.assertIsNone(self.stop("Here is the brief."))

    def test_no_snapshot_document_redirect_does_not_hide_a_failed_check(self):
        self.no_snapshots()
        self.write("brief.md", "A short brief.\n")
        self.ran("pytest", ok=False)
        out = self.stop("Here is the brief.")
        self.assertIsNotNone(out)
        self.assertEqual(out["decision"], "block")
        self.assertIn("failed", out["reason"])
        self.assertIn("pytest", out["reason"])

    def test_no_snapshot_document_check_can_recover_after_failure(self):
        self.no_snapshots()
        self.write("brief.md", "A short brief.\n")
        self.ran("pytest", ok=False)
        self.ran("pytest")
        self.assertIsNone(self.stop("Here is the brief."))

    def test_no_snapshot_document_ignores_previous_turn_failure(self):
        self.ran("pytest", ok=False)
        self.no_snapshots()
        self.write("brief.md", "A short brief.\n")
        self.assertIsNone(self.stop("Here is the brief."))

    def test_no_snapshot_code_redirect_still_requires_a_check(self):
        self.no_snapshots()
        self.write("app.py", "x = 1\n")
        self.assertIn("app.py", self.stop()["reason"])

    def test_no_snapshot_edit_tool_still_requires_a_check(self):
        self.no_snapshots()
        self.edit("app.py")
        self.assertIn("app.py", self.stop()["reason"])

    def test_no_snapshot_variable_and_remote_targets_are_unverified(self):
        self.no_snapshots()
        for cmd in ('cat > "$OUTPUT"', "cp brief.md host:/tmp/brief.md"):
            self.ran(cmd)
        out = self.stop("Here is the result.")
        self.assertNotIn("decision", out)
        self.assertIn("NOT verified", out["systemMessage"])
        self.assertNotIn("vibe ✓", out["systemMessage"])

    def test_unknown_shell_target_does_not_hide_a_failed_check(self):
        self.no_snapshots()
        self.ran('cat > "$OUTPUT"')
        self.ran("pytest", ok=False)
        self.assertIn("failed", self.stop()["reason"])

    def test_no_snapshot_document_plus_code_still_blocks(self):
        self.no_snapshots()
        self.ran("cat > brief.md && cat > app.py")
        reason = self.stop()["reason"]
        self.assertIn("app.py", reason)
        self.assertNotIn("brief.md", reason)

    def test_shell_literal_targets_follow_cwd_and_ignore_heredoc_body(self):
        (self.dir / "src").mkdir()
        paths, uncertain = vibe.shell_targets("cd src && cat > 'a b.py' <<'EOF'\ncat > fake.py\nEOF", self.dir)
        self.assertEqual(paths, ["src/a b.py"])
        self.assertFalse(uncertain)

    def test_sed_and_copy_targets_are_checked_without_a_snapshot(self):
        self.no_snapshots()
        for cmd in ("sed -i 's/old/new/' app.py", "cp -p old.py app.py"):
            paths, uncertain = vibe.shell_targets(cmd, self.dir)
            self.assertEqual(paths, ["app.py"])
            self.assertFalse(uncertain)
        self.ran("sed -i 's/old/new/' app.py")
        self.assertIn("app.py", self.stop()["reason"])

    def test_macos_sed_document_write_does_not_invent_a_code_target(self):
        self.no_snapshots()
        for cmd in ("sed -i '' 's/old/new/' brief.md", "sed -i.bak 's/old/new/' brief.md"):
            paths, uncertain = vibe.shell_targets(cmd, self.dir)
            self.assertEqual(paths, ["brief.md"])
            self.assertFalse(uncertain)
            self.ran(cmd)
        self.assertIsNone(self.stop())

    def test_absolute_shell_program_and_leading_redirect_still_require_checks(self):
        self.no_snapshots()
        for cmd in ("/bin/cp old.py app.py", "> app.py"):
            self.ran(cmd)
        self.assertIn("app.py", self.stop()["reason"])


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
        for cmd in ("git push -f origin main", "git -c core.x=1 push --force",
                    "psql -c 'DROP TABLE users'", "supabase db reset", "python manage.py flush",
                    "echo 'DROP TABLE x;' | psql", "sqlite3 app.db 'DELETE FROM users;'", "git branch -D old"):
            reason = self.once(cmd)
            self.assertIn("cannot be undone", reason)
            self.assertIn("will not be asked", reason)

    def test_mixed_commands_keep_files_even_when_claude_goes_ahead(self):
        self.write(".gitignore", "shots/\n")
        self.write("shots/a.png", "img")
        self.once("rm -rf shots && git branch -D old")
        self.assertIn("rm -rf shots", self.cli("trash").stdout)

    def test_git_clean_with_ignored_files_keeps_a_copy(self):
        subprocess.run(["git", "-C", str(self.dir), "init", "-q"], check=True)
        self.write(".gitignore", "*.log\n")
        self.write("debug.log", "trace")
        self.assertIsNone(self.pre("Bash", command="git clean -fdx"))
        self.assertIn("git clean -fdx", self.cli("trash").stdout)

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
        self.assertIsNone(self.pre("Bash", command=f"S={self.tmproot}/shots && rm -rf $S/cut_*.png ${{S}}/old"))
        self.assertIsNone(self.pre("Bash", command="rm -rf ../elsewhere/src/__pycache__"))

    def test_searching_or_dry_runs_are_not_dangerous(self):
        for cmd in ("grep 'DROP TABLE' migration.sql", "git clean -ndf", "rg 'rm -rf' docs", f"rm -rf {self.tmproot}/build-cache",
                    "echo 'DROP TABLE users;'"):
            self.assertIsNone(self.pre("Bash", command=cmd), cmd)

    def test_ordinary_commands_pass(self):
        for cmd in ("git status", "ls -la", "npm run build", "git push origin main", "rm notes.txt",
                    "sqlite3 app.db 'DELETE FROM users WHERE id=3;'", "git restore --staged ."):
            self.assertIsNone(self.pre("Bash", command=cmd), cmd)

    def test_deleting_a_project_test_stops_claude_once(self):
        self.write("tests/test_login.py", "def test_a():\n    assert True\n")
        self.assertIn("deleting tests to get a pass", self.once("rm tests/test_login.py"))

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

    def test_review_excludes_other_sessions_files(self):
        self.fake_codex("LGTM")
        self.hook("prompt", prompt="Fix the total")
        self.edit("app.py")
        foreign = self.dir / "foreign.py"
        foreign.write_text("foreign_marker = 99\n")
        self.hook("post-tool", session_id="other", tool_name="Write", tool_input={"file_path": str(foreign)})
        self.ran("pytest")
        self.stop()
        self.assertEqual(self.codex()[1].returncode, 0)
        prompt = (self.bin / "prompt").read_text()
        self.assertIn("app.py", prompt)
        self.assertNotIn("foreign.py", prompt)
        self.assertNotIn("foreign_marker", prompt)

    def test_external_only_changes_do_not_start_a_review(self):
        self.fake_codex("LGTM")
        self.hook("prompt", prompt="Read the brief")
        (self.dir / "foreign.py").write_text("foreign_marker = 99\n")
        self.assertNotIn("Codex review running", self.stop()["systemMessage"])
        self.assertEqual(self.codex()[1].returncode, 0)
        self.assertFalse((self.bin / "prompt").exists())

    def test_mixed_author_file_is_not_sent_to_review(self):
        self.fake_codex("LGTM")
        self.hook("prompt", prompt="Fix the total")
        self.edit("app.py")
        (self.dir / "app.py").write_text("foreign_marker = 99\n")
        self.ran("pytest")
        self.stop()
        self.assertEqual(self.codex()[1].returncode, 0)
        self.assertFalse((self.bin / "prompt").exists())


class LedgerTests(Project):
    def records(self):
        with patch.dict(os.environ, self.env()):
            v = vibe.Vibe({"session_id": self.sid, "prompt_id": self.pid})
            return v, v.ledger()

    def test_stop_block_recheck_pass_and_seven_day_counts(self):
        self.hook("prompt", prompt="change")
        self.edit("app.py")
        self.stop()
        self.ran("pytest")
        self.stop(active=True)
        v, records = self.records()
        events = [e for e in records if e["ev"].startswith("stop_")]
        self.assertEqual([e["ev"] for e in events], ["stop_block", "stop_pass"])
        self.assertTrue(events[-1]["recovered"])
        self.assertTrue(all(e["sid"] == self.sid and e["pid"] == self.pid for e in events))
        self.assertEqual(json.loads(self.cli("status").stdout)["events_7d"],
                         {"stop_block": 1, "stop_pass": 1, "stop_unverified": 0, "undo": 0})

    def test_failed_and_unverified_endings_are_events(self):
        for index, failed in enumerate((False, True)):
            self.pid = "failure" + str(index)
            self.hook("prompt", prompt="change")
            self.edit("app.py", f"x = {index + 2}\n")
            if failed:
                self.ran("pytest", ok=False)
            self.stop()
            self.stop(active=True)
        events = [e for e in self.records()[1] if e["ev"] == "stop_unverified"]
        self.assertEqual(len(events), 2)

    def test_duplicate_stop_does_not_double_count(self):
        self.hook("prompt", prompt="change")
        self.edit("app.py")
        self.ran("pytest")
        self.stop()
        self.stop()
        self.assertEqual(sum(e["ev"] == "stop_pass" for e in self.records()[1]), 1)

    def test_rotation_preserves_records_and_counts_across_months(self):
        v, _ = self.records()
        old = {"ev": "stop_block", "sid": "old", "t": time.time() - 40 * 86400}
        recent = {"ev": "stop_pass", "sid": "other", "t": time.time() - 86400}
        path = v.dir / "ledger.jsonl"
        path.write_text(json.dumps(old) + "\n" + json.dumps(recent) + "\n")
        v.log(ev="padding", text="x" * 2_000_000)
        self.assertEqual(path.read_text(), "")
        old_month = time.strftime("%Y%m", time.localtime(old["t"]))
        self.assertTrue((v.dir / f"ledger-{old_month}.jsonl").exists())
        v.log(ev="stop_unverified")
        # Rotate again into the same month. It must append, not overwrite.
        v.log(ev="padding", text="y" * 2_000_000)
        records = v.ledger()
        self.assertEqual(len(records), 5)
        self.assertIn(old, records)
        counts = json.loads(self.cli("status").stdout)["events_7d"]
        self.assertEqual(counts, {"stop_block": 0, "stop_pass": 1, "stop_unverified": 1, "undo": 0})

    def test_turn_evidence_survives_rotation(self):
        self.hook("prompt", prompt="change")
        self.edit("app.py")
        self.ran("pytest")
        v, _ = self.records()
        v.log(ev="padding", text="x" * 2_000_000)
        self.assertIn("vibe ✓", self.stop()["systemMessage"])

    def test_override_and_undo_are_recorded(self):
        self.write("app.py", "x = 1\n")
        self.hook("prompt", prompt="change")
        self.pre("Bash", command="git push --force")
        self.pre("Bash", command="git push --force")
        self.write("app.py", "x = 2\n")
        result = self.cli("undo", "restore", self.snap_id("before request"))
        self.assertEqual(result.returncode, 0)
        records = self.records()[1]
        self.assertEqual(sum(e["ev"] == "override" for e in records), 1)
        undo = [e for e in records if e["ev"] == "undo"]
        self.assertEqual(len(undo), 1)
        self.assertTrue(undo[0]["ok"])
        self.assertTrue(undo[0]["sid"])
        self.assertEqual(json.loads(self.cli("status").stdout)["events_7d"]["undo"], 1)

    def test_sessions_with_same_prompt_id_keep_separate_proof(self):
        self.hook("prompt", prompt="first session")
        self.edit("app.py")
        self.stop()
        self.sid = "s2"
        self.hook("prompt", prompt="second session")
        self.edit("other.py")
        self.ran("pytest")
        self.stop()
        self.sid = "s1"
        self.assertIn("NOT verified", self.stop(active=True)["systemMessage"])
        counts = json.loads(self.cli("status").stdout)["events_7d"]
        self.assertEqual(counts["stop_block"], 1)
        self.assertEqual(counts["stop_pass"], 1)
        self.assertEqual(counts["stop_unverified"], 1)

    def test_parallel_writers_preserve_all_events(self):
        script = ("import importlib.util,sys; "
                  "s=importlib.util.spec_from_file_location('v',sys.argv[1]); "
                  "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                  "v=m.Vibe({'session_id':sys.argv[2]}); "
                  "[v.log(ev='stop_pass', payload='x'*250000) for _ in range(5)]")
        procs = [subprocess.Popen([sys.executable, "-c", script, str(VIBE), str(i)],
                                  env=self.env(), cwd=self.dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                 for i in range(3)]
        for p in procs:
            _, err = p.communicate(timeout=30)
            self.assertEqual(p.returncode, 0, err)
        records = self.records()[1]
        self.assertEqual(len(records), 15)
        self.assertEqual({e["sid"] for e in records}, {"0", "1", "2"})

    def test_stop_identity_ignores_transcript_growth(self):
        transcript = self.write("transcript.jsonl", "first\n")
        data = dict(session_id="s1", last_assistant_message="done", stop_hook_active=False,
                    transcript_path=transcript)
        before = vibe.stop_id(data)
        Path(transcript).write_text("longer transcript\n" * 20)
        self.assertEqual(before, vibe.stop_id(data))
        self.assertNotEqual(before, vibe.stop_id(dict(data, last_assistant_message="new result")))

    def test_failed_undo_is_recorded_with_session_when_supplied(self):
        env = self.env()
        env["CLAUDE_SESSION_ID"] = "undo-session"
        p = subprocess.run([sys.executable, str(VIBE), "undo", "restore", "bad-id"],
                           env=env, cwd=self.dir, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        events = [e for e in self.records()[1] if e["ev"] == "undo"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["sid"], "undo-session")
        self.assertFalse(events[0]["ok"])

    def test_truncated_legacy_line_does_not_swallow_new_event(self):
        v, _ = self.records()
        (v.dir / "ledger.jsonl").write_text('{"ev":"broken"')
        v.log(ev="stop_pass")
        records = v.ledger()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["ev"], "stop_pass")


class ScopeTests(Project):
    def setUp(self):
        super().setUp()
        self.hook("prompt", prompt="고쳐주세요")

    def test_unrelated_project_script_is_only_partial_proof(self):
        self.edit("app.py")
        self.write("noop.py", "pass\n")
        self.ran("python3 noop.py")
        result = self.stop("실행 결과를 확인했어요.")
        self.assertIn("부분 확인", result["systemMessage"])
        self.assertNotIn("vibe ✓", result["systemMessage"])
        self.assertIn("app.py", result["systemMessage"])

    def test_run_of_one_changed_file_does_not_cover_another(self):
        self.edit("app.py")
        self.edit("helper.py")
        self.ran("python3 app.py")
        self.assertIn("부분 확인", self.stop(active=True)["systemMessage"])
        self.ran("python3 helper.py")
        self.assertIn("vibe ✓", self.stop(active=True)["systemMessage"])

    def test_inline_import_of_another_module_is_partial(self):
        self.edit("app.py")
        self.write("noop.py", "pass\n")
        self.ran('python3 -c "import noop"')
        self.assertIn("부분 확인", self.stop()["systemMessage"])

    def test_receipt_names_test_build_and_run_evidence(self):
        self.edit("app.py")
        self.ran("pytest")
        self.ran("npm run build")
        self.ran("python3 app.py")
        message = self.stop()["systemMessage"]
        for label in ("시험 통과", "빌드 통과", "프로그램 실행"):
            self.assertIn(label, message)

    def test_check_in_other_folder_is_partial(self):
        self.edit("api/app.py")
        self.ran("cd web && npm test")
        self.assertIn("부분 확인", self.stop()["systemMessage"])

    def test_korean_completion_with_evidence_has_no_language_nag(self):
        self.edit("app.py")
        self.ran("pytest")
        self.assertNotIn("decision", self.stop("시험을 통과했고 `python3 app.py`로 보실 수 있어요."))

    def test_idle_turns_stay_silent_but_unchecked_changes_block(self):
        self.assertIsNone(self.hook("session-start", source="resume")[0])
        self.assertIsNone(self.ran("git status --short"))
        self.assertIsNone(self.stop("안녕하세요."))
        self.edit("app.py")
        self.assertEqual(self.stop()["decision"], "block")

    def test_writing_unchanged_content_has_no_guidance_or_receipt(self):
        self.write("app.py", "x = 1\n")
        self.pid = "same-content"
        self.hook("prompt", prompt="그대로 두기")
        self.assertIsNone(self.edit("app.py", "x = 1\n"))
        self.assertIsNone(self.stop())


class RemoteTests(Project):
    def setUp(self):
        super().setUp()
        self.hook("prompt", prompt="원격 작업")

    def test_remote_create_blocks_once_then_reports_unverified(self):
        self.ran("gh pr create -R org/repo --title fix --body ok", stdout="https://github.com/org/repo/pull/42\n")
        self.assertIn("원격 결과를 다시 읽어", self.stop("완료했어요.")["reason"])
        # Even missing stop_hook_active must not cause an endless loop.
        out = self.stop("다시 확인할 수 없어요.")
        self.assertNotIn("decision", out)
        self.assertIn("원격 결과 확인 못 함", out["systemMessage"])

    def test_same_target_after_write_is_verified(self):
        self.ran("gh issue create -R org/repo --title fix --body ok", stdout="https://github.com/org/repo/issues/7\n")
        self.ran("gh issue view 7 -R org/repo")
        out = self.stop("완료했어요.")
        self.assertIn("원격 결과 다시 읽음", out["systemMessage"])
        self.assertNotIn("decision", out)

    def test_other_target_repo_and_earlier_read_do_not_count(self):
        self.ran("gh pr view 42 -R org/repo")
        self.ran("gh pr merge 42 -R org/repo --squash")
        self.ran("gh pr view 43 -R org/repo")
        self.ran("gh pr view 42 -R org/other")
        self.assertEqual(self.stop()["decision"], "block")

    def test_failed_read_is_not_evidence_and_never_repeats_write(self):
        self.ran("gh issue close 7 -R org/repo")
        self.ran("gh issue view 7 -R org/repo", ok=False)
        self.assertEqual(self.stop()["decision"], "block")
        self.assertIn("원격 결과 확인 못 함", self.stop(active=True)["systemMessage"])
        with patch.dict(os.environ, self.env()):
            records = vibe.Vibe({"session_id": self.sid, "prompt_id": self.pid}).turn()
        self.assertEqual(sum(e.get("action") == "write" for e in records), 1)

    def test_unknown_created_identity_cannot_match_random_view(self):
        self.ran("gh pr create -R org/repo --title 42 --body ok", stdout="created")
        self.ran("gh pr view 42 -R org/repo")
        self.assertEqual(self.stop()["decision"], "block")

    def test_release_tag_re_read(self):
        self.ran("gh release create v1.0 -R org/repo")
        self.ran("gh release view v1.0 -R org/repo")
        self.assertIn("원격 결과 다시 읽음", self.stop()["systemMessage"])

    def test_git_push_requires_same_remote_and_branch(self):
        self.ran("git push origin main")
        self.ran("git ls-remote other refs/heads/main")
        self.ran("git ls-remote origin refs/heads/dev")
        self.assertEqual(self.stop()["decision"], "block")
        self.ran("git ls-remote origin refs/heads/main")
        self.assertIn("원격 결과 다시 읽음", self.stop(active=True)["systemMessage"])

    def test_push_can_be_re_read_with_workflow_on_same_repo_branch(self):
        self.ran("git push https://github.com/org/repo.git main")
        self.ran("gh run list -R org/repo --branch main")
        self.assertIn("원격 결과 다시 읽음", self.stop()["systemMessage"])

    def test_deployment_requires_exact_url(self):
        self.ran("vercel deploy --prod", stdout="Production: https://my-app.vercel.app\n")
        self.ran("curl https://other-app.vercel.app")
        self.assertEqual(self.stop()["decision"], "block")
        self.ran("curl -f https://my-app.vercel.app")
        self.assertIn("원격 결과 다시 읽음", self.stop(active=True)["systemMessage"])

    def test_npm_publish_requires_same_package_version(self):
        self.write("package.json", '{"name":"@org/pkg","version":"1.2.3"}')
        self.ran("npm publish")
        self.ran("npm view @org/pkg@1.2.2 version")
        self.assertEqual(self.stop()["decision"], "block")
        self.ran("npm view @org/pkg@1.2.3 version", stdout="1.2.3")
        self.assertIn("원격 결과 다시 읽음", self.stop(active=True)["systemMessage"])

    def test_local_check_does_not_verify_remote_write(self):
        self.edit("app.py")
        self.ran("gh pr merge 42 -R org/repo")
        self.ran("pytest")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertIn("원격 결과 확인 못 함", self.stop(active=True)["systemMessage"])

    def test_email_send_and_commands_that_only_mention_remote_are_out_of_scope(self):
        self.write("send_email.py", "pass\n")
        self.pid = "email"
        self.hook("prompt", prompt="이메일 보내기")
        self.ran("python3 send_email.py")
        self.ran("echo 'gh pr create'")
        self.assertIsNone(self.stop())

    def test_remote_read_before_a_second_write_does_not_cover_it(self):
        self.ran("gh issue close 7 -R org/repo")
        self.ran("gh issue view 7 -R org/repo")
        self.ran("gh issue close 7 -R org/repo")
        self.assertEqual(self.stop()["decision"], "block")

    def test_remote_only_events_are_counted(self):
        self.ran("gh issue close 7 -R org/repo")
        self.stop()
        self.ran("gh issue view 7 -R org/repo")
        self.stop(active=True)
        counts = json.loads(self.cli("status").stdout)["events_7d"]
        self.assertEqual(counts["stop_block"], 1)
        self.assertEqual(counts["stop_pass"], 1)

    def test_help_dry_run_and_vercel_reads_are_idle(self):
        for cmd in ("gh pr create --help", "git push --dry-run origin main", "npm publish --dry-run",
                    "vercel --help", "vercel --version", "vercel ls", "vercel inspect example"):
            self.assertIsNone(self.ran(cmd), cmd)
        self.assertIsNone(self.stop())

    def test_named_remotes_in_other_directories_do_not_match(self):
        self.write("one/.keep", "")
        self.write("two/.keep", "")
        self.ran("cd one && git push origin main")
        self.ran("cd two && git ls-remote origin main")
        self.assertEqual(self.stop()["decision"], "block")

    def test_list_remote_refs_reads_the_pushed_branch_from_output(self):
        self.ran("git push origin main")
        self.ran("git ls-remote origin", stdout="a" * 40 + "\trefs/heads/main\n")
        self.assertIn("원격 결과 다시 읽음", self.stop()["systemMessage"])

    def test_npm_view_version_output_identifies_the_published_version(self):
        self.write("package.json", '{"name":"@org/pkg","version":"1.2.3"}')
        self.pid = "publish-existing-package"
        self.hook("prompt", prompt="패키지 올리기")
        self.ran("npm publish")
        self.ran("npm view @org/pkg version", stdout='"1.2.3"\n')
        self.assertIn("원격 결과 다시 읽음", self.stop()["systemMessage"])

    def test_hidden_or_background_read_does_not_count(self):
        self.ran("gh issue close 7 -R org/repo")
        self.ran("gh issue view 7 -R org/repo || true")
        self.ran("gh issue view 7 -R org/repo &")
        self.assertEqual(self.stop()["decision"], "block")

    def test_readback_is_not_a_business_success_claim(self):
        self.ran("gh pr merge 42 -R org/repo")
        self.ran("gh pr view 42 -R org/repo --json state", stdout='{"state":"OPEN"}')
        message = self.stop()["systemMessage"]
        self.assertIn("원격 결과 다시 읽음", message)
        self.assertNotIn("merge succeeded", message)
        self.assertNotIn("완료", message)


class SessionTests(Project):
    def test_rules_wait_for_actual_work(self):
        self.assertIsNone(self.hook("session-start", source="startup")[0])
        self.assertIsNone(self.hook("prompt", prompt="hello")[0])
        self.assertIsNone(self.stop("Hello!"))
        out = self.edit("app.py")
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Prove it", ctx)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertLess(len(ctx), 1500)
        self.assertIsNone(self.edit("app.py", "x = 2\n"))

    def test_internal_errors_fail_open(self):
        out, p = self.hook("stop", last_assistant_message=None, stop_hook_active="weird", background_tasks=None)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
