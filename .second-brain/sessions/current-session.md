---
type: session
status: active
---

# Current Session

## Current State

- Codex is installed and connected to the supplied lab model route.
- Codex can check flight status through the local BarryFlights MCP server.
- The Maze app can use the repo-local MazeMaker skill to build checked 12x12 maze data and render it as an Amaze-style terminal board.
- The MazeMaker skill pattern lives at `.second-brain/patterns/mazemaker-skill.md`.
- The Maze play movement pattern lives at `.second-brain/patterns/maze-play-movement.md`.
- `dojo_app/maze_game.py` is stable runner code; it dispatches play mode into `dojo_app/maze_play.py`.
- `dojo_app/maze_play.py` is the scoped coding-agent file. Its play harness handles single-key input and redraw; the movement function is the placeholder a coding agent fills.
- The second brain is shared context for any agent that works in this repo.
- Codex should create the static Maze file first; OpenCode should only make that Maze playable.
- The local Codex and OpenCode adapters forward cache model aliases unchanged in both production and staging.
- The active leaderboard event is `self-paced`.
- Project-note promotion restores the checked note when Codex returns no usable draft.

## Recent Work

- The KB structure has a resolver, schema, project notes, session notes, decisions, and patterns.
- Agents should search `.second-brain/` for relevant notes before editing and update this note when task state changes.
- OpenCode config should load only top-level repo instructions, not exact second-brain memory files.
- The lab now keeps OpenCode visible in the play exercise: OpenCode adds movement, the command compiles the Maze files, and the same block launches the interactive Maze.
- Removed the temporary production alias fallback and bumped both adapter versions so the next adapter start or `--ensure` replaces stale fallback processes.
- Restored `config/dojo-event.toml` and its repository guard to `self-paced` after the final rehearsal.
- Added missing-draft coverage so an upstream model timeout cannot strand the shared-context checkpoint on stale evidence.
- Made the Maze input mode and W/A/S/D/Q controls explicit, added invalid-input recovery, and preserved terminal restoration across quit, EOF, and failures.
- Updated the bundled Dojo CLI so fresh evidence for each flag is independent of earlier captures while duplicate captures remain harmless.
- Staged a rebuilt Dojo CLI candidate with bounded capture retries, pending-capture reconciliation, and honest sync status reporting.
- Raised the upstream model-response timeout from 45 to 90 seconds in both local adapters and the direct baseline guardrail demo. Both adapter versions were bumped so `--ensure` replaces already-running 45-second processes.

## Open Questions

- The capture-reliability CLI candidate still needs helper publication, an image rebuild, and published DevNet terminal validation before release.

## Boundaries

- Do not store secrets or one-time credentials in the second brain.
- Keep Maze play changes in `dojo_app/maze_play.py` unless the current task explicitly says otherwise.
- For playable movement, replace only `choose_next_position(...)`; do not change the play harness.
- Do not add feature flags, network calls, credential reads, shell clear commands, curses, or external packages to the Maze game.

## Verification

- python3 scripts/verify_maze_movement.py
- python3 -m unittest tests.test_maze_game
- python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py
- python3 scripts/check_repo.py
- python3 -m unittest tests.test_devnet_codex_shim tests.test_devnet_openai_shim tests.test_setup_opencode_devnet
- python3 scripts/consistency_check.py
- python3 scripts/security_review.py dojo_app scripts
