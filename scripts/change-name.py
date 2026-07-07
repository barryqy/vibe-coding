#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess


NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,32}")


def main() -> int:
    print("Choose a player name with 3-32 letters, numbers, underscores, or hyphens.")
    try:
        player_name = input("New player name: ").strip()
    except EOFError:
        print("No name entered. Your player name is unchanged.")
        return 1

    if not player_name:
        print("Your player name is unchanged.")
        return 0
    if not NAME_PATTERN.fullmatch(player_name):
        print("That name must use 3-32 letters, numbers, underscores, or hyphens.")
        return 1

    dojo = shutil.which("dojo")
    if not dojo:
        print("dojo is not installed. Run ./scripts/setup_dojo.sh first.")
        return 1

    return subprocess.run([dojo, "join", "--name", player_name], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
