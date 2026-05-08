# Tool Options

The lab keeps the tool choice flexible:

## Claude Code

Claude Code is a terminal coding agent with project memory, permissions, hooks, MCP support, and non-interactive CLI modes. It is a strong fit when a learner already has Anthropic access and wants a polished commercial coding-agent workflow.

In this dojo, the Claude Code path uses:

- `./scripts/install_ai_tools.sh` to install the CLI with the official shell installer
- `python3 scripts/verify_ai_tools.py` to show the version and sign-in state
- `CLAUDE.md` for project guidance
- `.claude/settings.json` for project-level permission examples
- `python3 scripts/first_agent_result.py --tool claude` for a first plan-only run when Claude Code is authenticated
- `claude -p --permission-mode plan --max-turns 1 "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a plan-only comparison pass

Useful official docs:

- `https://code.claude.com/docs/en/setup`
- `https://code.claude.com/docs/en/cli-reference`
- `https://code.claude.com/docs/en/commands`
- `https://code.claude.com/docs/en/settings`
- `https://code.claude.com/docs/en/memory`
- `https://code.claude.com/docs/en/security`

## OpenCode

OpenCode is an open source coding agent with terminal, desktop, and IDE options. It supports many providers, local models, project rules through `AGENTS.md`, and permission controls through `opencode.json`.

In this dojo, the OpenCode path uses:

- `./scripts/install_ai_tools.sh` to install the CLI with the official shell installer
- `python3 scripts/verify_ai_tools.py` to show the version and credential state
- `python3 scripts/setup_opencode_devnet.py` to generate a local OpenAI-compatible provider config when the DevNet model route is available
- `python3 scripts/devnet_openai_shim.py --ensure` to start the local shim OpenCode streams from in the lab environment
- `python3 scripts/first_agent_result.py --tool opencode` for a first visible answer from OpenCode
- `python3 scripts/agent_code_task.py --tool opencode` for a real Build-mode patch in the dojo
- `AGENTS.md` for shared project guidance
- `opencode.json` for instruction-file and permission examples
- `opencode run --title vibe-coding-quality-loop --agent plan --file AGENTS.md --file docs/quality-bar.md "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a non-interactive comparison pass

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

Use OpenCode with the DevNet model proxy for the first lab result when available. Use Claude Code when the learner has signed in with their own Claude Code access. Keep deterministic gates as the required verification path, then use `scripts/agent_compare.py` to compare both tools on the same scoped task.
