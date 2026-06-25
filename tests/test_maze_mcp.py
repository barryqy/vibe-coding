from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from dojo_app import maze_game, maze_mcp_client, maze_mcp_server


class MazeMcpTests(unittest.TestCase):
    def test_build_maze_artifact_writes_checked_maze(self):
        with tempfile.TemporaryDirectory(dir=maze_mcp_server.ROOT) as tmp:
            rel_path = Path(tmp).relative_to(maze_mcp_server.ROOT) / "maze.txt"
            text = maze_mcp_server.build_maze_artifact("lab-42", "SWEN", str(rel_path))
            maze = maze_game.load_maze(str(maze_mcp_server.ROOT / rel_path))

        self.assertIn("MAZE_MCP=ready", text)
        self.assertIn("server=MazeMaker MCP", text)
        self.assertIn("tool=build_maze", text)
        self.assertIn("solvable=yes", text)
        self.assertIn("MAZE_MCP=pass", text)
        self.assertTrue(maze_game.trusted_maze_lines(maze))

    def test_build_maze_artifact_rejects_bad_order(self):
        with self.assertRaises(ValueError):
            maze_mcp_server.build_maze_artifact("lab-42", "NNNN")

    def test_build_maze_artifact_keeps_output_inside_repo(self):
        with self.assertRaises(ValueError):
            maze_mcp_server.build_maze_artifact("lab-42", "NESW", "../maze.txt")

    def test_stdio_mcp_client_calls_build_tool_when_dependency_exists(self):
        try:
            import mcp  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("mcp package is installed during the lab setup")

        with tempfile.TemporaryDirectory(dir=maze_mcp_server.ROOT) as tmp:
            rel_path = Path(tmp).relative_to(maze_mcp_server.ROOT) / "maze.txt"
            text = asyncio.run(
                maze_mcp_client.call_mcp_tool(
                    "build_maze",
                    {
                        "output_path": str(rel_path),
                    },
                )
            )

        self.assertIn("MAZE_MCP=pass", text)


if __name__ == "__main__":
    unittest.main()
