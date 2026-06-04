# Vibe Coding 101 Lab Helper

Student helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. install Codex CLI and OpenCode
2. get a first visible result from a coding agent
3. give the agent real project context
4. keep edits small enough to review
5. run quality and security checks before trusting the result
6. scan agent skills before trusting them
7. save useful decisions in a small second brain

## Quick Start

```bash
cd /home/developer/src
git clone https://github.com/barryqy/vibe-coding.git
cd vibe-coding
./scripts/setup_dojo.sh
```

Then continue with the DevNet guide. The lab walks through installing Codex CLI and OpenCode before it asks you to compare them.

## What Is Here

- `dojo_app/` is a tiny task tracker used for code-quality exercises.
- `tests/` contains unit tests that prove the app still works.
- `scripts/quality_gate.py` runs compile checks, unit tests, security review, and consistency checks.
- `scripts/security_review.py` catches risky code patterns that AI tools often introduce when prompts are too broad.
- `scripts/consistency_check.py` verifies the agent instructions and tool configs still point at the same quality bar.
- `scripts/tool_doctor.py` checks for Codex CLI, OpenCode, Ollama, DefenseClaw, and OpenAI-compatible model routes.
- `scripts/install_ai_tools.sh` installs Codex CLI and OpenCode with their official install scripts.
- `scripts/verify_ai_tools.py` shows versions and credential state.
- `scripts/setup_codex_devnet.py` creates a repo-local Codex config for the DevNet model route.
- `scripts/devnet_codex_shim.py` gives Codex a local Responses API route backed by the DevNet Learning Lab LLM proxy.
- `scripts/devnet_openai_shim.py` gives OpenCode a local OpenAI-compatible route backed by the same proxy.
- `scripts/setup_opencode_devnet.py` configures OpenCode to use that local route when the DevNet model variables are present.
- `scripts/first_agent_result.py` runs a first beginner-friendly Codex, OpenCode, or optional Claude Code prompt.
- `scripts/agent_compare.py` builds one shared coding task and shows how to hand it to Codex and OpenCode with the same repo rules.
- `scripts/agent_code_task.py` lets Codex or OpenCode make a real small patch, then shows the diff and reruns the repo check.
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

## Install and Use Codex CLI and OpenCode

Install the tools first:

```bash
./scripts/install_ai_tools.sh
python3 scripts/verify_ai_tools.py
```

In a DevNet lab environment, Codex can use the built-in model proxy and produce a first answer without a personal model key:

```bash
python3 scripts/setup_codex_devnet.py
python3 scripts/first_agent_result.py --tool codex
```

OpenCode can use the same model route for comparison:

```bash
python3 scripts/setup_opencode_devnet.py
python3 scripts/first_agent_result.py --tool opencode
```

After that first result, compare both agents with one shared prompt:

```bash
python3 scripts/agent_compare.py --tool both --show-rules
```

Then let Codex make a real patch in the dojo:

```bash
python3 scripts/agent_code_task.py --tool codex
git diff -- dojo_app/tasks.py tests/test_tasks.py
```

From a fresh clone or after resetting the two dojo files, OpenCode can run the same patch:

```bash
python3 scripts/agent_code_task.py --tool opencode
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

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe sample under `samples/` is intentionally bad and exists only so the scanner has something obvious to catch.
- The repo check is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
