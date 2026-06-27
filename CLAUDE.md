# Optional Claude Code Notes

Read `AGENTS.md` first. Then read `.second-brain/RESOLVER.md`, `.second-brain/schema.md`, and `.second-brain/sessions/current-session.md`. The same quality bar applies here.

Claude Code is optional for this DevNet lab because it normally needs personal sign-in. The required path starts with Codex CLI through the supplied DevNet model route, then uses OpenCode later as a second tool.

Good default loop:

```bash
python3 scripts/setup_codex_devnet.py
.venv/bin/python -m dojo_app.barryflights_mcp_client --tool flight_status --flight SKY451
CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" --sandbox read-only --output-last-message GAME_CONTRACT.md 'Use $rps-cli and the second brain to create the game contract. Return only the contract body. Do not create play.py or GAME_README.md.'
python3 scripts/check_repo.py
```

For the local MCP module, keep BarryFlights scoped to `dojo_app/barryflights_mcp_server.py`, `dojo_app/barryflights_mcp_client.py`, and `tests/test_barryflights_mcp.py`. The safe lesson is `flight_status`; the intentional security-module risk is `book_flight`, which writes a local demo ledger and returns fake AWS-style sample credentials. Do not add real credential reads, outbound network calls, or hidden exfiltration.

For the RPS game module, do not add a prebuilt game. Let Codex produce `GAME_CONTRACT.md`, then let OpenCode produce `play.py` and `GAME_README.md` from the attached contract, skill, and KB files.

OpenCode is attached to the same second brain through `scripts/setup_opencode_devnet.py`:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json OPENCODE_DISABLE_AUTOUPDATE=true OPENCODE_DISABLE_LSP_DOWNLOAD=true opencode run 'Use the attached project memory, rps-cli skill, and GAME_CONTRACT.md. This folder has no app code yet. Create play.py and GAME_README.md. Implement the complete rock-paper-scissors CLI game and --self-test. Run every VERIFY command in GAME_CONTRACT.md and fix failures before stopping.' --title rps-cli-build --agent build --model devnet/gpt-4o --file AGENTS.md --file .second-brain/RESOLVER.md --file .second-brain/projects/vibe-coding-dojo.md --file .second-brain/sessions/current-session.md --file .opencode/skills/rps-cli/SKILL.md --file GAME_CONTRACT.md
```

For the DefenseClaw mini-module:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

Do not approve commands that read `.env`, `.env.*`, `secrets/`, browser profiles, SSH keys, or cloud credentials. Use sample data only.

When you finish a meaningful fix or decision, update `.second-brain/sessions/current-session.md` or create a short durable note with `scripts/make_second_brain_note.py`.
