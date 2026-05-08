#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import urllib.request


KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
    "~/.claude/bin",
    "~/.claude/local",
]


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


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
    add_tool_dirs_to_path()
    print("TOOL_DOCTOR=ready")
    print(f"claude={has_cmd('claude')}")
    print(f"opencode={has_cmd('opencode')}")
    print(f"ollama={has_cmd('ollama')}")
    print(f"model_route={choose_route()}")
    print("install_tools=./scripts/install_ai_tools.sh")
    print("verify_tools=python3 scripts/verify_ai_tools.py")
    print("opencode_shim=python3 scripts/devnet_openai_shim.py --ensure")
    print("first_opencode_result=python3 scripts/first_agent_result.py --tool opencode")
    print("real_opencode_patch=python3 scripts/agent_code_task.py --tool opencode")
    print("agent_compare=python3 scripts/agent_compare.py --tool both --show-rules")
    print("recommendation=run deterministic gates every time; add an LLM coach only when a provider is available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
