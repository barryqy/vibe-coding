# Optional Claude Code Notes

Read `AGENTS.md` first. Then read `.second-brain/RESOLVER.md` and `.second-brain/sessions/current-session.md`. The same quality bar applies here.

Claude Code is optional for this DevNet lab because it normally needs personal sign-in. The required path starts with Codex CLI through the supplied DevNet model route, then uses OpenCode later as a comparison tool.

Use a planning pass before risky edits, especially changes that affect command execution, file deletion, authentication, or model routing.

Good default loop:

```bash
python3 scripts/setup_codex_devnet.py
.venv/bin/python -m dojo_app.barryflights_mcp_client --tool flight_status --flight SKY451
python3 -m dojo_app.maze_game
python3 scripts/check_repo.py
```

For the Maze game module, keep edits scoped to `dojo_app/maze_game.py` and `tests/test_maze_game.py`.

For the local MCP module, keep the clean BarryFlights MCP server scoped to `dojo_app/barryflights_mcp_server.py`, `dojo_app/barryflights_mcp_client.py`, and `tests/test_barryflights_mcp.py`. Do not add credential reads, outbound network calls, or hidden exfiltration to the clean server.

Keep `.second-brain/sessions/current-session.md` current as task state changes.

OpenCode is attached to the same second brain through `scripts/setup_opencode_devnet.py` and should continue from the current session note:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title maze-interactive --agent build --model devnet/gpt-4o "Read the second brain. Make the maze interactive so I can play it with arrow keys. Add a --play flag. Preserve run_static_maze, the default tile-rendered static output, and --render raw. Do not run shell commands during the edit; I will run the checks next." --file dojo_app/maze_game.py --file tests/test_maze_game.py --file .second-brain/sessions/current-session.md
```

For the DefenseClaw mini-module, keep the scanner path explicit:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_skill_demo.py
```

For this lab, do not approve commands that read `.env`, `.env.*`, `secrets/`, browser profiles, SSH keys, or cloud credentials. Use fake sample data only.

When you finish a meaningful fix or decision, create a short note:

```bash
python3 scripts/make_second_brain_note.py --title "Decision title" --why "Why this will matter later"
```
