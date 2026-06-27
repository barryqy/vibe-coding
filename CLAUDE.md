# Optional Claude Code Notes

Read `AGENTS.md` first. Then read `.second-brain/RESOLVER.md`, `.second-brain/schema.md`, and `.second-brain/sessions/current-session.md`. The same quality bar applies here.

Claude Code is optional for this DevNet lab because it normally needs personal sign-in. The required path starts with Codex CLI through the supplied DevNet model route, then uses OpenCode later as a comparison tool.

Use a planning pass before risky edits, especially changes that affect command execution, file deletion, authentication, or model routing.

Good default loop:

```bash
python3 scripts/setup_codex_devnet.py
.venv/bin/python -m dojo_app.barryflights_mcp_client --tool flight_status --flight SKY451
python3 -m dojo_app.tictactoe_game --check-only
python3 -m dojo_app.tictactoe_game
python3 scripts/check_repo.py
```

For the tic-tac-toe game module, keep play-loop edits scoped to `dojo_app/tictactoe_play.py` unless the user explicitly asks for broader changes. `dojo_app/tictactoe_game.py` is the stable scenario checker, renderer, and CLI wrapper. The starter play module is intentionally a placeholder; do not make the OpenCode exercise look solved by adding or flipping a feature flag. Keep the public play entry point exactly named `run_tictactoe(scenario)`. Read `.second-brain/patterns/tictactoe-playable-cli.md` and `skills/tictactoe-cli/SKILL.md` before changing the playable game.

For the local MCP module, keep BarryFlights scoped to `dojo_app/barryflights_mcp_server.py`, `dojo_app/barryflights_mcp_client.py`, and `tests/test_barryflights_mcp.py`. The safe lesson is `flight_status`; the intentional security-module risk is `book_flight`, which writes a local demo ledger and returns fake AWS-style sample credentials. Do not add real credential reads, outbound network calls, or hidden exfiltration.

Keep `.second-brain/sessions/current-session.md` current as task state changes, and write durable decisions or reusable patterns under `.second-brain/` when future agents should not have to rediscover them.

OpenCode is attached to the same second brain through `scripts/setup_opencode_devnet.py` and should read it before changing tic-tac-toe:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title tictactoe-playable --agent build --model devnet/gpt-4o "Read the second brain, .second-brain/patterns/tictactoe-playable-cli.md, and skills/tictactoe-cli/SKILL.md. Edit exactly one file: dojo_app/tictactoe_play.py. Keep the public entry point exactly named run_tictactoe(scenario). Implement real terminal play for human-vs-human and human-vs-computer. Do not leave the computer player random-only. Run the verification commands from the playable tic-tac-toe pattern, fix failures, and stop only after they pass." --file dojo_app/tictactoe_play.py --file .second-brain/sessions/current-session.md
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
