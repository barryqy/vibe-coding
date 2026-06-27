---
type: pattern
status: active
---

# Tic-Tac-Toe Playable CLI Pattern

## When To Use

Use this when the task asks an agent to make tic-tac-toe playable in the terminal.

## Steps

- Read `skills/tictactoe-cli/SKILL.md` before editing.
- Build actual play behavior, not only syntax-valid code.
- Keep the game simple: board rendering, winner checking, legal move handling, turn switching, and computer move choice.
- For this repo, keep the public entry point as `run_tictactoe(scenario)` in `dojo_app/tictactoe_play.py`.
- For an empty directory task, create `play.py` and a short `README.md`.
- Make the computer deterministic enough to review: win, block, center, corner, side.
- Add or keep a non-interactive check path. A smoke test that only prints a board is not enough.
- If `--smoke-test` asks for input, the task is not finished.
- If the computer player is random-only, the task is not finished.

## Verification

For this repo:

- `python3 -m py_compile dojo_app/tictactoe_game.py dojo_app/tictactoe_play.py`
- `python3 -m dojo_app.tictactoe_game --check-play-interface`
- `printf 'q\n' | python3 -m dojo_app.tictactoe_game --scenario-file .lab-state/codex-output/tictactoe-scenario.txt --play`

For an empty directory task:

- `python3 -m py_compile play.py`
- `python3 play.py --smoke-test` prints `TICTACTOE_SMOKE=pass`
- `printf '2\n1\nq\n' | timeout 10 python3 play.py`
- `printf '1\n1\n2\n4\n5\n7\n' | timeout 10 python3 play.py`
