#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import urllib.request
from pathlib import Path


KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
]
ROOT = Path(__file__).resolve().parents[1]


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


def has_cmd(name: str) -> str:
    if name == "defenseclaw":
        local = ROOT / ".lab-state" / "defenseclaw" / ".venv" / "bin" / "defenseclaw"
        if local.exists():
            return str(local)

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
    print(f"codex={has_cmd('codex')}")
    print(f"opencode={has_cmd('opencode')}")
    print(f"defenseclaw={has_cmd('defenseclaw')}")
    print(f"ollama={has_cmd('ollama')}")
    print(f"model_route={choose_route()}")
    print("install_codex=curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh && CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh")
    print("install_codex_fallback=npm config set prefix \"$HOME/.local\" && npm install -g @openai/codex")
    print("install_opencode=download https://github.com/anomalyco/opencode/releases/download/v1.0.190/opencode-linux-x64.tar.gz")
    print("check_codex=codex --version")
    print("check_opencode=opencode --version")
    print("codex_model_route=python3 scripts/setup_codex_devnet.py")
    print("opencode_model_route=python3 scripts/setup_opencode_devnet.py")
    print("codex_model_adapter=python3 scripts/start_codex_model_adapter.py")
    print("opencode_model_adapter=python3 scripts/start_opencode_model_adapter.py")
    print("check_repo=python3 scripts/check_repo.py")
    print("first_codex_result=CODEX_HOME=.lab-state/codex/home codex exec --cd \"$PWD\" \"Reply only with a tiny three-line ASCII cat.\"")
    print("first_opencode_result=OPENCODE_CONFIG=.lab-state/opencode-devnet.json opencode run --title vibe-coding-opencode-check --agent plan --model \"devnet/${LLM_MODEL:-gpt-5-nano}\" \"Reply only with a tiny three-line ASCII cat.\"")
    print("maze_game=python3 -m dojo_app.maze_game")
    print("agent_compare=python3 scripts/agent_compare.py --tool both --show-rules")
    print("defenseclaw_demo=python3 scripts/defenseclaw_skill_demo.py")
    print("recommendation=start with Codex, then run simple repo checks after code changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
