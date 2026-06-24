# Tool Options

The lab keeps the tool choice flexible, but the required DevNet path avoids personal model accounts.

## Codex CLI

Codex CLI is the required account-free replacement for the old Claude Code lab path. The dojo gives Codex a repo-local `CODEX_HOME` and a tiny model adapter, so it can talk to the DevNet Learning Lab LLM proxy instead of asking for a personal model sign-in.

In this dojo, the Codex path uses:

- `curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh` and `CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh` to install the CLI with the official standalone installer
- `npm config set prefix "$HOME/.local"` and `npm install -g @openai/codex` as the visible fallback if the standalone installer is blocked
- `codex --version` to confirm Codex is installed
- `python3 scripts/setup_codex_devnet.py` to generate `.lab-state/codex/home/config.toml`
- `python3 scripts/start_codex_model_adapter.py` to start the local model adapter
- `CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."` for a first visible answer from Codex
- `python3 -m dojo_app.snake_game` to run the tiny game used in the main exercise
- `AGENTS.md` for shared project guidance
- `CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" --sandbox read-only "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a non-interactive comparison pass

Useful official docs:

- `https://developers.openai.com/codex/`

## OpenCode

OpenCode is an open source coding agent with terminal, desktop, and IDE options. It supports many providers, local models, project rules through `AGENTS.md`, and permission controls through `opencode.json`.

In this dojo, the OpenCode path uses:

- `curl -fL --max-time 180 --progress-bar -o .lab-state/opencode-download/opencode-linux-x64.tar.gz https://github.com/anomalyco/opencode/releases/download/v1.0.190/opencode-linux-x64.tar.gz` to download the pinned DevNet Linux CLI archive
- `tar -xzf .lab-state/opencode-download/opencode-linux-x64.tar.gz -C .lab-state/opencode-download && install -m 755 .lab-state/opencode-download/opencode "$HOME/.opencode/bin/opencode" && ln -sf "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"` to install the CLI and keep it visible across lab command blocks
- `opencode --version` to confirm OpenCode is installed
- `python3 scripts/setup_opencode_devnet.py` to generate a local OpenAI-compatible provider config when the DevNet model route is available
- `python3 scripts/start_opencode_model_adapter.py` to start the local shim OpenCode streams from in the lab environment
- `OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title vibe-coding-opencode-check --agent plan --model devnet/gpt-4o "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."` for a first visible answer from OpenCode
- `python3 scripts/agent_compare.py --tool both --show-rules` for the same Snake-game prompt shape when you want a comparison run
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

Claude Code is useful when you already have Anthropic access, but it is not required for this DevNet lab. The required path should work without personal Claude Code sign-in.

Optional commands:

- `claude "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."`

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

Use Codex CLI with the DevNet model proxy for the required first result, BarryFlights MCP check, clean skill install, and tiny Snake game exercise. Bring in OpenCode later as the comparison agent with the same repo rules and check command. Keep Claude Code as an optional follow-up only when sign-in is already available.
