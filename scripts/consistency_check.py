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
    Path("scripts/agent_compare.py"),
    Path("scripts/agent_code_task.py"),
    Path("scripts/install_ai_tools.sh"),
    Path("scripts/devnet_codex_shim.py"),
    Path("scripts/setup_codex_devnet.py"),
    Path("scripts/devnet_openai_shim.py"),
    Path("scripts/setup_opencode_devnet.py"),
    Path("scripts/first_agent_result.py"),
    Path("scripts/verify_ai_tools.py"),
    Path("scripts/install_defenseclaw_cli.sh"),
    Path("scripts/defenseclaw_skill_demo.py"),
    Path("samples/skills/workspace-migration-assistant/SKILL.md"),
    Path("samples/skills/release-brief-helper/SKILL.md"),
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

    require("scripts/quality_gate.py" in agents, "AGENTS.md must require the repo check command", errors)
    require("scripts/security_review.py" in agents, "AGENTS.md must mention the security review", errors)
    require("scripts/defenseclaw_skill_demo.py" in agents, "AGENTS.md must mention the DefenseClaw mini-demo", errors)
    require("DefenseClaw" in quality, "quality bar must mention the DefenseClaw admission check", errors)
    require("Codex" in agents and "scripts/setup_codex_devnet.py" in agents, "AGENTS.md must mention the Codex DevNet setup", errors)
    require("OpenCode" in agents or "opencode.json" in agents, "AGENTS.md must mention OpenCode or opencode.json", errors)
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

    bash_perms = ((opencode.get("permission") or {}).get("bash") or {})
    require(
        "python3 scripts/defenseclaw_skill_demo.py*" in bash_perms,
        "opencode.json must allow the DefenseClaw skill demo",
        errors,
    )
    require(
        "python3 scripts/setup_codex_devnet.py*" in bash_perms,
        "opencode.json must allow the Codex DevNet setup helper",
        errors,
    )
    require(
        "python3 scripts/devnet_codex_shim.py*" in bash_perms,
        "opencode.json must allow the Codex DevNet shim helper",
        errors,
    )

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
