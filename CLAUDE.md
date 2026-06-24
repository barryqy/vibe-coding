# Optional Claude Code Notes

Read `AGENTS.md` first. Then read `.second-brain/RESOLVER.md` and `.second-brain/sessions/current-session.md`. The same quality bar applies here.

Claude Code is optional for this DevNet lab because it normally needs personal sign-in. The required path starts with Codex CLI through the supplied DevNet model route, then uses OpenCode later as a comparison tool.

Use a planning pass before risky edits, especially changes that affect command execution, file deletion, authentication, or model routing.

Good default loop:

```bash
python3 scripts/setup_codex_devnet.py
python3 -m dojo_app.maze_game
python3 scripts/check_repo.py
```

For the Maze game module, keep edits scoped to `dojo_app/maze_game.py` and `tests/test_maze_game.py`.

OpenCode is attached to the same second brain through `scripts/setup_opencode_devnet.py`. The current session note should explain the next small Maze task before OpenCode runs a direct prompt:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title maze-interactive --agent build --model devnet/gpt-4o "Read the second brain. Make the maze interactive so I can play it with arrow keys. Add a --play flag. Keep static mode working. Do not run shell commands during the edit; I will run the checks next."
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
