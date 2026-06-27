# Tool Options

The required DevNet path avoids personal model accounts.

## Codex CLI

Codex CLI is the first tool in the lab. The repo gives Codex a local `CODEX_HOME`, a DevNet model adapter, and the BarryFlights MCP server.

In this dojo, the Codex path uses:

- `curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh` and `CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh` to install the CLI
- `npm config set prefix "$HOME/.local"` and `npm install -g @openai/codex` as the fallback if the standalone installer is blocked
- `codex --version` to confirm Codex is installed
- `python3 scripts/setup_codex_devnet.py` to generate `.lab-state/codex/home/config.toml`
- `python3 scripts/start_codex_model_adapter.py` to start the local model adapter
- `usage` to check token counts recorded by the local adapter
- `.agents/skills/rps-cli/SKILL.md` as the documented project skill location
- `CODEX_HOME=.lab-state/codex/home codex exec --disable plugin_sharing --ephemeral --cd "$PWD" --sandbox read-only --output-last-message .lab-state/codex-output/rps-contract.raw.txt 'Use $rps-cli and the second brain...'` plus `python3 scripts/normalize_game_contract.py ... GAME_CONTRACT.md` to create a clean game contract

Useful official docs:

- `https://developers.openai.com/codex/`

## OpenCode

OpenCode is the second coding agent in the lab. It reads the same KB plus its project skill and builds the app from `GAME_CONTRACT.md`.

In this dojo, the OpenCode path uses:

- `curl -fL --max-time 180 --progress-bar -o .lab-state/opencode-download/opencode-linux-x64.tar.gz https://github.com/anomalyco/opencode/releases/download/v1.0.190/opencode-linux-x64.tar.gz` to download the pinned DevNet Linux CLI archive
- `tar -xzf .lab-state/opencode-download/opencode-linux-x64.tar.gz -C .lab-state/opencode-download && install -m 755 .lab-state/opencode-download/opencode "$HOME/.opencode/bin/opencode" && ln -sf "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"` to install the CLI
- `opencode --version` to confirm OpenCode is installed
- `python3 scripts/setup_opencode_devnet.py` to generate the local provider config
- `python3 scripts/start_opencode_model_adapter.py` to start the local model adapter
- `usage` to check token counts before or after longer OpenCode runs
- `.opencode/skills/rps-cli/SKILL.md` as the documented project skill location
- `opencode run 'Use the attached project memory, rps-cli skill, and GAME_CONTRACT.md...' --file ...` with the prompt before repeated `--file` attachments

Useful official docs:

- `https://opencode.ai/docs/`
- `https://opencode.ai/docs/cli/`
- `https://opencode.ai/docs/providers/`
- `https://opencode.ai/docs/rules/`
- `https://opencode.ai/docs/permissions/`
- `https://opencode.ai/docs/skills/`

## Claude Code

Claude Code is useful when you already have Anthropic access, but it is not required for this DevNet lab. The required path should work without personal Claude Code sign-in.

Useful official docs:

- `https://code.claude.com/docs/en/setup`
- `https://code.claude.com/docs/en/cli-reference`
- `https://code.claude.com/docs/en/settings`

## Recommendation

Use Codex CLI with the DevNet model proxy for the first result, the local BarryFlights MCP status check, and the RPS contract. Bring in OpenCode later to read the same KB and build the app from that contract. Run DefenseClaw checks before trusting new Skills or MCP servers.
