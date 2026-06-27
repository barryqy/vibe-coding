---
name: tictactoe-cli
description: Build or complete a small terminal tic-tac-toe game without prewritten game logic.
---

# Tic-Tac-Toe CLI Skill

Use this skill when the task asks for playable terminal tic-tac-toe.

## Build Rules

- Create the working game, not a plan or Markdown answer.
- Keep the code small, readable, and standard-library only.
- Do not add curses, shell clear commands, network calls, credential reads, or external packages.
- Do not leave the computer player as random-only. It should win if possible, block if needed, then choose center, a corner, then a side.
- Do not treat `py_compile` as enough. The game must also run through a scripted play path.
- Treat `--smoke-test` prompting for input as a failure. It must run to completion without a person typing.
- Treat a class or function named only around random computer play as incomplete unless it also checks win, block, center, corner, and side choices.

## Current Repo Shape

When working in this dojo repo:

- Edit `dojo_app/tictactoe_play.py`.
- Keep the public entry point exactly named `run_tictactoe(scenario)`.
- Do not move play mode into a new `main()` function.
- Do not edit `dojo_app/tictactoe_game.py` unless the user explicitly asks for it.
- Support both `scenario.mode` values: `human-vs-human` and `human-vs-computer`.
- Use the scenario board and `scenario.next_player` as the starting state.
- Print `TICTACTOE_PLAY=quit` when the user enters `q`.

Before stopping, run:

```bash
python3 -m py_compile dojo_app/tictactoe_game.py dojo_app/tictactoe_play.py
python3 -m dojo_app.tictactoe_game --check-play-interface
printf 'q\n' | python3 -m dojo_app.tictactoe_game --scenario-file .lab-state/codex-output/tictactoe-scenario.txt --play
```

## Empty Directory Shape

When the task starts from an empty directory:

- Create `play.py`.
- Add a short `README.md` with run commands.
- `python3 play.py` should start with a clear mode choice.
- Mode `1` should be human vs human.
- Mode `2` should be human vs computer, with the human as X and the computer as O.
- Moves should use positions `1` through `9`; `q` should quit cleanly.
- Invalid or occupied moves should not switch turns.
- Detect X wins, O wins, and draws, then exit cleanly.

`python3 play.py --smoke-test` must be non-interactive. It should use real `assert` checks and print exactly this only after the checks pass:

```text
TICTACTOE_SMOKE=pass
```

The smoke test should cover row, column, and diagonal wins; draw detection; invalid or occupied move handling; computer winning move; computer blocking move; and center preference.
If `--smoke-test` asks for a mode, a board position, or any other input, fix the code before stopping.

Before stopping, run:

```bash
python3 -m py_compile play.py
python3 play.py --smoke-test
printf '2\n1\nq\n' | timeout 10 python3 play.py
printf '1\n1\n2\n4\n5\n7\n' | timeout 10 python3 play.py
```
