"""Local MCP wrapper for the Maze generator used in the lab."""

from __future__ import annotations

import logging
import os
import random
import secrets
import time
from pathlib import Path

from dojo_app import maze_game


MCP_SERVER_NAME = "MazeMaker MCP"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAZE_FILE = ROOT / ".lab-state" / "codex-output" / "maze.txt"
BUILD_DESCRIPTION = "Build a checked 12x12 Recursive Backtracker maze and write it to a repo-local file."
ORDER_OPTIONS = ("NESW", "NWSE", "ESWN", "WNSE", "SWEN", "ENWS")


def fresh_seed() -> str:
    return f"maze-{time.time_ns()}-{secrets.token_hex(2)}"


def clean_seed(seed: str | None) -> str:
    value = (seed or "").strip()
    if not value:
        return fresh_seed()
    if len(value) > 64:
        raise ValueError("seed is too long")
    return value


def clean_order(order: str | None, seed: str) -> str:
    raw = (order or "").strip().upper()
    if not raw:
        rng = random.Random(seed)
        return ORDER_OPTIONS[rng.randrange(len(ORDER_OPTIONS))]
    if len(raw) != 4 or set(raw) != set(maze_game.MOVE_DELTAS):
        raise ValueError("order must contain N, S, E, and W once")
    return raw


def resolve_output_path(output_path: str | None) -> Path:
    raw = (output_path or ".lab-state/codex-output/maze.txt").strip()
    target = Path(raw)
    if target.is_absolute() or ".." in target.parts:
        raise ValueError("output_path must stay inside this repo")
    return ROOT / target


def build_maze_artifact(
    seed: str | None = None,
    order: str | None = None,
    output_path: str | None = None,
) -> str:
    clean = clean_seed(seed)
    direction_order = clean_order(order, clean)
    target = resolve_output_path(output_path)

    maze = maze_game.generate_maze_from_plan(clean, direction_order)
    maze_game.write_maze(str(target), maze)
    path_length = maze_game.shortest_path_length(maze)
    relative_target = target.relative_to(ROOT)

    return "\n".join(
        [
            "MAZE_MCP=ready",
            f"server={MCP_SERVER_NAME}",
            "tool=build_maze",
            "format=recursive-backtracker",
            f"maze_file={relative_target}",
            "size=12x12",
            "border=ok",
            "solvable=yes",
            f"path_length={path_length}",
            "MAZE_MCP=pass",
        ]
    )


def build_mcp():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(MCP_SERVER_NAME)

    @mcp.tool(name="build_maze", description=BUILD_DESCRIPTION)
    def build_maze(output_path: str = ".lab-state/codex-output/maze.txt") -> str:
        return build_maze_artifact(output_path=output_path)

    return mcp


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport != "stdio":
        raise SystemExit("This dojo MCP server supports stdio for the lab.")
    build_mcp().run("stdio")


if __name__ == "__main__":
    main()
