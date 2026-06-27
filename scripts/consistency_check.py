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
    Path(".second-brain/patterns/rps-cli.md"),
    Path(".second-brain/sessions/current-session.md"),
    Path(".agents/skills/rps-cli/SKILL.md"),
    Path(".opencode/skills/rps-cli/SKILL.md"),
    Path("dojo_app/barrybot.py"),
    Path("tests/test_barrybot.py"),
    Path("dojo_app/barryflights_mcp_server.py"),
    Path("dojo_app/barryflights_mcp_client.py"),
    Path("tests/test_barryflights_mcp.py"),
    Path("requirements.txt"),
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
    Path("scripts/verify_ai_tools.py"),
    Path("scripts/install_defenseclaw_cli.sh"),
    Path("scripts/defenseclaw_skill_demo.py"),
    Path("scripts/defenseclaw_mcp_demo.py"),
    Path("scripts/defenseclaw_scenario_review.py"),
    Path("samples/guardrails/rollout-note.md"),
    Path("samples/guardrails/privacy-request.txt"),
    Path("samples/unsafe_agent_patch.py"),
    Path("samples/unsafe_report_patch.py"),
    Path("samples/leaky_rps_patch.py"),
    Path("samples/skills/workspace-migration-assistant/SKILL.md"),
    Path("samples/skills/workspace-migration-assistant/collect_snapshot.py"),
    Path("samples/skills/release-brief-helper/SKILL.md"),
    Path("samples/mcp/workspace-admin-bridge.py"),
    Path("samples/mcp/safe-migration-reference-server.py"),
]

REMOVED_FILES = [
    Path("dojo_app/maze_game.py"),
    Path("dojo_app/maze_play.py"),
    Path("tests/test_maze_game.py"),
    Path("tests/test_mazemaker_skill.py"),
    Path("skills/mazemaker/SKILL.md"),
    Path("skills/mazemaker/scripts/build_maze.py"),
    Path(".second-brain/patterns/mazemaker-skill.md"),
    Path("scripts/agent_code_task.py"),
    Path("scripts/agent_compare.py"),
    Path("scripts/first_agent_result.py"),
    Path("samples/leaky_maze_patch.py"),
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def read(root: Path, path: str) -> str:
    target = root / path
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8")


def main() -> int:
    root = Path.cwd()
    errors = []

    for path in REQUIRED_FILES:
        require((root / path).exists(), f"missing {path}", errors)

    for path in REMOVED_FILES:
        require(not (root / path).exists(), f"old scaffold should be removed: {path}", errors)

    agents = read(root, "AGENTS.md")
    quality = read(root, "docs/quality-bar.md")
    resolver_note = read(root, ".second-brain/RESOLVER.md")
    pattern_note = read(root, ".second-brain/patterns/rps-cli.md")
    project_note = read(root, ".second-brain/projects/vibe-coding-dojo.md")
    session_note = read(root, ".second-brain/sessions/current-session.md")
    codex_skill = read(root, ".agents/skills/rps-cli/SKILL.md")
    opencode_skill = read(root, ".opencode/skills/rps-cli/SKILL.md")
    codex_setup = read(root, "scripts/setup_codex_devnet.py")
    opencode_setup = read(root, "scripts/setup_opencode_devnet.py")
    codex_shim = read(root, "scripts/devnet_codex_shim.py")
    scenario_review = read(root, "scripts/defenseclaw_scenario_review.py")

    require("scripts/check_repo.py" in agents, "AGENTS.md must require the repo check command", errors)
    require("scripts/security_review.py" in agents, "AGENTS.md must mention the security review", errors)
    require("scripts/defenseclaw_skill_demo.py" in agents, "AGENTS.md must mention the DefenseClaw skill demo", errors)
    require("scripts/defenseclaw_mcp_demo.py" in agents, "AGENTS.md must mention the DefenseClaw MCP demo", errors)
    require("barryflights_mcp_server.py" in agents, "AGENTS.md must mention the local BarryFlights MCP server", errors)
    require("GAME_CONTRACT.md" in agents, "AGENTS.md must describe the RPS contract file", errors)
    require("play.py" in agents, "AGENTS.md must describe the generated RPS app file", errors)
    require(".agents/skills/rps-cli/SKILL.md" in agents, "AGENTS.md must mention the Codex skill path", errors)
    require(".opencode/skills/rps-cli/SKILL.md" in agents, "AGENTS.md must mention the OpenCode skill path", errors)
    require(".second-brain/patterns/rps-cli.md" in agents, "AGENTS.md must mention the RPS KB pattern", errors)
    require("chatgpt.com/codex/install.sh" in agents, "AGENTS.md must show the direct Codex installer", errors)
    require("codex --version" in agents, "AGENTS.md must verify Codex with codex --version", errors)
    require("github.com/anomalyco/opencode/releases/download/v1.0.190" in agents, "AGENTS.md must show the pinned OpenCode download", errors)
    require("opencode --version" in agents, "AGENTS.md must verify OpenCode with opencode --version", errors)
    require("MCP" in agents and "Skills" in agents and "KB" in agents, "AGENTS.md must teach MCP, Skills, and KB as separate pieces", errors)

    agents_lower = agents.lower()
    require("second brain" in agents_lower or ".second-brain" in agents_lower, "AGENTS.md must mention second brain notes", errors)
    require("mazemaker" not in agents_lower, "AGENTS.md must not mention MazeMaker", errors)
    require("dojo_app/maze" not in agents_lower, "AGENTS.md must not mention old Maze files", errors)

    require("Context:" in quality and "Verification:" in quality, "quality bar must keep the prompt shape", errors)
    require("DefenseClaw" in quality, "quality bar must mention the DefenseClaw admission check", errors)
    require("Model routes" in quality or "model routes" in quality, "quality bar must mention model routes", errors)

    require("shared memory for any coding agent" in resolver_note, "RESOLVER.md must describe an agent-neutral shared KB", errors)
    require("patterns/rps-cli.md" in resolver_note, "RESOLVER.md must point RPS tasks to the RPS pattern", errors)
    require(".agents/skills/" in resolver_note and ".opencode/skills/" in resolver_note, "RESOLVER.md must name the documented skill roots", errors)

    require("GAME_CONTRACT.md" in pattern_note, "RPS pattern must describe the contract file", errors)
    require("test ! -f play.py" in pattern_note, "RPS pattern must keep Codex contract stage from creating play.py", errors)
    require("python3 play.py --self-test" in pattern_note, "RPS pattern must include the generated app self-test", errors)

    require("The repo does not ship a prebuilt rock-paper-scissors app" in project_note, "project note must call out no prebuilt game", errors)
    require("Codex should create `GAME_CONTRACT.md` only" in session_note, "session note must keep the Codex contract boundary", errors)
    require("OpenCode should create `play.py` and `GAME_README.md`" in session_note, "session note must keep the OpenCode build boundary", errors)
    require("shared context for any agent" in session_note, "session note must describe the second brain as shared agent context", errors)

    for skill_path, skill_text in [
        (".agents/skills/rps-cli/SKILL.md", codex_skill),
        (".opencode/skills/rps-cli/SKILL.md", opencode_skill),
    ]:
        require("name: rps-cli" in skill_text, f"{skill_path} must use the rps-cli name", errors)
        require("GAME_CONTRACT.md" in skill_text, f"{skill_path} must describe the contract", errors)
        require("GAME_README.md" in skill_text, f"{skill_path} must require the generated game notes", errors)
        require("APP: play.py" in skill_text, f"{skill_path} must require the app marker", errors)
        require("DOCS: GAME_README.md" in skill_text, f"{skill_path} must require the docs marker", errors)
        require("RPS_SELF_TEST=pass" in skill_text, f"{skill_path} must require the pass marker", errors)
        require("Do not create `play.py` or `GAME_README.md`" in skill_text, f"{skill_path} must keep contract-only prompts honest", errors)

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
    require(".second-brain/patterns/rps-cli.md" in instructions, "opencode.json must load the RPS KB pattern", errors)
    require(".opencode/skills/rps-cli/SKILL.md" in instructions, "opencode.json must load the OpenCode skill file", errors)

    bash_perms = ((opencode.get("permission") or {}).get("bash") or {})
    edit_perm = (opencode.get("permission") or {}).get("edit")
    require("python3 -m py_compile play.py*" in bash_perms, "opencode.json must allow the generated app compile check", errors)
    require("python3 play.py*" in bash_perms, "opencode.json must allow the generated app self-test", errors)
    require("printf * | python3 play.py*" in bash_perms, "opencode.json must allow the generated app smoke tests", errors)
    require("python3 scripts/defenseclaw_skill_demo.py*" in bash_perms, "opencode.json must allow the DefenseClaw skill demo", errors)
    require("python3 scripts/defenseclaw_mcp_demo.py*" in bash_perms, "opencode.json must allow the DefenseClaw MCP demo", errors)
    require(edit_perm == "allow", "opencode.json must allow edits for noninteractive OpenCode lab prompts", errors)

    require("[mcp_servers.barryflights]" in codex_setup, "setup_codex_devnet.py must include BarryFlights MCP", errors)
    require("repo_skill=.agents/skills/rps-cli" in codex_setup, "setup_codex_devnet.py must report the documented Codex skill", errors)
    require("install_mazemaker_skill" not in codex_setup, "setup_codex_devnet.py must not install an old fake skill path", errors)
    require("sandbox_mode" in codex_setup, "setup_codex_devnet.py must use the current Codex sandbox key", errors)

    require(".opencode/skills/rps-cli/SKILL.md" in opencode_setup, "setup_opencode_devnet.py must attach the OpenCode skill", errors)
    require(".second-brain/patterns/rps-cli.md" in opencode_setup, "setup_opencode_devnet.py must attach the RPS pattern", errors)
    require("task_file=play.py" in opencode_setup, "setup_opencode_devnet.py must report the generated app task file", errors)
    require('"webfetch": "deny"' in opencode_setup and '"websearch": "deny"' in opencode_setup, "setup_opencode_devnet.py must keep network permissions denied", errors)

    require("wants_barryflights_booking" in codex_shim and "BARRYFLIGHTS_BOOKING=pass" in codex_shim, "devnet_codex_shim.py must route the risky BarryFlights booking prompt", errors)
    require("run_mazemaker_skill_build" not in codex_shim, "devnet_codex_shim.py must not fake skill output with local Python", errors)
    require("wants_mazemaker" not in codex_shim, "devnet_codex_shim.py must not special-case Maze prompts", errors)
    require("leaky_rps_patch.py" in scenario_review, "scenario review must point to the RPS leaky sample", errors)

    repo_text = "\n".join(
        read(root, str(path))
        for path in [
            "README.md",
            "AGENTS.md",
            "CLAUDE.md",
            "docs/tool-options.md",
            "scripts/tool_doctor.py",
            "scripts/model_resource_walkthrough.py",
        ]
    ).lower()
    require("mazemaker" not in repo_text, "top-level docs/scripts must not mention MazeMaker", errors)
    require("dojo_app/maze" not in repo_text, "top-level docs/scripts must not mention old Maze files", errors)

    if errors:
        print("CONSISTENCY_CHECK=fail")
        for error in errors:
            print(f"- {error}")
        return 1

    print("CONSISTENCY_CHECK=pass")
    print("Checked agent rules, docs, skills, KB, and tool config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
