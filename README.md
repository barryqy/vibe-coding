# Vibe Coding 101 Lab Helper

Helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI
2. connect Codex to the supplied DevNet model route
3. install the local BarryFlights MCP demo with Codex CLI and book a demo flight
4. create a small second brain that Codex and OpenCode can both read
5. ask Codex to generate 12x12 Maze data, then render it as a tile board
6. attach OpenCode to the same KB and unlock the Maze play mode
7. scan credentials, PII, keys, and agent skills before trusting them

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
export PATH="$HOME/.local/bin:$PATH"
codex_bwrap="$HOME/.codex/packages/standalone/current/codex-resources/bwrap"
if command -v bwrap >/dev/null 2>&1; then
  echo "CODEX_SANDBOX_HELPER=system"
elif [ -x "$codex_bwrap" ]; then
  ln -sf "$codex_bwrap" "$HOME/.local/bin/bwrap"
  echo "CODEX_SANDBOX_HELPER=bundled-codex"
else
  echo "CODEX_SANDBOX_HELPER=not-found"
fi
codex --version
```

Then continue with the DevNet guide. The lab starts with Codex CLI, then brings in OpenCode later as a second tool to compare against the same rules.

## What Is Here

- `dojo_app/` is a tiny code dojo used for agent and security exercises.
- `dojo_app/maze_game.py` is the tiny terminal Maze game used during the lab. It renders a tile board by default and keeps `--render raw` for debugging the source maze data.
- `dojo_app/barryflights_mcp_server.py` is the local BarryFlights MCP server used for the first tool-call lesson.
- `dojo_app/barryflights_mcp_client.py` calls that local MCP server over stdio.
- `dojo_app/barrybot.py` is a legacy starter agent kept for optional follow-up experiments.
- `tests/` contains unit tests that prove the app still works.
- `scripts/check_repo.py` runs compile checks, unit tests, security review, and consistency checks.
- `scripts/security_review.py` catches risky code patterns that AI tools often introduce when prompts are too broad.
- `scripts/consistency_check.py` verifies the agent instructions and tool configs still point at the same quality bar.
- `scripts/setup_dojo.sh` creates the tiny local state folders if you want a quick repo reset point.
- `scripts/tool_doctor.py` is an optional diagnostic for Codex CLI, OpenCode, Ollama, DefenseClaw, and model routes.
- `scripts/install_ai_tools.sh` is an optional fallback installer. The DevNet guide shows the direct Codex and OpenCode install commands first.
- `scripts/setup_codex_devnet.py` creates a repo-local Codex config for the DevNet model route.
- `scripts/start_codex_model_adapter.py` connects Codex to the lab model route.
- `scripts/start_opencode_model_adapter.py` connects OpenCode to the lab model route.
- `scripts/setup_opencode_devnet.py` configures OpenCode to use that local route when the DevNet model variables are present.
- `scripts/first_agent_result.py` is a legacy optional helper for comparing first prompts.
- `scripts/agent_compare.py` builds one shared Maze planning task and shows how to hand it to Codex and OpenCode with the same repo rules.
- `scripts/install_defenseclaw_cli.sh` installs the pinned DefenseClaw CLI path used by the mini-module.
- `scripts/defenseclaw_skill_demo.py` scans a malicious skill and a clean skill, then prints stable pass/fail markers.
- `scripts/ai_coach.py` uses the DevNet LLM proxy, Ollama, or another OpenAI-compatible endpoint when available, with a deterministic fallback when no model is configured.
- `AGENTS.md`, `opencode.json`, `CLAUDE.md`, and `.claude/settings.json` show repo-level ways to keep coding tools inside the same boundaries.
- `samples/skills/` contains the DefenseClaw admission-gate examples.
- `.second-brain/` is a small durable-memory starter for reusable decisions, project notes, and cross-tool session notes.

## Optional Model Routes

The deterministic checks work without a model account. If you want the optional AI coach to call a real model, use one of these routes:

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

## Install and Use Codex CLI First

Install Codex first with the official standalone installer:

```bash
if curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh; then
  CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh
else
  npm config set prefix "$HOME/.local"
  npm install -g @openai/codex
fi
export PATH="$HOME/.local/bin:$PATH"
codex_bwrap="$HOME/.codex/packages/standalone/current/codex-resources/bwrap"
if command -v bwrap >/dev/null 2>&1; then
  echo "CODEX_SANDBOX_HELPER=system"
elif [ -x "$codex_bwrap" ]; then
  ln -sf "$codex_bwrap" "$HOME/.local/bin/bwrap"
  echo "CODEX_SANDBOX_HELPER=bundled-codex"
else
  echo "CODEX_SANDBOX_HELPER=not-found"
fi
codex --version
```

In a DevNet lab environment, Codex can use the built-in model route without a personal model key:

```bash
python3 scripts/setup_codex_devnet.py
python3 scripts/start_codex_model_adapter.py
CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."
```

Install the local BarryFlights MCP server with Codex CLI:

```bash
CODEX_HOME=.lab-state/codex/home \
codex mcp add barryflights -- \
  "$PWD/.venv/bin/python" "$PWD/dojo_app/barryflights_mcp_server.py"

CODEX_HOME=.lab-state/codex/home codex mcp list | sed -n '1,20p'
```

Ask Codex to book a demo flight through BarryFlights:

```bash
CODEX_HOME=.lab-state/codex/home \
codex exec \
  --cd "$PWD" \
  --sandbox workspace-write \
  "Use the local BarryFlights MCP demo to book a demo flight from SFO to LAS for Alex on Friday."
```

Later in the lab, install OpenCode and point it at the same model route for comparison:

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

Then let OpenCode read the same second brain and unlock the Maze play mode:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json \
opencode run \
  --title maze-interactive \
  --agent build \
  --model devnet/gpt-4o \
  "Read the second brain and implement only the OpenCode Next Task. Keep the change small. Do not remove existing functions. Do not run shell commands during the edit; I will run the checks next." \
  --file dojo_app/maze_game.py \
  --file .second-brain/sessions/current-session.md
```

Print the tiny Maze as a readable board:

```bash
python3 -m dojo_app.maze_game
```

Inspect the raw maze data:

```bash
python3 -m dojo_app.maze_game --render raw
```

After the interactive change, play it:

```bash
python3 -m dojo_app.maze_game --play
```

After that, compare both agents with one shared prompt:

```bash
python3 scripts/agent_compare.py --tool both --show-rules
```

Claude Code remains optional when you already have sign-in on your own machine:

```bash
claude "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."
```

## Explore DefenseClaw

Install the pinned DefenseClaw CLI path, then scan one intentionally unsafe skill and one clean skill:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_skill_demo.py
```

The expected markers are:

```text
DEFENSECLAW_BAD_SKILL=blocked
DEFENSECLAW_CLEAN_SKILL=clean
DEFENSECLAW_MINI=pass
```

You can also scan the intentionally leaky Maze sample:

```bash
python3 scripts/security_review.py samples/leaky_maze_patch.py || true
```

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe samples under `samples/` are intentionally bad and exist only so scanners have something obvious to catch.
- The repo check is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
