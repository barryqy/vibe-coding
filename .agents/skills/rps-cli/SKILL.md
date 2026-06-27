---
name: rps-cli
description: Create or build the Vibe Coding dojo rock-paper-scissors CLI contract and app.
---

# RPS CLI

Use this skill for the dojo rock-paper-scissors command-line game.

The exercise has two honest stages:

1. Codex writes a contract in `GAME_CONTRACT.md`.
2. OpenCode reads the contract and builds the app in `play.py`.

Do not create hidden helper code, call bundled game scripts, or fake the result with a prebuilt implementation.

## Contract Stage

When the prompt asks for the game contract, create or replace `GAME_CONTRACT.md` only. Do not create `play.py` or `GAME_README.md`.

The contract must include these lines exactly:

```text
APP: play.py
DOCS: GAME_README.md
GAME: rock-paper-scissors
MARKER: RPS_SELF_TEST=pass
```

It must also name these modes and checks:

```text
MODE: human-vs-computer
MODE: human-vs-human
VERIFY: python3 -m py_compile play.py
VERIFY: timeout 10s python3 play.py --self-test
VERIFY: printf '1\nrock\nq\n' | timeout 10s python3 play.py
VERIFY: printf '1\nlizard\nq\n' | timeout 10s python3 play.py
VERIFY: printf '2\nrock\nscissors\nq\n' | timeout 10s python3 play.py
```

State the behavior plainly:

- choose human-vs-computer with `1` and human-vs-human with `2`
- accept `rock`, `paper`, `scissors`, and `q`
- reject invalid moves and keep running
- support human-vs-computer and human-vs-human
- handle `--self-test` from command-line arguments before any `input()` call
- print `RPS_SELF_TEST=pass` from `--self-test`
- make every `VERIFY:` command finish on its own without manual input
- use only the Python standard library
- avoid network calls, credential reads, shell clear commands, curses, and external packages

## Build Stage

When the prompt asks to build the app, read `GAME_CONTRACT.md` first and create:

- `play.py`
- `GAME_README.md`

The app should be a small terminal program that can run in a plain shell. Keep the code simple enough to review in one sitting. Add a `--self-test` path that exercises winner logic, invalid input handling, and both game modes without waiting for interactive input.

Before stopping, run every `VERIFY:` command from `GAME_CONTRACT.md` and fix failures.
