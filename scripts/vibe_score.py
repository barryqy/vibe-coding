#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def has_text(path: str, needle: str) -> bool:
    file_path = Path(path)
    return file_path.exists() and needle.lower() in file_path.read_text(encoding="utf-8").lower()


def main() -> int:
    checks = {
        "context": has_text("AGENTS.md", "Project Map"),
        "constraints": has_text("docs/quality-bar.md", "Constraints:"),
        "verification": has_text("docs/quality-bar.md", "Verification:"),
        "security": has_text("AGENTS.md", ".env"),
        "memory": Path(".second-brain").exists(),
    }

    score = sum(20 for passed in checks.values() if passed)
    print(f"VIBE_SCORE={score}")
    for name, passed in checks.items():
        print(f"{name}={'pass' if passed else 'missing'}")
    return 0 if score >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())

