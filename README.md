# Vibe Coding 101 Lab Helper

Helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

Full lab is available at https://cs.co/vc

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI
2. connect Codex to the supplied DevNet model route
3. use the local BarryFlights MCP demo included with the dojo and check a flight status
4. create a small second brain that coding agents can share
5. ask Codex to use the second brain to find the MazeMaker skill, then verify the generated 12x12 Maze data
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
- `dojo_app/maze_game.py` is the stable tiny terminal Maze app used during the lab. It can check raw maze data, render an Amaze-style terminal board, keep `--render raw` for debugging the source maze data, and dispatch play mode into `dojo_app/maze_play.py`.
- `dojo_app/maze_play.py` is the scoped OpenCode exercise file. It starts as a placeholder and becomes the playable movement loop.
- `dojo_app/cli_confetti.py` provides the dependency-free terminal celebration shown after a solved Maze, inspired by [cli-confetti](https://github.com/IonicaBizau/cli-confetti).
- `skills/mazemaker/SKILL.md` is the repo-local MazeMaker skill used to create checked Maze artifacts.
- `skills/mazemaker/scripts/build_maze.py` writes solvable Recursive Backtracker maze data to a repo-local file.
- `dojo_app/barryflights_mcp_server.py` is the local BarryFlights MCP server. `flight_status` is the safe read-only lesson; `book_flight` is the intentionally risky security-module lesson.
- `dojo_app/barryflights_mcp_client.py` calls that local MCP server over stdio.
- `dojo_app/barrybot.py` is a legacy starter agent kept for optional follow-up experiments.
- `tests/` contains unit tests that prove the app still works.
- `scripts/check_repo.py` runs compile checks, unit tests, security review, and consistency checks.
- `scripts/security_review.py` catches risky code patterns that AI tools often introduce when prompts are too broad.
- `scripts/consistency_check.py` verifies the agent instructions and tool configs still point at the same quality bar.
- `scripts/setup_dojo.sh` initializes dependencies, local state, and the repo-local Codex model route.
- `bin/dojo-linux-x86_64` is the stripped challenge CLI binary. Its private Rust source is maintained outside this public helper repo.
- `config/dojo-event.toml` selects the leaderboard event; without that file, the CLI uses `self-paced`.
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
- `AGENTS.md`, `opencode.json`, and `CLAUDE.md` show repo-level ways to keep coding tools inside the same boundaries.
- `samples/guardrails/`, `samples/skills/`, and `samples/mcp/` contain the DefenseClaw scenario and admission-gate examples.
- `.second-brain/` is a small durable-memory starter for reusable decisions, project notes, cross-tool session notes, and the MazeMaker skill pattern.

The setup script installs `dojo` into `~/.local/bin`, assigns a unique player name, and joins the configured event. Use `dojo challenges`, `dojo status`, or `dojo leaderboard` at any point. A custom public name can be selected with `dojo join --name NAME`.

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

In a DevNet lab environment, the initial dojo setup connects Codex to the built-in model route without a personal model key:

```bash
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."
```

Check the local BarryFlights tool that is included with the dojo:

```bash
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
CODEX_HOME=.lab-state/codex/home codex exec \
  --disable plugin_sharing \
  --ephemeral \
  --skip-git-repo-check \
  --cd "$PWD" \
  --sandbox workspace-write \
  "Use the local BarryFlights MCP demo to book a flight from SFO to LAS for Alex today. Return only the evidence lines for the booking result, the ledger path, and any credential-looking extra output."
```

Ask Codex to search the second brain, then check and render the Amaze-style terminal board:

```bash
mkdir -p .lab-state/codex-output

CODEX_HOME=.lab-state/codex/home \
codex exec \
  --disable plugin_sharing \
  --ephemeral \
  --cd "$PWD" \
  --sandbox read-only \
  --output-last-message .lab-state/codex-output/mazemaker-skill.txt \
  "Search .second-brain/ for project context, then create the next Maze artifact for this repo.
Save the maze to .lab-state/codex-output/maze.txt.
Return only the skill result." \
  > .lab-state/codex-output/maze-codex.log 2>&1

if [ -s .lab-state/codex-output/mazemaker-skill.txt ]; then
  cat .lab-state/codex-output/mazemaker-skill.txt
  echo
fi

grep -q '^MAZEMAKER_SKILL=pass$' .lab-state/codex-output/mazemaker-skill.txt
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

Then let OpenCode search the same second brain and make the Maze playable:

```bash
OPENCODE_CONFIG=.lab-state/opencode-devnet.json \
opencode run \
  --title maze-interactive \
  --agent build \
  --model "devnet/${LLM_MODEL:-gpt-5-nano}" \
  "Search .second-brain/ for Maze play context, then update dojo_app/maze_play.py so w/a/s/d movement works. Keep the change scoped to choose_next_position. Follow the repo memory for walls, bounds, invalid keys, and verification. Use OpenCode file tools for the search; reserve Bash for the verifier and compile check. If an edit reports oldString not found, re-read the file and retry with the exact current text. Do not stop until the movement verifier and compile check both pass." \
  --file dojo_app/maze_play.py
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
python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py
python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --play
```

Reach `E` to trigger the terminal confetti celebration.

After that, compare both agents with one shared prompt:

```bash
python3 scripts/agent_compare.py --tool both --show-rules
```

Claude Code remains optional when you already have sign-in on your own machine:

```bash
claude "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."
```

## Darkside of AI

Run the local risk demos first so the bad outcomes are visible:

```bash
python3 scripts/run_darkside_code_demo.py
python3 scripts/run_risky_skill_demo.py
python3 scripts/run_risky_mcp_demo.py
```

Then install the pinned DefenseClaw CLI path and scan one intentionally unsafe skill, one clean skill, and the malicious MCP server:

```bash
./scripts/install_defenseclaw_cli.sh
python3 scripts/defenseclaw_skill_demo.py
bash scripts/run_defenseclaw_mcp_demo.sh
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
python3 scripts/security_review.py samples/leaky_maze_patch.py || true
```

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe samples under `samples/` are intentionally bad and exist only so scanners have something obvious to catch.
- The repo check is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
