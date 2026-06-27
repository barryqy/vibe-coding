---
type: project
status: active
---

# Vibe Coding Dojo

## Summary

This repo is a small AI coding dojo. Coding agents use the supplied lab model route, read the same second brain before editing, and keep task state current as they work.

The main coding boundary is intentionally clear:

- Codex creates `GAME_CONTRACT.md` from the repo skill and KB.
- OpenCode creates `play.py` and `GAME_README.md` from that contract.
- The repo does not ship a prebuilt rock-paper-scissors app for the exercise.

## Current Files

- `.agents/skills/rps-cli/SKILL.md` is the Codex project skill for the contract stage.
- `.opencode/skills/rps-cli/SKILL.md` is the OpenCode project skill for the build stage.
- `.second-brain/patterns/rps-cli.md` records the contract-to-build pattern.
- `GAME_CONTRACT.md` is created during the lab and should name the app, modes, and verification commands.
- `play.py` is created during the OpenCode build stage.
- `dojo_app/barryflights_mcp_server.py` contains the local BarryFlights MCP server.
- `dojo_app/barryflights_mcp_client.py` calls the local MCP server over stdio.
- `scripts/model_usage.py` is exposed as `usage` by setup and reports adapter-recorded token counts.
- `scripts/check_repo.py` is the repo-level verification command.

## Boundaries

- Do not fake the game by running a bundled generator or hidden helper.
- Keep contract-only Codex prompts from creating `play.py`.
- Keep OpenCode build prompts focused on `GAME_CONTRACT.md`, `play.py`, and `GAME_README.md`.
- Do not add network calls, credential reads, shell clear commands, curses, or external packages to the game.
- Keep the local BarryFlights `flight_status` path clean; risky MCP behavior belongs in the security module.
- Treat remaining model budget as platform-owned. The local `usage` command shows exact token counts and any gateway-reported budget details, but it should not invent a hard remaining budget when the route does not expose one.

## Verification

- python3 scripts/check_repo.py
- grep -q '^APP: play.py$' GAME_CONTRACT.md
- grep -q '^MARKER: RPS_SELF_TEST=pass$' GAME_CONTRACT.md
- python3 scripts/normalize_game_contract.py .lab-state/codex-output/rps-contract.raw.txt GAME_CONTRACT.md
- python3 -m py_compile play.py
- timeout 10s python3 play.py --self-test
