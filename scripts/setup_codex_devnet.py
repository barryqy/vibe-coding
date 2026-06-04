#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".lab-state" / "codex"
HOME = STATE / "home"
CONFIG = HOME / "config.toml"
SHIM_BASE_URL = "http://127.0.0.1:8776/v1"


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")

    if not base_url or not api_key:
        print("CODEX_DEVNET_CONFIG=skipped")
        print("reason=LLM_BASE_URL or LLM_API_KEY is missing")
        return 0

    HOME.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(
        "\n".join(
            [
                f"model = {toml_string(model)}",
                'model_provider = "devnet"',
                'approval_policy = "never"',
                'sandbox = "read-only"',
                'web_search = "disabled"',
                'model_reasoning_effort = "none"',
                'model_reasoning_summary = "none"',
                "",
                "[model_providers.devnet]",
                'name = "DevNet Learning Lab LLM"',
                f"base_url = {toml_string(SHIM_BASE_URL)}",
                'wire_api = "responses"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("CODEX_DEVNET_CONFIG=ready")
    print(f"codex_home={HOME.relative_to(ROOT)}")
    print(f"path={CONFIG.relative_to(ROOT)}")
    print(f"model=devnet/{model}")
    print("shim=python3 scripts/devnet_codex_shim.py --ensure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
