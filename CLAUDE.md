# Optional Claude Code Notes

Read `AGENTS.md` first. The same quality bar applies here.

Claude Code is optional for this DevNet lab because it normally needs personal sign-in. The required attendee path starts with Codex CLI through the supplied DevNet model route, then uses OpenCode later as a comparison tool.

Use a planning pass before risky edits, especially changes that affect command execution, file deletion, authentication, or model routing.

Good default loop:

```bash
python3 scripts/setup_codex_devnet.py
python3 -m dojo_app.pong_game
python3 scripts/check_repo.py
```

For the Pong game module, keep edits scoped to `dojo_app/pong_game.py` and `tests/test_pong_game.py`.

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
