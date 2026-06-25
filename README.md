# Vibe Coding 101 Lab Helper

Helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI
2. connect Codex to the supplied DevNet model route
3. use the local BarryFlights MCP demo included with the dojo and check a flight status
4. create a small second brain that coding agents can share
5. ask Codex to use the second brain to find the MazeMaker MCP pattern, then verify the generated 12x12 Maze data
6. attach OpenCode to the same KB and make the Maze playable
7. replay a risky MCP booking, then scan agent skills before trusting them

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
- `dojo_app/maze_game.py` is the tiny terminal Maze game used during the lab. It can check raw maze data, render an Amaze-style terminal board, and keep `--render raw` for debugging the source maze data.
- `dojo_app/maze_mcp_server.py` is the local MazeMaker MCP server. `build_maze` creates a checked Recursive Backtracker maze and writes it to a repo-local file.
- `dojo_app/maze_mcp_client.py` calls that local MazeMaker MCP server over stdio.
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
- `scripts/agent_compare.py` builds one shared Maze planning task and shows how to hand it to Codex and OpenCode with the same repo rules.
- `scripts/install_defenseclaw_cli.sh` installs the pinned DefenseClaw CLI path used by the mini-module.
- `scripts/defenseclaw_skill_demo.py` scans a malicious skill and a clean skill, then prints stable pass/fail markers.
- `scripts/ai_coach.py` uses the DevNet LLM proxy, Ollama, or another OpenAI-compatible endpoint when available, with a deterministic fallback when no model is configured.
- `AGENTS.md`, `opencode.json`, `CLAUDE.md`, and `.claude/settings.json` show repo-level ways to keep coding tools inside the same boundaries.
- `samples/skills/` contains the DefenseClaw admission-gate examples.
- `.second-brain/` is a small durable-memory starter for reusable decisions, project notes, cross-tool session notes, and the MazeMaker MCP pattern.

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
.venv/bin/python -m dojo_app.barryflights_mcp_client \
  --tool book_flight \
  --traveler-name Alex \
  --origin SFO \
  --destination LAS \
  --date today
```

Ask Codex to read the second brain, then check and render the Amaze-style terminal board:

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
  --output-last-message .lab-state/codex-output/maze-mcp.txt \
  "Read the second brain for project context, then create the next Maze artifact for this repo.
Save the maze to .lab-state/codex-output/maze.txt.
Return only the tool result." \
  > .lab-state/codex-output/maze-codex.log 2>&1

cat .lab-state/codex-output/maze-mcp.txt
echo

if ! grep -q '^MAZE_MCP=pass$' .lab-state/codex-output/maze-mcp.txt || [ ! -f .lab-state/codex-output/maze.txt ]; then
  echo "Codex did not return a MazeMaker result. Running the second-brain MazeMaker pattern now."
  .venv/bin/python -m dojo_app.maze_mcp_client \
    --maze-file .lab-state/codex-output/maze.txt \
    > .lab-state/codex-output/maze-mcp.txt
  cat .lab-state/codex-output/maze-mcp.txt
  echo
fi

grep -q '^MAZE_MCP=pass$' .lab-state/codex-output/maze-mcp.txt
test -f .lab-state/codex-output/maze.txt

python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --check-only

python3 -m dojo_app.maze_game \
  --maze-file .lab-state/codex-output/maze.txt \
  --render amaze
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

Then let OpenCode read the same second brain and make the Maze playable:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json \
opencode run \
  --title maze-interactive \
  --agent build \
  --model devnet/gpt-4o \
  "Read the second brain for project context. Make the Maze interactive so I can play it in the terminal. Keep the change small and use the existing play-mode path. Do not add external packages, network calls, credential reads, curses, or shell clear commands. Then stop." \
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
python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --play
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

You can also scan an intentionally leaky sample file:

```bash
python3 scripts/security_review.py samples/leaky_maze_patch.py || true
```

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe samples under `samples/` are intentionally bad and exist only so scanners have something obvious to catch.
- The repo check is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
