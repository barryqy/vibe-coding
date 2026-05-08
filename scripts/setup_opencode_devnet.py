#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".lab-state" / "opencode-devnet.json"


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
        "default_agent": "plan",
        "instructions": ["AGENTS.md", "docs/quality-bar.md"],
        "model": f"devnet/{model}",
        "tools": {
            "write": False,
            "edit": False,
            "bash": False,
        },
        "provider": {
            "devnet": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "DevNet Learning Lab LLM",
                "options": {
                    "baseURL": base_url,
                    "apiKey": api_key,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
