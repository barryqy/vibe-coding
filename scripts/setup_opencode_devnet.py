#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dojo_app.lab_output import print_status
OUT = ROOT / ".lab-state" / "opencode-devnet.json"
SHIM_BASE_URL = "http://127.0.0.1:8765/v1"
INSTRUCTIONS = [
    "AGENTS.md",
    "docs/quality-bar.md",
]


def install_lab_commands() -> None:
    cprint_source = ROOT / "scripts" / "cprint"
    cprint_target = Path.home() / ".local" / "bin" / "cprint"

    if cprint_source.exists():
        cprint_target.parent.mkdir(parents=True, exist_ok=True)
        try:
            cprint_target.unlink()
        except FileNotFoundError:
            pass
        cprint_target.symlink_to(cprint_source)


def main() -> int:
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    install_lab_commands()

    if not base_url or not api_key:
        print_status("OPENCODE_DEVNET_CONFIG=skipped")
        print_status("reason=LLM_BASE_URL or LLM_API_KEY is missing")
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
            "bash": {
                "python3 -m dojo_app.barryflights_mcp_client*": "allow",
                "python3 -m dojo_app.maze_game*": "allow",
                "printf * | python3 -m dojo_app.maze_game*": "allow",
                "python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py*": "allow",
                "python3 skills/mazemaker/scripts/build_maze.py*": "allow",
                "python3 .lab-state/codex/home/skills/mazemaker/scripts/build_maze.py*": "allow",
                ".venv/bin/python -m dojo_app.barryflights_mcp_client*": "allow",
                "python3 scripts/check_repo.py*": "allow",
                "*": "allow",
            },
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

    print_status("OPENCODE_DEVNET_CONFIG=ready")
    print_status(f"path={OUT.relative_to(ROOT)}")
    print_status(f"model=devnet/{model}")
    print_status("kb_search=.second-brain")
    print_status("edit_permission=allow")
    print_status("task_file=dojo_app/maze_play.py")
    print_status("adapter=python3 scripts/start_opencode_model_adapter.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
