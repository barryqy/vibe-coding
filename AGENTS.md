# Agent Instructions

This repo is a small DevNet training dojo for AI-assisted coding. Keep changes readable, boring, and easy to review.

## Project Map

- `dojo_app/` contains small support apps used by the lab.
- `dojo_app/barryflights_mcp_server.py` is the local BarryFlights MCP server. `flight_status` is the safe read-only lesson; `book_flight` is the intentionally risky security-module lesson that returns fake AWS-style sample credentials.
- `dojo_app/barryflights_mcp_client.py` calls that MCP server over stdio.
- `.agents/skills/rps-cli/SKILL.md` is the Codex project skill for the rock-paper-scissors contract.
- `.opencode/skills/rps-cli/SKILL.md` is the OpenCode project skill for the rock-paper-scissors build.
- `.second-brain/` stores shared KB notes: resolver, schema, project notes, current session state, decisions, and reusable patterns.
- `.second-brain/patterns/rps-cli.md` describes the Codex-to-OpenCode handoff.
- `GAME_CONTRACT.md` is generated during the lab by Codex and is not committed.
- `play.py` and `GAME_README.md` are generated during the lab by OpenCode and are not prebuilt in this repo.
- `docs/quality-bar.md` is the shared definition of good work.
- `scripts/check_repo.py` runs compile checks, unit tests, security review, and consistency checks.
- `samples/guardrails/`, `samples/skills/`, `samples/mcp/`, and `samples/leaky_rps_patch.py` contain clean and intentionally unsafe examples for DefenseClaw.

## Working Rules

- Start by reading `README.md`, this file, `docs/quality-bar.md`, `.second-brain/RESOLVER.md`, `.second-brain/schema.md`, and `.second-brain/sessions/current-session.md`.
- Treat MCP, Skills, and KB as different parts of the harness:
  - MCP is a callable tool boundary.
  - Skills are task instructions stored in documented skill folders.
  - KB is durable Markdown context that carries decisions across tools and sessions.
- Do not fake the game by running a bundled generator, hidden helper, or prebuilt implementation.
- Keep Codex contract prompts from creating `play.py`; they should produce `GAME_CONTRACT.md`.
- Keep OpenCode build prompts focused on `GAME_CONTRACT.md`, `play.py`, and `GAME_README.md`.
- Keep public examples free of secrets, real customer data, and private endpoints.
- Do not read `.env`, `.env.*`, or anything under `secrets/`.
- Keep `.second-brain/sessions/current-session.md` current when task state changes.

## Install Codex

```bash
if curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh; then
  CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh
else
  npm config set prefix "$HOME/.local"
  npm install -g @openai/codex
fi
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
codex_bwrap="$HOME/.codex/packages/standalone/current/codex-resources/bwrap"
if command -v bwrap >/dev/null 2>&1; then
  echo "Using the system sandbox helper."
elif [ -x "$codex_bwrap" ]; then
  ln -sf "$codex_bwrap" "$HOME/.local/bin/bwrap"
  echo "Using the sandbox helper bundled with Codex."
else
  echo "Sandbox helper not found."
fi
codex --version
```

## Codex Model Route And MCP Check

```bash
python3 scripts/setup_codex_devnet.py
python3 scripts/start_codex_model_adapter.py
```

`scripts/setup_codex_devnet.py` creates the repo-local Codex config, points it at the lab model, reports the Codex skill path, and registers the local BarryFlights MCP server.

```bash
python3 scripts/setup_codex_devnet.py >/dev/null
.venv/bin/python -m dojo_app.barryflights_mcp_client --list-tools
```

For the stable flight-status lesson, Codex reaches the local BarryFlights MCP client through the repo adapter:

```bash
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
if ! status_output="$(CODEX_HOME=.lab-state/codex/home codex exec \
    --disable plugin_sharing \
    --cd "$PWD" \
    --sandbox read-only \
    "Use the local BarryFlights MCP demo to check the status of flight SKY451." 2>&1)"; then
  printf '%s\n' "$status_output"
  exit 1
fi

printf '%s\n' "$status_output" | awk '
  /^BARRYFLIGHTS_STATUS=pass$/ { capture=1 }
  capture { print }
  /^MCP_DEPARTURE=/ && capture { found=1; exit }
  END { if (!found) exit 1 }
'
```

## Codex Contract Stage

Use the documented Codex skill path and the second-brain KB. The output file is the contract; the app should not exist yet.

```bash
rm -f GAME_CONTRACT.md play.py
CODEX_HOME=.lab-state/codex/home \
codex exec \
  --disable plugin_sharing \
  --ephemeral \
  --cd "$PWD" \
  --sandbox read-only \
  --output-last-message GAME_CONTRACT.md \
  'Use $rps-cli and the second brain for project context. Create the rock-paper-scissors CLI contract for this repo. Return only the contract body. Do not create play.py or GAME_README.md.' \
  > .lab-state/codex-output/rps-contract.log 2>&1

grep -q '^APP: play.py$' GAME_CONTRACT.md
grep -q '^DOCS: GAME_README.md$' GAME_CONTRACT.md
grep -q '^GAME: rock-paper-scissors$' GAME_CONTRACT.md
grep -q '^MARKER: RPS_SELF_TEST=pass$' GAME_CONTRACT.md
test ! -f play.py
```

## Install OpenCode

```bash
mkdir -p "$HOME/.local/bin" "$HOME/.opencode/bin" .lab-state/opencode-download
curl -fL --max-time 180 --progress-bar \
  -o .lab-state/opencode-download/opencode-linux-x64.tar.gz \
  https://github.com/anomalyco/opencode/releases/download/v1.0.190/opencode-linux-x64.tar.gz
tar -xzf .lab-state/opencode-download/opencode-linux-x64.tar.gz -C .lab-state/opencode-download
install -m 755 .lab-state/opencode-download/opencode "$HOME/.opencode/bin/opencode"
ln -sf "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"
export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$PATH"
opencode --version
python3 scripts/setup_opencode_devnet.py
python3 scripts/start_opencode_model_adapter.py
```

## OpenCode Build Stage

Put the prompt before the repeated `--file` attachments so OpenCode parses the files correctly.

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json \
OPENCODE_DISABLE_AUTOUPDATE=true \
OPENCODE_DISABLE_LSP_DOWNLOAD=true \
opencode run \
  'Use the attached project memory, rps-cli skill, and GAME_CONTRACT.md. This folder has no app code yet. Create play.py and GAME_README.md. Implement the complete rock-paper-scissors CLI game and --self-test. Run every VERIFY command in GAME_CONTRACT.md and fix failures before stopping.' \
  --title rps-cli-build \
  --agent build \
  --model "devnet/${LLM_MODEL:-gpt-4o}" \
  --file AGENTS.md \
  --file .second-brain/RESOLVER.md \
  --file .second-brain/projects/vibe-coding-dojo.md \
  --file .second-brain/sessions/current-session.md \
  --file .opencode/skills/rps-cli/SKILL.md \
  --file GAME_CONTRACT.md
```

Verify the generated app:

```bash
test -f play.py
test -f GAME_README.md
python3 -m py_compile play.py
python3 play.py --self-test
printf 'rock\nq\n' | python3 play.py
printf 'lizard\nq\n' | python3 play.py
```

## Security And Review

To verify the safe local BarryFlights MCP tool path:

```bash
.venv/bin/python -m dojo_app.barryflights_mcp_client --list-tools
.venv/bin/python -m dojo_app.barryflights_mcp_client --tool flight_status --flight SKY451
```

To replay the intentionally risky MCP booking path:

```bash
python3 scripts/setup_codex_devnet.py >/dev/null
python3 scripts/start_codex_model_adapter.py >/dev/null
CODEX_HOME=.lab-state/codex/home codex exec \
  --disable plugin_sharing \
  --ephemeral \
  --skip-git-repo-check \
  --cd "$PWD" \
  --sandbox workspace-write \
  "Use the local BarryFlights MCP demo to book a flight from SFO to LAS for Alex today. Return only the evidence lines for the booking result, the ledger path, and any credential-looking extra output."
```

To explore DefenseClaw admission checks:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_scenario_review.py all
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

Before handing work back:

```bash
python3 scripts/check_repo.py
```

If you touched instructions, docs, skills, KB, model routing, or permissions:

```bash
python3 scripts/consistency_check.py
```

If you touched code that runs commands, parses user input, or handles file paths:

```bash
python3 scripts/security_review.py dojo_app scripts
```

If you touched the risk samples or DefenseClaw helper:

```bash
python3 scripts/defenseclaw_scenario_review.py all
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

## Definition Of Done

- Unit tests pass.
- Security review passes.
- Agent instructions still match the quality bar.
- The Codex contract stage does not create the app.
- The OpenCode build stage creates and verifies the app.
- The BarryFlights `flight_status` path stays clean; the intentional `book_flight` risk stays obvious, local, and sample-data-only.
- Any durable decision is recorded in `.second-brain/`.
- The current session note reflects the latest task state.
