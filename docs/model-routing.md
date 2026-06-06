# Model Routing

`scripts/ai_coach.py` uses this order:

0. deterministic mock output when `VIBE_LLM_FORCE_MOCK=1`
1. `VIBE_LLM_BASE_URL`, `VIBE_LLM_API_KEY`, and `VIBE_LLM_MODEL`
2. DevNet lab variables: `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`
3. local Ollama on `http://127.0.0.1:11434/v1`
4. deterministic mock output

This keeps the lab from failing just because a learner does not have a model account.

The optional API call uses the OpenAI-compatible `/chat/completions` shape so the same script can talk to a local server or a hosted provider.

BarryBot uses the same idea:

1. `BARRYBOT_LLM_BASE_URL`, `BARRYBOT_LLM_API_KEY`, and `BARRYBOT_LLM_MODEL`
2. `VIBE_LLM_BASE_URL`, `VIBE_LLM_API_KEY`, and `VIBE_LLM_MODEL`
3. DevNet lab variables: `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`
4. deterministic local fallback

The DevNet lab route currently defaults to `gpt-4o` when `LLM_MODEL` is not set. Treat the displayed model name as part of the risk decision: model quality, origin, safety ranking, and data handling all matter when an agent can call tools.

For coding-agent exercises, the repo-local helpers adapt the same DevNet variables to each tool:

- `scripts/setup_codex_devnet.py` writes `.lab-state/codex/home/config.toml` and points Codex at `http://127.0.0.1:8776/v1`.
- `scripts/devnet_codex_shim.py --ensure` exposes a small Responses API stream for Codex and forwards requests to the DevNet `/chat/completions` route.
- `scripts/setup_opencode_devnet.py` writes `.lab-state/opencode-devnet.json`.
- `scripts/devnet_openai_shim.py --ensure` exposes the OpenAI-compatible chat-completions route OpenCode expects.

Keep these files under `.lab-state/` so the lab does not change a learner's global tool configuration.

Useful model resources:

- Cisco LLM Security Leaderboard: `https://leaderboard.aidefense.cisco.com/`
- Cisco Model Ancestry Map: `https://cs.co/ma`
