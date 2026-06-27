---
type: session
status: active
---

# Current Session

## Current State

- Codex is installed and connected to the supplied lab model route.
- Codex can check flight status through the local BarryFlights MCP server.
- `usage` is available after setup and shows token counts recorded by the local adapters.
- The second brain is shared context for any agent that works in this repo.
- The current coding flow uses a repo skill and KB pattern for a rock-paper-scissors CLI game.
- Codex should create `GAME_CONTRACT.md` only.
- OpenCode should create `play.py` and `GAME_README.md` from `GAME_CONTRACT.md`.
- The contract is normalized from Codex's raw final message before OpenCode reads it.

## Recent Work

- The KB structure has a resolver, schema, project notes, session notes, decisions, and patterns.
- The RPS skill lives in the documented project skill locations for Codex and OpenCode.
- The DevNet model route returns token usage on successful calls, but the staging probe did not find a separate remaining-budget endpoint.
- Agents should read the KB before editing and update this note when task state changes.

## Open Questions

- None right now.

## Boundaries

- Do not store secrets or one-time credentials in the second brain.
- Do not add a prebuilt game implementation to the repo for the main exercise.
- Do not add feature flags, network calls, credential reads, shell clear commands, curses, or external packages to the generated game.

## Verification

- python3 scripts/check_repo.py
- python3 scripts/normalize_game_contract.py .lab-state/codex-output/rps-contract.raw.txt GAME_CONTRACT.md
- timeout 10s python3 play.py --self-test, after OpenCode creates `play.py`
