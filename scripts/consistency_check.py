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
    Path(".second-brain/patterns/tictactoe-scenario.md"),
    Path(".second-brain/sessions/current-session.md"),
    Path("dojo_app/barrybot.py"),
    Path("tests/test_barrybot.py"),
    Path("dojo_app/tictactoe_game.py"),
    Path("dojo_app/tictactoe_play.py"),
    Path("tests/test_tictactoe_game.py"),
    Path("dojo_app/barryflights_mcp_server.py"),
    Path("dojo_app/barryflights_mcp_client.py"),
    Path("tests/test_barryflights_mcp.py"),
    Path("requirements.txt"),
    Path("scripts/agent_compare.py"),
    Path("scripts/agent_code_task.py"),
    Path("scripts/barrybot_demo.py"),
    Path("scripts/install_ai_tools.sh"),
    Path("scripts/check_repo.py"),
    Path("scripts/devnet_codex_shim.py"),
    Path("tests/test_devnet_codex_shim.py"),
    Path("scripts/start_codex_model_adapter.py"),
    Path("scripts/setup_codex_devnet.py"),
    Path("scripts/devnet_openai_shim.py"),
    Path("scripts/start_opencode_model_adapter.py"),
    Path("scripts/setup_opencode_devnet.py"),
    Path("scripts/first_agent_result.py"),
    Path("scripts/verify_ai_tools.py"),
    Path("scripts/install_defenseclaw_cli.sh"),
    Path("scripts/defenseclaw_skill_demo.py"),
    Path("scripts/defenseclaw_mcp_demo.py"),
    Path("scripts/defenseclaw_scenario_review.py"),
    Path("samples/guardrails/rollout-note.md"),
    Path("samples/guardrails/privacy-request.txt"),
    Path("samples/unsafe_report_patch.py"),
    Path("samples/skills/workspace-migration-assistant/SKILL.md"),
    Path("samples/skills/workspace-migration-assistant/collect_snapshot.py"),
    Path("samples/skills/release-brief-helper/SKILL.md"),
    Path("samples/mcp/workspace-admin-bridge.py"),
    Path("samples/mcp/safe-migration-reference-server.py"),
    Path("samples/leaky_tictactoe_patch.py"),
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
    session_note = (
        root / ".second-brain/sessions/current-session.md"
    ).read_text(encoding="utf-8") if (root / ".second-brain/sessions/current-session.md").exists() else ""
    schema_note = (
        root / ".second-brain/schema.md"
    ).read_text(encoding="utf-8") if (root / ".second-brain/schema.md").exists() else ""
    resolver_note = (
        root / ".second-brain/RESOLVER.md"
    ).read_text(encoding="utf-8") if (root / ".second-brain/RESOLVER.md").exists() else ""
    tictactoe_pattern = (
        root / ".second-brain/patterns/tictactoe-scenario.md"
    ).read_text(encoding="utf-8") if (root / ".second-brain/patterns/tictactoe-scenario.md").exists() else ""
    tictactoe_game = (root / "dojo_app/tictactoe_game.py").read_text(encoding="utf-8") if (root / "dojo_app/tictactoe_game.py").exists() else ""
    tictactoe_play = (root / "dojo_app/tictactoe_play.py").read_text(encoding="utf-8") if (root / "dojo_app/tictactoe_play.py").exists() else ""

    require("scripts/check_repo.py" in agents, "AGENTS.md must require the repo check command", errors)
    require("scripts/security_review.py" in agents, "AGENTS.md must mention the security review", errors)
    require("scripts/defenseclaw_skill_demo.py" in agents, "AGENTS.md must mention the DefenseClaw mini-demo", errors)
    require("scripts/defenseclaw_mcp_demo.py" in agents, "AGENTS.md must mention the DefenseClaw MCP demo", errors)
    require("dojo_app/tictactoe_game.py" in agents, "AGENTS.md must mention the tic-tac-toe game", errors)
    require("python3 -m dojo_app.tictactoe_game" in agents, "AGENTS.md must mention the tic-tac-toe command", errors)
    require("--check-only" in agents, "AGENTS.md must mention the tic-tac-toe scenario check command", errors)
    require("barryflights_mcp_server.py" in agents, "AGENTS.md must mention the local BarryFlights MCP server", errors)
    require("DefenseClaw" in quality, "quality bar must mention the DefenseClaw admission check", errors)
    require("Model routes" in quality or "model routes" in quality, "quality bar must mention model routes", errors)
    require("Codex" in agents and "scripts/setup_codex_devnet.py" in agents, "AGENTS.md must mention the Codex DevNet setup", errors)
    require("OpenCode" in agents or "opencode.json" in agents, "AGENTS.md must mention OpenCode or opencode.json", errors)
    require("current-session.md" in agents, "AGENTS.md must mention the current second-brain session note", errors)
    require("schema.md" in agents, "AGENTS.md must tell agents to read the second-brain schema", errors)
    require("OpenCode Next Task" not in session_note, "current-session.md must stay general, not carry an OpenCode-specific task", errors)
    require("OpenCode Next Task" not in agents, "AGENTS.md must use a direct prompt, not a hidden OpenCode task note", errors)
    require("shared context for any agent" in session_note, "current-session.md must describe the second brain as shared agent context", errors)
    session_lower = session_note.lower()
    require("current state" in session_lower and "recent work" in session_lower, "current-session.md must keep general session structure", errors)
    require("open questions" in session_lower and "verification" in session_lower, "current-session.md must include open questions and verification", errors)
    require("Project Note" in schema_note, "schema.md must define project notes", errors)
    require("Session Note" in schema_note, "schema.md must define session notes", errors)
    require("Decision Note" in schema_note, "schema.md must define decision notes", errors)
    require("Pattern Note" in schema_note, "schema.md must define pattern notes", errors)
    require("shared memory for any coding agent" in resolver_note, "RESOLVER.md must describe an agent-neutral shared KB", errors)
    require("patterns/tictactoe-scenario.md" in resolver_note, "RESOLVER.md must point tic-tac-toe tasks to the scenario pattern", errors)
    require("TICTACTOE_CHECK=pass" in tictactoe_pattern, "tictactoe-scenario.md must describe the scenario check marker", errors)
    require("--write-clean" in tictactoe_game, "tictactoe_game.py must normalize model prose into the tiny scenario format", errors)
    require("PLAY_MODE_ENABLED" not in tictactoe_game + tictactoe_play, "tic-tac-toe must not hide play mode behind a switch", errors)
    require("--play" in tictactoe_game, "tictactoe_game.py must expose a play flag for the OpenCode exercise", errors)
    require("from dojo_app.tictactoe_play import run_tictactoe" in tictactoe_game, "tictactoe_game.py must dispatch play mode through dojo_app/tictactoe_play.py", errors)
    require("def run_tictactoe(" in tictactoe_play, "tictactoe_play.py must expose the OpenCode play entrypoint", errors)
    require("human-vs-computer" in tictactoe_game and "human-vs-human" in tictactoe_game, "tic-tac-toe game must know both play modes", errors)
    require("python3 -m unittest tests.test_tictactoe_game" in session_note, "current-session.md must include the focused tic-tac-toe test", errors)
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
        ".second-brain/sessions/current-session.md" in instructions,
        "opencode.json must load the current second-brain session note",
        errors,
    )
    require(
        ".second-brain/patterns/tictactoe-scenario.md" in instructions,
        "opencode.json must load the tic-tac-toe scenario pattern",
        errors,
    )

    bash_perms = ((opencode.get("permission") or {}).get("bash") or {})
    edit_perm = (opencode.get("permission") or {}).get("edit")
    codex_setup = (root / "scripts/setup_codex_devnet.py").read_text(encoding="utf-8")
    opencode_setup = (root / "scripts/setup_opencode_devnet.py").read_text(encoding="utf-8")
    agent_task = (root / "scripts/agent_code_task.py").read_text(encoding="utf-8")
    require(
        "python3 scripts/defenseclaw_skill_demo.py*" in bash_perms,
        "opencode.json must allow the DefenseClaw skill demo",
        errors,
    )
    require(
        "python3 scripts/defenseclaw_mcp_demo.py*" in bash_perms,
        "opencode.json must allow the DefenseClaw MCP demo",
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
        "python3 -m py_compile dojo_app/tictactoe_game.py dojo_app/tictactoe_play.py*" in bash_perms,
        "opencode.json must allow the focused tic-tac-toe syntax check",
        errors,
    )
    require(
        "python3 -m dojo_app.tictactoe_game*" in bash_perms,
        "opencode.json must allow the tic-tac-toe game command",
        errors,
    )
    require(
        "printf * | python3 -m dojo_app.tictactoe_game*" in bash_perms,
        "opencode.json must allow the piped tic-tac-toe smoke test",
        errors,
    )
    require("python3 -m dojo_app.barryflights_mcp_client*" in bash_perms, "opencode.json must allow the local BarryFlights MCP client", errors)
    require(
        "[mcp_servers.barryflights]" in codex_setup,
        "setup_codex_devnet.py must include the local BarryFlights MCP server in the repo-local Codex config",
        errors,
    )
    codex_shim = (root / "scripts/devnet_codex_shim.py").read_text(encoding="utf-8")
    require(
        "wants_barryflights_booking" in codex_shim and "BARRYFLIGHTS_BOOKING=pass" in codex_shim,
        "devnet_codex_shim.py must route the risky BarryFlights booking prompt",
        errors,
    )
    require("local_skill=" not in codex_setup, "setup_codex_devnet.py must not stage a local game skill for the tic-tac-toe path", errors)
    manual_mcp_command = "codex mcp " + "add barryflights"
    require(
        manual_mcp_command not in agents,
        "AGENTS.md should not expose manual MCP registration in the required path",
        errors,
    )
    require(
        "python3 scripts/start_opencode_model_adapter.py*" in bash_perms,
        "opencode.json must allow the OpenCode model adapter command",
        errors,
    )
    require(
        edit_perm == "allow",
        "opencode.json must allow edits so noninteractive OpenCode lab prompts do not hang",
        errors,
    )
    require(
        '"edit": "allow"' in opencode_setup and '"webfetch": "deny"' in opencode_setup,
        "setup_opencode_devnet.py must attach OpenCode to the lab KB while keeping network permissions denied",
        errors,
    )
    require(
        "task_file=dojo_app/tictactoe_play.py" in opencode_setup,
        "setup_opencode_devnet.py must report the tic-tac-toe play task file",
        errors,
    )
    require(
        ".second-brain/sessions/current-session.md" in opencode_setup,
        "setup_opencode_devnet.py must attach the current second-brain session note",
        errors,
    )
    require(
        ".second-brain/patterns/tictactoe-scenario.md" in opencode_setup,
        "setup_opencode_devnet.py must attach the tic-tac-toe scenario pattern",
        errors,
    )
    require(
        "dojo_app/tasks.py" not in opencode_setup and "tests/test_tasks.py" not in opencode_setup,
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
