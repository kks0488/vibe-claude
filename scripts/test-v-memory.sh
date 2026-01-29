#!/usr/bin/env bash
# Integration test for scripts/v-memory.sh using a local memU stub server.

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: Missing required dependency: $cmd" >&2
    exit 1
  fi
}

require_cmd python3
require_cmd curl

TMP_DIR="$(mktemp -d)"
OUT_DIR="$TMP_DIR/out"
HOME_DIR="$TMP_DIR/home"
SERVER_PY="$TMP_DIR/memu_stub.py"
mkdir -p "$OUT_DIR" "$HOME_DIR"

cleanup() {
  if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

PORT="$(python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)"

cat > "$SERVER_PY" <<'PY'
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

port = int(sys.argv[1])
out_dir = Path(sys.argv[2]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True), encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "memu-stub/0.1"

    def _send(self, code: int, payload: object) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _read_json(self) -> object:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/health"):
            self._send(200, {"status": "ok"})
            return
        if self.path.startswith("/items"):
            self._send(200, {"success": True, "items": []})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/memorize":
            data = self._read_json()
            write_json(out_dir / "memorize.json", data)
            self._send(200, {"success": True, "id": "test-1"})
            return
        if self.path == "/retrieve":
            data = self._read_json()
            write_json(out_dir / "retrieve.json", data)
            self._send(200, {"success": True, "results": [{"id": "test-1", "content": "ok"}]})
            return
        if self.path == "/check-similar":
            data = self._read_json()
            write_json(out_dir / "check-similar.json", data)
            self._send(200, {"success": True, "similar": False})
            return
        self._send(404, {"error": "not found"})

    def do_DELETE(self) -> None:  # noqa: N802
        if self.path.startswith("/items/"):
            self._send(200, {"success": True})
            return
        self._send(404, {"error": "not found"})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


HTTPServer(("127.0.0.1", port), Handler).serve_forever()
PY

python3 -u "$SERVER_PY" "$PORT" "$OUT_DIR" &
SERVER_PID=$!

MEMU_API="http://127.0.0.1:$PORT"

echo "Waiting for memU stub on $MEMU_API..."
for _ in $(seq 1 30); do
  if curl -s "$MEMU_API/health" | grep -q "ok"; then
    break
  fi
  sleep 0.1
done

export HOME="$HOME_DIR"
export MEMU_API
export MEMU_USER_ID="vibe-test"

title='Title with "quotes" ✓'
content=$'Line1\nLine2 "quotes" and backslash \\\\ and unicode こんにちは'

echo "Testing save (local + memU sync)..."
bash "$ROOT_DIR/scripts/v-memory.sh" save lesson "$title" "$content" >/dev/null

OUT_DIR="$OUT_DIR" TITLE="$title" CONTENT="$content" python3 - <<'PY'
import os
import json
from pathlib import Path

out_dir = Path(os.environ["OUT_DIR"])
title = os.environ["TITLE"]
content = os.environ["CONTENT"]
payload = json.loads((out_dir / "memorize.json").read_text(encoding="utf-8"))

assert payload["user_id"] == "vibe-test"
assert payload["metadata"]["title"] == title
assert payload["metadata"]["type"] == "lesson"
assert payload["content"] == content
PY

echo "Testing search (memU)..."
query='hello "world"'
bash "$ROOT_DIR/scripts/v-memory.sh" search "$query" 3 >/dev/null

OUT_DIR="$OUT_DIR" QUERY="$query" python3 - <<'PY'
import os
import json
from pathlib import Path

payload = json.loads((Path(os.environ["OUT_DIR"]) / "retrieve.json").read_text(encoding="utf-8"))
assert payload["query"] == os.environ["QUERY"]
assert payload["user_id"] == "vibe-test"
assert payload["limit"] == 3
PY

echo "Testing memU unavailable fallback (save/search/list)..."
export MEMU_API="http://127.0.0.1:1"

bash "$ROOT_DIR/scripts/v-memory.sh" save lesson "local-only" "needle" >/dev/null

output="$(bash "$ROOT_DIR/scripts/v-memory.sh" search needle 2)"
echo "$output" | grep -q "Found:"  # local grep fallback should find it

output="$(bash "$ROOT_DIR/scripts/v-memory.sh" list lessons)"
echo "$output" | grep -qi "Local Memories"

echo "OK: v-memory integration + escaping verified"
