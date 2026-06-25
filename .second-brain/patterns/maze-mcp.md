---
type: pattern
status: active
---

# MazeMaker MCP Pattern

## When To Use

Use this when the task asks for a new Maze artifact, generated Maze data, or a Maze file for this repo.

## Steps

- Use the local MazeMaker MCP `build_maze` tool.
- Save the Maze data to `.lab-state/codex-output/maze.txt`.
- Verify the saved file with `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --check-only`.
- Render it with `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --render amaze`.

## Verification

- The MCP result should include `MAZE_MCP=pass`.
- The checker should include `MAZE_CHECK=pass`.
