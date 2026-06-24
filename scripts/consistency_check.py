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
    Path(".second-brain/RESOLVER.md"),
    Path(".second-brain/schema.md"),
    Path(".second-brain/projects/vibe-coding-dojo.md"),
    Path(".second-brain/sessions/current-agent-handoff.md"),
    Path("dojo_app/barrybot.py"),
    Path("tests/test_barrybot.py"),
    Path("dojo_app/maze_game.py"),
    Path("tests/test_maze_game.py"),
    Path("scripts/agent_compare.py"),
    Path("scripts/agent_code_task.py"),
    Path("scripts/barrybot_demo.py"),
    Path("scripts/install_ai_tools.sh"),
    Path("scripts/check_repo.py"),
    Path("scripts/devnet_codex_shim.py"),
    Path("scripts/start_codex_model_adapter.py"),
    Path("scripts/setup_codex_devnet.py"),
    Path("scripts/devnet_openai_shim.py"),
    Path("scripts/start_opencode_model_adapter.py"),
    Path("scripts/setup_opencode_devnet.py"),
    Path("scripts/first_agent_result.py"),
    Path("scripts/verify_ai_tools.py"),
    Path("scripts/install_defenseclaw_cli.sh"),
    Path("scripts/defenseclaw_skill_demo.py"),
    Path("samples/skills/maze-score-booster/SKILL.md"),
    Path("samples/skills/maze-score-booster/score_booster.py"),
    Path("samples/skills/maze-game-coach/SKILL.md"),
    Path("samples/leaky_maze_patch.py"),
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
    install_script = (root / "scripts/install_ai_tools.sh").read_text(encoding="utf-8")

    require("scripts/check_repo.py" in agents, "AGENTS.md must require the repo check command", errors)
    require("scripts/security_review.py" in agents, "AGENTS.md must mention the security review", errors)
    require("scripts/defenseclaw_skill_demo.py" in agents, "AGENTS.md must mention the DefenseClaw mini-demo", errors)
    require("dojo_app/maze_game.py" in agents, "AGENTS.md must mention the Maze game", errors)
    require("python3 -m dojo_app.maze_game" in agents, "AGENTS.md must mention the Maze game command", errors)
    require("DefenseClaw" in quality, "quality bar must mention the DefenseClaw admission check", errors)
    require("Model routes" in quality or "model routes" in quality, "quality bar must mention model routes", errors)
    require("Codex" in agents and "scripts/setup_codex_devnet.py" in agents, "AGENTS.md must mention the Codex DevNet setup", errors)
    require("OpenCode" in agents or "opencode.json" in agents, "AGENTS.md must mention OpenCode or opencode.json", errors)
    require("current-agent-handoff.md" in agents, "AGENTS.md must mention the current second-brain handoff", errors)
    require("chatgpt.com/codex/install.sh" in agents, "AGENTS.md must show the direct Codex installer", errors)
    require("codex --version" in agents, "AGENTS.md must verify Codex with codex --version", errors)
    require("github.com/anomalyco/opencode/releases/download/v1.0.190" in agents, "AGENTS.md must show the pinned OpenCode download", errors)
    require("opencode --version" in agents, "AGENTS.md must verify OpenCode with opencode --version", errors)
    require("--codex-only" in install_script and "--opencode-only" in install_script, "install_ai_tools.sh must support split install modes", errors)
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
    require(".second-brain/RESOLVER.md" in instructions, "opencode.json must load the second-brain resolver", errors)
    require(
        ".second-brain/sessions/current-agent-handoff.md" in instructions,
        "opencode.json must load the current second-brain handoff",
        errors,
    )

    bash_perms = ((opencode.get("permission") or {}).get("bash") or {})
    edit_perm = (opencode.get("permission") or {}).get("edit")
    devnet_setup = (root / "scripts/setup_opencode_devnet.py").read_text(encoding="utf-8")
    agent_task = (root / "scripts/agent_code_task.py").read_text(encoding="utf-8")
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
        "opencode.json must allow the Codex model adapter helper",
        errors,
    )
    require(
        "python3 scripts/start_codex_model_adapter.py*" in bash_perms,
        "opencode.json must allow the Codex model adapter command",
        errors,
    )
    require(
        "python3 scripts/check_repo.py*" in bash_perms,
        "opencode.json must allow the repo check command",
        errors,
    )
    require(
        "python3 -m dojo_app.maze_game*" in bash_perms,
        "opencode.json must allow the Maze game command",
        errors,
    )
    require(
        "python3 scripts/start_opencode_model_adapter.py*" in bash_perms,
        "opencode.json must allow the OpenCode model adapter command",
        errors,
    )
    require(
        edit_perm == "ask",
        "opencode.json must require approval for edits",
        errors,
    )
    require(
        '"edit": "allow"' in devnet_setup and '"webfetch": "deny"' in devnet_setup,
        "setup_opencode_devnet.py must attach OpenCode to the lab KB while keeping network permissions denied",
        errors,
    )
    require(
        ".second-brain/sessions/current-agent-handoff.md" in devnet_setup,
        "setup_opencode_devnet.py must attach the current second-brain handoff",
        errors,
    )
    require(
        "dojo_app/tasks.py" not in devnet_setup and "tests/test_tasks.py" not in devnet_setup,
        "setup_opencode_devnet.py still references the old tasks exercise",
        errors,
    )
    require(
        '"codex",\n            "exec",\n            "exec"' not in agent_task,
        "agent_code_task.py must not invoke codex exec twice",
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
