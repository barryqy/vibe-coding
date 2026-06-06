#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the BarryBot mini-agent.")
    parser.add_argument(
        "--prompt",
        default="What should I check before trusting AI-generated code?",
        help="Prompt to send to BarryBot.",
    )
    args = parser.parse_args(argv)

    from dojo_app import barrybot

    route = getattr(barrybot, "route_from_env", lambda: {"name": "starter", "model": "starter"})()
    ask = getattr(barrybot, "ask_barrybot", None)
    if ask is None:
        print("BARRYBOT_DEMO=starter")
        print("reason=BarryBot has not been built yet")
        print("next_step=python3 scripts/agent_code_task.py --tool codex")
        return 0

    print("BARRYBOT_DEMO=starting")
    print(f"barrybot_route={route.get('name', 'unknown')}")
    print(f"barrybot_model={route.get('model', 'unknown')}")
    print(f"prompt={args.prompt}")
    print("BARRYBOT_RESPONSE=begin")
    print(ask(args.prompt))
    print("BARRYBOT_RESPONSE=end")
    print("BARRYBOT_DEMO=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
