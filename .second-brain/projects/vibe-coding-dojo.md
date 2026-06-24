---
type: project
status: active
---

# Vibe Coding Dojo

## Summary

This repo is a small AI coding dojo. Codex is used first with the supplied lab model route. OpenCode joins later and reads the same second brain before working on the Pong game.

## Current Files

- `dojo_app/pong_game.py` contains Pong.
- `tests/test_pong_game.py` contains the direct Pong tests.
- `scripts/check_repo.py` is the repo-level verification command.

## Boundaries

- Keep the game deterministic.
- Do not add network calls, credential reads, terminal clear codes, or external packages.
- Keep changes scoped to the game and its direct tests unless the handoff says otherwise.
