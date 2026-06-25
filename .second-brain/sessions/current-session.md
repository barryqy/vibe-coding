---
type: session
status: active
---

# Current Session

## Current State

- Codex is installed and connected to the supplied lab model route.
- The local BarryFlights MCP server returned a clean flight_status result.
- The second brain now carries the OpenCode task for after the Maze is generated.

## OpenCode Next Task

- Add a `--play` flag to `dojo_app/maze_game.py` so the Maze can be played in the terminal.
- Keep the existing static path unchanged: do not remove, rename, or replace `run_static_maze`, `render_maze`, `load_lab_maze`, or `main`.
- Keep `args = parser.parse_args(argv)` in `main` before reading `args.maze_file`, `args.render`, or `args.play`.
- Add `move_player(maze, position, key)` as a pure helper. Support `w`, `a`, `s`, `d`, `up`, `down`, `left`, and `right`. Never move into `#`.
- Add `render_player_maze(maze, position, render)` so play mode visibly shows the player as `@` on the board.
- Add one or two `MazeGameTests` methods for the pure movement/render helpers only. Do not test the input loop.
- Use simple line input in play mode: show controls, accept `w/a/s/d`, `up/down/left/right`, and `q` to quit.
- Do not add network calls, credential reads, terminal clear codes, curses, or external packages.

## Next Action

- Let OpenCode implement the play mode from this shared memory.
- After the edit, run `python3 -m unittest tests.test_maze_game` and `python3 scripts/check_repo.py`.

## Boundaries

- Do not store secrets or one-time credentials in the second brain.

## Verification

- python3 -m unittest tests.test_maze_game
- python3 scripts/check_repo.py
