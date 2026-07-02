---
type: pattern
status: active
---

# Maze Play Movement Pattern

## When To Use

Use this when the task asks to make the saved Maze playable, add keyboard movement, or update Maze play behavior.

## Steps

- Edit only `dojo_app/maze_play.py`.
- Replace only the body of `choose_next_position(maze, position, command)`.
- Leave `run_play_maze(...)` alone; it already handles input, redraw, rendering, quit, and return codes.
- Use the existing `MOVE_DELTAS` mapping for `w`, `a`, `s`, and `d`.
- If the command is not in `MOVE_DELTAS`, return the current position.
- Compute the target row and column from the current position and the selected delta.
- If the target is outside the Maze or the target cell is `#`, return the current position.
- Otherwise return the target position.
- Do not add feature flags, external packages, network calls, credential reads, curses, or shell clear commands.

## Verification

- Run `python3 scripts/verify_maze_movement.py` and fix the movement function until it exits successfully.
- Run `python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py`.
- The lab guide launches the real interactive Maze after OpenCode finishes.
