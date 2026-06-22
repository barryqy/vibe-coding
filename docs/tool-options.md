# Tool Options

The lab keeps the tool choice flexible, but the required DevNet path avoids personal model accounts.

## Codex CLI

Codex CLI is the required account-free replacement for the old Claude Code lab path. The dojo gives Codex a repo-local `CODEX_HOME` and a tiny model adapter, so it can talk to the DevNet Learning Lab LLM proxy instead of asking each student to sign in.

In this dojo, the Codex path uses:

- `./scripts/install_ai_tools.sh --codex-only` to install the CLI with the official shell installer or pinned fallback
- `command -v codex && codex --version` to confirm Codex is installed
- `python3 scripts/setup_codex_devnet.py` to generate `.lab-state/codex/home/config.toml`
- `python3 scripts/start_codex_model_adapter.py` to start the local model adapter
- `python3 scripts/first_agent_result.py --tool codex` for a first visible answer from Codex
- `python3 scripts/agent_code_task.py --tool codex` to build BarryBot in the dojo
- `python3 scripts/barrybot_demo.py --prompt "What should I check before trusting generated code?"` to run the mini-agent
- `AGENTS.md` for shared project guidance
- `CODEX_HOME=.lab-state/codex/home codex exec --disable plugin_sharing --ephemeral --sandbox read-only "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a non-interactive comparison pass

Useful official docs:

- `https://developers.openai.com/codex/`

## OpenCode

OpenCode is an open source coding agent with terminal, desktop, and IDE options. It supports many providers, local models, project rules through `AGENTS.md`, and permission controls through `opencode.json`.

In this dojo, the OpenCode path uses:

- `./scripts/install_ai_tools.sh --opencode-only` to install the CLI with the official shell installer
- `command -v opencode && opencode --version` to confirm OpenCode is installed
- `python3 scripts/setup_opencode_devnet.py` to generate a local OpenAI-compatible provider config when the DevNet model route is available
- `python3 scripts/start_opencode_model_adapter.py` to start the local shim OpenCode streams from in the lab environment
- `python3 scripts/first_agent_result.py --tool opencode` for a first visible answer from OpenCode
- `python3 scripts/agent_code_task.py --tool opencode` for the same BarryBot build when you want a comparison run
- `AGENTS.md` for shared project guidance
- `opencode.json` for instruction-file and permission examples
- `opencode run --title vibe-coding-quality-loop --agent plan --file AGENTS.md --file docs/quality-bar.md "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a non-interactive comparison pass

Useful official docs:

- `https://opencode.ai/docs/`
- `https://opencode.ai/docs/cli/`
- `https://opencode.ai/docs/providers/`
- `https://opencode.ai/docs/rules/`
- `https://opencode.ai/docs/permissions/`

## Claude Code

Claude Code is useful when a learner already has Anthropic access, but it is not required for this DevNet lab. A 300-person event should not depend on personal Claude Code sign-in.

Optional commands:

- `python3 scripts/first_agent_result.py --tool claude`
- `python3 scripts/agent_code_task.py --tool claude`

If Claude Code is installed but not authenticated, the helpers print the sign-in command and exit cleanly.

Useful official docs:

- `https://code.claude.com/docs/en/setup`
- `https://code.claude.com/docs/en/cli-reference`
- `https://code.claude.com/docs/en/settings`

## Local Models

Local models are useful for privacy, demos, and cost control. They are not always available in a DevNet lab container, so this repo treats them as optional.

Useful official docs:

- `https://docs.ollama.com/api/openai-compatibility`
- `https://lmstudio.ai/docs/developer`

## Recommendation for This Lab

Use Codex CLI with the DevNet model proxy for the required first result and BarryBot build. Bring in OpenCode later as the comparison agent with the same repo rules and check command. Keep Claude Code as an optional follow-up only when the learner already has sign-in.
