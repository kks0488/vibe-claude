#!/usr/bin/env python3
"""Build the animated README demos (assets/demo-*.svg). Run: python3 assets/make_demos.py

Each demo is a looping terminal transcript drawn with plain SVG + CSS keyframes, so it plays
inside an <img> tag on GitHub without scripts.
"""

from html import escape
from pathlib import Path

W, PAD, LINE, TOP = 920, 28, 30, 74
COLORS = {"fg": "#e6edf3", "dim": "#8b949e", "you": "#f0f6fc", "tool": "#79c0ff", "ok": "#3fb950",
          "stop": "#ff7b72", "warn": "#d29922", "vibe": "#d97757", "codex": "#bc8cff"}
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


def build(name, title, desc, lines, loop=18.0):
    """lines: (appear_at_seconds, kind, text, typed). kind picks the color and the bullet."""
    height = TOP + LINE * len(lines) + PAD + 8
    css, body = [], []
    for i, (at, kind, text, typed) in enumerate(lines):
        start = at / loop * 100
        css.append(f"@keyframes a{i}{{0%,{start:.2f}%{{opacity:0}}{start + 0.8:.2f}%,93%{{opacity:1}}97%,100%{{opacity:0}}}}"
                   f".l{i}{{opacity:0;animation:a{i} {loop}s linear infinite}}")
        y = TOP + LINE * i
        x = PAD + 26
        bullet = ""
        if kind == "you":
            bullet = f'<text x="{PAD}" y="{y}" fill="{COLORS["vibe"]}" font-weight="700">›</text>'
        elif kind in ("tool", "say"):
            dot = COLORS["tool"] if kind == "tool" else COLORS["fg"]
            bullet = f'<circle cx="{PAD + 6}" cy="{y - 6}" r="4.5" fill="{dot}"/>'
        else:
            x = PAD + 42
        color = {"you": COLORS["you"], "tool": COLORS["fg"], "say": COLORS["fg"], "out": COLORS["dim"],
                 "ok": COLORS["ok"], "stop": COLORS["stop"], "warn": COLORS["warn"], "codex": COLORS["codex"],
                 "receipt": COLORS["ok"]}[kind]
        weight = ' font-weight="700"' if kind in ("you", "receipt", "stop") else ""
        content = text
        if kind == "receipt":  # highlighted receipt bar
            body.append(f'<g class="l{i}"><rect x="{PAD + 32}" y="{y - 21}" width="{W - 2 * PAD - 40}" height="29" '
                        f'rx="6" fill="#3fb950" fill-opacity="0.13" stroke="#3fb950" stroke-opacity="0.55"/>'
                        f'<text x="{x}" y="{y}" fill="{color}"{weight}>{escape(content)}</text></g>')
            continue
        line = f'<g class="l{i}">{bullet}<text x="{x}" y="{y}" fill="{color}"{weight}>{rich(content)}</text>'
        if typed:  # typewriter: a cover slides right to reveal the text
            dur = max(0.6, len(text) * 0.035)
            s, e = at / loop * 100 + 0.8, (at + dur) / loop * 100
            css.append(f"@keyframes t{i}{{0%,{s:.2f}%{{transform:translateX(0)}}{e:.2f}%,100%{{transform:translateX({W}px)}}}}"
                       f".c{i}{{animation:t{i} {loop}s linear infinite}}")
            line += f'<rect class="c{i}" x="{x - 2}" y="{y - 22}" width="{W}" height="30" fill="#0d1117"/>'
        body.append(line + "</g>")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" role="img" aria-labelledby="t d">
<title id="t">{escape(title)}</title>
<desc id="d">{escape(desc)}</desc>
<style>
text{{font-family:{FONT};font-size:17px;white-space:pre}}
{"".join(css)}
@media (prefers-reduced-motion: reduce){{[class^=l]{{animation:none!important;opacity:1!important}}[class^=c]{{display:none}}}}
</style>
<rect width="{W}" height="{height}" rx="14" fill="#0d1117"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="14" fill="none" stroke="#30363d"/>
<circle cx="26" cy="24" r="6" fill="#ff5f57"/><circle cx="46" cy="24" r="6" fill="#febc2e"/><circle cx="66" cy="24" r="6" fill="#28c840"/>
<text x="{W / 2}" y="29" fill="{COLORS["dim"]}" text-anchor="middle" style="font-size:14px">claude · vibe-claude</text>
{chr(10).join(body)}
</svg>
'''
    Path(__file__).with_name(name).write_text(svg)


def rich(text):
    """`code` spans in a soft color."""
    parts = text.split("`")
    out = []
    for i, part in enumerate(parts):
        out.append(f'<tspan fill="{COLORS["tool"]}">{escape(part)}</tspan>' if i % 2 else escape(part))
    return "".join(out)


build("demo-proof.svg", "vibe-claude proof demo",
      "Claude says done without running anything, vibe-claude stops it, Claude runs the tests, and a receipt "
      "built from the real exit codes appears.", [
          (0.2, "you", "make the checkout button green", True),
          (1.6, "tool", "Edit  app/checkout.tsx", False),
          (2.6, "say", "Done! The button is green now.", True),
          (4.2, "stop", "vibe: you changed code but nothing ran to check it. Run the tests.", False),
          (6.0, "tool", "Bash  `npm test`", False),
          (7.0, "ok", "✓ 24 passed  (exit 0, recorded by the hook)", False),
          (8.4, "say", "Done. Open http://localhost:3000/checkout to see it.", True),
          (10.4, "receipt", "vibe ✓ 1 file changed · checked: npm test · Codex review running", False),
          (12.6, "codex", "Codex (a different model) reviewed the change: LGTM", False),
      ])

build("demo-guard.svg", "vibe-claude guard and undo demo",
      "Before files are deleted they are backed up, an irreversible database reset makes Claude stop and check, "
      "and undo brings the files back. The user is never asked a technical question.", [
          (0.2, "you", "clean up the old screenshots", True),
          (1.6, "tool", "Bash  `rm -rf qa/shots`", False),
          (2.5, "warn", "vibe: 212 files are not in git, copied to the trash first (7 days)", False),
          (4.2, "tool", "Bash  `supabase db reset`", False),
          (5.1, "stop", "vibe: this wipes the database and cannot be undone. Did the user ask?", False),
          (7.0, "say", "You only asked about screenshots, so I left the database alone.", True),
          (9.6, "you", "wait, I needed those screenshots. undo", True),
          (11.2, "tool", "/vibe-claude:undo  →  trash restore 20261009-1631", False),
          (12.4, "ok", "✓ 212 files are back. Nothing else changed.", False),
      ])

build("demo-proof-ko.svg", "vibe-claude 증명 데모",
      "Claude가 아무것도 실행하지 않고 다 했다고 하자 vibe-claude가 막고, Claude가 테스트를 돌린 뒤 실제 결과로 만든 "
      "영수증이 나타나요.", [
          (0.2, "you", "결제 버튼을 초록색으로 바꿔줘", True),
          (1.6, "tool", "Edit  app/checkout.tsx", False),
          (2.6, "say", "다 했어요! 버튼이 초록색이 됐어요.", True),
          (4.2, "stop", "vibe: 코드를 바꿨는데 확인한 기록이 없어요. 테스트를 돌리세요.", False),
          (6.0, "tool", "Bash  `npm test`", False),
          (7.0, "ok", "✓ 24개 통과  (hook이 기록한 실제 결과)", False),
          (8.4, "say", "완료. http://localhost:3000/checkout 을 열어 확인하세요.", True),
          (10.4, "receipt", "vibe ✓ 파일 1개 변경 · 확인됨: npm test · Codex 검토 중", False),
          (12.6, "codex", "Codex(다른 AI)가 변경을 검토했어요: 문제 없음", False),
      ])

build("demo-guard-ko.svg", "vibe-claude 안전장치와 되돌리기 데모",
      "지우기 전에 파일을 보관하고, 되돌릴 수 없는 데이터베이스 초기화 앞에서 Claude가 멈춰 판단하고, 되돌리기로 파일이 "
      "돌아와요. 사용자에게는 기술적인 질문을 하지 않아요.", [
          (0.2, "you", "예전 스크린샷 정리해줘", True),
          (1.6, "tool", "Bash  `rm -rf qa/shots`", False),
          (2.5, "warn", "vibe: git에 없는 파일 212개를 지우기 전에 휴지통에 보관했어요 (7일)", False),
          (4.2, "tool", "Bash  `supabase db reset`", False),
          (5.1, "stop", "vibe: 데이터베이스를 지우고 되돌릴 수 없어요. 사용자가 요청했나요?", False),
          (7.0, "say", "스크린샷만 요청하셨으니 데이터베이스는 그대로 뒀어요.", True),
          (9.6, "you", "아 잠깐, 그 스크린샷 필요했어. 되돌려줘", True),
          (11.2, "tool", "/vibe-claude:undo  →  휴지통에서 복구", False),
          (12.4, "ok", "✓ 파일 212개가 돌아왔어요. 다른 건 그대로예요.", False),
      ])
