# Optional Claude Code Notes

Read `AGENTS.md` first, then search `.second-brain/` for notes that match the task. The same quality bar applies here.

Claude Code is optional for this DevNet lab because it normally needs personal sign-in. The required path starts with Codex CLI through the supplied DevNet model route, then uses OpenCode later as a comparison tool.

Use a planning pass before risky edits, especially changes that affect command execution, file deletion, authentication, or model routing.

Good default loop:

```bash
python3 scripts/setup_codex_devnet.py
.venv/bin/python -m dojo_app.barryflights_mcp_client --tool flight_status --flight SKY451
python3 .lab-state/codex/home/skills/mazemaker/scripts/build_maze.py --maze-file .lab-state/codex-output/maze.txt
python3 -m dojo_app.maze_game
python3 scripts/check_repo.py
```

For the Maze game module, keep play-loop edits scoped to `dojo_app/maze_play.py` unless the user explicitly asks for broader changes. `dojo_app/maze_game.py` is the stable loader, checker, renderer, and CLI wrapper. The starter play module is intentionally a placeholder; do not make the OpenCode exercise look solved by adding or flipping a feature flag.

For the local MCP module, keep BarryFlights scoped to `dojo_app/barryflights_mcp_server.py`, `dojo_app/barryflights_mcp_client.py`, and `tests/test_barryflights_mcp.py`. The safe lesson is `flight_status`; the intentional security-module risk is `book_flight`, which writes a local demo ledger and returns fake AWS-style sample credentials. Do not add real credential reads, outbound network calls, or hidden exfiltration.

Keep `.second-brain/sessions/current-session.md` current as task state changes, and write durable decisions or reusable patterns under `.second-brain/` when future agents should not have to rediscover them.

OpenCode is attached to the repo through `scripts/setup_opencode_devnet.py` and should search the second brain before changing the Maze:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title maze-interactive --agent build --model devnet/gpt-4o "Search .second-brain/ for Maze project context. Edit exactly one file: dojo_app/maze_play.py. Replace only the body of choose_next_position(maze, position, command). Do not edit run_play_maze; it already handles single-key input, redraw, rendering, quit, and return codes. Use the existing MOVE_DELTAS mapping. If command is not in MOVE_DELTAS, return the current position. Otherwise compute the target row and column. If the target is outside the maze or is #, return the current position. Otherwise return the target position. Use four spaces for indentation and no tabs. After editing, run only python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py. If compile fails, fix the code and run py_compile again. Do not run python3 -m dojo_app.maze_game and do not run the play smoke test; the lab runs that next. Do not edit dojo_app/maze_game.py, tests, config, or second-brain files. Do not add feature flags, external packages, network calls, credential reads, curses, or shell clear commands. Then stop." --file dojo_app/maze_play.py
```

For the DefenseClaw mini-module, keep the scanner path explicit:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

For this lab, do not approve commands that read `.env`, `.env.*`, `secrets/`, browser profiles, SSH keys, or cloud credentials. Use sample data only.

When you finish a meaningful fix or decision, create a short note:

```bash
python3 scripts/make_second_brain_note.py --title "Decision title" --why "Why this will matter later"
```
