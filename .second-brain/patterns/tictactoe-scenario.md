---
type: pattern
status: active
---

# Tic-Tac-Toe Scenario Pattern

## When To Use

Use this when the task asks for a new tic-tac-toe starting scenario for this repo.

## Steps

- Ask Codex for one small scenario.
- Save it to `.lab-state/codex-output/tictactoe-scenario.txt`.
- Keep the format to `MODE`, `NEXT`, and a three-row `BOARD`.
- Verify it with `python3 -m dojo_app.tictactoe_game --scenario-file .lab-state/codex-output/tictactoe-scenario.txt --check-only`.

## Verification

- The checker should include `TICTACTOE_CHECK=pass`.
