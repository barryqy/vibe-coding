---
type: pattern
status: active
---

# MazeMaker Skill Pattern

## When To Use

Use this when the task asks for a new Maze artifact, generated Maze data, or a Maze file for this repo.

## Steps

- Use the repo-local MazeMaker skill.
- Run `python3 .lab-state/codex/home/skills/mazemaker/scripts/build_maze.py --maze-file .lab-state/codex-output/maze.txt`.
- Verify the saved file with `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --check-only`.
- Render it with `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --render amaze`.

## Verification

- The skill result should include `MAZEMAKER_SKILL=pass`.
- The checker should include `MAZE_CHECK=pass`.
