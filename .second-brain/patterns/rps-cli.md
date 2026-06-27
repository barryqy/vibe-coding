---
type: pattern
status: active
---

# RPS CLI Build Pattern

## When To Use

Use this pattern when a task asks Codex or OpenCode to create the dojo rock-paper-scissors CLI game.

## Steps

Codex contract stage:

1. Read `.agents/skills/rps-cli/SKILL.md`.
2. Create `GAME_CONTRACT.md`.
3. Do not create `play.py` or `GAME_README.md`.
4. Include the required app name, game name, modes, verification commands, and `RPS_SELF_TEST=pass` marker.

OpenCode build stage:

1. Read `.opencode/skills/rps-cli/SKILL.md`.
2. Read `GAME_CONTRACT.md`.
3. Create `play.py` and `GAME_README.md`.
4. Run every `VERIFY:` command from the contract.
5. Update `.second-brain/sessions/current-session.md` with the current state if the task changes the repo.

## Verification

```bash
grep -q '^APP: play.py$' GAME_CONTRACT.md
grep -q '^DOCS: GAME_README.md$' GAME_CONTRACT.md
grep -q '^MARKER: RPS_SELF_TEST=pass$' GAME_CONTRACT.md
test ! -f play.py
```

After OpenCode builds the app:

```bash
test -f play.py
test -f GAME_README.md
python3 -m py_compile play.py
timeout 10s python3 play.py --self-test
printf '1\nrock\nq\n' | timeout 10s python3 play.py
printf '1\nlizard\nq\n' | timeout 10s python3 play.py
printf '2\nrock\nscissors\nq\n' | timeout 10s python3 play.py
```
