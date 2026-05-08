#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import urllib.request


def has_cmd(name: str) -> str:
    path = shutil.which(name)
    return path if path else "not found"


def ollama_ready() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/v1/models")
        with urllib.request.urlopen(req, timeout=1) as response:
            json.loads(response.read().decode("utf-8"))
        return True
    except Exception:
        return False


def choose_route() -> str:
    if os.getenv("VIBE_LLM_BASE_URL"):
        return "custom OpenAI-compatible endpoint"
    if os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY"):
        return "DevNet Learning Lab LLM proxy"
    if ollama_ready():
        return "local Ollama OpenAI-compatible endpoint"
    return "deterministic mock coach"


def main() -> int:
    print("TOOL_DOCTOR=ready")
    print(f"claude={has_cmd('claude')}")
    print(f"opencode={has_cmd('opencode')}")
    print(f"ollama={has_cmd('ollama')}")
    print(f"model_route={choose_route()}")
    print("recommendation=run deterministic gates every time; add an LLM coach only when a provider is available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

