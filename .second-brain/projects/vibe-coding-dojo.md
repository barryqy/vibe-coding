---
type: project
status: active
---

# Vibe Coding Dojo

## Summary

This repo is a small AI coding dojo. Coding agents use the supplied lab model route, read the same second brain before editing, and keep task state current as they work.

## Current Files

- `dojo_app/tictactoe_game.py` contains tic-tac-toe scenario parsing, validation, rendering, and the stable `--play` dispatch.
- `dojo_app/tictactoe_play.py` contains the scoped play-loop entrypoint. OpenCode fills this file for human-vs-computer and human-vs-human play.
- `.second-brain/patterns/tictactoe-scenario.md` tells agents how to create a small scenario file.
- `.second-brain/patterns/tictactoe-playable-cli.md` tells agents how to turn a scenario or empty folder into a playable terminal game.
- `skills/tictactoe-cli/SKILL.md` gives OpenCode the tic-tac-toe build rules without hiding the implementation in helper code.
- `tests/test_tictactoe_game.py` contains the direct tic-tac-toe tests.
- `dojo_app/barryflights_mcp_server.py` contains the clean local BarryFlights MCP server.
- `dojo_app/barryflights_mcp_client.py` calls the local MCP server over stdio.
- `scripts/check_repo.py` is the repo-level verification command.

## Boundaries

- Keep tic-tac-toe scenarios small enough for Codex to write directly.
- When a task asks for a new tic-tac-toe scenario, use `.second-brain/patterns/tictactoe-scenario.md`.
- When a task asks for playable tic-tac-toe, use `.second-brain/patterns/tictactoe-playable-cli.md` and `skills/tictactoe-cli/SKILL.md`.
- When a task asks for playable tic-tac-toe behavior, implement real play in `dojo_app/tictactoe_play.py`; do not edit the stable scenario checker unless the task explicitly asks for it.
- Do not stop after syntax checks alone. A playable task needs a scripted run path.
- Do not add network calls, credential reads, shell clear commands, curses, or external packages.
- Keep the local BarryFlights MCP server clean; risky MCP behavior belongs in the security module.
- Keep changes scoped to the game and its direct tests unless the current task says otherwise.

## Verification

- python3 scripts/check_repo.py
