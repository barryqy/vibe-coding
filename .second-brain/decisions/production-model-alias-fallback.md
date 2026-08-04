---
type: decision
status: deprecated
---

# Production Model Alias Fallback

## Superseded Decision

The temporary production-only translation from `gpt-5-nano-cache` to `gpt-5-nano` and from `gpt-5-cache` to `gpt-5` was removed on 2026-08-03 after the production proxy gained cache-alias support. The adapters now forward the requested model unchanged.

## Why It Matters

Production can now exercise the same cache-aware model route as staging. Keeping the fallback would hide cache behavior and prevent production verification of the service and lab scripts.

## Evidence

- `tests/test_devnet_codex_shim.py`
- `tests/test_devnet_openai_shim.py`
