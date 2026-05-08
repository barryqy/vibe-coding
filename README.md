# Vibe Coding 101 Lab Helper

Student helper repo for the DevNet lab **AI Tool Training - Vibe Coding 101**.

The lab teaches a practical loop for AI-assisted coding:

1. give the agent real project context
2. keep edits small enough to review
3. run quality and security checks every time
4. save useful decisions in a small second brain
5. use a local or hosted model only when it improves the loop

## Quick Start

```bash
cd /home/developer/src
git clone https://github.com/barryqy/vibe-coding.git
cd vibe-coding
./scripts/setup_dojo.sh
```

Then continue with the DevNet guide.

## What Is Here

- `dojo_app/` is a tiny task tracker used for code-quality exercises.
- `tests/` contains unit tests that prove the app still works.
- `scripts/quality_gate.py` runs compile checks, unit tests, security review, and consistency checks.
- `scripts/security_review.py` catches risky code patterns that AI tools often introduce when prompts are too broad.
- `scripts/consistency_check.py` verifies the agent instructions and tool configs still point at the same quality bar.
- `scripts/tool_doctor.py` checks for Claude Code, OpenCode, Ollama, and OpenAI-compatible model routes.
- `scripts/agent_compare.py` builds one shared coding task and shows how to hand it to Claude Code and OpenCode with the same repo rules.
- `scripts/ai_coach.py` uses the DevNet LLM proxy, Ollama, or another OpenAI-compatible endpoint when available, with a deterministic fallback when no model is configured.
- `.claude/settings.json`, `CLAUDE.md`, `AGENTS.md`, and `opencode.json` show one repo-level way to keep AI coding tools inside the same boundaries.
- `.second-brain/` is a small durable-memory starter for reusable decisions and workflows.

## Optional Model Routes

The lab works without a model account. If you want the optional AI coach to call a real model, use one of these routes:

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

## Compare Claude Code and OpenCode

The DevNet pod may not have either CLI installed, but you can still create the shared prompt and see the exact commands:

```bash
python3 scripts/agent_compare.py --tool both --show-rules
```

On a machine where the tools are installed and authenticated, this runs a plan-only/read-only pass:

```bash
python3 scripts/agent_compare.py --tool claude --run
python3 scripts/agent_compare.py --tool opencode --run
```

## Safety Notes

- Do not put real secrets in this repo.
- The unsafe sample under `samples/` is intentionally bad and exists only so the scanner has something obvious to catch.
- The quality gate is deliberately simple. It is a teaching harness, not a replacement for a full CI system.
