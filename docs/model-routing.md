# Model Routing

`scripts/ai_coach.py` uses this order:

0. deterministic mock output when `VIBE_LLM_FORCE_MOCK=1`
1. `VIBE_LLM_BASE_URL`, `VIBE_LLM_API_KEY`, and `VIBE_LLM_MODEL`
2. DevNet lab variables: `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`
3. local Ollama on `http://127.0.0.1:11434/v1`
4. deterministic mock output

This keeps the lab from failing just because a learner does not have a model account.

The optional API call uses the OpenAI-compatible `/chat/completions` shape so the same script can talk to a local server or a hosted provider.
