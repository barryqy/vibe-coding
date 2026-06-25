#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".lab-state" / "codex"
HOME = STATE / "home"
CONFIG = HOME / "config.toml"
MODEL_CATALOG = HOME / "model-catalog.json"
SHIM_BASE_URL = "http://127.0.0.1:8776/v1"


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def model_catalog(model: str) -> dict:
    return {
        "models": [
            {
                "slug": model,
                "display_name": "DevNet Lab Model",
                "description": "Model supplied by the DevNet learning lab.",
                "default_reasoning_level": "none",
                "supported_reasoning_levels": [],
                "shell_type": "shell_command",
                "visibility": "list",
                "supported_in_api": True,
                "priority": 0,
                "supports_reasoning_summaries": False,
                "support_verbosity": False,
                "truncation_policy": {"mode": "tokens", "limit": 10000},
                "supports_parallel_tool_calls": False,
                "experimental_supported_tools": [],
                "context_window": 128000,
                "max_context_window": 128000,
                "base_instructions": "You are Codex, a coding agent.",
                "model_messages": {
                    "instructions_template": (
                        "You are Codex, a coding agent. Help the user complete "
                        "software tasks clearly and safely.\n\n{{ personality }}"
                    ),
                    "instructions_variables": {
                        "personality_default": "",
                        "personality_friendly": "Be concise, helpful, and collaborative.",
                        "personality_pragmatic": "Be concise, factual, and focused on the task.",
                    },
                },
            }
        ]
    }


def main() -> int:
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")

    if not base_url or not api_key:
        HOME.mkdir(parents=True, exist_ok=True)
        print("CODEX_MODEL_ROUTE=skipped")
        print("reason=LLM_BASE_URL or LLM_API_KEY is missing")
        return 0

    HOME.mkdir(parents=True, exist_ok=True)
    MODEL_CATALOG.write_text(
        json.dumps(model_catalog(model), indent=2) + "\n",
        encoding="utf-8",
    )
    CONFIG.write_text(
        "\n".join(
            [
                f"model = {toml_string(model)}",
                'model_provider = "devnet"',
                "model_context_window = 128000",
                f"model_catalog_json = {toml_string(str(MODEL_CATALOG))}",
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

    print("CODEX_MODEL_ROUTE=ready")
    print(f"codex_home={HOME.relative_to(ROOT)}")
    print(f"config={CONFIG.relative_to(ROOT)}")
    print(f"model={model}")
    print(f"model_catalog={MODEL_CATALOG.relative_to(ROOT)}")
    print("model_context_window=128000")
    print("adapter=python3 scripts/start_codex_model_adapter.py")
    print("mcp_install=codex mcp add barryflights")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
