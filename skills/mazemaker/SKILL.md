---
name: mazemaker
description: Build checked 12x12 terminal Maze artifacts for the Vibe Coding dojo. Use when Codex needs to create, regenerate, or save solvable Maze data for dojo_app/maze_game.py, especially when the prompt mentions MazeMaker, a Maze artifact, recursive backtracking, .lab-state/codex-output/maze.txt, or the repo-local second brain.
---

# MazeMaker

MazeMaker creates a small raw Maze file that `dojo_app/maze_game.py` can verify, render, and later play. Use the bundled script instead of hand-drawing maze rows.

## Workflow

1. Run `scripts/build_maze.py` from the repo root.
2. Save the Maze data to `.lab-state/codex-output/maze.txt` unless the user gives another repo-local output path.
3. Verify the saved file with `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --check-only`.
4. Render it with `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --render amaze`.

## Command

From the repo root:

```bash
python3 skills/mazemaker/scripts/build_maze.py --maze-file .lab-state/codex-output/maze.txt
```

If this skill is installed under `CODEX_HOME`, the equivalent command is:

```bash
python3 .lab-state/codex/home/skills/mazemaker/scripts/build_maze.py --maze-file .lab-state/codex-output/maze.txt
```

## Output Contract

The script prints stable evidence:

```text
MAZEMAKER_SKILL=ready
skill=mazemaker
format=recursive-backtracker
maze_file=.lab-state/codex-output/maze.txt
size=12x12
border=ok
solvable=yes
path_length=...
MAZEMAKER_SKILL=pass
```

Do not add network calls, external packages, credential reads, curses, or shell clear commands. Maze generation should stay local, deterministic for a fixed seed, and verified before use.
