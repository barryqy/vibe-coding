---
type: project
status: active
---

# Vibe Coding Dojo

## Summary

This repo is a small AI coding dojo. Coding agents use the supplied lab model route, read the same second brain before editing, and keep task state current as they work.

## Current Files

- `dojo_app/maze_game.py` contains Maze parsing, solvability checks, rendering, and the stable `--play` dispatch.
- `dojo_app/maze_play.py` contains the scoped play-loop entrypoint. The harness handles single-key input and redraw; OpenCode only fills the movement function.
- `skills/mazemaker/SKILL.md` is the repo-local MazeMaker skill.
- `skills/mazemaker/scripts/build_maze.py` creates checked Recursive Backtracker maze data.
- `.second-brain/patterns/mazemaker-skill.md` tells agents to use the MazeMaker skill for new Maze artifacts.
- `.second-brain/patterns/maze-play-movement.md` tells agents how to add movement without touching the play harness.
- `tests/test_maze_game.py` contains the direct Maze tests.
- `dojo_app/barryflights_mcp_server.py` contains the clean local BarryFlights MCP server.
- `dojo_app/barryflights_mcp_client.py` calls the local MCP server over stdio.
- `scripts/run_risky_mcp_demo.py` exercises the intentionally unsafe `workspace-admin-bridge` file-read path and saves the local MCP response under `.lab-state/darkside/`.
- `bin/dojo-linux-x86_64` requires the submitted Flag 5 answer to match the fake secret in that saved MCP response; the answer is not sent to the leaderboard.
- `scripts/promote_project_note.py` validates Codex drafts and restores the checked note when no usable draft is returned.
- `scripts/check_repo.py` is the repo-level verification command.
- `config/dojo-event.toml` is the only leaderboard event selector used by `dojo join`.
- `scripts/devnet_model_route.py` contains the exact production-only cache alias fallback shared by the Codex and OpenCode adapters.

## Boundaries

- Keep maze generation checked and repeatable when a fixed seed is used.
- When a task asks for a new Maze artifact, use the MazeMaker skill pattern from `.second-brain/patterns/mazemaker-skill.md`.
- When a task asks for playable Maze behavior, use the Maze play movement pattern and implement real movement in `dojo_app/maze_play.py`; do not edit the stable Maze loader, renderer, or play harness unless the task explicitly asks for it.
- Do not add network calls, credential reads, shell clear commands, curses, or external packages.
- Keep the local BarryFlights MCP server clean; risky MCP behavior belongs in the security module.
- Keep the risky MCP exercise local and explicit: it demonstrates unrestricted file access, not prompt injection or real network exfiltration.
- Keep credential fixtures Vibe Coding-specific and fake. Do not reveal the Flag 5 answer in learner instructions or the release binary.
- A missing or schema-invalid Codex draft may enter the checked-note fallback; other file and Git errors stay fatal.
- Keep changes scoped to the game and its direct tests unless the current task says otherwise.
- Keep event switches limited to `config/dojo-event.toml` and the matching repository guard.
- Keep production model fallbacks exact to the known production endpoint. Staging and unrelated endpoints must pass requested models through unchanged.

## Verification

- python3 scripts/check_repo.py
- shasum -a 256 -c bin/dojo-linux-x86_64.sha256
- python3 -m unittest tests.test_devnet_model_route tests.test_devnet_codex_shim tests.test_devnet_openai_shim
