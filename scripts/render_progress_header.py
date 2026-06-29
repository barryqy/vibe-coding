#!/usr/bin/env python3
"""Regenerate lab progress headers between PROGRESS markers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB_SOURCE = ROOT.parent / "llabsource-vibe-coding"
CONFIG = LAB_SOURCE / "config.json"
LABS = LAB_SOURCE / "labs"
START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"


def module_index_from_name(name: str) -> int:
    match = re.match(r"(\d+)-", name)
    return int(match.group(1)) if match else 0


def short_label(title: str, index: int) -> str:
    defaults = {
        0: "Intro",
        1: "Codex",
        2: "MCP",
        3: "Memory",
        4: "Maze",
        5: "OpenCode",
        6: "Darkside",
        7: "DefenseClaw",
        8: "Risky MCP",
        9: "Wrap-up",
    }
    if index in defaults:
        return defaults[index]
    return title.split()[0][:12] if title.strip() else f"M{index}"


def build_header(current: int, total: int = 9) -> str:
  part1 = list(range(1, 6))
  part2 = list(range(6, 10))
  pct = int(round((current / total) * 100)) if current else 0
  filled = max(0, min(10, pct // 10))
  meter = "[" + "#" * filled + "-" * (10 - filled) + f"] {pct}%"

  def pill(num: int, label: str, active: bool) -> str:
      bg = "#0d6efd" if active else "#e9ecef"
      fg = "#ffffff" if active else "#495057"
      border = "#0a58ca" if active else "#ced4da"
      weight = "700" if active else "400"
      return (
          f'<span style="display:inline-block;margin:2px 4px;padding:4px 10px;'
          f"border-radius:999px;border:1px solid {border};background:{bg};"
          f'color:{fg};font-size:12px;font-weight:{weight};">{num} {label}</span>'
      )

  part1_html = "".join(
      pill(i, short_label("", i), i == current) for i in part1
  )
  part2_html = "".join(
      pill(i, short_label("", i), i == current) for i in part2
  )

  part_name = (
      "Part 1 — Vibe Coding" if current in part1 or current == 0
      else "Part 2 — Securing AI Agents"
  )
  module_line = f"Module {current} of {total}" if current else "Lab overview"

  html = f"""<div style="margin:0 0 1.25rem 0;padding:12px 14px;border:1px solid #dee2e6;border-radius:10px;background:#f8f9fa;font-family:system-ui,sans-serif;">
<div style="font-size:13px;font-weight:600;color:#212529;margin-bottom:6px;">{part_name} · {module_line}</div>
<div style="font-size:11px;color:#6c757d;margin-bottom:8px;">Part 1 — Vibe Coding (Modules 1–5)</div>
<div style="line-height:1.8;margin-bottom:10px;">{part1_html}</div>
<div style="font-size:11px;color:#6c757d;margin-bottom:8px;">Part 2 — Securing AI Agents (Modules 6–9)</div>
<div style="line-height:1.8;margin-bottom:8px;">{part2_html}</div>
<div style="font-size:12px;color:#495057;">{meter}</div>
</div>"""

  fallback = (
      f"**{part_name}** | {module_line}\n\n"
      f"`{meter}`"
  )

  return (
      f"{START}\n{html}\n\n"
      f"<!-- PROGRESS:FALLBACK -->\n{fallback}\n"
      f"{END}"
  )


def update_file(path: Path, header: str) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(header, text, count=1)
    else:
        new_text = header + "\n\n" + text.lstrip("\n")
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labs-dir", type=Path, default=LABS)
    args = parser.parse_args()

    items = json.loads(CONFIG.read_text(encoding="utf-8"))["items"]
    changed = 0
    for item in items:
        rel = item["content"].replace("labs/", "")
        path = args.labs_dir / rel
        if not path.exists():
            print(f"skip missing {path}")
            continue
        idx = module_index_from_name(rel)
        if update_file(path, build_header(idx)):
            changed += 1
            print(f"updated {path.name}")
    print(f"PROGRESS_HEADERS={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
