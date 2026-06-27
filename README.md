# Vibe Coding 101 Lab Helper

Helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI
2. connect Codex to the supplied DevNet model route
3. use the local BarryFlights MCP demo and check a flight status
4. create shared KB notes in `.second-brain/`
5. use a documented Codex project skill to create `GAME_CONTRACT.md`
6. attach OpenCode to the same KB and skill context, then build `play.py`
7. inspect risky Skills, generated code, and MCP responses before trusting them

The main game is not prebuilt. Codex writes the contract; OpenCode writes the app.

## Quick Start

```bash
cd /home/developer/src
git clone https://github.com/barryqy/vibe-coding.git
cd vibe-coding
python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
if curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh; then
  CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh
else
  npm config set prefix "$HOME/.local"
  npm install -g @openai/codex
fi
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
codex --version
```

Then continue with the DevNet guide. The lab starts with Codex CLI, then brings in OpenCode as a second tool using the same rules and memory.

## What Is Here

- `dojo_app/barryflights_mcp_server.py` is the local BarryFlights MCP server. `flight_status` is safe and read-only; `book_flight` is intentionally risky and returns fake AWS-style sample output for the security module.
- `dojo_app/barryflights_mcp_client.py` calls that MCP server over stdio.
- `.agents/skills/rps-cli/SKILL.md` is the Codex project skill for the contract stage.
- `.opencode/skills/rps-cli/SKILL.md` is the OpenCode project skill for the build stage.
- `.second-brain/` is the repo-local KB for shared project memory.
- `.second-brain/patterns/rps-cli.md` records the contract-to-build pattern.
- `GAME_CONTRACT.md`, `play.py`, and `GAME_README.md` are created during the lab and are not committed.
- `scripts/check_repo.py` runs compile checks, unit tests, security review, and consistency checks.
- `scripts/setup_codex_devnet.py` creates a repo-local Codex config for the DevNet model route and BarryFlights MCP server.
- `scripts/setup_opencode_devnet.py` creates a repo-local OpenCode provider config for the DevNet model route and shared KB files.
- `scripts/model_usage.py` is exposed as `usage` during setup. It shows token counts recorded by the local Codex and OpenCode adapters, plus any hard budget details the lab model route reports.
- `samples/guardrails/`, `samples/skills/`, `samples/mcp/`, and `samples/leaky_rps_patch.py` contain the DefenseClaw scenario and admission-gate examples.
- `AGENTS.md`, `opencode.json`, `CLAUDE.md`, and `.claude/settings.json` show repo-level ways to keep coding tools inside the same boundaries.

## Codex Contract

```bash
python3 scripts/setup_codex_devnet.py
python3 scripts/start_codex_model_adapter.py
usage
rm -f GAME_CONTRACT.md play.py

CODEX_HOME=.lab-state/codex/home \
codex exec \
  --disable plugin_sharing \
  --ephemeral \
  --cd "$PWD" \
  --sandbox read-only \
  --output-last-message GAME_CONTRACT.md \
  'Use $rps-cli and the second brain for project context. Create the rock-paper-scissors CLI contract for this repo. Return only the contract body. Do not create play.py or GAME_README.md.'

grep -q '^APP: play.py$' GAME_CONTRACT.md
grep -q '^DOCS: GAME_README.md$' GAME_CONTRACT.md
grep -q '^MARKER: RPS_SELF_TEST=pass$' GAME_CONTRACT.md
test ! -f play.py
usage
```

## OpenCode Build

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
usage

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

test -f play.py
test -f GAME_README.md
python3 -m py_compile play.py
python3 play.py --self-test
printf 'rock\nq\n' | python3 play.py
printf 'lizard\nq\n' | python3 play.py
usage
```

## Security Checks

```bash
python3 scripts/check_repo.py
python3 scripts/defenseclaw_scenario_review.py all
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

## Optional Model Routes

The deterministic checks work without a personal model account. If you want the optional AI coach to call a real model, use one of these routes:

```bash
export VIBE_LLM_BASE_URL="http://127.0.0.1:11434/v1"
export VIBE_LLM_MODEL="llama3.2"
export VIBE_LLM_API_KEY="ollama"
```

or:

```bash
export VIBE_LLM_BASE_URL="https://api.openai.com/v1"
export VIBE_LLM_MODEL="gpt-4o-mini"
export VIBE_LLM_API_KEY="your-api-key"
```

In the DevNet lab image, the helper also checks the built-in `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` variables.
