#!/usr/bin/env python3
"""vibe-claude v6: proof, guard and undo for people who don't read code.

One script, called by hooks/hooks.json as `vibe.py <event>`, plus a small CLI
(`vibe.py undo|checks|status`) used by the undo skill. Standard library only.
State lives outside the project in ~/.vibe-claude (override: VIBE_HOME), so a
cloned repository cannot plant commands and `git clean` cannot delete backups.
Every hook fails open: an internal error never blocks the user's work.
"""

import hashlib
from contextlib import contextmanager
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "6.1.0"
LEDGER_MAX = 2_000_000
DEFAULTS = {"codex": "auto", "ratchet": True, "snapshots": True, "packages": True, "lang": None, "safe_to_delete": []}
DOC_EXT = {"md", "mdx", "txt", "rst", "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "pdf", "csv", "lock",
           "log", "snap", "map"}
MAX_FILE = 5_000_000      # files bigger than this are not snapshotted
TRASH_MAX = 300_000_000   # deletes of unbacked-up files up to this size are copied to the trash first
TRASH_FILES = 20_000
TRASH_KEEP = 7 * 86400    # trash older than this is emptied
KEEP_SNAPSHOTS = 150      # older snapshots are pruned
SHADOW_EXCLUDES = """node_modules/
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.next/
.nuxt/
.turbo/
.cache/
dist/
build/
target/
coverage/
*.log
.DS_Store
.git/
"""
SECRET_FILES = re.compile(r"(^|/)\.env(\.[\w.-]+)?$|\.(pem|key|p12|pfx)$|(^|/)(id_rsa|id_ed25519)[^/]*$")

# --------------------------------------------------------------------------- text shown to the user

MSG = {
    "receipt_ok": ("vibe ✓ {n} file(s) changed / checked: {checks}{codex} / undo: /vibe-claude:undo",
                   "vibe ✓ 파일 {n}개 변경 / 확인됨: {checks}{codex} / 되돌리기: /vibe-claude:undo"),
    "receipt_none": ("vibe ⚠ {n} file(s) changed / NOT verified: nothing was run to check it{codex} / undo: /vibe-claude:undo",
                     "vibe ⚠ 파일 {n}개 변경 / 확인 안 됨: 실행해서 확인한 기록이 없어요{codex} / 되돌리기: /vibe-claude:undo"),
    "receipt_fail": ("vibe ✗ {n} file(s) changed / check FAILED: {cmd}{codex} / undo: /vibe-claude:undo",
                     "vibe ✗ 파일 {n}개 변경 / 검사 실패: {cmd}{codex} / 되돌리기: /vibe-claude:undo"),
    "receipt_partial": ("vibe ⚠ {n} file(s) changed / partially verified: {checks}, but {cmd} gave no clear result{codex} / undo: /vibe-claude:undo",
                        "vibe ⚠ 파일 {n}개 변경 / 부분 확인: {checks}, 하지만 {cmd}는 결과가 불분명해요{codex} / 되돌리기: /vibe-claude:undo"),
    "receipt_scope": ("vibe ⚠ {n} file(s) changed / partially verified: {checks}; uncovered: {files}{codex} / undo: /vibe-claude:undo",
                      "vibe ⚠ 파일 {n}개 변경 / 부분 확인: {checks}; 확인 못 한 파일: {files}{codex} / 되돌리기: /vibe-claude:undo"),
    "remote_missing": ("remote result NOT verified", "원격 결과 확인 못 함"),
    "remote_ok": ("remote result re-read", "원격 결과 다시 읽음"),
    "codex_wait": (" / Codex review running", " / Codex 검토 중"),
    "irreversible": (" / could not be undone: {what}", " / 되돌릴 수 없는 작업이 있었어요 — {what}"),
    "irreversible_only": ("vibe ⚠ could not be undone: {what}", "vibe ⚠ 되돌릴 수 없는 작업이 있었어요 — {what}"),
}


def t(key, lang, **kw):
    en, ko = MSG[key]
    return (ko if lang == "ko" else en).format(**kw)


# --------------------------------------------------------------------------- core


def read_input():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False))


def run(args, cwd=None, env=None, timeout=30, input_text=None):
    try:
        p = subprocess.run(args, cwd=cwd, env=env, input=input_text, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as e:
        return 127, "", str(e)


def inside(path, root):
    try:
        return os.path.commonpath([os.path.realpath(path), os.path.realpath(root)]) == os.path.realpath(root)
    except ValueError:
        return False


class Vibe:
    def __init__(self, data):
        self.data = data
        root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
        self.root = Path(root).resolve()
        # Never keep state for a home folder or filesystem root: too big to snapshot.
        self.enabled = self.root.is_dir() and self.root not in (Path.home().resolve(), Path("/"))
        home = Path(os.environ.get("VIBE_HOME") or Path.home() / ".vibe-claude")
        slug = re.sub(r"[^\w.-]", "_", self.root.name)[:40]
        self.dir = home / "projects" / f"{slug}-{hashlib.sha1(str(self.root).encode()).hexdigest()[:10]}"
        self.sid = str(data.get("session_id", ""))
        self.pid = str(data.get("prompt_id", ""))

    # ---- files
    def state_name(self, name):
        # Stop decisions, warning retries and review budgets belong to a session.
        if name == "state.json" and self.sid and self.sid != "cli":
            return "state-" + hashlib.sha1(self.sid.encode()).hexdigest()[:16] + ".json"
        return name

    def load(self, name, default):
        try:
            return json.loads((self.dir / self.state_name(name)).read_text())
        except (OSError, ValueError):
            return default

    def save(self, name, value):
        name = self.state_name(name)
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.dir / f"{name}.{os.getpid()}.tmp"
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
        tmp.replace(self.dir / name)

    @property
    def config(self):
        cfg = dict(DEFAULTS)
        cfg.update(self.load("config.json", {}))
        try:
            project = json.loads((self.root / ".vibe" / "config.json").read_text())
            cfg.update({k: v for k, v in project.items() if k in DEFAULTS})
        except (OSError, ValueError, AttributeError):
            pass
        return cfg

    @property
    def lang(self):
        return self.config["lang"] or self.load("state.json", {}).get("lang") or (
            "ko" if os.environ.get("LANG", "").startswith("ko") else "en")

    def state_update(self, **kw):
        st = self.load("state.json", {})
        st.update(kw)
        self.save("state.json", st)
        return st

    # ---- ledger
    @contextmanager
    def ledger_lock(self):
        """Serialize append, rotation and readers across hook processes."""
        self.dir.mkdir(parents=True, exist_ok=True)
        with (self.dir / "ledger.lock").open("a+b") as lock:
            if os.name == "nt":
                import msvcrt
                lock.write(b"\0")
                lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock, fcntl.LOCK_UN)

    def ledger(self):
        """Read archives too, including requests that straddle a rotation."""
        with self.ledger_lock():
            return self.read_ledger()

    def read_ledger(self):
        """Caller holds ledger_lock, including when checking event idempotency."""
        out = []
        paths = sorted(self.dir.glob("ledger-[0-9][0-9][0-9][0-9][0-9][0-9].jsonl"))
        paths.append(self.dir / "ledger.jsonl")
        for path in paths:
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                try:
                    e = json.loads(line)
                    if isinstance(e, dict):
                        out.append(e)
                except ValueError:
                    continue  # old or interrupted records are not events
        return sorted(out, key=lambda e: e.get("t", 0))

    def log(self, **entry):
        if not self.enabled:
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        entry.update(t=time.time(), sid=self.sid, pid=self.pid, version=VERSION)
        path = self.dir / "ledger.jsonl"
        with self.ledger_lock():
            if entry.get("event_id") and any(e.get("event_id") == entry["event_id"] for e in self.read_ledger()):
                return
            with path.open("a+b") as f:
                # Do not join a new event to a truncated legacy record.
                f.seek(0, os.SEEK_END)
                if f.tell():
                    f.seek(-1, os.SEEK_END)
                    if f.read(1) != b"\n":
                        f.write(b"\n")
                f.write((json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
            if path.stat().st_size > LEDGER_MAX:
                # Append to monthly archives. Keep even malformed legacy lines.
                months = {}
                for line in path.read_text().splitlines(keepends=True):
                    try:
                        ts = json.loads(line).get("t", entry["t"])
                        month = time.strftime("%Y%m", time.localtime(ts))
                    except (ValueError, TypeError, AttributeError, OverflowError, OSError):
                        month = time.strftime("%Y%m")
                    months.setdefault(month, []).append(line)
                for month, lines in months.items():
                    with (self.dir / f"ledger-{month}.jsonl").open("a") as archive:
                        archive.writelines(lines)
                path.write_text("")

    def turn(self):
        """Ledger entries of the current user request (same prompt_id)."""
        out = []
        for e in self.ledger():
            if e.get("sid") != self.sid:
                continue
            if self.pid:
                if e.get("pid") == self.pid:
                    out.append(e)
            elif e.get("ev") == "turn":
                out = [e]
            else:
                out.append(e)
        return out

    def stop_event(self, ev, **details):
        turn = self.turn()
        start = next((e["t"] for e in reversed(turn) if e.get("ev") == "turn"), 0)
        key = hashlib.sha1(json.dumps([self.sid, self.pid, start, stop_id(self.data), ev]).encode()).hexdigest()
        if not any(e.get("event_id") == key for e in turn):
            self.log(ev=ev, event_id=key, **details)

    # ---- shadow snapshots: a private git repository outside the project, never the user's .git
    def git(self, *args, index=None, timeout=60, input_text=None):
        env = dict(os.environ, GIT_DIR=str(self.dir / "shadow.git"), GIT_WORK_TREE=str(self.root),
                   GIT_INDEX_FILE=str(index or self.dir / "shadow.git" / "index"),
                   GIT_AUTHOR_NAME="vibe", GIT_AUTHOR_EMAIL="vibe@localhost",
                   GIT_COMMITTER_NAME="vibe", GIT_COMMITTER_EMAIL="vibe@localhost")
        for k in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE"):
            env.pop(k, None)
        return run(["git", *args], cwd=self.root, env=env, timeout=timeout, input_text=input_text)

    def snapshots_on(self):
        st = self.load("state.json", {})
        return (self.enabled and self.config["snapshots"] and shutil.which("git")
                and time.time() > st.get("snap_paused_until", 0))

    def snapshot(self, kind, label=""):
        """Save the project's files; return the snapshot id, or None when no backup was made.

        Every snapshot is a standalone commit with its own ref (refs/snaps/<time>), so pruning old ones
        never changes the id of a recent one.
        """
        if not self.snapshots_on():
            return None
        repo = self.dir / "shadow.git"
        if not repo.exists():
            self.dir.mkdir(parents=True, exist_ok=True)
            if run(["git", "init", "-q", "--bare", str(repo)])[0]:
                return None
            for key, value in (("core.bare", "false"), ("gc.auto", "0"), ("core.autocrlf", "false"),
                               ("core.quotepath", "false")):
                run(["git", "--git-dir", str(repo), "config", key, value])
            (repo / "info").mkdir(exist_ok=True)
            (repo / "info" / "exclude").write_text(SHADOW_EXCLUDES)
        big = self.exclude_big_files(repo)
        started = time.time()
        rc, _, _ = self.git("add", "-A", ".", timeout=40)
        if rc == 124 or time.time() - started > 20:  # too slow for this project: pause for a day
            self.state_update(snap_paused_until=time.time() + 86400)
        if rc:
            return None
        for rel in big:  # ignore rules do not apply to files already in the index
            self.git("rm", "-q", "--cached", "--ignore-unmatch", "--", rel)
        if big and self.git("ls-files", "-z", "--", *big)[1].strip("\0"):
            return None  # a large file is still in the index: better no backup than a huge one
        rc, tree, _ = self.git("write-tree")
        if rc:
            return None
        tree = tree.strip()
        latest = self.snapshots(1)
        if latest and kind not in ("turn", "undo"):
            _, head_tree, _ = self.git("rev-parse", latest[0]["sha"] + "^{tree}")
            if head_tree.strip() == tree:
                return latest[0]["sha"]
        meta = json.dumps({"t": time.time(), "kind": kind, "label": label[:120]}, ensure_ascii=False)
        rc, commit, _ = self.git("commit-tree", tree, "-m", meta)
        if rc:
            return None
        commit = commit.strip()
        self.git("update-ref", f"refs/snaps/{time.time():017.6f}-{commit[:8]}", commit)
        return commit

    def exclude_big_files(self, repo):
        """Keep files over MAX_FILE out of snapshots, remembering them across runs."""
        big_file = repo / "big-files"
        try:
            known = set(filter(None, big_file.read_text().split("\0")))
        except OSError:
            known = set()
        _, out, _ = self.git("ls-files", "-z", "--others", "--cached", "--exclude-standard", timeout=30)
        big = set()
        for rel in known | set(filter(None, out.split("\0"))):
            try:
                if (self.root / rel).is_file() and (self.root / rel).stat().st_size > MAX_FILE:
                    big.add(rel)
            except OSError:
                pass
        big_file.write_text("\0".join(sorted(big)))
        escape = lambda rel: "/" + re.sub(r"([\\*?\[\]!#])", r"\\\1", rel)
        (repo / "info" / "exclude").write_text(SHADOW_EXCLUDES + "\n".join(escape(r) for r in sorted(big)) + "\n")
        return sorted(big)

    def prune(self):
        """Delete all but the newest KEEP_SNAPSHOTS snapshots (recent ids stay valid)."""
        rc, out, _ = self.git("for-each-ref", "--sort=-refname", "--format=%(refname)", "refs/snaps/")
        refs = out.split()
        if rc or len(refs) <= KEEP_SNAPSHOTS + 20:
            return
        keep = {s.get("snap") for s in self.load("state.json", {}).get("turns", {}).values()}
        for ref in refs[KEEP_SNAPSHOTS:]:
            _, sha, _ = self.git("rev-parse", ref)
            if sha.strip() not in keep:
                self.git("update-ref", "-d", ref)
        self.git("gc", "-q", "--prune=now", timeout=300)

    def snapshots(self, limit=20):
        rc, out, _ = self.git("for-each-ref", "--sort=-refname", f"--count={limit}",
                              "--format=%(objectname) %(contents:subject)", "refs/snaps/")
        snaps = []
        if rc:
            return snaps
        for line in out.splitlines():
            sha, _, meta = line.partition(" ")
            try:
                info = json.loads(meta)
            except ValueError:
                info = {"t": 0, "kind": "?", "label": meta}
            info["sha"] = sha
            snaps.append(info)
        return snaps

    def resolve(self, snap_id):
        if not re.fullmatch(r"[0-9a-f]{6,40}", snap_id or ""):
            return None
        rc, sha, _ = self.git("rev-parse", "-q", "--verify", snap_id + "^{commit}")
        sha = sha.strip()
        if rc or not self.git("for-each-ref", "--points-at", sha, "refs/snaps/")[1].strip():
            return None
        return sha

    def files_in(self, ref):
        rc, out, _ = self.git("ls-tree", "-r", "-z", "--name-only", ref)
        return set(filter(None, out.split("\0"))) if rc == 0 else set()

    def changed(self, before, after):
        """[(status, path)] between two snapshots, or None when they cannot be compared."""
        rc, out, _ = self.git("diff", "--name-status", "-z", "--no-renames", before, after)
        if rc:
            return None
        parts = out.split("\0")
        return [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2) if parts[i]]

    def restore(self, sha):
        target = self.files_in(sha)
        before = self.snapshot("undo", "before undo to " + sha[:10])
        if not before:
            return False, "could not back up the current files first, so nothing was changed"
        current = self.files_in(before)
        extra = current - target
        problems = []
        for rel in target | extra:
            parts = Path(rel).parts
            p = self.root
            for i, part in enumerate(parts[:-1]):
                p = p / part
                prefix = "/".join(parts[:i + 1])
                if p.is_symlink() or (p.exists() and not p.is_dir() and prefix not in current):
                    problems.append(rel)
                    break
            else:
                full = self.root / rel
                if rel in target and full.is_dir() and not full.is_symlink():
                    problems.append(rel)  # a folder now sits where a file goes; it may hold unsaved files
                elif rel in target and (full.is_file() or full.is_symlink()) and rel not in current:
                    problems.append(rel)  # an existing file that is not in the backup would be overwritten
        if problems:
            return False, ("stopped without changing anything: restoring would overwrite or delete files that have "
                           "no backup (ignored or too large): " + ", ".join(sorted(problems)[:5]))
        index = self.dir / "restore.index"
        try:
            if self.git("read-tree", sha, index=index)[0]:
                return False, "unknown snapshot"
            rc, _, err = self.git("checkout-index", "-a", "-f", index=index)
            if rc:
                return False, err
        finally:
            index.unlink(missing_ok=True)
        for rel in extra:
            p = self.root / rel
            if (p.is_file() or p.is_symlink()) and inside(p.parent, self.root):
                p.unlink()
        return True, before

    def unsaved_under(self, targets):
        """True when a target holds files the backup does not cover (ignored, too large, or outside)."""
        for target in targets:
            path = os.path.realpath(target)
            if not inside(path, self.root):
                return True
            rel = os.path.relpath(path, self.root)
            if rel == ".":
                return True
            if self.git("check-ignore", "-q", "--no-index", rel)[0] == 0:
                return True
            _, out, _ = self.git("ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory",
                                 "--", rel, timeout=30)
            if out.strip("\0"):
                return True
            try:
                big = set(filter(None, (self.dir / "shadow.git" / "big-files").read_text().split("\0")))
            except OSError:
                big = set()
            if any(b == rel or b.startswith(rel.rstrip("/") + "/") for b in big):
                return True
        return False


# --------------------------------------------------------------------------- reading shell commands

OPERATORS = {"&&", "||", ";", "|", "&", "|&", ";;"}
REDIRECTS = re.compile(r"^[0-9]*(>>?|<<?<?|>&|<&|&>>?|>\|)$")
WRAPPERS = {"sudo", "doas", "env", "nohup", "time", "command", "exec", "nice", "timeout", "caffeinate", "xargs", "builtin"}
WRAPPER_ARGS = {"sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U"}, "env": {"-u", "-C", "-S"},
                "nice": {"-n"}, "xargs": {"-I", "-n", "-P", "-L", "-d", "-s", "-E"}, "timeout": {"-s", "-k"}}


HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][\w-]*)\2")


def strip_heredocs(cmd):
    """Drop here-document bodies (`<<EOF ... EOF`): they are text fed to a program, not commands."""
    out, waiting = [], []
    for line in cmd.split("\n"):
        if waiting:
            dash, word = waiting[0]
            if (line.lstrip("\t") if dash else line) == word:
                waiting.pop(0)
            continue
        out.append(line)
        waiting = [(m.group(1), m.group(3)) for m in HEREDOC.finditer(line)]
    return "\n".join(out)


def segments(cmd):
    """Split a shell command into [(operator_before, tokens)], dropping redirections and here-documents."""
    lex = shlex.shlex(strip_heredocs(cmd).replace("\n", " ; "), posix=True, punctuation_chars=";&|<>()")
    lex.whitespace_split = True
    try:
        toks = list(lex)
    except ValueError:
        toks = cmd.split()
    segs, cur, op, skip = [], [], "", False
    for i, tk in enumerate(toks):
        if skip:
            skip = False
            continue
        if tk in OPERATORS:
            if cur:
                segs.append((op, cur))
            cur, op = [], tk
        elif tk in ("(", ")", "{", "}"):
            continue
        elif REDIRECTS.match(tk):
            if cur and cur[-1].isdigit():
                cur.pop()
            skip = True
        else:
            cur.append(tk)
    if cur:
        segs.append((op, cur))
    elif op in ("&", "|", "||", "&&"):  # trailing operator, e.g. `pytest &` runs in the background
        segs.append((op, []))
    return segs


def unwrap(toks):
    """Drop env assignments and wrappers (sudo, env, npx, uv run, python -m ...) to find the real program."""
    toks = list(toks)
    while toks:
        name = os.path.basename(toks[0])
        if re.match(r"^[A-Za-z_]\w*=", toks[0]):
            toks.pop(0)
        elif name in WRAPPERS:
            toks.pop(0)
            while toks and (toks[0].startswith("-") or (name == "env" and re.match(r"^[A-Za-z_]\w*=", toks[0]))):
                opt = toks.pop(0)
                if opt in WRAPPER_ARGS.get(name, ()) and toks:
                    toks.pop(0)
            if name == "timeout" and toks:
                toks.pop(0)
        elif name in ("npx", "bunx"):
            toks.pop(0)
            while toks and toks[0].startswith("-"):
                if toks.pop(0) in ("-p", "--package") and toks:
                    toks.pop(0)
        elif name in ("pnpm", "yarn") and len(toks) > 1 and toks[1] in ("dlx", "exec"):
            toks = toks[2:]
        elif name in ("uv", "poetry", "pipenv", "pdm", "hatch", "rye") and len(toks) > 1 and toks[1] == "run":
            toks = toks[2:]
            while toks and toks[0].startswith("-"):
                toks.pop(0)
        elif re.match(r"^python[\d.]*$", name) and len(toks) > 2 and toks[1] == "-m":
            toks = toks[2:]
        else:
            break
    return toks


TEST_PROGS = {"pytest", "py.test", "unittest", "nose2", "tox", "nox", "vitest", "jest", "mocha", "jasmine", "karma",
              "rspec", "phpunit", "pest", "bats", "ctest", "ava", "tap"}
TYPE_PROGS = {"tsc", "vue-tsc", "mypy", "pyright", "basedpyright"}
LINT_PROGS = {"eslint", "ruff", "flake8", "pylint", "shellcheck", "golangci-lint", "biome", "stylelint", "rubocop",
              "swiftlint", "oxlint", "hadolint"}
FORMAT_CHECK = {"prettier", "black", "gofmt", "rustfmt"}
LANG_TOOLS = {"go", "cargo", "swift", "dotnet", "deno", "mix", "flutter", "dart", "zig"}
BUILD_TOOLS = {"vite", "next", "nuxt", "astro", "turbo", "webpack", "esbuild", "rollup", "tsup", "parcel"}
RUNNERS = {"python", "python3", "node", "bun", "deno", "ruby", "php", "tsx", "ts-node", "bash", "sh", "zsh", "perl"}
LONG_RUNNING = {"dev", "start", "serve", "watch", "preview"}
INFO_FLAGS = {"--help", "-h", "--version", "-V", "--list", "--collect-only", "--co", "--dry-run", "--listTests"}


def script_kind(name):
    name = name.lower()
    if any(w in name for w in LONG_RUNNING):
        return None
    if re.search(r"test|spec|e2e", name):
        return "test"
    if re.search(r"type|tsc", name):
        return "type"
    if "lint" in name or name in ("check", "validate"):
        return "lint"
    if "build" in name or name == "compile":
        return "build"
    return None


def verifier(toks, root=None):
    """Return the kind of check a single command is ('test', 'type', 'lint', 'build', 'run') or None."""
    toks = unwrap(toks)
    if not toks or any(a in INFO_FLAGS or a.startswith("--watch") for a in toks[1:]):
        return None
    prog, args = os.path.basename(toks[0]), toks[1:]
    sub = args[0] if args else ""
    if prog in TEST_PROGS:
        return "test"
    if prog in TYPE_PROGS:
        return "type"
    if prog in LINT_PROGS:
        return None if prog == "ruff" and sub == "format" and "--check" not in args else "lint"
    if prog in FORMAT_CHECK:
        return "lint" if "--check" in args or "-l" in args else None
    if prog in ("npm", "pnpm", "yarn", "bun"):
        if sub in ("test", "t", "tst"):
            return "test"
        if sub == "run" and len(args) > 1:
            return script_kind(args[1])
        if prog != "npm" and sub and not sub.startswith("-") and sub not in ("install", "add", "i", "remove", "x"):
            return script_kind(sub)
        return None
    if prog in LANG_TOOLS:
        return {"test": "test", "build": "build", "check": "type", "vet": "type", "clippy": "lint",
                "lint": "lint"}.get(sub)
    if prog in ("make", "gmake"):
        if sub in ("test", "check", "tests"):
            return "test"
        return "build" if not sub or sub in ("all", "build") else None
    if prog in ("mvn", "mvnw", "./mvnw"):
        return "test" if {"test", "verify"} & set(args) else ("build" if {"package", "install", "compile"} & set(args) else None)
    if prog in ("gradle", "gradlew"):
        return "test" if {"test", "check"} & set(args) else ("build" if {"build", "assemble"} & set(args) else None)
    if prog == "xcodebuild":
        return "test" if "test" in args else "build"
    if prog == "playwright" and sub == "test" or prog == "cypress" and sub == "run":
        return "test"
    if prog in BUILD_TOOLS and (sub == "build" or prog in ("webpack", "esbuild", "rollup", "tsup", "parcel")):
        return "build"
    if prog == "claude" and args[:2] == ["plugin", "validate"]:
        return "lint"
    if prog in ("curl", "wget", "http", "xh") and any(re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0)", a) for a in args):
        return "run"
    if prog in RUNNERS:
        if "-n" in args and prog in ("bash", "sh", "zsh"):
            return "lint"
        inline = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-c", "-e", "--eval", "-p")), None)
        if inline is not None:  # inline code counts only when it actually loads project code
            return "run" if root and loads_project_code(inline, root) else None
        if "-" in args:
            return None
        target = next((a for a in args if not a.startswith("-")), "")
        if target and root and (Path(root) / target).is_file():
            return "test" if re.search(r"(^|/)tests?/|(^|/)test_|_test\.|\.test\.", target) else "run"
    return None


def loads_project_code(code, root):
    names = re.findall(r"(?:^|[;\s(])(?:from|import)\s+([A-Za-z_][\w.]*)", code)
    names += [m.lstrip("./") for m in re.findall(r"(?:require\(|import\(|from\s+)['\"](\.{1,2}/[^'\"]+)['\"]", code)]
    for name in names:
        base = Path(root) / name.replace(".", "/") if "/" not in name else Path(root) / name
        candidates = [base] + [base.with_name(base.name + ext) for ext in (".py", ".js", ".mjs", ".cjs", ".ts")]
        if base.is_dir() and (base / "__init__.py").exists() or any(c.is_file() for c in candidates):
            return True
    return False


def suggest_checks(root):
    """Check commands this project already has, to point Claude at the real tests."""
    root, out = Path(root), []
    try:
        scripts = json.loads((root / "package.json").read_text()).get("scripts", {})
        out += [f"npm run {k}" if k != "test" else "npm test" for k in ("test", "build", "typecheck", "lint") if k in scripts]
    except (OSError, ValueError, AttributeError):
        pass
    if list(root.glob("tests/test_*.py")) + list(root.glob("test_*.py")) + list(root.glob("tests/**/test_*.py")):
        out.append("python3 -m pytest (or: python3 -m unittest discover -s tests)")
    for marker, cmd in (("Cargo.toml", "cargo test"), ("go.mod", "go test ./..."), ("Package.swift", "swift test")):
        if (root / marker).exists():
            out.append(cmd)
    try:
        if re.search(r"^test:", (root / "Makefile").read_text(), re.M):
            out.append("make test")
    except OSError:
        pass
    return out[:3]


NARROWING = {"--ignore", "--ignore-glob", "--deselect", "-k", "-m", "--lf", "--last-failed", "--sw", "--stepwise",
             "--testPathIgnorePatterns", "--testNamePattern", "-t", "--grep", "-g", "--exclude", "--skip", "--filter",
             "-run", "--run", "--only", "--onlyChanged", "-o", "--changed", "--findRelatedTests", "--shard",
             "--testPathPattern", "--modulePathIgnorePatterns", "--exclude-dir", "--select", "--extend-exclude"}


def checks_in(cmd, root=None, base=None):
    """Find checks in a command. Returns [{kind, prog, pos, trusted, argv, cwd, simple}].

    `trusted` means the command's exit code really reflects that check: it ran unconditionally (no `||`
    before it) and everything after it is joined with `&&` (or `|` under `set -o pipefail`).
    """
    segs = segments(cmd)
    here = os.path.realpath(str(base or root or "."))
    found, pipefail, cwd = [], False, here
    for i, (op, toks) in enumerate(segs):
        if not toks:
            continue
        if toks[0] == "set" and "pipefail" in toks:
            pipefail = not any(x.startswith("+") for x in toks)
            continue
        if toks[0] == "cd" and len(toks) > 1:
            cwd = os.path.realpath(os.path.join(cwd, os.path.expanduser(toks[1])))
            continue
        kind = verifier(toks, root)
        if not kind:
            continue
        before = [o for o, _ in segs[1:i + 1]]
        after = [o for o, _ in segs[i + 1:]]
        if "||" in before or (i + 1 < len(segs) and segs[i + 1][0] == "|" and not pipefail):
            trusted = False
        else:
            trusted = all(o == "&&" or (o == "|" and pipefail) for o in after)
        real = unwrap(toks)
        scope = [a for a in real[1:] if not a.startswith("-") or a.split("=")[0] in NARROWING]
        found.append({"kind": kind, "prog": os.path.basename(real[0]), "trusted": trusted,
                      "pos": sorted(scope), "argv": toks, "cwd": cwd,
                      "simple": len(segs) == 1 or (len(segs) == 2 and segs[0][1][:1] == ["cd"] and segs[1][0] == "&&")})
    return found


NOT_A_CHECK = re.compile(r"deploy|publish|release|upload|push|install|migrat|seed|drop|reset|delete|remove|clean|prod")


def rememberable(argv):
    """Only plain check commands may be re-run automatically: no env prefixes, deploys or extra make targets."""
    if not argv or re.match(r"^[A-Za-z_]\w*=", argv[0]):
        return False
    toks = unwrap(argv)
    if not toks:
        return False
    prog, pos = os.path.basename(toks[0]), [a for a in toks[1:] if not a.startswith("-")]
    if any(NOT_A_CHECK.search(a.lower()) for a in pos):
        return False
    if prog in ("make", "gmake"):
        return bool(pos) and all(a in ("test", "check", "tests") for a in pos)
    if prog in ("npm", "pnpm", "yarn", "bun"):
        return (pos in (["test"], ["t"]) or (pos[:1] == ["run"] and len(pos) == 2)
                or (prog != "npm" and len(pos) == 1))
    if prog in ("mvn", "mvnw", "gradle", "gradlew"):
        return all(a in ("test", "check", "verify", "build", "assemble", "compile", "package") for a in pos)
    return True


def is_code(path):
    base = os.path.basename(path)
    return base.rsplit(".", 1)[-1].lower() not in DOC_EXT if "." in base else True


TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs)/|(^|/)test_[^/]+\.py$|_test\.(py|go)$"
                       r"|\.(test|spec)\.[cm]?[jt]sx?$|Tests?\.(java|kt|swift|cs)$")
SKIP_MARK = re.compile(r"@pytest\.mark\.(skip|xfail)|\bpytest\.(skip|xfail)\(|\b(it|test|describe)\.(skip|only|todo)\("
                       r"|\bx(it|describe|test)\(|\bt\.Skip\(|@(Ignore|Disabled)\b|@unittest\.skip|\bskip\(\)")
ASSERTS = re.compile(r"\bassert\w*\b|\bexpect\s*\(|\.should\b|\bt\.(Error|Fatal)f?\(|\bXCTAssert\w*")
TRIVIAL = re.compile(r"\bassert\s+(True|1)\b|expect\((true|1)\)\.(toBe|toEqual)\((true|1)\)|assertTrue\(True\)")


def weakening(old, new):
    reasons = []
    if len(SKIP_MARK.findall(new)) > len(SKIP_MARK.findall(old)):
        reasons.append("skip")
    a, b = len(ASSERTS.findall(old)), len(ASSERTS.findall(new))
    if b < a:
        reasons.append(f"checks {a}→{b}")
    if len(TRIVIAL.findall(new)) > len(TRIVIAL.findall(old)):
        reasons.append("always-true check")
    return ", ".join(reasons)


# --------------------------------------------------------------------------- guard rules

DB_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "mongosh", "mongo", "duckdb", "clickhouse-client",
              "cockroach", "supabase", "turso", "wrangler", "prisma"}
#   (programs or None for any, pattern on the command's own words, english, korean, file backup helps)
DANGER = [
    (DB_CLIENTS | {"echo", "cat", "printf"}, r"(?i)\b(drop\s+(table|database|schema|collection)|truncate\s+(table\s+)?\w+)",
     "deletes a database table and its data", "데이터베이스 표와 그 안의 데이터를 지워요", False),
    (DB_CLIENTS | {"echo", "cat", "printf"}, r"(?i)\bdelete\s+from\s+[\w.\"`\[\]]+\s*(;|$)",
     "deletes every row of a database table", "데이터베이스 표의 모든 줄을 지워요", False),
    ({"prisma"}, r"\bmigrate\s+reset\b", "wipes the database", "데이터베이스를 통째로 비워요", False),
    ({"supabase"}, r"\bdb\s+reset\b", "wipes the database", "데이터베이스를 통째로 비워요", False),
    ({"rails", "rake", "bin/rails"}, r"\bdb:(drop|reset|schema:load)\b", "wipes the database", "데이터베이스를 통째로 비워요", False),
    ({"dropdb"}, r"", "deletes a whole database", "데이터베이스 전체를 지워요", False),
    ({"redis-cli"}, r"(?i)\bflush(all|db)\b", "wipes the database", "데이터베이스를 통째로 비워요", False),
    ({"manage.py"}, r"\bflush\b", "wipes the database", "데이터베이스를 통째로 비워요", False),
    ({"find"}, r"(\s|^)-delete\b|-exec(dir)?\s+rm\b", "deletes every file that matches a search", "검색에 걸린 파일을 전부 지워요", True),
    ({"mkfs", "newfs"}, r"", "erases a whole disk", "디스크 전체를 지워요", False),
    ({"diskutil"}, r"\b(erase\w*|partition\w*|reformat)\b", "erases a whole disk", "디스크 전체를 지워요", False),
    ({"dd"}, r"\bof=/dev/", "overwrites a disk", "디스크를 덮어써요", False),
    ({"docker", "podman"}, r"\b(system|volume)\s+prune\b|\bvolume\s+rm\b|\bcompose\b.*\bdown\b.*\s(-v|--volumes)\b",
     "deletes saved container data", "컨테이너에 저장된 데이터를 지워요", False),
    ({"docker-compose"}, r"\bdown\b.*\s(-v|--volumes)\b", "deletes saved container data", "컨테이너에 저장된 데이터를 지워요", False),
    ({"terraform", "tofu", "pulumi"}, r"\b(destroy|down)\b", "deletes live online resources", "실제로 운영 중인 온라인 자원을 지워요", False),
    ({"kubectl"}, r"\bdelete\b", "deletes live online resources", "실제로 운영 중인 온라인 자원을 지워요", False),
    ({"heroku"}, r"\b(apps:destroy|pg:reset)\b", "deletes live online resources", "실제로 운영 중인 온라인 자원을 지워요", False),
    ({"gh"}, r"\brepo\s+delete\b", "deletes the online repository", "온라인 저장소를 지워요", False),
    ({"vercel", "netlify"}, r"\b(rm|remove|delete)\b", "deletes live online resources", "실제로 운영 중인 온라인 자원을 지워요", False),
    ({"aws"}, r"\bs3\s+(rm|rb)\b.*--recursive|\bs3\s+rb\b|\b(delete-db|terminate-instances|delete-bucket)\b",
     "deletes live online resources", "실제로 운영 중인 온라인 자원을 지워요", False),
    ({"chmod", "chown"}, r"(\s|^)-R\b.*\b0?777\b|(\s|^)-R\s+\S+\s+/(\s|$)", "changes permissions of everything",
     "모든 파일의 권한을 바꿔요", True),
]
GIT_EFFECTS = {
    "reset": ("throws away all unsaved code changes", "저장하지 않은 코드 변경이 전부 사라져요", True),
    "clean": ("deletes every file git does not track", "git이 관리하지 않는 파일을 전부 지워요", True),
    "discard": ("throws away unsaved changes in every file", "모든 파일의 저장 안 된 변경을 버려요", True),
    "push": ("overwrites the online copy of the project history", "온라인에 있는 프로젝트 기록을 덮어써요", False),
    "branch": ("deletes a branch even if its work was never merged", "합쳐지지 않은 작업이 있어도 브랜치를 지워요", False),
    "stash": ("deletes saved-aside work", "따로 보관해 둔 작업을 지워요", False),
    "rewrite": ("rewrites the whole project history", "프로젝트 기록 전체를 다시 써요", False),
}
CACHES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".parcel-cache", ".turbo"}
REGENERABLE = {"node_modules", "dist", "build", "out", ".next", ".nuxt", ".turbo", "coverage", "__pycache__",
               ".pytest_cache", ".mypy_cache", ".ruff_cache", "target", ".cache", ".parcel-cache", ".vite"}
TEMP_ROOTS = [os.path.realpath(p) for p in (os.environ.get("VIBE_TEMP_ROOTS", "").split(os.pathsep) if
              os.environ.get("VIBE_TEMP_ROOTS") else {"/tmp", "/private/tmp", "/var/folders", tempfile.gettempdir()})
              if os.path.isdir(p)]


def git_danger(args):
    """args: words after `git` (global options already removed). Return a GIT_EFFECTS key or None."""
    sub, rest = (args[0], args[1:]) if args else ("", [])
    flags = [a for a in rest if a.startswith("-")]
    short = "".join(a[1:] for a in flags if not a.startswith("--"))
    if sub == "reset" and "--hard" in rest:
        return "reset"
    if sub == "clean" and ("f" in short or "--force" in rest) and not ("n" in short or "--dry-run" in rest):
        return "clean"
    if sub in ("checkout", "restore") and "--staged" not in rest and ("." in rest or "-f" in rest or "--force" in rest
                                                                      or ":/" in rest):
        return "discard"
    if sub == "push" and ("f" in short or "--force" in rest or any(a.startswith("--force") for a in rest)
                          or any(a.startswith("+") for a in rest if not a.startswith("-"))):
        return "push"
    if sub == "branch" and ("D" in short or ("--delete" in rest and "--force" in rest)):
        return "branch"
    if sub == "stash" and rest[:1] in (["drop"], ["clear"]):
        return "stash"
    if sub in ("filter-branch", "filter-repo"):
        return "rewrite"
    return None


def committed_test(path, root):
    """A project test someone relies on: inside the project and, in a git project, committed (not a scratch file)."""
    if not inside(path, root):
        return False
    rc, _, _ = run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"], timeout=10)
    return rc != 0 or run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", path], timeout=10)[0] == 0


def rm_verdict(toks, root, cwd=None):
    """Return ('deny'|'ask'|None, english, korean, resolved targets) for one rm-like command."""
    home = os.path.realpath(str(Path.home()))
    cwd = cwd or str(root)
    flags = "".join(x.lstrip("-") for x in toks[1:] if x.startswith("-") and x != "--")
    recursive = "r" in flags.lower() or "recursive" in flags
    targets = [x for x in toks[1:] if not x.startswith("-")]
    if not targets:
        return "ask", "deletes the files listed by the previous command", "앞 명령이 찾은 파일들을 지워요", [cwd]
    unsafe, paths = [], []
    for target in targets:
        expanded = os.path.expanduser(target.replace("${HOME}", "~").replace("$HOME", "~"))
        resolved = os.path.realpath(os.path.join(cwd, expanded))
        base = os.path.basename(expanded.rstrip("/"))
        scope = os.path.realpath(os.path.join(cwd, os.path.dirname(expanded) or ".")) if base == "*" else resolved
        if (recursive or base == "*") and (scope in ("/", home) or inside(root, scope)):
            return "deny", f"deletes everything in {target}", f"{target} 안의 모든 것을 지워요", [scope]
        if not inside(resolved, root) and any(inside(resolved, tr) and resolved != tr for tr in TEMP_ROOTS):
            continue
        name = os.path.basename(resolved)
        if name in CACHES or (name in REGENERABLE and inside(resolved, root)):
            continue
        unsafe.append(target)
        paths.append(scope if base == "*" else resolved)
    if recursive and unsafe:
        return "ask", f"permanently deletes {', '.join(unsafe[:3])} and everything inside", \
            f"{', '.join(unsafe[:3])} 폴더와 그 안의 모든 것을 영구히 지워요", paths
    tests = [x for x in targets if TEST_PATH.search(x) and committed_test(os.path.realpath(os.path.join(cwd, x)), root)]
    if tests:
        return "ask", f"deletes test file(s) {', '.join(tests[:3])}", f"테스트 파일 {', '.join(tests[:3])}을(를) 지워요", \
            [os.path.realpath(os.path.join(cwd, x)) for x in tests]
    if any("*" in x for x in unsafe):
        return "ask", f"deletes every file matching {', '.join(unsafe[:3])}", \
            f"{', '.join(unsafe[:3])}에 맞는 파일을 전부 지워요", paths
    return None, "", "", []


def git_affected(cwd, key, git_args=()):
    """Files a git reset/checkout/clean in `cwd` would overwrite or delete, as absolute paths."""
    rc, top, _ = run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], timeout=10)
    if rc:
        return [cwd]
    rev = next((a for a in list(git_args)[1:] if not a.startswith("-")), "HEAD") if key == "reset" else "HEAD"
    ignored = key == "clean" and any("x" in a.lower() for a in git_args if a.startswith("-") and not a.startswith("--"))
    if key == "clean":
        args = ["ls-files", "-z", "--others"] + ([] if ignored else ["--exclude-standard"])
    else:
        args = ["diff", "-z", "--name-only", rev, "--"]
    rc, out, _ = run(["git", "-C", top.strip(), *args], timeout=20)
    return [os.path.join(top.strip(), rel) for rel in out.split("\0") if rel][:2000] if rc == 0 else [cwd]


def expand(token, env):
    """Expand $NAME and ${NAME} for variables whose value is known; leave the rest untouched."""
    return re.sub(r"\$\{?([A-Za-z_]\w*)\}?", lambda m: env.get(m.group(1), m.group(0)), token)


def danger(cmd, root, base=None, depth=0):
    """Return (verdict, english, korean, backup_helps, targets) for the riskiest part of a whole command."""
    rank = {None: 0, "ask": 1, "deny": 2}
    worst, helps_all, targets, hard = (None, "", ""), True, [], []
    cwd = os.path.realpath(str(base or root))
    segs = segments(cmd)
    env = {k: os.environ[k] for k in ("HOME", "TMPDIR") if k in os.environ}
    for i, (_, raw) in enumerate(segs):
        raw = [expand(tk, env) for tk in raw]
        assigns = [tk for tk in raw if re.match(r"^[A-Za-z_]\w*=", tk)]
        if raw and (len(assigns) == len(raw) or raw[0] == "export" and all("=" in tk for tk in raw[1:])):
            env.update(tk.split("=", 1) for tk in raw if "=" in tk)
            continue
        toks = unwrap(raw)
        if not toks:
            continue
        prog, hit = os.path.basename(toks[0]), None
        nxt = unwrap(segs[i + 1][1]) if i + 1 < len(segs) and segs[i + 1][0] == "|" and segs[i + 1][1] else []
        if prog == "cd" and len(toks) > 1:
            cwd = os.path.realpath(os.path.join(cwd, os.path.expanduser(toks[1])))
            continue
        if prog in RUNNERS and len(toks) > 1 and os.path.basename(toks[1]) == "manage.py":
            prog, toks = "manage.py", toks[1:]
        inline = None
        if prog in ("bash", "sh", "zsh", "dash") and "-c" in toks[:-1]:
            inline = toks[toks.index("-c") + 1]
        elif prog == "eval":
            inline = " ".join(toks[1:])
        if inline is not None and depth < 3:
            v, en, ko, helps, tg, inner_hard = danger(inline, root, cwd, depth + 1)
            hit = (v, en, ko, True, tg) if v else None
            hard += inner_hard
        elif prog in ("rm", "rmdir", "unlink", "shred", "srm"):
            v, en, ko, tg = rm_verdict(toks, root, cwd)
            hit = (v, en, ko, True, tg) if v else None
        elif prog == "git":
            args, git_cwd = list(toks[1:]), cwd
            while args and args[0].startswith("-"):
                opt = args.pop(0)
                if opt in ("-C", "--work-tree") and args:
                    git_cwd = os.path.realpath(os.path.join(git_cwd, os.path.expanduser(args.pop(0))))
                elif opt.startswith("--work-tree="):
                    git_cwd = os.path.realpath(os.path.join(git_cwd, opt.split("=", 1)[1]))
                elif opt in ("-c", "--git-dir", "--namespace", "--exec-path") and args:
                    args.pop(0)
            key = git_danger(args)
            if key:
                en, ko, helps = GIT_EFFECTS[key]
                hit = ("ask", en, ko, helps, git_affected(git_cwd, key, args) if helps else [])
        else:
            words = " ".join(toks[1:])
            for progs, pattern, en, ko, helps in DANGER:
                if prog in ("echo", "cat", "printf") and not (nxt and os.path.basename(nxt[0]) in DB_CLIENTS):
                    break  # printing SQL is harmless unless it is piped into a database
                if prog in progs and (not pattern or re.search(pattern, words)):
                    # find deletes under its search folders; for other rules the scope is unknown (the project)
                    where = [a for a in toks[1:] if not a.startswith(("-", "(", "!"))][:1] if prog == "find" else []
                    hit = ("ask", en, ko, helps, [os.path.realpath(os.path.join(cwd, w)) for w in where] or [cwd])
                    break
        if hit:
            helps_all = helps_all and hit[3]
            targets += hit[4]
            if not hit[3] or hit[1].startswith("deletes test file"):
                hard.append((hit[1], hit[2]))  # needs a decision: no backup undoes it, or it is about cheating
            if rank[hit[0]] > rank[worst[0]]:
                worst = hit[:3]
    if worst[0]:
        return worst[0], worst[1], worst[2], helps_all, targets, hard
    return None, "", "", False, [], hard


SECRETS = [
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key"),
    (r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}", "OpenAI/Anthropic API key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{36,}\b", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{40,}", "GitHub token"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\b(sk|rk)_live_[A-Za-z0-9]{20,}", "Stripe live key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "private key"),
    (r"(?i)\bservice_role\b[\"']?\s*[:=]\s*[\"']eyJ[A-Za-z0-9_-]{20,}", "Supabase service-role key"),
]


def redact(text):
    text = re.sub(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?(-----END [A-Z0-9 ]*PRIVATE KEY-----|\Z)",
                  "[redacted private key]", text, flags=re.S)
    for pattern, label in SECRETS:
        text = re.sub(pattern, f"[redacted {label}]", text)
    return text


VALUE_OPTS = {
    "npm": {"--registry", "--prefix", "-w", "--workspace", "--tag", "--omit", "--include", "--cache", "--userconfig",
            "--save-prefix", "-C", "--dir", "--filter", "--cwd"},
    "pypi": {"-t", "--target", "-i", "--index-url", "--extra-index-url", "-r", "--requirement", "-c", "--constraint",
             "-e", "--editable", "--prefix", "--root", "--platform", "--python-version", "--implementation", "--abi",
             "-f", "--find-links", "--src", "--upgrade-strategy", "--progress-bar", "--cache-dir", "--trusted-host",
             "--proxy", "--timeout", "--retries", "--log", "--report", "--python", "-p", "--group", "--optional",
             "--extra", "--index", "--default-index", "--source", "-G"},
    "crates": {"--path", "--git", "--branch", "--tag", "--rev", "--registry", "-p", "--package", "-F", "--features",
               "--rename", "--target", "--manifest-path"},
}
PRIVATE_FLAGS = {"--registry", "-i", "--index-url", "--extra-index-url", "-f", "--find-links", "--index",
                 "--default-index", "--source", "--git", "--path"}


PRIVATE_ENV = re.compile(r"^(PIP_(EXTRA_)?INDEX_URL|PIP_FIND_LINKS|UV_(EXTRA_)?INDEX(_URL)?|UV_DEFAULT_INDEX"
                         r"|NPM_CONFIG_REGISTRY|npm_config_registry|YARN_NPM_REGISTRY_SERVER|CARGO_REGISTRIES_\w+)=")


def install_targets(cmd):
    """Yield (ecosystem, package, private) for package install commands."""
    for _, raw in segments(cmd):
        toks = unwrap(raw)
        if not toks:
            continue
        name, rest, eco = os.path.basename(toks[0]), toks[1:], None
        if name in ("npm", "pnpm", "yarn", "bun") and rest and rest[0] in ("i", "install", "add"):
            eco, rest = "npm", rest[1:]
        elif name in ("pip", "pip3", "uv", "poetry", "pdm", "pipenv"):
            if name == "uv" and rest[:1] == ["pip"]:
                rest = rest[1:]
            if rest and rest[0] in ("install", "add"):
                eco, rest = "pypi", rest[1:]
        elif name == "cargo" and rest[:1] == ["add"]:
            eco, rest = "crates", rest[1:]
        if not eco:
            continue
        private = any(a.split("=")[0] in PRIVATE_FLAGS for a in rest) or any(PRIVATE_ENV.match(a) for a in raw)
        skip = False
        for arg in rest:
            if skip:
                skip = False
                continue
            if arg.startswith("-"):
                skip = arg in VALUE_OPTS[eco] and "=" not in arg
                continue
            if arg.startswith((".", "/", "~")) or "://" in arg or ":" in arg or ("/" in arg and not arg.startswith("@")):
                continue
            if arg.endswith((".whl", ".tar.gz", ".zip", ".tgz", ".txt")):
                continue
            pkg = re.match(r"^(@[^/@\s]+/[^@\s]+|[^@\s]+)", arg) if eco == "npm" else re.match(r"^[A-Za-z0-9_.-]+", arg)
            if pkg:
                yield eco, pkg.group(1) if eco == "npm" else pkg.group(0), private


def private_registry(eco, name, root):
    """True when the project or user points this ecosystem at a non-public registry."""
    def has(path, pattern):
        try:
            return re.search(pattern, Path(path).expanduser().read_text(errors="replace"), re.M) is not None
        except OSError:
            return False
    if eco == "npm":
        scope = name.split("/")[0] if name.startswith("@") else ""
        if os.environ.get("NPM_CONFIG_REGISTRY") or os.environ.get("npm_config_registry"):
            return True
        pat = r"^\s*registry\s*=" + (f"|^\\s*{re.escape(scope)}:registry\\s*=" if scope else "")
        return any(has(p, pat) for p in (Path(root) / ".npmrc", "~/.npmrc", Path(root) / ".yarnrc.yml"))
    if eco == "pypi":
        if any(os.environ.get(k) for k in ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "UV_INDEX_URL", "UV_INDEX",
                                           "UV_EXTRA_INDEX_URL", "UV_DEFAULT_INDEX")):
            return True
        return any(has(p, r"index-url|^\s*\[\[tool\.(uv\.index|poetry\.source|pdm\.source)\]\]|^\s*\[\[source\]\]")
                   for p in (Path(root) / "pyproject.toml", Path(root) / "pip.conf", Path(root) / "Pipfile",
                             "~/.config/pip/pip.conf", "~/.pip/pip.conf", "~/Library/Application Support/pip/pip.conf",
                             "~/.config/uv/uv.toml"))
    if eco == "crates":
        return any(has(p, r"^\s*\[(registries|source)") for p in (Path(root) / ".cargo/config.toml", "~/.cargo/config.toml"))
    return False


def package_info(eco, name):
    """Return (exists, age_days) or (None, None) when the registry cannot be reached."""
    url = {"npm": f"https://registry.npmjs.org/{name.replace('/', '%2F')}",
           "pypi": f"https://pypi.org/pypi/{name}/json",
           "crates": f"https://crates.io/api/v1/crates/{name}"}[eco]
    req = urllib.request.Request(url, headers={"User-Agent": "vibe-claude/" + VERSION, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        return (False, None) if e.code == 404 else (None, None)
    except (OSError, ValueError):
        return None, None
    created = None
    if eco == "npm":
        created = data.get("time", {}).get("created")
    elif eco == "pypi":
        uploads = [f.get("upload_time_iso_8601") for files in data.get("releases", {}).values() for f in files]
        created = min(filter(None, uploads), default=None)
    elif eco == "crates":
        created = data.get("crate", {}).get("created_at")
    if not created:
        return True, None
    try:
        then = time.mktime(time.strptime(created[:19], "%Y-%m-%dT%H:%M:%S"))
        return True, int((time.time() - then) / 86400)
    except ValueError:
        return True, None


# --------------------------------------------------------------------------- events

RULES = """vibe-claude is active. The user may not read code, so:
1. Prove it, don't claim it. Hooks record check results. After changing files, run a related test, build or program after the last change. Run it alone or joined with `&&`. After a supported remote change, re-read the same target before reporting completion.
2. Report in plain words: what changed for the user, how they can see it themselves (a URL, a command, or where to click), and what might break. No diffs or code unless asked.
3. Same error twice: change the approach instead of retrying.
4. Change only what was asked. Never weaken, skip or delete tests to make them pass; fix the code.
5. Earlier states are saved automatically; the user can return to one with /vibe-claude:undo. Never ask the user to judge technical risk; when vibe-claude stops an action, you decide from the conversation. If you keep deleting a folder that only holds generated output (screenshots, build results), run `python3 "{vibe}" allow-delete <folder>` from the project so it is not copied to the trash each time."""


def on_session_start(v):
    return  # A greeting must not inject work instructions. Wait for an actual change.


def work_guidance(v):
    turn = v.turn()
    if not any(e.get("ev") == "turn" for e in turn) or any(e.get("ev") == "guidance" for e in turn):
        return
    v.log(ev="guidance")
    emit({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                 "additionalContext": RULES.replace("{vibe}", str(Path(__file__).resolve()))}})


def on_prompt(v):
    if not v.enabled:
        return
    prompt = str(v.data.get("prompt", ""))
    lang = "ko" if re.search(r"[가-힣]", prompt) else ("en" if re.search(r"[A-Za-z]{3}", prompt) else None)
    snap = v.snapshot("turn", prompt.strip().splitlines()[0][:100] if prompt.strip() else "")
    st = v.load("state.json", {})
    if lang:
        st["lang"] = lang
    turns = st.get("turns", {})
    turns[v.pid or v.sid] = {"snap": snap, "prompt": prompt[:600], "t": time.time()}
    st["turns"] = dict(list(turns.items())[-20:])
    st["current_snap"] = snap
    st["codex_rounds"] = 0
    v.save("state.json", st)
    v.log(ev="turn")
    if snap and int(hashlib.sha1(snap.encode()).hexdigest(), 16) % 40 == 0:
        v.prune()


def new_content(tool, inp, old):
    if tool == "Write":
        return str(inp.get("content", ""))
    if tool == "Edit":
        edits = [inp]
    elif tool == "MultiEdit":
        edits = inp.get("edits", []) or []
    elif tool == "NotebookEdit":
        return str(inp.get("new_source", ""))
    else:
        return None
    text = old
    for e in edits:
        a, b = str(e.get("old_string", "")), str(e.get("new_string", ""))
        text = text.replace(a, b) if e.get("replace_all") else text.replace(a, b, 1)
    return text


def deny(reason):
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})


def warn_once(v, key, reason, note):
    """Stop Claude once so it decides, instead of asking a user who cannot judge code.

    The identical action retried in the same request goes through and is noted on the receipt.
    """
    st = v.load("state.json", {})
    turn = v.pid or v.sid
    seen = st.get("warned", {}).get(turn, [])
    digest = hashlib.sha1(key.encode()).hexdigest()[:16]
    if digest in seen:
        v.log(ev="override", what=note)
        return False
    v.state_update(warned={turn: seen + [digest]})
    deny(reason + " The user does not read code and will not be asked, so you decide: check the conversation. If this "
         "is clearly what the user wanted, run exactly the same action again and it will go through, then tell the "
         "user in plain words what was done. Otherwise choose a safer way.")
    return True


def trash(v, targets, cmd):
    """Copy files the backup does not cover into the trash so the delete can be undone. None if too big."""
    files, size = [], 0
    for target in targets:
        path = Path(target)
        if path.is_symlink() or path.is_file():
            walk = [path]
        elif path.is_dir():
            walk = (Path(d) / f for d, dirs, names in os.walk(path) for f in names + [x for x in dirs if
                                                                                       (Path(d) / x).is_symlink()])
        else:
            continue
        for f in walk:
            try:
                size += f.lstat().st_size
            except OSError:
                continue
            files.append(f)
            if size > TRASH_MAX or len(files) > TRASH_FILES:
                return None
    if not files:
        return "nothing"
    tid = time.strftime("%Y%m%d-%H%M%S-") + hashlib.sha1(cmd.encode()).hexdigest()[:6]
    base = v.dir / "trash" / tid
    for f in files:
        rel = os.path.relpath(f, v.root) if inside(f, v.root) else os.path.join("_outside", str(f.absolute()).lstrip("/"))
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if f.is_symlink():
                os.symlink(os.readlink(f), dest)
            else:
                shutil.copy2(f, dest)
        except OSError:
            return None
    (base / ".vibe-trash.json").write_text(json.dumps({"t": time.time(), "cmd": cmd[:300], "files": len(files)}))
    for old in (v.dir / "trash").iterdir():
        try:
            if time.time() - old.stat().st_mtime > TRASH_KEEP:
                shutil.rmtree(old, ignore_errors=True)
        except OSError:
            pass
    return tid


def on_pre_tool(v):
    tool = v.data.get("tool_name", "")
    inp = v.data.get("tool_input", {}) or {}
    lang = v.lang
    if tool == "Bash":
        return pre_bash(v, str(inp.get("command", "")), lang)
    path = str(inp.get("file_path") or inp.get("notebook_path") or "")
    if not path:
        return
    try:
        old = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        old = ""
    new = new_content(tool, inp, old)
    if new is None:
        return
    rel = os.path.relpath(path, v.root) if inside(path, v.root) else path
    if not SECRET_FILES.search(path):
        for pattern, label in SECRETS:
            if re.search(pattern, new) and not re.search(pattern, old):
                return deny(f"vibe-claude blocked this edit: it would write a real-looking {label} into {rel}. "
                            "Secrets in code leak when the project is shared or deployed. Read it from an "
                            "environment variable and keep the value in a .env file that is git-ignored, then tell "
                            "the user in plain words where to paste their key.")
    if old and tool != "NotebookEdit" and TEST_PATH.search(rel):
        detail = weakening(old, new)
        if detail:
            return warn_once(v, "edit:" + path + hashlib.sha1(new.encode()).hexdigest(),
                             f"vibe-claude stopped this edit once: it weakens a test in {rel} ({detail}). Tests are the "
                             "only proof the app works for a user who cannot read code. Fix the code instead, unless "
                             "the test itself is wrong.",
                             f"테스트 수정({rel})" if lang == "ko" else f"changed a test ({rel})")


def pre_bash(v, cmd, lang):
    verdict, en, ko, helps, targets, hard = danger(cmd, v.root, v.data.get("cwd"))
    if verdict == "deny":
        return deny(f"vibe-claude blocked a catastrophic command ({en}). Do not try to work around this. "
                    "Explain to the user in plain words what you wanted to do and find a narrower command.")
    if verdict:
        snap = v.snapshot("guard", cmd[:100])
        if hard:  # databases, force pushes, cloud resources, test deletion: Claude must decide
            tests = [e for e, _ in hard if e.startswith("deletes test file")]
            other = [e for e, _ in hard if not e.startswith("deletes test file")]
            reason = "vibe-claude stopped this once:" + (f" it {'; '.join(other)}, and that cannot be undone." if other else "") \
                + (f" It {'; '.join(tests)}; deleting tests to get a pass hides broken code." if tests else "")
            note = ", ".join(dict.fromkeys(k if lang == "ko" else e for e, k in hard))
            if warn_once(v, "bash:" + cmd, reason, note):
                return
        # Files: keep everything recoverable. The snapshot covers most; copy the rest to the trash.
        safe = [os.path.realpath(os.path.join(v.root, d)) for d in v.config["safe_to_delete"] if isinstance(d, str) and d]
        targets = [x for x in targets if not any(inside(x, d) for d in safe)]  # folders marked disposable
        unsaved = [x for x in targets if not snap or v.unsaved_under([x])]
        if unsaved:
            tid = trash(v, unsaved, cmd)
            if tid:
                v.log(ev="trash", id=tid, cmd=cmd[:300])
            elif warn_once(v, "big:" + cmd, f"vibe-claude stopped this once: it {en}, and the files are too large (over "
                           f"{TRASH_MAX // 1_000_000} MB) to keep a copy, so it could not be undone.",
                           ko if lang == "ko" else en):
                return
        return
    if re.search(r"\bgit\b.*\b(checkout|switch|merge|rebase|pull|stash|apply|am)\b|\bsed\s+-i|\bmv\s|\bperl\s+-[a-z]*i", cmd):
        v.snapshot("guard", cmd[:100])
    if v.config["packages"]:
        for eco, name, private in list(install_targets(cmd))[:8]:
            if private or private_registry(eco, name, v.root):
                continue  # never send private package names to a public registry
            exists, age = package_info(eco, name)
            if exists is False:
                return deny(f"vibe-claude blocked install: the {eco} package '{name}' does not exist on the public "
                            "registry. AI models often invent package names, and attackers register those names with "
                            "malware. Find the real package name in official documentation. If it lives in a private "
                            "registry, pass that registry explicitly (for example --registry or --index-url).")
            if exists and age is not None and age < 14:
                return warn_once(v, "bash:" + cmd, f"vibe-claude stopped this install once: the {eco} package '{name}' "
                                 f"is only {age} days old. Brand-new packages with familiar-looking names are a common "
                                 "malware trick. Make sure it is the official package.",
                                 f"새 패키지 설치({name})" if lang == "ko" else f"installed a new package ({name})")


def check_syntax(path, root):
    ext = path.rsplit(".", 1)[-1].lower()
    py = sys.executable or "python3"
    if ext == "py":
        return run([py, "-c", "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read(), sys.argv[1])", path])
    if ext == "json":
        return run([py, "-c", "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))", path])
    if ext == "toml" and sys.version_info >= (3, 11):
        return run([py, "-c", "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))", path])
    if ext in ("yaml", "yml"):
        return run([py, "-c", "import sys\ntry:\n import yaml\nexcept ImportError:\n sys.exit(0)\n"
                    "list(yaml.safe_load_all(open(sys.argv[1],encoding='utf-8')))", path])
    if ext in ("sh", "bash"):
        return run(["bash", "-n", path])
    if ext in ("js", "mjs", "cjs") and shutil.which("node"):
        return run(["node", "--check", path])
    if ext == "ipynb":
        code = ("import ast,json,sys\nnb=json.load(open(sys.argv[1],encoding='utf-8'))\n"
                "for i,c in enumerate(nb.get('cells',[])):\n"
                " if c.get('cell_type')=='code':\n"
                "  src=''.join(c.get('source',[])) if isinstance(c.get('source'),list) else c.get('source','')\n"
                "  src='\\n'.join('' if l.lstrip().startswith(('%','!')) else l for l in src.splitlines())\n"
                "  ast.parse(src, f'cell {i+1}')\n")
        return run([py, "-c", code, path])
    if ext in ("ts", "tsx", "mts", "cts") and shutil.which("node"):
        d = Path(path).resolve().parent
        while d != d.parent:  # only when the project ships its own TypeScript
            ts = d / "node_modules" / "typescript"
            if ts.is_dir():
                code = ("const ts=require(process.argv[1]);const fs=require('fs');const f=process.argv[2];"
                        "const r=ts.transpileModule(fs.readFileSync(f,'utf8'),{fileName:f,reportDiagnostics:true,"
                        "compilerOptions:{jsx:'preserve'}});const d=(r.diagnostics||[]).filter(x=>x.category===1);"
                        "for(const x of d){const p=x.file?x.file.getLineAndCharacterOfPosition(x.start):{line:0};"
                        "console.error(`${f}:${p.line+1}: ${ts.flattenDiagnosticMessageText(x.messageText,'\\n')}`)}"
                        "process.exit(d.length?1:0)")
                return run(["node", "-e", code, str(ts), path], timeout=60)
            if d == root:
                break
            d = d.parent
    return 0, "", ""


MUTATES = re.compile(r"(^|[;&|(]\s*|\b(sudo|env|xargs)\s+)(rm|rmdir|unlink|mv|cp|rsync|tee|truncate|patch|ln)\b"
                     r"|\bgit\s+(rm|mv|checkout|restore|reset|clean|stash|apply|am|merge|rebase|pull|switch|cherry-pick)\b"
                     r"|\b(sed|perl)\s+-\w*i|\bfind\b.*(-delete|-exec)|[^<>&0-9]>>?\s*(?!/dev/null)[^\s&>|]+"
                     r"|\b(npx|pnpm|yarn|npm)\s+.*\b(codemod|prettier\s+--write|eslint\s+--fix)|--fix\b|--write\b")


def in_project(check, root):
    """The check ran in this project and does not point at files outside it."""
    if not inside(check["cwd"], root):
        return False
    for arg in check["pos"]:
        value = arg.split("=", 1)[1] if arg.startswith("-") and "=" in arg else arg
        path = os.path.join(check["cwd"], os.path.expanduser(value))
        if (value.startswith(("/", "~", "..")) or os.path.exists(path)) and not inside(path, root):
            return False
    return True


def tool_missing(prog, out, code):
    """The checker itself is not installed (no evidence either way), as opposed to the project failing."""
    p = re.escape(prog)
    return bool(re.search(rf"No module named '?{p}'?\s*$|(^|[\s:]){p}: (command )?not found|command not found: {p}\b"
                          rf"|Missing script: \"?{p}|npm (ERR!|error) Missing script", out[-2000:], re.M))


def option(args, *names):
    for i, a in enumerate(args):
        for name in names:
            if a.startswith(name + "="):
                return a.split("=", 1)[1]
            if a == name and i + 1 < len(args):
                return args[i + 1]
    return ""


def positional(args):
    """Only positional targets, never option values such as a PR title."""
    takes_value = {"-R", "--repo", "-b", "--branch", "--head", "--base", "-t", "--title", "--body",
                   "--body-file", "--json", "--jq", "--template", "--state", "--limit", "-L", "--registry",
                   "--tag", "--access", "--cwd", "--scope", "--target", "--token", "-H", "--hostname"}
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a in takes_value:
            skip = True
        elif not a.startswith("-"):
            out.append(a)
    return out


def repo_name(value):
    value = re.sub(r"\.git$", "", value.strip())
    value = re.sub(r"^(?:https?://|ssh://git@|git@)", "", value).replace(":", "/")
    return re.sub(r"^github\.com/", "", value)


def remote_commands(cmd, root, base, output=""):
    """Bounded Bash support. Unknown identities stay pending, never match a random read.

    These records say a target was re-read, not that a deployment or business action succeeded.
    No writes or network calls are executed here.
    """
    found, cwd = [], Path(base or root).resolve()
    segs = segments(cmd)
    for i, (op, toks) in enumerate(segs):
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) > 1:
            cwd = (cwd / toks[1]).resolve()
            continue
        real = unwrap(toks)
        if not real:
            continue
        prog, args = os.path.basename(real[0]), real[1:]
        if any(a in INFO_FLAGS for a in args):
            continue
        # Compound responses do not identify which command produced the output.
        stdout = output if len(segs) == 1 else ""
        trusted = not any(o in ("||", "&", "|") for o, _ in segs[1:i + 1]) and all(
            o == "&&" for o, _ in segs[i + 1:])
        record = None
        if prog == "gh":
            repo = option(args, "-R", "--repo")
            repo = repo or run(["git", "config", "--get", "remote.origin.url"], cwd=cwd)[1].strip()
            scope = repo_name(repo) if repo else "cwd:" + str(cwd)
            # gh supports global --repo before the resource as well as after it.
            rest = list(args)
            for flag in ("-R", "--repo"):
                if flag in rest:
                    n = rest.index(flag)
                    del rest[n:n + 2]
            rest = [a for a in rest if not a.startswith("--repo=")]
            if len(rest) < 2:
                continue
            resource, action, tail = rest[0], rest[1], rest[2:]
            target_args = positional(tail)
            target = target_args[0] if target_args else ""
            url = re.search(r"https://github\.com/([^\s/]+/[^\s/]+)/(pull|issues|releases/tag)/([^\s]+)",
                            target or stdout)
            if url:
                scope, target = url[1], url[3].rstrip(".,)")
            write = (resource, action) in {("pr", "create"), ("pr", "merge"), ("issue", "create"),
                                              ("issue", "close"), ("release", "create")}
            read = resource in ("pr", "issue", "release", "run") and action in ("view", "list")
            if write or read:
                # Create options/files are not target identities. Only returned URLs identify new items.
                if action == "create" and resource in ("pr", "issue") and not url:
                    target = ""
                if resource == "run":
                    target = option(tail, "--branch", "-b")
                    if not target and action == "view":
                        try:
                            target = json.loads(stdout).get("headBranch", "")
                        except (ValueError, AttributeError):
                            pass
                record = dict(action="write" if write else "read", service="gh:" + resource,
                              scope=scope, target=target)
        elif prog == "git":
            # -C and -c alter command context; do not guess at their remote identity.
            if not args or args[0] not in ("push", "ls-remote"):
                continue
            action = args[0]
            pos = positional(args[1:])
            remote = pos[0] if pos else "origin"
            url = run(["git", "config", "--get", f"remote.{remote}.url"], cwd=cwd)[1].strip()
            scope = repo_name(url or remote) if url or re.search(r"[:/@]", remote) else f"cwd:{cwd}:{remote}"
            refs = pos[1:]
            if action == "push" and not refs:
                branch = run(["git", "symbolic-ref", "--short", "HEAD"], cwd=cwd)[1].strip()
                refs = [branch] if branch else [""]
            elif action == "ls-remote" and not refs:
                refs = re.findall(r"^[0-9a-fA-F]+\s+(refs/[^\s]+)$", stdout, re.M)
            for ref in refs or [""]:
                dest = ref.split(":", 1)[-1].lstrip("+")
                if dest and not dest.startswith("refs/"):
                    dest = "refs/heads/" + dest
                found.append(dict(action="write" if action == "push" else "read", service="git",
                                  scope=scope, target=dest, trusted=trusted))
        elif prog == "vercel" and (not args or args[0] in ("deploy", "--prod")):
            urls = re.findall(r"https://[a-zA-Z0-9.-]+\.vercel\.app(?:/[^\s]*)?", stdout)
            record = dict(action="write", service="deploy", scope="url", target=urls[-1].rstrip("/") if urls else "")
        elif prog == "curl":
            if any(a in args for a in ("-X", "--request", "-d", "--data", "--data-raw", "-F", "--form", "-T", "--upload-file")):
                continue
            urls = [a.rstrip("/") for a in args if a.startswith("https://")]
            if len(urls) == 1:
                record = dict(action="read", service="deploy", scope="url", target=urls[0])
        elif prog == "npm" and args and args[0] in ("publish", "view"):
            action = args[0]
            registry = option(args, "--registry") or "default"
            if action == "publish":
                pos = positional(args[1:])
                folder = (cwd / pos[0]).resolve() if pos else cwd
                try:
                    package = json.loads((folder / "package.json").read_text())
                    target = package["name"] + "@" + package["version"]
                    registry = option(args, "--registry") or package.get("publishConfig", {}).get("registry", "default")
                except (OSError, ValueError, KeyError, TypeError):
                    target = ""
            else:
                pos = positional(args[1:])
                target = pos[0] if pos else ""
                if target and "@" not in target.lstrip("@"):
                    # `npm view NAME version` may return the exact published version.
                    version = stdout.strip().strip('"')
                    if len(pos) > 1 and pos[1] == "version" and re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", version):
                        target += "@" + version
            record = dict(action="write" if action == "publish" else "read", service="npm", scope=registry, target=target)
        if record:
            found.append(dict(record, trusted=trusted))
    return found


def remote_pending(v):
    pending, read = [], []
    for e in v.turn():
        if e.get("ev") != "remote":
            continue
        if e.get("action") == "write":
            pending.append(e)
        elif e.get("ok") and e.get("target"):
            matches = [w for w in pending if w.get("ok") and w.get("target") == e["target"]
                       and w.get("scope") == e.get("scope") and w.get("service") == e.get("service")]
            # A workflow read can confirm a push to the same repo and explicit branch.
            if e.get("service") == "gh:run":
                matches += [w for w in pending if w.get("ok") and w.get("service") == "git"
                            and w.get("scope") == e.get("scope") and w.get("target") == "refs/heads/" + e["target"]]
            for w in matches:
                pending.remove(w)
                read.append(w)
    return pending, read


def on_post_tool(v, failed=False):
    tool = v.data.get("tool_name", "")
    inp = v.data.get("tool_input", {}) or {}
    if tool == "Bash":
        cmd = str(inp.get("command", ""))
        resp = v.data.get("tool_response", {}) or {}
        interrupted = isinstance(resp, dict) and resp.get("interrupted")
        output = str(resp.get("stdout", "")) if isinstance(resp, dict) else ""
        remote = remote_commands(cmd, v.root, v.data.get("cwd"), output) if v.enabled else []
        for r in remote:
            v.log(ev="remote", **r, ok=not failed and not interrupted and r["trusted"] and not inp.get("run_in_background"))
        if any(r["action"] == "write" for r in remote) and not failed:
            work_guidance(v)
        if v.enabled and MUTATES.search(cmd):
            v.log(ev="mutate", cmd=cmd[:300])
        found = checks_in(cmd, v.root, v.data.get("cwd"))
        if not found or not v.enabled or inp.get("run_in_background"):
            return
        if failed:
            if v.data.get("is_interrupt"):
                return
            err = str(v.data.get("error", ""))
            m = re.match(r"Exit code (\d+)", err)
            code = int(m.group(1)) if m else 1
            found = [c for c in found if in_project(c, v.root)]
            if not found or len(found) == 1 and tool_missing(found[0]["prog"], err, code):
                return
            c = found[-1]
            v.log(ev="run", cmd=cmd[:500], kind=c["kind"], prog=c["prog"], pos=c["pos"], cwd=c["cwd"], exit=code, ok=False)
            return
        if isinstance(resp, dict) and resp.get("interrupted"):
            return
        found = [c for c in found if in_project(c, v.root)]  # checks of another project prove nothing here
        for c in found:
            v.log(ev="run", cmd=cmd[:500], kind=c["kind"], prog=c["prog"], pos=c["pos"], cwd=c["cwd"],
                  exit=0 if c["trusted"] else None, ok=c["trusted"])
            argv = [a for a in c["argv"]]
            if (c["trusted"] and c["simple"] and c["kind"] in ("test", "type", "lint", "build") and v.config["ratchet"]
                    and rememberable(argv) and not any(re.search(r"[`$]", a) for a in argv) and inside(c["cwd"], v.root)):
                green = [g for g in v.load("green.json", []) if g.get("argv") != argv or g.get("cwd") != c["cwd"]]
                green.append({"argv": argv, "cwd": c["cwd"], "kind": c["kind"], "prog": c["prog"], "pos": c["pos"],
                              "t": time.time()})
                v.save("green.json", green[-5:])
        if any(c["trusted"] for c in found):
            v.snapshot("good", cmd[:100])
        return
    path = str(inp.get("file_path") or inp.get("notebook_path") or "")
    if not path or not os.path.isfile(path):
        return
    if v.enabled and inside(path, v.root):
        v.log(ev="edit", path=os.path.relpath(os.path.realpath(path), v.root), code=is_code(path))
    rc, out, err = check_syntax(path, v.root)
    if rc and rc not in (124, 127):
        emit({"decision": "block", "reason": f"Syntax check failed for {path}:\n{(err or out)[:4000]}"})
    elif v.enabled and inside(path, v.root) and proof(v):
        work_guidance(v)


def supersedes(newer, older):
    """A later run of the same check in the same folder replaces an earlier one unless it is narrower."""
    return (newer.get("kind") == older.get("kind") and newer.get("prog") == older.get("prog")
            and newer.get("cwd") == older.get("cwd") and set(newer.get("pos", [])) <= set(older.get("pos", [])))


SHELL_CHANGES = "(files changed by shell commands)"


def proof(v, files=None):
    """What changed in this request, and the evidence gathered after the last change."""
    turn = v.turn()
    st = v.load("state.json", {})
    info = st.get("turns", {}).get(v.pid or v.sid, {})
    edits = {e["path"]: e["t"] for e in turn if e.get("ev") == "edit"}
    mutations = [e["t"] for e in turn if e.get("ev") == "mutate"]
    if files is None and info.get("snap"):
        now = v.snapshot("check", "end of request")
        diff = v.changed(info["snap"], now) if now else None
        if diff is not None:
            files = sorted(p for _, p in diff if is_code(p))
    if files is None:  # snapshots unavailable: trust the edit tools, and assume shell edits changed something
        files = sorted(p for p in edits if is_code(p)) + ([SHELL_CHANGES] if mutations else [])
    if not files:
        return None
    # When was the code last touched? Edit-tool times, or file times for changes made by shell commands
    # (files written by a check finish before that check is logged, so they never count as "after" it).
    times = [info.get("t", 0)]
    for rel in files:
        times.append(edits.get(rel, 0))
        if rel not in edits:  # changed by a shell command, which may keep or fake the old file time (cp -p)
            times.extend(mutations[-1:])
        try:
            times.append(min((v.root / rel).stat().st_mtime, time.time()))
        except OSError:
            pass
    last_change = max(times)
    runs = sorted((e for e in turn if e.get("ev") == "run" and e["t"] >= last_change), key=lambda e: e["t"])
    passed, failed, unclear = [], [], []
    for r in runs:
        if r.get("ok"):
            failed = [f for f in failed if not supersedes(r, f)]
            unclear = [u for u in unclear if not supersedes(r, u)]
            passed.append(r)
        elif r.get("exit") is None:
            unclear.append(r)
        else:
            passed = [x for x in passed if not supersedes(r, x)]
            failed.append(r)
    uncovered = [rel for rel in files if not any(covers(r, rel, v.root) for r in passed)]
    return {"files": files, "passed": passed, "failed": failed, "unclear": unclear, "uncovered": uncovered}


def covers(check, rel, root):
    """Conservative evidence scope, not a claim about semantic test coverage."""
    cwd = check.get("cwd", str(root))
    target = Path(root) / rel
    if rel == SHELL_CHANGES or not inside(target, cwd):
        return False
    kind = check.get("kind")
    pos = check.get("pos", [])
    if kind != "run":
        # A filtered run cannot stand in for all changed files.
        if any(a.split("=", 1)[0] in NARROWING for a in pos):
            return False
        paths = [Path(cwd) / a for a in pos if (Path(cwd) / a).exists()]
        return not paths or any(inside(target, p) if p.is_dir() else target.resolve() == p.resolve() for p in paths)
    if target.resolve() in [(Path(cwd) / a).resolve() for a in pos]:
        return True
    # Only explicit imports of this changed file count for inline execution.
    for source in pos:
        imports = re.findall(r"(?:^|[;\s(])(?:from|import)\s+([A-Za-z_][\w.]*)", source)
        imports += re.findall(r"(?:require\(|import\(|from\s+)['\"](\.{1,2}/[^'\"]+)['\"]", source)
        for name in imports:
            base = Path(cwd) / (name.replace(".", "/") if "/" not in name else name)
            candidates = [base, base / "__init__.py"] + [Path(str(base) + ext) for ext in (".py", ".js", ".mjs", ".cjs", ".ts")]
            if target.resolve() in [p.resolve() for p in candidates]:
                return True
    return False


def check_label(check, lang):
    labels = {"test": ("tests passed", "시험 통과"), "build": ("build passed", "빌드 통과"),
              "run": ("program ran", "프로그램 실행"), "lint": ("lint passed", "문법 검사 통과"),
              "type": ("types passed", "자료형 검사 통과")}
    label = labels.get(check.get("kind"), ("check passed", "검사 통과"))[lang == "ko"]
    return label + ": " + short(check["cmd"])


def short(cmd):
    cmd = re.sub(r"^(cd\s+\S+\s*&&\s*)+", "", cmd.strip())
    return cmd if len(cmd) <= 40 else cmd[:37] + "..."


def ratchet(v, p):
    """Re-run remembered checks (single commands that passed before) that were not run since the last change.

    Returns (cmd, output) for the first one that now fails. Checks that time out or cannot finish within the
    budget are logged as unclear, so the receipt never claims more than was checked.
    """
    budget = time.time() + 240
    for g in v.load("green.json", []):
        argv, cwd = g.get("argv"), g.get("cwd")
        if not argv or not isinstance(argv, list) or not rememberable(argv):
            continue
        if any(supersedes(r, g) for r in p["passed"] + p["failed"]):
            continue
        if not cwd or not os.path.isdir(cwd) or not inside(cwd, v.root) or verifier(argv, v.root) != g.get("kind"):
            continue
        cmd = shlex.join(argv)
        entry = dict(ev="run", cmd=cmd, kind=g["kind"], prog=g.get("prog"), pos=g.get("pos", []), cwd=cwd, ratchet=True)
        if time.time() > budget:
            v.log(**entry, exit=None, ok=False)
            continue
        rc, out, err = run(argv, cwd=cwd, timeout=max(10, min(120, budget - time.time())))
        if rc in (124, 127):
            v.log(**entry, exit=None, ok=False)
            continue
        v.log(**entry, exit=rc, ok=rc == 0)
        if rc:
            return cmd, (out + err)[-1500:]
    return None


HOW_TO_SEE = re.compile(r"https?://|localhost|`[^`]+`|확인|열어|실행|눌러|클릭|접속|들어가|새로고침"
                        r"|\b(open|run|visit|click|try|check|go to|reload|refresh)\b", re.I)


def stop_id(d):
    raw = json.dumps([d.get("session_id"), d.get("prompt_id"), d.get("last_assistant_message"),
                      bool(d.get("stop_hook_active"))], ensure_ascii=False)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def on_stop(v):
    if not v.enabled:
        return
    d = v.data
    sid = stop_id(d)
    waiting = bool(d.get("background_tasks"))
    p = proof(v)
    pending, reread = remote_pending(v)
    overrides = list(dict.fromkeys(e.get("what", "") for e in v.turn() if e.get("ev") == "override"))
    if not p and not pending and not reread:
        v.state_update(stop={"id": sid, "decision": "nochange", "t": time.time()})
        if overrides:
            emit({"systemMessage": t("irreversible_only", v.lang, what=", ".join(overrides[:3]))})
        return
    reason = None
    broken = ratchet(v, p) if p and p["passed"] and not p["failed"] and v.config["ratchet"] else None
    # Block once per stop sequence. After that, or while background work runs, end honestly with the receipt.
    blocked = any(e.get("ev") == "stop_block" for e in v.turn())
    if not d.get("stop_hook_active") and not blocked and (not waiting or pending):
        if pending:
            reason = ("Re-read the remote result for the same target after your change (gh pr/issue view, gh run "
                      "list/view, git ls-remote, curl the deployment URL, or npm view). Do not repeat the write. "
                      "If it cannot be checked, say the remote result is not verified."
                      if v.lang != "ko" else "원격 결과를 다시 읽어 확인하세요. 변경한 같은 대상을 조회하고, 변경 명령을 다시 실행하지 마세요. 확인할 수 없으면 원격 결과 확인 못 함이라고 알려주세요.")
        elif p and p["failed"]:
            r = p["failed"][-1]
            reason = (f"The last check failed after your final change: `{r['cmd']}` (exit {r['exit']}). Fix the problem "
                      "and re-run it. If you cannot fix it, tell the user plainly that it still fails and why.")
        elif p and not p["passed"]:
            if p["unclear"]:
                reason = (f"Your check `{p['unclear'][-1]['cmd']}` hid its real result: something after it (`;`, `||`, "
                          "or a pipe without `set -o pipefail`) decides the exit code. Re-run the check on its own.")
            else:
                hints = suggest_checks(v.root)
                reason = ("You changed code (" + ", ".join(p["files"][:5]) + ") but nothing was run to check it after "
                          "your last change. Run the tests, the build, or the program itself now and report the real "
                          "result." + (" This project has: " + "; ".join(hints) + "." if hints else "") +
                          " If no check is possible, tell the user plainly what is not verified.")
        elif broken:
            cmd, out = broken
            reason = (f"Regression: `{cmd}` passed earlier in this project and fails now.\n{out}\nFix what broke "
                      "it. If that check is obsolete, remove it with: python3 "
                      f"\"{Path(__file__).resolve()}\" checks forget \"{cmd}\"")
        if p and not reason and not HOW_TO_SEE.search(str(d.get("last_assistant_message") or "")):
            reason = ("Before finishing, tell the user in plain words how they can see the result themselves: a URL "
                      "to open, a command to run, or where to click. They cannot read the code.")
    if reason:
        v.state_update(stop={"id": sid, "decision": "block", "t": time.time()})
        v.stop_event("stop_block", reason="remote_readback" if pending else "local_proof")
        return emit({"decision": "block", "reason": reason})
    p = (proof(v, files=p["files"]) or p) if p else None
    lang, n = v.lang, len(p["files"]) if p else 0
    codex = t("codex_wait", lang) if not waiting and codex_ready(v) else ""
    if not p:
        msg = "vibe " + ("⚠ " if pending else "✓ ") + t("remote_missing" if pending else "remote_ok", lang)
    elif p["failed"]:
        msg = t("receipt_fail", lang, n=n, cmd=short(p["failed"][-1]["cmd"]), codex=codex)
    elif p["passed"]:
        checks = ", ".join(dict.fromkeys(check_label(r, lang) for r in p["passed"]))
        if p["unclear"]:
            msg = t("receipt_partial", lang, n=n, checks=checks, cmd=short(p["unclear"][-1]["cmd"]), codex=codex)
        elif p["uncovered"]:
            msg = t("receipt_scope", lang, n=n, checks=checks, files=", ".join(p["uncovered"][:5]), codex=codex)
        else:
            msg = t("receipt_ok", lang, n=n, checks=checks, codex=codex)
    else:
        msg = t("receipt_none", lang, n=n, codex=codex)
    if overrides:
        msg += t("irreversible", lang, what=", ".join(overrides[:3]))
    if p and (pending or reread):
        msg += " | " + t("remote_missing" if pending else "remote_ok", lang)
        if pending:
            msg = msg.replace("vibe ✓", "vibe ⚠", 1)
    verified = not pending and (not p or (p["passed"] and not p["failed"] and not p["unclear"] and not p["uncovered"]))
    v.stop_event("stop_pass" if verified else "stop_unverified", recovered=blocked,
                 reason="remote_readback" if pending else "local_proof")
    v.state_update(stop={"id": sid, "decision": "allow" if verified else "unverified", "t": time.time()})
    emit({"systemMessage": msg})


# --------------------------------------------------------------------------- codex second opinion

REVIEW_PROMPT = """You are an independent reviewer. Another AI agent just made the change below for a user who cannot read code, so you are the only real reviewer.
Report only real problems: the change does not do what the user asked, breaks existing behavior, loses data, leaks secrets, or fakes verification (weakened or deleted tests, hard-coded expected outputs, swallowed errors). Ignore style.
You may read files in the repository for context. Do not modify anything.
If there are no real problems, reply with exactly: LGTM
Otherwise reply with at most 5 lines: `- path:line — problem — why it matters to the user`.

User request:
{prompt}

Change (unified diff; secret files are left out and secret-looking values are redacted):
{diff}
"""


def codex_ready(v):
    if v.config["codex"] == "off" or not shutil.which("codex"):
        return False
    return run(["codex", "login", "status"], timeout=15)[0] == 0


def on_codex(v):
    """Async Stop hook (asyncRewake): exit 2 wakes Claude with the reviewer's findings."""
    if not v.enabled or v.data.get("background_tasks"):
        return 0
    sid, started = stop_id(v.data), time.time()
    wait = float(os.environ.get("VIBE_STOP_WAIT", "300"))
    while time.time() - started < wait:  # wait for this exact Stop's verdict from the synchronous hook
        st = v.load("state.json", {}).get("stop", {})
        if st.get("id") == sid and st.get("t", 0) >= started - 3:  # this Stop, not an identical earlier one
            break
        time.sleep(0.5)
    else:
        return 0
    if st.get("decision") not in ("allow", "unverified") or not codex_ready(v):
        return 0
    state = v.load("state.json", {})
    if state.get("codex_rounds", 0) >= 2:
        return 0
    turn = state.get("turns", {}).get(v.pid or v.sid, {})
    before, after = turn.get("snap"), v.snapshot("review", "after change")
    if not before or not after:
        return 0
    names = v.changed(before, after) or []
    paths = [rel for _, rel in names if not SECRET_FILES.search(rel)][:400]
    rc, keyed, _ = v.git("grep", "-l", "-z", "-E", "BEGIN [A-Z0-9 ]*PRIVATE KEY", after, "--", *paths) if paths else (1, "", "")
    if rc not in (0, 1):
        return 0  # could not scan for keys: send nothing
    holding_keys = {k.split(":", 1)[1] for k in keyed.split("\0") if ":" in k}
    paths = [rel for rel in paths if rel not in holding_keys]
    if not paths:
        return 0
    _, diff, _ = v.git("diff", "--no-color", before, after, "--", *[":(literal)" + rel for rel in paths])
    if not diff.strip():
        return 0
    digest = hashlib.sha1(diff.encode()).hexdigest()
    if digest in state.get("reviewed", []):
        return 0
    diff = redact(diff)
    if len(diff) > 80_000:
        diff = diff[:80_000] + "\n[diff truncated; read the changed files directly]"
    v.state_update(codex_rounds=state.get("codex_rounds", 0) + 1)
    out_dir = v.dir / "reviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / time.strftime("%Y%m%d-%H%M%S.md")
    prompt = REVIEW_PROMPT.format(prompt=redact(turn.get("prompt", "(unknown)")), diff=diff)
    rc, _, err = run(["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "--ephemeral",
                      "-C", str(v.root), "-o", str(out_file), "-"], input_text=prompt, timeout=840)
    try:
        verdict = out_file.read_text().strip()
    except OSError:
        verdict = ""
    if rc or not verdict:
        return 0  # not marked as reviewed, so the next stop tries again
    v.state_update(reviewed=(v.load("state.json", {}).get("reviewed", []) + [digest])[-50:])
    if re.match(r"^\W*LGTM\b", verdict):
        return 0
    sys.stderr.write(
        "[vibe-claude] An independent reviewer (OpenAI Codex, a different model) checked the change you just "
        f"finished and reported possible problems:\n{verdict[:4000]}\n\nCheck each point against the code; the "
        "reviewer can be wrong. Fix the real problems and re-run the checks. Then tell the user in plain words what "
        "the reviewer found and what you did.\n")
    return 2


# --------------------------------------------------------------------------- CLI for the undo skill


def ago(ts):
    s = int(time.time() - ts)
    return f"{s // 60}m ago" if s < 3600 else (f"{s // 3600}h ago" if s < 86400 else time.strftime("%m-%d %H:%M", time.localtime(ts)))


KINDS = {"turn": "before request", "guard": "before risky command", "good": "checks passed",
         "undo": "before an undo", "review": "after change", "check": "end of request"}


def cli(argv):
    v = Vibe({"cwd": os.getcwd(), "session_id": os.environ.get("CLAUDE_SESSION_ID", "cli")})
    cmd = argv[0] if argv else "status"
    if cmd == "undo":
        sub = argv[1] if len(argv) > 1 else "list"
        if sub == "list":
            current = v.snapshot("now", "current state")
            snaps = [s for s in v.snapshots(60) if s["kind"] in ("turn", "guard", "good", "undo")][:15]
            if not current or not snaps:
                print("No snapshots yet." if v.snapshots_on() else "Snapshots are off or unavailable here.")
                return 0
            print("id          when          kind                   label  [difference from now]")
            mine = v.load("state.json", {}).get("current_snap") or next(
                (s["sha"] for s in snaps if s["kind"] == "turn"), None)
            for s in snaps:
                _, stat, _ = v.git("diff", "--shortstat", s["sha"], current)
                note = " (start of the current request)" if s["sha"] == mine else ""
                print(f"{s['sha'][:10]}  {ago(s['t']):>12}  {KINDS.get(s['kind'], s['kind']):<21}  "
                      f"{s['label'][:70]!r}  [{stat.strip() or 'same as now'}]{note}")
            return 0
        if sub in ("show", "restore") and len(argv) > 2:
            target = v.resolve(argv[2])
            if not target:
                if sub == "restore":
                    v.log(ev="undo", ok=False, reason="unknown_snapshot")
                print("No such snapshot id. Run `undo list` and copy an id from the first column.", file=sys.stderr)
                return 1
            if sub == "show":
                current = v.snapshot("now", "current state")
                print(v.git("diff", "--stat", target, current)[1] or "No differences.")
                return 0
            ok, info = v.restore(target)
            v.log(ev="undo", target=target, ok=ok)
            print(f"Restored. The files from just before this undo were saved as snapshot {info[:10]}; restore that id "
                  "to undo the undo." if ok else f"Not restored: {info}")
            return 0 if ok else 1
    if cmd == "trash":
        base = v.dir / "trash"
        entries = sorted((x for x in base.iterdir() if x.is_dir()), reverse=True) if base.is_dir() else []
        if len(argv) > 2 and argv[1] == "restore":
            src = base / argv[2]
            if not re.fullmatch(r"[\w-]+", argv[2]) or not src.is_dir():
                print("No such trash id. Run `trash` to list them.", file=sys.stderr)
                return 1
            restored = skipped = 0
            for d, _, names in os.walk(src):
                for name in names:
                    f = Path(d) / name
                    rel = os.path.relpath(f, src)
                    if rel == ".vibe-trash.json":
                        continue
                    dest = Path("/" + rel[len("_outside/"):]) if rel.startswith("_outside/") else v.root / rel
                    if dest.exists() or dest.is_symlink():
                        skipped += 1
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest, follow_symlinks=False)
                    restored += 1
            print(f"Restored {restored} file(s); left {skipped} that exist again untouched.")
            return 0
        for e in entries[:15]:
            try:
                meta = json.loads((e / ".vibe-trash.json").read_text())
            except (OSError, ValueError):
                meta = {}
            print(f"{e.name}  {ago(meta.get('t', 0)):>10}  {meta.get('files', '?')} file(s)  $ {meta.get('cmd', '')[:90]}")
        if not entries:
            print("Trash is empty.")
        return 0
    if cmd == "allow-delete" and len(argv) > 1:
        rel = os.path.relpath(os.path.realpath(argv[1]), v.root)
        if rel.startswith("..") or rel == ".":
            print("Only folders inside the project can be marked.", file=sys.stderr)
            return 1
        cfg = v.load("config.json", {})
        cfg["safe_to_delete"] = sorted(set(cfg.get("safe_to_delete", [])) | {rel})
        v.save("config.json", cfg)
        print(f"Deleting files under {rel} will no longer ask (its contents are not backed up).")
        return 0
    if cmd == "checks":
        green = v.load("green.json", [])
        if len(argv) > 2 and argv[1] == "forget":
            v.save("green.json", [g for g in green if shlex.join(g.get("argv", [])) != argv[2]])
            print("Forgotten.")
        else:
            print("\n".join(shlex.join(g["argv"]) for g in green if g.get("argv")) or "No remembered checks.")
        return 0
    if cmd == "status":
        since = time.time() - 7 * 86400
        counts = dict.fromkeys(("stop_block", "stop_pass", "stop_unverified", "undo"), 0)
        for e in v.ledger():
            if e.get("t", 0) >= since and e.get("ev") in counts:
                counts[e["ev"]] += 1
        print(json.dumps({"version": VERSION, "project": str(v.root), "state": str(v.dir), "enabled": v.enabled,
                          "config": v.config, "codex": codex_ready(v), "snapshots": len(v.snapshots(1000)),
                          "events_7d": counts,
                          "checks": [shlex.join(g["argv"]) for g in v.load("green.json", []) if g.get("argv")]},
                         indent=1, ensure_ascii=False))
        return 0
    print("usage: vibe.py undo [list|show ID|restore ID] | trash [restore ID] | checks [forget CMD] | allow-delete FOLDER"
          " | status",
          file=sys.stderr)
    return 2


EVENTS = {"session-start": on_session_start, "prompt": on_prompt, "pre-tool": on_pre_tool,
          "post-tool": on_post_tool, "post-tool-fail": lambda v: on_post_tool(v, failed=True),
          "stop": on_stop, "codex": on_codex}


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    if event not in EVENTS:
        return cli(sys.argv[1:])
    data = read_input()
    v = Vibe(data)
    try:
        return EVENTS[event](v) or 0
    except Exception as e:  # fail open, but leave a trace
        try:
            v.dir.mkdir(parents=True, exist_ok=True)
            with (v.dir / "errors.log").open("a") as f:
                f.write(f"{time.ctime()} {event}: {type(e).__name__}: {e}\n")
        except OSError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
