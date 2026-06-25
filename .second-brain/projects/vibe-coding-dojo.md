---
type: project
status: active
---

# Vibe Coding Dojo

## Summary

This repo is a small AI coding dojo. Coding agents use the supplied lab model route, read the same second brain before editing, and keep task state current as they work.

## Current Files

- `dojo_app/maze_game.py` contains Maze parsing, solvability checks, rendering, and play mode.
- `dojo_app/maze_mcp_server.py` exposes the local MazeMaker MCP `build_maze` tool.
- `dojo_app/maze_mcp_client.py` calls MazeMaker over stdio for local checks.
- `.second-brain/patterns/maze-mcp.md` tells agents to use MazeMaker MCP for new Maze artifacts.
- `tests/test_maze_game.py` contains the direct Maze tests.
- `dojo_app/barryflights_mcp_server.py` contains the clean local BarryFlights MCP server.
- `dojo_app/barryflights_mcp_client.py` calls the local MCP server over stdio.
- `scripts/check_repo.py` is the repo-level verification command.

## Boundaries

- Keep maze generation checked and repeatable when a fixed seed is used.
- When a task asks for a new Maze artifact, use the MazeMaker MCP pattern from `.second-brain/patterns/maze-mcp.md`.
- Do not add network calls, credential reads, shell clear commands, curses, or external packages.
- Keep the local BarryFlights MCP server clean; risky MCP behavior belongs in the security module.
- Keep changes scoped to the game and its direct tests unless the current task says otherwise.

## Verification

- python3 scripts/check_repo.py
