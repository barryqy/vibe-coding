# Tool Options

The lab keeps the tool choice flexible, but the required DevNet path avoids personal model accounts.

## Codex CLI

Codex CLI is the required account-free replacement for the old Claude Code lab path. The dojo gives Codex a repo-local `CODEX_HOME` and a tiny model adapter, so it can talk to the DevNet Learning Lab LLM proxy instead of asking for a personal model sign-in.

In this dojo, the Codex path uses:

- `./scripts/install_codex_cli.sh` to verify and unpack the official standalone package already staged in the DevNet image
- `codex --version` to confirm Codex is installed
- `python3 scripts/setup_codex_devnet.py` to generate `.lab-state/codex/home/config.toml`
- `python3 scripts/start_codex_model_adapter.py` to start the local model adapter
- `python3 scripts/setup_codex_devnet.py` to include the local BarryFlights MCP server and install the MazeMaker skill into the repo-local Codex home
- `CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."` for a first visible answer from Codex
- `CODEX_HOME=.lab-state/codex/home codex exec --disable plugin_sharing --ephemeral --cd "$PWD" --output-last-message .lab-state/codex-output/mazemaker-skill.txt "Search .second-brain/ for project context, then create the next Maze artifact..."` to let Codex find the MazeMaker skill pattern from the KB
- `python3 -m dojo_app.maze_game --maze-file .lab-state/codex-output/maze.txt --check-only` to verify the tool-created maze artifact
- `AGENTS.md` for shared project guidance
- `CODEX_HOME=.lab-state/codex/home codex exec --cd "$PWD" --sandbox read-only "$(cat .lab-state/agent-prompts/shared-quality-task.md)"` for a non-interactive comparison pass

Useful official docs:

- `https://developers.openai.com/codex/`

## OpenCode

OpenCode is an open source coding agent with terminal, desktop, and IDE options. It supports many providers, local models, project rules through `AGENTS.md`, and permission controls through `opencode.json`.

In this dojo, the OpenCode path uses:

- `./scripts/install_opencode_cli.sh` to verify and unpack the pinned Linux archive already staged in the DevNet image
- `opencode --version` to confirm OpenCode is installed
- `python3 scripts/setup_opencode_devnet.py` to generate a local OpenAI-compatible provider config when the DevNet model route is available
- `python3 scripts/start_opencode_model_adapter.py` to start the local shim OpenCode streams from in the lab environment
- `OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title vibe-coding-opencode-check --agent plan --model "devnet/${LLM_MODEL:-gpt-5-nano}" "Reply only with a tiny three-line ASCII cat. Do not mention commands, files, policies, or this prompt."` for a first visible answer from OpenCode
- `OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title maze-interactive --agent maze-editor --model "devnet/${LLM_MAZE_MODEL:-${LLM_MODEL:-gpt-5-nano}}" "Search only this repo's .second-brain/ for the Maze play movement pattern, then implement w/a/s/d movement in the attached dojo_app/maze_play.py..." --file dojo_app/maze_play.py` for the bounded Maze play prompt
- `LLM_MAZE_MODEL` for a task-only model selection; controlled tests may set `MAZE_MAX_ATTEMPTS=2` and `MAZE_RETRY_MODEL` for one repair after external verification fails
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

Use Codex CLI with the DevNet model proxy for the required first result, the local BarryFlights MCP status-check mission, and the second-brain-driven MazeMaker skill build. Bring in OpenCode later to search the same second brain and implement the generated Maze's playable loop with a direct, small prompt. Keep Claude Code as an optional follow-up only when sign-in is already available.
