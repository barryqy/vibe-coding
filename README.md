# Vibe Coding 101 Lab Helper

Student helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI
2. connect Codex to the supplied DevNet model route
3. use a live BarryFlights MCP demo to check flight status
4. install a clean local skill and build a tiny Snake game
5. compare OpenCode later on the same rules
6. scan credentials, PII, keys, and agent skills before trusting them
7. save useful decisions in a small second brain

## Quick Start

```bash
cd /home/developer/src
git clone https://github.com/barryqy/vibe-coding.git
cd vibe-coding
./scripts/setup_dojo.sh
```

Then continue with the DevNet guide. The lab starts with Codex CLI, then brings in OpenCode later as a second tool to compare against the same rules.

## What Is Here

- `dojo_app/` is a tiny code dojo used for agent and security exercises.
- `dojo_app/snake_game.py` is the tiny terminal game learners run and improve during the lab.
- `dojo_app/barrybot.py` is a legacy starter agent kept for optional follow-up experiments.
- `tests/` contains unit tests that prove the app still works.
- `scripts/check_repo.py` runs compile checks, unit tests, security review, and consistency checks.
- `scripts/security_review.py` catches risky code patterns that AI tools often introduce when prompts are too broad.
- `scripts/consistency_check.py` verifies the agent instructions and tool configs still point at the same quality bar.
- `scripts/tool_doctor.py` checks for Codex CLI, OpenCode, Ollama, DefenseClaw, and OpenAI-compatible model routes.
- `scripts/install_ai_tools.sh` installs Codex CLI, OpenCode, or both, depending on the flag you pass.
- `scripts/setup_codex_devnet.py` creates a repo-local Codex config for the DevNet model route.
- `scripts/start_codex_model_adapter.py` connects Codex to the lab model route.
- `scripts/start_opencode_model_adapter.py` connects OpenCode to the lab model route.
- `scripts/setup_opencode_devnet.py` configures OpenCode to use that local route when the DevNet model variables are present.
- `scripts/first_agent_result.py` runs a first beginner-friendly Codex, OpenCode, or optional Claude Code prompt.
- `scripts/agent_compare.py` builds one shared Snake-game planning task and shows how to hand it to Codex and OpenCode with the same repo rules.
- `scripts/install_defenseclaw_cli.sh` installs the pinned DefenseClaw CLI path used by the mini-module.
- `scripts/defenseclaw_skill_demo.py` scans a malicious skill and a clean skill, then prints stable pass/fail markers.
- `scripts/ai_coach.py` uses the DevNet LLM proxy, Ollama, or another OpenAI-compatible endpoint when available, with a deterministic fallback when no model is configured.
- `AGENTS.md`, `opencode.json`, `CLAUDE.md`, and `.claude/settings.json` show repo-level ways to keep coding tools inside the same boundaries.
- `samples/skills/` contains the DefenseClaw admission-gate examples.
- `.second-brain/` is a small durable-memory starter for reusable decisions and workflows.

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

Install Codex first:

```bash
./scripts/install_ai_tools.sh --codex-only
command -v codex
codex --version
```

In a DevNet lab environment, Codex can use the built-in model proxy and produce a first answer without a personal model key:

```bash
python3 scripts/setup_codex_devnet.py
python3 scripts/first_agent_result.py --tool codex
```

Later in the lab, install OpenCode and point it at the same model route for comparison:

```bash
./scripts/install_ai_tools.sh --opencode-only
python3 scripts/setup_opencode_devnet.py
python3 scripts/first_agent_result.py --tool opencode
```

Run the tiny Snake game:

```bash
python3 -m dojo_app.snake_game
```

After that, compare both agents with one shared prompt:

```bash
python3 scripts/agent_compare.py --tool both --show-rules
```

Claude Code remains optional for learners who already have sign-in on their own machine:

```bash
python3 scripts/first_agent_result.py --tool claude
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

You can also scan the intentionally leaky Snake sample:

```bash
python3 scripts/security_review.py samples/leaky_snake_patch.py || true
```

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe samples under `samples/` are intentionally bad and exist only so scanners have something obvious to catch.
- The repo check is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
