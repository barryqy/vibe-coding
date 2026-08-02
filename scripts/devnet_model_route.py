#!/usr/bin/env python3
from __future__ import annotations

PRODUCTION_LLM_BASE_URL = "https://devnet.cisco.com/v1/llmproxy"
PRODUCTION_MODEL_FALLBACKS = {
    "gpt-5-nano-cache": "gpt-5-nano",
    "gpt-5-cache": "gpt-5",
}


def upstream_model(base_url: str, requested_model: str) -> str:
    normalized_url = base_url.strip().rstrip("/")
    if normalized_url != PRODUCTION_LLM_BASE_URL:
        return requested_model

    return PRODUCTION_MODEL_FALLBACKS.get(requested_model, requested_model)
