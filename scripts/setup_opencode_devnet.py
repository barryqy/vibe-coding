#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".lab-state" / "opencode-devnet.json"
SHIM_BASE_URL = "http://127.0.0.1:8765/v1"
INSTRUCTIONS = [
    "AGENTS.md",
    "docs/quality-bar.md",
    ".second-brain/RESOLVER.md",
    ".second-brain/schema.md",
    ".second-brain/projects/vibe-coding-dojo.md",
    ".second-brain/sessions/current-agent-handoff.md",
]


def main() -> int:
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")

    if not base_url or not api_key:
        print("OPENCODE_DEVNET_CONFIG=skipped")
        print("reason=LLM_BASE_URL or LLM_API_KEY is missing")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "default_agent": "build",
        "instructions": INSTRUCTIONS,
        "model": f"devnet/{model}",
        "permission": {
            "edit": "allow",
            "bash": "ask",
            "webfetch": "deny",
            "websearch": "deny",
        },
        "provider": {
            "devnet": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "DevNet Learning Lab LLM",
                "options": {
                    "baseURL": SHIM_BASE_URL,
                    "apiKey": "devnet-shim",
                },
                "models": {
                    model: {
                        "name": f"DevNet {model}",
                        "limit": {
                            "context": 128000,
                            "output": 4096,
                        },
                    }
                },
            }
        },
    }
    OUT.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    print("OPENCODE_DEVNET_CONFIG=ready")
    print(f"path={OUT.relative_to(ROOT)}")
    print(f"model=devnet/{model}")
    print("kb=.second-brain")
    print("edit_permission=allow")
    print("adapter=python3 scripts/start_opencode_model_adapter.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
