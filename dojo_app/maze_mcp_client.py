from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dojo_app.maze_mcp_server import MCP_SERVER_NAME


ROOT = Path(__file__).resolve().parents[1]
SERVER_MODULE = "dojo_app.maze_mcp_server"


def text_from_result(result: Any) -> str:
    content = getattr(result, "content", None) or []
    parts = [item.text for item in content if hasattr(item, "text") and item.text]
    if parts:
        return "\n".join(parts)
    structured = getattr(result, "structuredContent", None)
    return json.dumps(structured, sort_keys=True) if structured is not None else ""


async def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", SERVER_MODULE],
        cwd=str(ROOT),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
    return text_from_result(result)


async def list_mcp_tools() -> list[str]:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", SERVER_MODULE],
        cwd=str(ROOT),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
    return sorted(tool.name for tool in tools.tools)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Call the local MazeMaker MCP server.")
    parser.add_argument("--list-tools", action="store_true", help="List local MCP tools and exit")
    parser.add_argument("--maze-file", default=".lab-state/codex-output/maze.txt")
    args = parser.parse_args(argv)

    try:
        if args.list_tools:
            tools = asyncio.run(list_mcp_tools())
            print("LOCAL_MCP=ready")
            print(f"server={MCP_SERVER_NAME}")
            print("tools=" + ",".join(tools))
            print("LOCAL_MCP=pass")
            return 0

        response = asyncio.run(call_mcp_tool("build_maze", {"output_path": args.maze_file}))
    except ModuleNotFoundError as exc:
        if exc.name == "mcp":
            print("LOCAL_MCP=missing-dependency")
            print("next=.venv/bin/python -m pip install -r requirements.txt")
            return 1
        raise

    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
