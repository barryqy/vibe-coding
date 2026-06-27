---
type: session
status: active
---

# Current Session

## Current State

- Codex is installed and connected to the supplied lab model route.
- Codex can check flight status through the local BarryFlights MCP server.
- The Maze app can use the repo-local MazeMaker skill to build checked 12x12 maze data and render it as an Amaze-style terminal board.
- The MazeMaker skill pattern lives at `.second-brain/patterns/mazemaker-skill.md`.
- `dojo_app/maze_game.py` is stable runner code; it dispatches play mode into `dojo_app/maze_play.py`.
- `dojo_app/maze_play.py` is the scoped coding-agent file. Its play harness handles single-key input and redraw; the movement function is the placeholder a coding agent fills.
- The second brain is shared context for any agent that works in this repo.

## Recent Work

- The KB structure has a resolver, schema, project notes, session notes, decisions, and patterns.
- Agents should read the KB before editing and update this note when task state changes.

## Open Questions

- None right now.

## Boundaries

- Do not store secrets or one-time credentials in the second brain.
- Keep Maze play changes in `dojo_app/maze_play.py` unless the current task explicitly says otherwise.
- Do not add feature flags, network calls, credential reads, shell clear commands, curses, or external packages to the Maze game.

## Verification

- python3 -m unittest tests.test_maze_game
- python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py
- python3 scripts/check_repo.py
