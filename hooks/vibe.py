#!/usr/bin/env python3
"""vibe-claude v6: proof, guard and undo for people who don't read code.

One script, called by hooks/hooks.json as `vibe.py <event>`, plus a small CLI
(`vibe.py undo|checks|status`) used by the undo skill. Standard library only.
Every hook fails open: an internal error never blocks the user's work.
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "6.0.0"
DEFAULTS = {"codex": "auto", "ratchet": True, "snapshots": True, "packages": True, "lang": None}
DOC_EXT = {"md", "mdx", "txt", "rst", "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "pdf", "csv", "lock", "log"}
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
.vibe/
.git/
"""

# --------------------------------------------------------------------------- text

MSG = {
    "receipt_ok": ("vibe ✓ {n} file(s) changed · checked: {checks}{codex} · undo: /vibe-claude:undo",
                   "vibe ✓ 파일 {n}개 변경 · 확인됨: {checks}{codex} · 되돌리기: /vibe-claude:undo"),
    "receipt_none": ("vibe ⚠ {n} file(s) changed · nothing was run to check it · undo: /vibe-claude:undo",
                     "vibe ⚠ 파일 {n}개 변경 · 실행해서 확인한 기록이 없어요 · 되돌리기: /vibe-claude:undo"),
    "receipt_fail": ("vibe ✗ {n} file(s) changed · last check failed: {cmd} · undo: /vibe-claude:undo",
                     "vibe ✗ 파일 {n}개 변경 · 마지막 검사 실패: {cmd} · 되돌리기: /vibe-claude:undo"),
    "codex_wait": (" · Codex review running", " · Codex 검토 중"),
    "ask_head": ("⚠ Hard to undo: {what}.", "⚠ 되돌리기 어려운 명령이에요: {what}."),
    "ask_files": ("A backup of your files was saved just now (/vibe-claude:undo).",
                  "방금 파일 백업을 만들어 뒀어요(/vibe-claude:undo로 되돌릴 수 있어요)."),
    "ask_nofiles": ("A file backup cannot bring this back.", "파일 백업으로는 되돌릴 수 없어요."),
    "ask_tail": ("Allow only if you asked for this.", "직접 요청한 일일 때만 허락하세요."),
    "tests_weak": ("⚠ Claude wants to weaken a test ({detail}) in {path}. Tests are what prove the app works. "
                   "Allow only if Claude explained why the test itself is wrong.",
                   "⚠ Claude가 테스트를 약하게 바꾸려고 해요({detail}) — {path}. 테스트는 앱이 제대로 되는지 증명하는 장치예요. "
                   "테스트 자체가 틀렸다는 설명을 들었을 때만 허락하세요."),
    "pkg_new": ("⚠ The package '{name}' is very new ({days} days old) or rarely used. "
                "Fake look-alike packages often look like this. Allow only if you trust it.",
                "⚠ '{name}' 패키지는 생긴 지 {days}일밖에 안 됐거나 거의 쓰이지 않아요. "
                "가짜 패키지가 이런 모습인 경우가 많아요. 믿을 수 있을 때만 허락하세요."),
}


def t(key, lang, **kw):
    en, ko = MSG[key]
    return (ko if lang == "ko" else en).format(**kw)


# --------------------------------------------------------------------------- core


def read_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
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


class Vibe:
    def __init__(self, data):
        self.data = data
        root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
        self.root = Path(root).resolve()
        self.dir = self.root / ".vibe"
        # Never keep state for a home folder or filesystem root: too big to snapshot.
        self.enabled = self.root.is_dir() and self.root not in (Path.home().resolve(), Path("/"))
        self.sid = data.get("session_id", "")
        self.pid = data.get("prompt_id", "")

    # ---- files
    def ensure(self):
        self.dir.mkdir(exist_ok=True)
        ignore = self.dir / ".gitignore"
        if not ignore.exists():
            ignore.write_text("*\n")

    def load(self, name, default):
        try:
            return json.loads((self.dir / name).read_text())
        except (OSError, ValueError):
            return default

    def save(self, name, value):
        self.ensure()
        tmp = self.dir / (name + ".tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
        tmp.replace(self.dir / name)

    @property
    def config(self):
        cfg = dict(DEFAULTS)
        cfg.update(self.load("config.json", {}))
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
    def log(self, **entry):
        if not self.enabled:
            return
        self.ensure()
        entry.update(t=time.time(), sid=self.sid, pid=self.pid)
        path = self.dir / "ledger.jsonl"
        with path.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if path.stat().st_size > 2_000_000:  # keep the newest half
            lines = path.read_text().splitlines()
            path.write_text("\n".join(lines[len(lines) // 2:]) + "\n")

    def turn(self):
        """Ledger entries of the current user request (same prompt_id)."""
        out = []
        try:
            lines = (self.dir / "ledger.jsonl").read_text().splitlines()
        except OSError:
            return out
        for line in lines:
            try:
                e = json.loads(line)
            except ValueError:
                continue
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

    # ---- shadow snapshots (a private git repo in .vibe/, never the user's .git)
    def git(self, *args, index=None, timeout=60, input_text=None):
        env = dict(os.environ, GIT_DIR=str(self.dir / "shadow.git"), GIT_WORK_TREE=str(self.root),
                   GIT_INDEX_FILE=str(index or self.dir / "shadow.git" / "index"),
                   GIT_AUTHOR_NAME="vibe", GIT_AUTHOR_EMAIL="vibe@localhost",
                   GIT_COMMITTER_NAME="vibe", GIT_COMMITTER_EMAIL="vibe@localhost")
        env.pop("GIT_OBJECT_DIRECTORY", None)
        return run(["git", *args], cwd=self.root, env=env, timeout=timeout, input_text=input_text)

    def snapshot(self, kind, label=""):
        if not (self.enabled and self.config["snapshots"] and shutil.which("git")):
            return None
        self.ensure()
        repo = self.dir / "shadow.git"
        if not repo.exists():
            if run(["git", "init", "-q", "--bare", str(repo)])[0]:
                return None
            run(["git", "--git-dir", str(repo), "config", "core.bare", "false"])
            run(["git", "--git-dir", str(repo), "config", "gc.auto", "0"])
            (repo / "info").mkdir(exist_ok=True)
            (repo / "info" / "exclude").write_text(SHADOW_EXCLUDES)
        if self.git("add", "-A", ".", timeout=40)[0]:
            return None
        rc, tree, _ = self.git("write-tree")
        if rc:
            return None
        tree = tree.strip()
        rc, head, _ = self.git("rev-parse", "-q", "--verify", "refs/heads/snaps")
        head = head.strip() if rc == 0 else ""
        if head:
            _, head_tree, _ = self.git("rev-parse", head + "^{tree}")
            if head_tree.strip() == tree and kind not in ("turn", "undo"):
                return head
        meta = json.dumps({"t": time.time(), "kind": kind, "label": label[:120]}, ensure_ascii=False)
        args = ["commit-tree", tree, "-m", meta] + (["-p", head] if head else [])
        rc, commit, _ = self.git(*args)
        if rc:
            return None
        commit = commit.strip()
        self.git("update-ref", "refs/heads/snaps", commit)
        return commit

    def snapshots(self, limit=20):
        rc, out, _ = self.git("log", "-n", str(limit), "--format=%H %s", "refs/heads/snaps")
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

    def files_in(self, ref):
        rc, out, _ = self.git("ls-tree", "-r", "-z", "--name-only", ref)
        return set(filter(None, out.split("\0"))) if rc == 0 else set()

    def restore(self, sha):
        before = self.snapshot("undo", "before undo to " + sha[:8])
        if not before:
            return False, "could not snapshot current state"
        extra = self.files_in(before) - self.files_in(sha)
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
            if p.is_file() or p.is_symlink():
                p.unlink()
        return True, before


# --------------------------------------------------------------------------- classification

VERIFY = [
    ("test", r"\b(pytest|py\.test|nose2|tox|nox|vitest|jest|mocha|jasmine|karma|rspec|phpunit|bats|ctest)\b"
             r"|\bpython3?\s+-m\s+(pytest|unittest)\b|\b(cypress\s+run|playwright\s+test)\b"
             r"|\b(npm|pnpm|yarn|bun)\s+(run\s+)?test\b|\b(deno|go|cargo|swift|dotnet|mix|flutter|dart)\s+test\b"
             r"|\bmvn\b.*\b(test|verify)\b|\bgradlew?\b.*\b(test|check)\b|\bxcodebuild\b.*\btest\b"
             r"|\bmake\s+(test|check)\b|\b(bash|sh|python3?|node)\s+(\./)?tests?/[\w./-]*\.(sh|py|js)\b"),
    ("type", r"\b(tsc|mypy|pyright|basedpyright)\b|\b(npm|pnpm|yarn|bun)\s+(run\s+)?(typecheck|type-check|check-types)\b"
             r"|\bcargo\s+check\b|\bgo\s+vet\b"),
    ("lint", r"\b(eslint|ruff|flake8|pylint|shellcheck|golangci-lint|biome|stylelint|rubocop|swiftlint|clippy)\b"
             r"|\b(npm|pnpm|yarn|bun)\s+(run\s+)?lint\b|\bprettier\b.*--check|\bbash\s+-n\b|\bclaude\s+plugin\s+validate\b"),
    ("build", r"\b(npm|pnpm|yarn|bun)\s+(run\s+)?build\b|\b(cargo|go|swift|dotnet|zig)\s+build\b|\bxcodebuild\b"
              r"|\b(vite|next|nuxt|astro|webpack|esbuild|turbo)\s+build\b|\bgradlew?\b.*\b(build|assemble)\b"
              r"|\bmvn\b.*\b(package|install|compile)\b|(^|[;&]\s*)make(\s|$)"),
    ("run", r"\b(curl|wget|http)\b.*\b(localhost|127\.0\.0\.1|0\.0\.0\.0)\b"),
]
RUNNERS = {"python", "python3", "node", "bun", "deno", "ruby", "php", "tsx", "ts-node", "bash", "sh", "zsh", "perl"}
LONG_RUNNING = re.compile(r"--watch\b|\b(dev|serve|start|watch)\b")
PIPE = re.compile(r"(?<!\|)\|(?!\|)")
SWALLOW = re.compile(r"\|\|\s*(true|:|exit\s+0)\b|;\s*(true|exit\s+0)\s*$")


def classify(cmd, root=None):
    for kind, pattern in VERIFY:
        if re.search(pattern, cmd):
            return kind
    if root:  # running a project file directly counts as a smoke run
        for segment in re.split(r"&&|;|\n", cmd):
            try:
                toks = shlex.split(segment)
            except ValueError:
                continue
            if len(toks) >= 2 and os.path.basename(toks[0]) in RUNNERS:
                arg = next((x for x in toks[1:] if not x.startswith("-")), "")
                if "-c" not in toks and "-e" not in toks and arg and (Path(root) / arg).is_file():
                    return "run"
    return None


def masked(cmd):
    """True when the exit code cannot be trusted (piped into tail/grep, or errors swallowed)."""
    if SWALLOW.search(cmd):
        return True
    segments = PIPE.split(cmd)
    return len(segments) > 1 and "pipefail" not in cmd and not classify(segments[-1])


MISSING_TOOL = re.compile(r"No module named \S+$|command not found|ENOENT|Cannot find module|Missing script:"
                          r"|is not recognized as|not installed", re.M)
FAIL_OUT = re.compile(r"\b\d+ (failed|errors?)\b|\bFAILED\b|\bFAIL\b|npm ERR!|\bTraceback\b|\berror(\[\w+\])?:|✗|\bfailing\b")
PASS_OUT = re.compile(r"\b\d+ passed\b|^OK\b|[Aa]ll (tests|checks) passed|\b0 (failures|errors)\b|✓|\b\d+ passing\b|\bsucceeded\b", re.M)


def is_code(path):
    return path.rsplit(".", 1)[-1].lower() not in DOC_EXT if "." in os.path.basename(path) else True


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

#   (pattern, english effect, korean effect, files-backup-helps)
DANGER = [
    (r"\bgit\s+reset\b[^;&|]*--hard", "throws away all unsaved code changes", "저장하지 않은 코드 변경이 전부 사라져요", True),
    (r"\bgit\s+clean\b[^;&|]*\s-\w*f", "deletes every file git does not track", "git이 관리하지 않는 파일을 전부 지워요", True),
    (r"\bgit\s+(checkout|restore)\s+(--\s+)?\.(\s|$)|\bgit\s+checkout\s+-f\b",
     "throws away unsaved changes in every file", "모든 파일의 저장 안 된 변경을 버려요", True),
    (r"\bgit\s+push\b[^;&|]*(\s--force\b|\s-f\b|--force-with-lease|\s\+\S)",
     "overwrites the online copy of the project history", "온라인에 있는 프로젝트 기록을 덮어써요", False),
    (r"\bgit\s+branch\b[^;&|]*\s-D\b", "deletes a branch even if its work was never merged",
     "합쳐지지 않은 작업이 있어도 브랜치를 지워요", False),
    (r"\bgit\s+stash\s+(drop|clear)\b", "deletes saved-aside work", "따로 보관해 둔 작업을 지워요", False),
    (r"\bgit\s+(filter-branch|filter-repo)\b", "rewrites the whole project history", "프로젝트 기록 전체를 다시 써요", False),
    (r"(?i)\b(drop\s+(table|database|schema|collection)|truncate\s+(table\s+)?\w+)",
     "deletes a database table and its data", "데이터베이스 표와 그 안의 데이터를 지워요", False),
    (r"(?i)\bdelete\s+from\s+[\w.\"`\[\]]+\s*(;|$|\"|')", "deletes every row of a database table",
     "데이터베이스 표의 모든 줄을 지워요", False),
    (r"(?i)\b(prisma\s+migrate\s+reset|supabase\s+db\s+reset|rails\s+db:(drop|reset)|rake\s+db:(drop|reset)|dropdb"
     r"|flushall|flushdb|manage\.py\s+flush)\b", "wipes the database", "데이터베이스를 통째로 비워요", False),
    (r"\bfind\b[^;&|]*(\s-delete\b|-exec\s+rm\b)", "deletes every file that matches a search", "검색에 걸린 파일을 전부 지워요", True),
    (r"\b(mkfs\S*|diskutil\s+(erase\w*|partition\w*))\b|\bdd\b[^;&|]*\bof=/dev/", "erases a whole disk",
     "디스크 전체를 지워요", False),
    (r"\bdocker\s+(system|volume)\s+prune\b|\bdocker\s+volume\s+rm\b|\bdocker[- ]compose\b[^;&|]*\bdown\b[^;&|]*\s-v\b",
     "deletes saved container data", "컨테이너에 저장된 데이터를 지워요", False),
    (r"\b(terraform|tofu)\s+destroy\b|\bkubectl\s+delete\b|\bheroku\s+(apps:destroy|pg:reset)\b"
     r"|\bgh\s+repo\s+delete\b|\bvercel\s+(rm|remove)\b", "deletes live online resources", "실제로 운영 중인 온라인 자원을 지워요", False),
    (r"\bchmod\s+-R\s+0?777\b", "makes every file writable by anyone", "모든 파일을 누구나 고칠 수 있게 바꿔요", True),
]
REGENERABLE = {"node_modules", "dist", "build", "out", ".next", ".nuxt", ".turbo", "coverage", "__pycache__",
               ".pytest_cache", ".mypy_cache", ".ruff_cache", "target", ".cache", ".parcel-cache", ".vite", "tmp"}
SECRETS = [
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key"),
    (r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}", "OpenAI/Anthropic API key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{36,}\b", "GitHub token"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\b(sk|rk)_live_[A-Za-z0-9]{20,}", "Stripe live key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "private key"),
    (r"(?i)\bservice_role\b[\"']?\s*[:=]\s*[\"']eyJ[A-Za-z0-9_-]{20,}", "Supabase service-role key"),
]
SECRET_OK_FILES = re.compile(r"(^|/)\.env(\.[\w.-]+)?$|\.(pem|key)$")


def split_commands(cmd):
    for segment in re.split(r"&&|\|\||;|\||\n", cmd):
        try:
            toks = shlex.split(segment)
        except ValueError:
            toks = segment.split()
        while toks and (re.match(r"^\w+=", toks[0]) or toks[0] in ("sudo", "command", "exec", "nohup", "time", "xargs")):
            toks.pop(0)
        if toks:
            yield toks


def rm_verdict(cmd, root):
    """Return ('deny'|'ask'|None, effect_en, effect_ko) for rm-like commands."""
    home = str(Path.home())
    for toks in split_commands(cmd):
        if os.path.basename(toks[0]) not in ("rm", "rmdir", "unlink"):
            continue
        flags = "".join(x.lstrip("-") for x in toks[1:] if x.startswith("-") and x != "--")
        recursive = "r" in flags.lower() or "recursive" in flags
        targets = [x for x in toks[1:] if not x.startswith("-")]
        if not targets:
            return "ask", "deletes the files listed by the previous command", "앞 명령이 찾은 파일들을 지워요"
        for target in targets:
            expanded = os.path.expanduser(target.replace("$HOME", home).replace("${HOME}", home))
            resolved = os.path.realpath(os.path.join(root, expanded))
            if resolved in ("/", home, str(root)) or target in ("/*", "~/*", "*", ".", "..", "./*"):
                if recursive or "*" in target:
                    return "deny", f"deletes everything in {target}", f"{target} 안의 모든 것을 지워요"
        unsafe = [x for x in targets if not (os.path.basename(x.rstrip("/")) in REGENERABLE
                                             or re.match(r"^(/tmp|/private/tmp|/var/folders|\$TMPDIR)", x))]
        if recursive and unsafe:
            return "ask", f"permanently deletes {', '.join(unsafe[:3])} and everything inside", \
                f"{', '.join(unsafe[:3])} 폴더와 그 안의 모든 것을 영구히 지워요"
        tests = [x for x in targets if TEST_PATH.search(x)]
        if tests:
            return "ask", f"deletes test file(s) {', '.join(tests[:3])}", f"테스트 파일 {', '.join(tests[:3])}을(를) 지워요"
        if any("*" in x for x in unsafe):
            return "ask", f"deletes every file matching {', '.join(unsafe[:3])}", f"{', '.join(unsafe[:3])}에 맞는 파일을 전부 지워요"
    return None, "", ""


def install_targets(cmd):
    """Yield (ecosystem, package) for package install commands."""
    for toks in split_commands(cmd):
        name = os.path.basename(toks[0])
        rest = toks[1:]
        eco = None
        if name in ("npm", "pnpm", "yarn", "bun") and rest and rest[0] in ("i", "install", "add"):
            eco, rest = "npm", rest[1:]
        elif name in ("pip", "pip3", "uv", "poetry") or (name.startswith("python") and rest[:2] == ["-m", "pip"]):
            if name.startswith("python"):
                rest = rest[2:]
            if name == "uv" and rest[:1] == ["pip"]:
                rest = rest[1:]
            if rest and rest[0] in ("install", "add"):
                eco, rest = "pypi", rest[1:]
        elif name == "cargo" and rest[:1] == ["add"]:
            eco, rest = "crates", rest[1:]
        if not eco:
            continue
        skip_next = False
        for arg in rest:
            if skip_next:
                skip_next = False
                continue
            if arg in ("-r", "--requirement", "-e", "--editable", "-c", "--constraint", "--index-url", "-i", "--registry"):
                skip_next = True
                continue
            if arg.startswith("-") or "/" in arg and not arg.startswith("@") or arg.startswith(".") or ":" in arg:
                continue
            if eco == "npm":
                pkg = re.match(r"^(@[^/@]+/[^@]+|[^@]+)", arg)
            else:
                pkg = re.match(r"^[A-Za-z0-9_.-]+", arg)
            if pkg:
                yield eco, pkg.group(1) if eco == "npm" else pkg.group(0)


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
1. Prove it, don't claim it. A hook records every command and its exit code. After you change code, run a real check (tests, build, or the program itself) after the last edit, without piping it into tail/grep or adding `|| true`, before you say it is done.
2. Report in plain words: what changed for the user, how they can see it themselves (a URL, a command, or where to click), and what might break. No diffs or code unless asked.
3. Same error twice: change the approach instead of retrying.
4. Change only what was asked. Never weaken, skip or delete tests to make them pass; fix the code.
5. Earlier states are saved automatically; the user can return to one with /vibe-claude:undo."""


def on_session_start(v):
    emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": RULES}})


def on_prompt(v):
    if not v.enabled:
        return
    prompt = str(v.data.get("prompt", ""))
    lang = "ko" if re.search(r"[가-힣]", prompt) else ("en" if re.search(r"[A-Za-z]{3}", prompt) else None)
    st = v.load("state.json", {})
    if lang:
        st["lang"] = lang
    snap = v.snapshot("turn", prompt.strip().splitlines()[0][:100] if prompt.strip() else "")
    turns = st.get("turns", {})
    turns[v.pid or v.sid] = {"snap": snap, "prompt": prompt[:600], "t": time.time()}
    st["turns"] = dict(list(turns.items())[-20:])
    st["codex_rounds"] = 0
    v.save("state.json", st)
    v.log(ev="turn")


def new_content(tool, inp, old):
    if tool == "Write":
        return inp.get("content", "")
    if tool == "Edit":
        edits = [inp]
    elif tool == "MultiEdit":
        edits = inp.get("edits", [])
    else:
        return None
    text = old
    for e in edits:
        a, b = e.get("old_string", ""), e.get("new_string", "")
        text = text.replace(a, b) if e.get("replace_all") else text.replace(a, b, 1)
    return text


def ask(reason):
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                 "permissionDecisionReason": reason}})


def deny(reason):
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})


def on_pre_tool(v):
    tool = v.data.get("tool_name", "")
    inp = v.data.get("tool_input", {}) or {}
    lang = v.lang
    if tool == "Bash":
        return pre_bash(v, str(inp.get("command", "")), lang)
    path = inp.get("file_path") or inp.get("notebook_path") or ""
    if not path:
        return
    try:
        old = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        old = ""
    new = new_content(tool, inp, old)
    if new is None:
        return
    rel = os.path.relpath(path, v.root) if path.startswith(str(v.root)) else path
    if not SECRET_OK_FILES.search(path):
        for pattern, label in SECRETS:
            if re.search(pattern, new) and not re.search(pattern, old):
                return deny(f"vibe-claude blocked this edit: it would write a real-looking {label} into {rel}. "
                            "Secrets in code leak when the project is shared or deployed. Read it from an "
                            "environment variable and keep the value in a .env file that is git-ignored, then tell "
                            "the user in plain words where to paste their key.")
    if old and TEST_PATH.search(rel):
        detail = weakening(old, new)
        if detail:
            return ask(t("tests_weak", lang, detail=detail, path=rel))


def pre_bash(v, cmd, lang):
    verdict, en, ko = rm_verdict(cmd, v.root)
    files_help = True
    if not verdict:
        for pattern, d_en, d_ko, helps in DANGER:
            if re.search(pattern, cmd):
                verdict, en, ko, files_help = "ask", d_en, d_ko, helps
                break
    if verdict:
        v.snapshot("guard", cmd[:100])
        what = ko if lang == "ko" else en
        if verdict == "deny":
            return deny(f"vibe-claude blocked a catastrophic command ({en}). Do not try to work around this. "
                        "Explain to the user in plain words what you wanted to do and find a narrower command.")
        tail = t("ask_files" if files_help else "ask_nofiles", lang)
        return ask(f"{t('ask_head', lang, what=what)}\n{tail} {t('ask_tail', lang)}\n$ {cmd[:300]}")
    if re.search(r"\bgit\s+(checkout|switch|merge|rebase|pull|stash|apply|am)\b|\bsed\s+-i|\bmv\s", cmd):
        v.snapshot("guard", cmd[:100])
    if v.config["packages"]:
        for eco, name in list(install_targets(cmd))[:8]:
            exists, age = package_info(eco, name)
            if exists is False:
                return deny(f"vibe-claude blocked install: the {eco} package '{name}' does not exist. AI models often "
                            "invent package names, and attackers register those names with malware. Find the real "
                            "package name from official documentation before installing anything.")
            if exists and age is not None and age < 14:
                return ask(t("pkg_new", lang, name=name, days=age))


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
                    "yaml.safe_load(open(sys.argv[1],encoding='utf-8'))", path])
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


def on_post_tool(v, failed=False):
    tool = v.data.get("tool_name", "")
    inp = v.data.get("tool_input", {}) or {}
    if tool == "Bash":
        cmd = str(inp.get("command", ""))
        kind = classify(cmd, v.root)
        if not kind or not v.enabled:
            return
        if failed:
            if v.data.get("is_interrupt"):
                return
            m = re.match(r"Exit code (\d+)", str(v.data.get("error", "")))
            code = int(m.group(1)) if m else 1
            out = str(v.data.get("error", ""))
            if code == 127 or MISSING_TOOL.search(out[-2000:]):
                return  # the checker is not installed: no evidence either way
        elif inp.get("run_in_background"):
            return
        else:
            resp = v.data.get("tool_response", {}) or {}
            code = 0
            out = str(resp.get("stdout", "")) + str(resp.get("stderr", ""))
        hidden = masked(cmd)
        ok = code == 0 and not hidden
        if hidden and code == 0:  # trust the tool's own output, never the model's words
            tail = out[-3000:]
            ok = bool(PASS_OUT.search(tail)) and not FAIL_OUT.search(tail)
            code = 0 if ok else ("?" if FAIL_OUT.search(tail) else None)
        v.log(ev="run", cmd=cmd[:500], kind=kind, exit=code, ok=ok, masked=hidden, cwd=v.data.get("cwd", ""))
        if ok and not hidden and kind in ("test", "type", "lint", "build") and not LONG_RUNNING.search(cmd) \
                and len(cmd) < 300 and v.config["ratchet"]:
            green = [g for g in v.load("green.json", []) if g.get("cmd") != cmd]
            green.append({"cmd": cmd, "cwd": v.data.get("cwd") or str(v.root), "kind": kind, "t": time.time()})
            v.save("green.json", green[-5:])
            v.snapshot("good", cmd[:100])
        return
    path = inp.get("file_path") or inp.get("notebook_path") or ""
    if not path or not os.path.isfile(path):
        return
    if v.enabled and str(Path(path).resolve()).startswith(str(v.root) + os.sep):
        v.log(ev="edit", path=os.path.relpath(Path(path).resolve(), v.root), code=is_code(path))
    rc, out, err = check_syntax(path, v.root)
    if rc and rc not in (124, 127):
        emit({"decision": "block", "reason": f"Syntax check failed for {path}:\n{(err or out)[:4000]}"})


def proof(v):
    """Summarize the current request: edited files and the evidence after the last edit."""
    turn = v.turn()
    edits = [e for e in turn if e.get("ev") == "edit" and e.get("code")]
    if not edits:
        return None
    last_edit = max(e["t"] for e in edits)
    runs = [e for e in turn if e.get("ev") == "run" and e["t"] >= last_edit]
    files = sorted({e["path"] for e in edits})
    latest = {}
    for r in runs:
        latest[r["cmd"]] = r
    passed = [r for r in latest.values() if r.get("ok")]
    failed = [r for r in latest.values() if r.get("exit") not in (0, None)]
    unclear = [r for r in latest.values() if r.get("exit") is None]
    return {"files": files, "passed": passed, "failed": failed, "unclear": unclear, "last_edit": last_edit}


def short(cmd):
    cmd = re.sub(r"^(cd\s+\S+\s*&&\s*)+", "", cmd.strip())
    return cmd if len(cmd) <= 40 else cmd[:37] + "..."


def ratchet(v, p):
    """Re-run checks that passed before but were not re-run since the last edit."""
    done = {r["cmd"] for r in p["passed"]} | {r["cmd"] for r in p["failed"]}
    budget = time.time() + 240
    for g in v.load("green.json", []):
        if g["cmd"] in done or time.time() > budget:
            continue
        cwd = g.get("cwd") if g.get("cwd") and os.path.isdir(g["cwd"]) else str(v.root)
        rc, out, err = run(["bash", "-c", g["cmd"]], cwd=cwd, timeout=max(10, min(120, budget - time.time())))
        if rc == 124:
            continue
        v.log(ev="run", cmd=g["cmd"], kind=g["kind"], exit=rc, ok=rc == 0, masked=False, cwd=cwd, ratchet=True)
        if rc:
            return g["cmd"], (out + err)[-1500:]
    return None


HOW_TO_SEE = re.compile(r"https?://|localhost|`[^`]+`|확인|열어|실행|눌러|클릭|접속|들어가|\b(open|run|visit|click|try|check|go to)\b",
                        re.I)


def on_stop(v):
    if not v.enabled:
        return
    d = v.data
    active = bool(d.get("stop_hook_active"))
    if d.get("background_tasks"):
        return
    p = proof(v)
    if not p:
        v.state_update(stop={"pid": v.pid, "decision": "allow", "t": time.time()})
        return
    reason = None
    if not active:
        if p["failed"]:
            r = p["failed"][-1]
            reason = (f"The last check failed after your final edit: `{r['cmd']}` (exit {r['exit']}). Fix the problem "
                      "and re-run it. If you cannot fix it, tell the user plainly that it still fails and why.")
        elif not p["passed"]:
            if p["unclear"]:
                reason = (f"Your check `{p['unclear'][-1]['cmd']}` hid its real result (a pipe or `|| true` replaces "
                          "the exit code). Re-run it without the pipe, or with `set -o pipefail;` in front.")
            else:
                reason = ("You changed code (" + ", ".join(p["files"][:5]) + ") but nothing was run to check it after "
                          "your last edit. Run the tests, the build, or the program itself now and report the real "
                          "result. If no check is possible, tell the user plainly what is not verified.")
        elif v.config["ratchet"]:
            broken = ratchet(v, p)
            if broken:
                cmd, out = broken
                reason = (f"Regression: `{cmd}` passed earlier in this project and fails now.\n{out}\nFix what broke "
                          "it. If that check is obsolete, remove it with: python3 "
                          f"\"{Path(__file__).resolve()}\" checks forget \"{cmd}\"")
        if not reason and not HOW_TO_SEE.search(str(d.get("last_assistant_message", ""))):
            reason = ("Before finishing, tell the user in plain words how they can see the result themselves: a URL "
                      "to open, a command to run, or where to click. They cannot read the code.")
    if reason:
        v.state_update(stop={"pid": v.pid, "decision": "block", "t": time.time()})
        return emit({"decision": "block", "reason": reason})
    p = proof(v) or p
    lang, n = v.lang, len(p["files"])
    codex = t("codex_wait", lang) if codex_ready(v) else ""
    if p["failed"]:
        msg = t("receipt_fail", lang, n=n, cmd=short(p["failed"][-1]["cmd"]))
    elif p["passed"]:
        checks = ", ".join(dict.fromkeys(short(r["cmd"]) for r in p["passed"]))
        msg = t("receipt_ok", lang, n=n, checks=checks, codex=codex)
    else:
        msg = t("receipt_none", lang, n=n)
    v.state_update(stop={"pid": v.pid, "decision": "allow", "t": time.time()})
    emit({"systemMessage": msg})


# --------------------------------------------------------------------------- codex second opinion

REVIEW_PROMPT = """You are an independent reviewer. Another AI agent just made the change below for a user who cannot read code, so you are the only real reviewer.
Report only real problems: the change does not do what the user asked, breaks existing behavior, loses data, leaks secrets, or fakes verification (weakened or deleted tests, hard-coded expected outputs, swallowed errors). Ignore style.
You may read files in the repository for context. Do not modify anything.
If there are no real problems, reply with exactly: LGTM
Otherwise reply with at most 5 lines: `- path:line — problem — why it matters to the user`.

User request:
{prompt}

Change (unified diff):
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
    started = time.time()
    while time.time() - started < 300:  # wait for the synchronous Stop hook's verdict
        st = v.load("state.json", {}).get("stop", {})
        if st.get("pid") == v.pid and st.get("t", 0) >= started - 5:
            break
        time.sleep(1)
    else:
        return 0
    if st.get("decision") != "allow" or not proof(v) or not codex_ready(v):
        return 0
    state = v.load("state.json", {})
    if state.get("codex_rounds", 0) >= 2:
        return 0
    turn = state.get("turns", {}).get(v.pid or v.sid, {})
    before, after = turn.get("snap"), v.snapshot("review", "after change")
    if not before or not after:
        return 0
    _, diff, _ = v.git("diff", "--no-color", before, after, "--", ".")
    if not diff.strip():
        return 0
    digest = hashlib.sha1(diff.encode()).hexdigest()
    if digest in state.get("reviewed", []):
        return 0
    if len(diff) > 80_000:
        diff = diff[:80_000] + "\n[diff truncated; read the changed files directly]"
    v.state_update(codex_rounds=state.get("codex_rounds", 0) + 1,
                   reviewed=(state.get("reviewed", []) + [digest])[-50:])
    out_dir = v.dir / "reviews"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / time.strftime("%Y%m%d-%H%M%S.md")
    prompt = REVIEW_PROMPT.format(prompt=turn.get("prompt", "(unknown)"), diff=diff)
    rc, _, err = run(["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "--ephemeral",
                      "-C", str(v.root), "-o", str(out_file), "-"], input_text=prompt, timeout=840)
    try:
        verdict = out_file.read_text().strip()
    except OSError:
        verdict = ""
    if rc or not verdict or re.match(r"^\W*LGTM\b", verdict):
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


def cli(argv):
    v = Vibe({"cwd": os.getcwd()})
    cmd = argv[0] if argv else "status"
    if cmd == "undo":
        sub = argv[1] if len(argv) > 1 else "list"
        if sub == "list":
            current = v.snapshot("now", "current state")
            snaps = [(i, s) for i, s in enumerate(v.snapshots(40)) if s["kind"] != "now"][:15]
            if not current or not snaps:
                print("No snapshots yet.")
                return 0
            kinds = {"turn": "before request", "guard": "before risky command", "good": "checks passed",
                     "undo": "before an undo", "review": "after change"}
            for i, s in snaps:
                _, stat, _ = v.git("diff", "--shortstat", s["sha"], current)
                print(f"{i:>2}. {ago(s['t']):>12}  {kinds.get(s['kind'], s['kind']):<21} {s['label'][:70]!r}  "
                      f"[differs from now: {stat.strip() or 'no'}]")
            return 0
        if sub in ("show", "restore") and len(argv) > 2 and argv[2].isdigit():
            snaps = v.snapshots(int(argv[2]) + 1)
            if int(argv[2]) >= len(snaps):
                print("No such snapshot.", file=sys.stderr)
                return 1
            target = snaps[int(argv[2])]["sha"]
            if sub == "show":
                current = v.snapshot("now", "current state")
                print(v.git("diff", "--stat", target, current)[1] or "No differences.")
                return 0
            ok, info = v.restore(target)
            print("Restored. The state just before this undo was saved as a new snapshot (run list to see it)."
                  if ok else f"Failed: {info}")
            return 0 if ok else 1
    if cmd == "checks":
        green = v.load("green.json", [])
        if len(argv) > 2 and argv[1] == "forget":
            v.save("green.json", [g for g in green if g["cmd"] != argv[2]])
            print("Forgotten.")
        else:
            print("\n".join(g["cmd"] for g in green) or "No remembered checks.")
        return 0
    if cmd == "status":
        print(json.dumps({"version": VERSION, "project": str(v.root), "enabled": v.enabled, "config": v.config,
                          "codex": codex_ready(v), "snapshots": len(v.snapshots(1000)),
                          "checks": [g["cmd"] for g in v.load("green.json", [])]}, indent=1, ensure_ascii=False))
        return 0
    print("usage: vibe.py undo [list|show N|restore N] | checks [forget CMD] | status", file=sys.stderr)
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
            if v.enabled:
                v.ensure()
                with (v.dir / "errors.log").open("a") as f:
                    f.write(f"{time.ctime()} {event}: {type(e).__name__}: {e}\n")
        except OSError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
