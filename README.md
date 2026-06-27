# Vibe Coding 101 Lab Helper

Helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI
2. connect Codex to the supplied DevNet model route
3. use the local BarryFlights MCP demo included with the dojo and check a flight status
4. create a small second brain that coding agents can share
5. ask Codex to create one tiny tic-tac-toe scenario, then verify it
6. attach OpenCode to the same KB and make tic-tac-toe playable
7. replay a risky MCP booking, then scan agent skills before trusting them

## Quick Start

```bash
cd /home/developer/src
if [ ! -d vibe-coding ]; then
  git clone https://github.com/barryqy/vibe-coding.git
else
  git -C vibe-coding pull --ff-only
fi
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

Then continue with the DevNet guide. The lab starts with Codex CLI, then brings in OpenCode later as a second tool to compare against the same rules.

## What Is Here

- `dojo_app/` is a tiny code dojo used for agent and security exercises.
- `dojo_app/tictactoe_game.py` is the stable tiny terminal tic-tac-toe app used during the lab. It checks a Codex-created scenario, renders the board, and dispatches play mode into `dojo_app/tictactoe_play.py`.
- `dojo_app/tictactoe_play.py` is the scoped OpenCode exercise file. It starts as a placeholder and becomes the playable human-vs-computer and human-vs-human loop.
- `dojo_app/barryflights_mcp_server.py` is the local BarryFlights MCP server. `flight_status` is the safe read-only lesson; `book_flight` is the intentionally risky security-module lesson.
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
- `scripts/agent_compare.py` builds one shared tiny-game task and shows how to hand it to Codex and OpenCode with the same repo rules.
- `scripts/install_defenseclaw_cli.sh` installs the pinned DefenseClaw CLI path used by the mini-module.
- `scripts/defenseclaw_scenario_review.py` reviews the prompt, privacy, generated-code, and MCP risk scenarios used in the DefenseClaw module.
- `scripts/defenseclaw_skill_demo.py` scans a malicious skill and a clean skill, then prints stable pass/fail markers.
- `scripts/ai_coach.py` uses the DevNet LLM proxy, Ollama, or another OpenAI-compatible endpoint when available, with a deterministic fallback when no model is configured.
- `AGENTS.md`, `opencode.json`, `CLAUDE.md`, and `.claude/settings.json` show repo-level ways to keep coding tools inside the same boundaries.
- `samples/guardrails/`, `samples/skills/`, and `samples/mcp/` contain the DefenseClaw scenario and admission-gate examples.
- `.second-brain/` is a small durable-memory starter for reusable decisions, project notes, cross-tool session notes, and the tic-tac-toe scenario pattern.

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

In a DevNet lab environment, Codex can use the built-in model route without a personal model key:

```bash
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
python3 scripts/setup_codex_devnet.py
python3 scripts/start_codex_model_adapter.py
CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."
```

Check the local BarryFlights tool that is included with the dojo:

```bash
python3 scripts/setup_codex_devnet.py >/dev/null
.venv/bin/python -m dojo_app.barryflights_mcp_client --list-tools
```

Ask Codex to check a flight through BarryFlights:

In the DevNet lab, Codex reaches the supplied model through the repo-local adapter. For this one status-check prompt, the adapter calls the local BarryFlights MCP client so the exercise has a stable tool result. The flight data is a demo dataset.

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

Later in the security module, replay the intentionally risky booking tool and inspect the fake AWS-style sample credential output:

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

Ask Codex to read the second brain, then create one small tic-tac-toe scenario:

```bash
mkdir -p .lab-state/codex-output
python3 scripts/setup_codex_devnet.py >/dev/null
python3 scripts/start_codex_model_adapter.py >/dev/null

CODEX_HOME=.lab-state/codex/home \
codex exec \
  --disable plugin_sharing \
  --ephemeral \
  --cd "$PWD" \
  --sandbox read-only \
  --output-last-message .lab-state/codex-output/tictactoe-scenario.txt \
  "Read the second brain for project context, then create one tic-tac-toe scenario for this repo.
Return only this format:
MODE: human-vs-computer
NEXT: X
BOARD:
. . .
. . .
. . ." \
  > .lab-state/codex-output/tictactoe-codex.log 2>&1

python3 -m dojo_app.tictactoe_game \
  --scenario-file .lab-state/codex-output/tictactoe-scenario.txt \
  --write-clean .lab-state/codex-output/tictactoe-scenario.txt \
  --check-only >/dev/null

cat .lab-state/codex-output/tictactoe-scenario.txt
python3 -m dojo_app.tictactoe_game --scenario-file .lab-state/codex-output/tictactoe-scenario.txt --check-only
python3 -m dojo_app.tictactoe_game --scenario-file .lab-state/codex-output/tictactoe-scenario.txt
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

Then let OpenCode read the same second brain and make tic-tac-toe playable:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json \
opencode run \
  --title tictactoe-playable \
  --agent build \
  --model devnet/gpt-4o \
  "Read the second brain for project context. Edit exactly one file: dojo_app/tictactoe_play.py. Keep the public entry point exactly named run_tictactoe(scenario). Replace the placeholder body with a terminal play loop. Support both scenario.mode values: human-vs-human and human-vs-computer. Use positions 1-9 for moves, q to quit, X and O turns, win detection, draw detection, and a simple computer move that wins if possible, blocks if needed, otherwise chooses center, a corner, then a side. Do not rename run_tictactoe, replace it with main, or move the play entry point into a class. After editing, run python3 -m py_compile dojo_app/tictactoe_game.py dojo_app/tictactoe_play.py and python3 -m dojo_app.tictactoe_game --check-play-interface. If either check fails, fix the code and run both checks again. Do not edit dojo_app/tictactoe_game.py, tests, config, or second-brain files. Do not add feature flags, external packages, network calls, credential reads, curses, or shell clear commands. Then stop." \
  --file dojo_app/tictactoe_play.py \
  --file .second-brain/sessions/current-session.md
```

Print the tiny tic-tac-toe scenario as a readable board:

```bash
python3 -m dojo_app.tictactoe_game
```

Inspect the scenario:

```bash
cat .lab-state/codex-output/tictactoe-scenario.txt
```

After the interactive change, play it:

```bash
python3 -m py_compile dojo_app/tictactoe_game.py dojo_app/tictactoe_play.py
python3 -m dojo_app.tictactoe_game --check-play-interface
printf 'q\n' | python3 -m dojo_app.tictactoe_game --scenario-file .lab-state/codex-output/tictactoe-scenario.txt --play
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

Install the pinned DefenseClaw CLI path, review the local scenario set, then scan one intentionally unsafe skill and one clean skill:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_scenario_review.py all
python3 scripts/defenseclaw_skill_demo.py
python3 scripts/defenseclaw_mcp_demo.py
```

The expected markers are:

```text
DEFENSECLAW_BAD_SKILL=blocked
DEFENSECLAW_CLEAN_SKILL=clean
DEFENSECLAW_MINI=pass
DEFENSECLAW_MCP=pass
```

You can also scan an intentionally leaky sample file:

```bash
python3 scripts/security_review.py samples/leaky_tictactoe_patch.py || true
```

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe samples under `samples/` are intentionally bad and exist only so scanners have something obvious to catch.
- The repo check is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
