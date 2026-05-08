#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("opencode.json"),
    Path(".claude/settings.json"),
    Path("docs/quality-bar.md"),
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    root = Path.cwd()
    errors = []

    for path in REQUIRED_FILES:
        require((root / path).exists(), f"missing {path}", errors)

    agents = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").exists() else ""
    quality = (root / "docs/quality-bar.md").read_text(encoding="utf-8") if (root / "docs/quality-bar.md").exists() else ""

    require("scripts/quality_gate.py" in agents, "AGENTS.md must require the quality gate", errors)
    require("scripts/security_review.py" in agents, "AGENTS.md must mention the security review", errors)
    agents_lower = agents.lower()
    require(
        "second brain" in agents_lower or ".second-brain" in agents_lower,
        "AGENTS.md must mention second brain notes",
        errors,
    )
    require("Context:" in quality and "Verification:" in quality, "quality bar must keep the prompt shape", errors)

    for config_path in [root / "opencode.json", root / ".claude/settings.json"]:
        if not config_path.exists():
            continue
        try:
            json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{config_path} is not valid JSON: {exc}")

    opencode = {}
    if (root / "opencode.json").exists():
        opencode = json.loads((root / "opencode.json").read_text(encoding="utf-8"))
    instructions = opencode.get("instructions", [])
    require("AGENTS.md" in instructions, "opencode.json must load AGENTS.md", errors)
    require("docs/quality-bar.md" in instructions, "opencode.json must load docs/quality-bar.md", errors)

    if errors:
        print("CONSISTENCY_CHECK=fail")
        for error in errors:
            print(f"- {error}")
        return 1

    print("CONSISTENCY_CHECK=pass")
    print("Checked agent rules, docs, and tool config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
