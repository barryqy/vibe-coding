# Tool Options

The lab keeps the tool choice flexible:

## Claude Code

Claude Code is a terminal coding agent with project memory, permissions, hooks, MCP support, and non-interactive CLI modes. It is a strong fit when a learner already has Anthropic access and wants a polished commercial coding-agent workflow.

In this dojo, the Claude Code path uses:

- `CLAUDE.md` for project guidance
- `.claude/settings.json` for project-level permission examples
- `claude -p --permission-mode plan --max-turns 1 "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a plan-only comparison pass

Useful official docs:

- `https://code.claude.com/docs/en/cli-reference`
- `https://code.claude.com/docs/en/commands`
- `https://code.claude.com/docs/en/settings`
- `https://code.claude.com/docs/en/memory`
- `https://code.claude.com/docs/en/security`

## OpenCode

OpenCode is an open source coding agent with terminal, desktop, and IDE options. It supports many providers, local models, project rules through `AGENTS.md`, and permission controls through `opencode.json`.

In this dojo, the OpenCode path uses:

- `AGENTS.md` for shared project guidance
- `opencode.json` for instruction-file and permission examples
- `opencode run --title vibe-coding-quality-loop --file AGENTS.md --file docs/quality-bar.md "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a non-interactive comparison pass

Useful official docs:

- `https://opencode.ai/docs/`
- `https://opencode.ai/docs/cli/`
- `https://opencode.ai/docs/providers/`
- `https://opencode.ai/docs/rules/`
- `https://opencode.ai/docs/permissions/`

## Local Models

Local models are useful for privacy, demos, and cost control. They are not always available in a DevNet lab container, so this repo treats them as optional.

Useful official docs:

- `https://docs.ollama.com/api/openai-compatibility`
- `https://lmstudio.ai/docs/developer`

## Recommendation for This Lab

Use deterministic gates as the default path. Use `scripts/agent_compare.py` to compare Claude Code and OpenCode on the same scoped task. Add an LLM coach when a DevNet proxy, Ollama, LM Studio, or another OpenAI-compatible endpoint is available.
