---
type: decision
status: active
---

# Select Dojo Events at Runtime

## Decision

Keep a fail-closed event placeholder in the reusable image and let `scripts/setup_dojo.sh [event-code]` write the selected event to ignored runtime state. With no argument, setup selects `self-paced`.

## Why It Matters

Future workshops can select their event in the lab instructions without rebuilding the DevNet image or downloading a different helper checkout. The tracked repo stays clean, and running Dojo before setup fails instead of joining the wrong leaderboard.

## Evidence

- `python3 scripts/check_repo.py`
- `python3 -m unittest tests.test_configure_dojo_event`
