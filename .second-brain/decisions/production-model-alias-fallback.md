---
type: decision
status: active
---

# Production Model Alias Fallback

## Decision

Translate `gpt-5-nano-cache` to `gpt-5-nano` and `gpt-5-cache` to `gpt-5` only when a local adapter sends a request to `https://devnet.cisco.com/v1/llmproxy`. Keep the requested aliases in client configuration and leave every other endpoint unchanged.

## Why It Matters

The production lab template can advertise cache aliases before the production proxy accepts them. Applying the fallback at the two adapter boundaries repairs existing lab instructions without changing staging, publishing course content, or rewriting injected environment variables.

Remove this compatibility fallback after the production proxy supports the cache aliases.

## Evidence

- `scripts/devnet_model_route.py`
- `tests/test_devnet_model_route.py`
- `tests/test_devnet_codex_shim.py`
- `tests/test_devnet_openai_shim.py`
