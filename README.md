# Vibe Coding 101 Lab Helper

Helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

Full lab is available at https://cs.co/vc

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI from the package preloaded in the DevNet image
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
./scripts/setup_dojo.sh
./scripts/install_codex_cli.sh
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
codex --version
```

Then continue with the DevNet guide. The lab starts with Codex CLI, then brings in OpenCode later as a second tool to compare against the same rules.

## What Is Here

- `dojo_app/` is a tiny code dojo used for agent and security exercises.
- `dojo_app/maze_game.py` is the stable tiny terminal Maze app used during the lab. It can check raw maze data, render an Amaze-style terminal board, keep `--render raw` for debugging the source maze data, and dispatch play mode into `dojo_app/maze_play.py`.
- `dojo_app/maze_play.py` is the scoped OpenCode exercise file. It starts as a placeholder and becomes the playable movement loop.
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
- `bin/dojo-linux-x86_64` is the stripped challenge CLI binary. It verifies fresh ordered evidence before clearing the terminal for a flag celebration; its private Rust source is maintained outside this public helper repo.
- `config/dojo-event.toml` selects the leaderboard event. The normal lab uses `self-paced`; event builds may replace it with a short event code.
- `scripts/player` is installed as `player` and prints the assigned leaderboard name.
- `scripts/tool_doctor.py` is an optional diagnostic for Codex CLI, OpenCode, Ollama, DefenseClaw, and model routes.
- `scripts/install_codex_cli.sh` and `scripts/install_opencode_cli.sh` install verified packages already staged in the DevNet image, without live downloads.
- `scripts/install_ai_tools.sh` is an optional network fallback for development outside the DevNet image.
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

The setup script installs `dojo` into `~/.local/bin`, assigns a unique player name, and joins the self-paced leaderboard. Player names cannot be changed. Use `player` to recall the assigned name, or run `dojo challenges`, `dojo status`, or `dojo leaderboard` at any point.

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

The DevNet image includes the official standalone package. Install it into your lab home without downloading it again:

```bash
./scripts/install_codex_cli.sh
export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
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
./scripts/install_opencode_cli.sh
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
  --agent maze-editor \
  --model "devnet/${LLM_MAZE_MODEL:-${LLM_MODEL:-gpt-5-nano}}" \
  "Search only this repo's .second-brain/ for the Maze play movement pattern, then implement w/a/s/d movement in the attached dojo_app/maze_play.py. Edit only choose_next_position and follow the memory rules for MOVE_DELTAS, walls, bounds, invalid keys, and verification. Run the movement verifier and compile check from the maze-editor contract. If a check fails, edit from its diagnostics before rerunning it; never rerun an unchanged failing check. Use real Python line breaks, not literal backslash-n text. Report MAZE_EDIT_OK only after both checks pass; otherwise report MAZE_EDIT_FAILED with the last failing check." \
  --file dojo_app/maze_play.py
```

The Maze command prefers `LLM_MAZE_MODEL`, then falls back to `LLM_MODEL`. The learner flow makes one attempt by default. Controlled evaluations can set `MAZE_MAX_ATTEMPTS=2` and `MAZE_RETRY_MODEL` for one repair attempt, but only after the external movement verifier or compile check fails.

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

Reach `E` to record the win, inspect the solved Maze, then run the separate flag-capture step for the terminal celebration.

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

The controlled context-attack exercise uses `scripts/run_context_attack.sh`.
It returns success only after the disclosure evidence is observed. A semantic
`check-output` result gets one retry with a sanitized pod-specific session hint;
empty responses and rate-limit, provider, budget, timeout, or configuration
failures do not. The first request stays identical across learners so the normal
cached workload is preserved.

Codex uses `LLM_MODEL` as its default. If `LLM_KEY_MODELS` advertises additional
aliases, `codex exec --model <alias>` can select one for a task; the local
adapter rejects unlisted aliases and forwards an approved alias unchanged. Its
readiness check also fingerprints the routing environment so setup restarts an
adapter that still has stale model, key, URL, or output-limit settings.
`LLM_CONTEXT_ATTACK_MODEL` applies an approved alias only to the controlled
context-attack task.

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
