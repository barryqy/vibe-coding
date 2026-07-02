#!/usr/bin/env python3
from __future__ import annotations

import os


def route_name() -> str:
    if os.getenv("VIBE_LLM_BASE_URL"):
        return "custom-openai-compatible"
    if os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY"):
        return "devnet-lab"
    return "not-configured"


def route_model() -> str:
    return os.getenv("VIBE_LLM_MODEL") or os.getenv("LLM_MODEL") or "gpt-5-nano"


def main() -> int:
    print("LLM_WALKTHROUGH=ready")
    print(f"llm_route={route_name()}")
    print(f"llm_model={route_model()}")
    print("llm_shape=messages in, text out")
    print("agent_shape=llm plus instructions plus tools plus checks")
    print("resource_security_leaderboard=https://leaderboard.aidefense.cisco.com/")
    print("resource_model_ancestry=https://cs.co/ma")
    print("model_ancestry_example=Cursor Composer 2 and China-based Moonshot AI Kimi K2.5")
    print("maze_next=python3 -m dojo_app.maze_game")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
