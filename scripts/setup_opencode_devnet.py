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
MAZE_AGENT_NAME = "maze-editor"
MAZE_AGENT_MAX_STEPS = 16
MAZE_AGENT_PROMPT = """You are the bounded Module 5 Maze movement editor. This is an implementation task, not a review. The task is incomplete until dojo_app/maze_play.py has been edited and both required checks have returned exit code 0 in this session.

Use this sequence:
1. Search only this repo's .second-brain/ once for the Maze play movement pattern.
2. Read the attached dojo_app/maze_play.py and edit only choose_next_position.
3. Run python3 scripts/verify_maze_movement.py.
4. Run python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py.

If a check fails, use its diagnostics to edit the function before rerunning it. Never rerun an unchanged failing check. Use actual line breaks in Python source, not literal backslash-n text. After no more than two corrective edits, stop and report MAZE_EDIT_FAILED with the exact last failure instead of looping. Do not edit other files or update memory or session notes. Return MAZE_EDIT_OK only when both latest checks passed."""


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
    model = os.getenv("LLM_MODEL", "gpt-5-nano")
    maze_model = os.getenv("LLM_MAZE_MODEL") or model
    retry_model = os.getenv("MAZE_RETRY_MODEL") or maze_model
    configured_models = list(dict.fromkeys([model, maze_model, retry_model]))
    try:
        output_limit = int(os.getenv("LAB_LLM_MAX_OUTPUT_TOKENS", "512"))
    except ValueError:
        output_limit = 512
    output_limit = min(max(output_limit, 128), 1024)
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
        "agent": {
            MAZE_AGENT_NAME: {
                "description": "Complete the bounded Module 5 Maze movement edit and checks.",
                "mode": "primary",
                "maxSteps": MAZE_AGENT_MAX_STEPS,
                "prompt": MAZE_AGENT_PROMPT,
                "permission": {
                    "edit": "allow",
                    "bash": {
                        "*": "deny",
                        "python3 scripts/verify_maze_movement.py": "allow",
                        "python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py": "allow",
                    },
                    "webfetch": "deny",
                    "external_directory": "deny",
                    "doom_loop": "deny",
                },
            }
        },
        "permission": {
            "read": {
                "*": "allow",
                "*.env": "deny",
                "*.env.*": "deny",
                "secrets/**": "deny",
            },
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
            "external_directory": "deny",
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
                    model_name: {
                        "name": f"DevNet {model_name}",
                        "limit": {
                            "context": 128000,
                            "output": output_limit,
                        },
                    }
                    for model_name in configured_models
                },
            }
        },
    }
    OUT.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    print_status("OPENCODE_DEVNET_CONFIG=ready")
    print_status(f"path={OUT.relative_to(ROOT)}")
    print_status(f"model=devnet/{model}")
    print_status(f"maze_model=devnet/{maze_model}")
    print_status(f"maze_retry_model=devnet/{retry_model}")
    print_status(f"model_output_limit={output_limit}")
    print_status("kb_search=.second-brain")
    print_status("kb_scope=repo-only")
    print_status("edit_permission=allow")
    print_status("task_file=dojo_app/maze_play.py")
    print_status(f"task_agent={MAZE_AGENT_NAME}")
    print_status(f"task_max_steps={MAZE_AGENT_MAX_STEPS}")
    print_status("adapter=python3 scripts/start_opencode_model_adapter.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
