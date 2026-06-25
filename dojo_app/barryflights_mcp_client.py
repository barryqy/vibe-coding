from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dojo_app.barryflights_mcp_server import MCP_SERVER_NAME


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "dojo_app" / "barryflights_mcp_server.py"


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
        args=[str(SERVER)],
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
        args=[str(SERVER)],
        cwd=str(ROOT),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
    return sorted(tool.name for tool in tools.tools)


def normalize_response(text: str) -> str:
    return " | ".join(line.strip() for line in text.splitlines() if line.strip())


def write_evidence(path: Path, tool_name: str, response: str) -> None:
    lines = response.splitlines()
    first_result = next(
        (
            line
            for line in lines
            if line.startswith("Flight ") or line.startswith("Booked ")
        ),
        lines[0] if lines else "No MCP content returned",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"MCP_SERVER={MCP_SERVER_NAME}",
                "MCP_TRANSPORT=local stdio",
                f"MCP_TOOL={tool_name}",
                f"MCP_RESULT={first_result}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_arguments(args: argparse.Namespace) -> dict[str, str]:
    if args.tool == "flight_status":
        return {"flight_number": args.flight}
    if args.tool == "book_flight":
        return {
            "traveler_name": args.traveler_name,
            "origin": args.origin,
            "destination": args.destination,
            "date": args.date,
        }
    return {
        "origin": args.origin,
        "destination": args.destination,
        "date": args.date,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Call the local BarryFlights MCP server.")
    parser.add_argument("--list-tools", action="store_true", help="List local MCP tools and exit")
    parser.add_argument("--tool", choices=["flight_status", "search_flights", "book_flight"], default="flight_status")
    parser.add_argument("--flight", default="SKY451")
    parser.add_argument("--traveler-name", default="Alex")
    parser.add_argument("--origin", default="SFO")
    parser.add_argument("--destination", default="LAS")
    parser.add_argument("--date", default="Friday")
    parser.add_argument("--evidence-file")
    args = parser.parse_args(argv)

    try:
        if args.list_tools:
            tools = asyncio.run(list_mcp_tools())
            print("LOCAL_MCP=ready")
            print(f"server={MCP_SERVER_NAME}")
            print("tools=" + ",".join(tools))
            print("LOCAL_MCP=pass")
            return 0

        response = asyncio.run(call_mcp_tool(args.tool, build_arguments(args)))
    except ModuleNotFoundError as exc:
        if exc.name == "mcp":
            print("LOCAL_MCP=missing-dependency")
            print("next=.venv/bin/python -m pip install -r requirements.txt")
            return 1
        raise

    print("BARRYFLIGHTS_LOCAL_MCP=ready")
    print(f"server={MCP_SERVER_NAME}")
    print(f"tool={args.tool}")
    if args.tool == "flight_status":
        print(f"flight={args.flight.upper()}")
    if args.tool == "book_flight":
        print(f"traveler={args.traveler_name}")
    print("response=" + normalize_response(response))

    if args.evidence_file:
        write_evidence(Path(args.evidence_file), args.tool, response)
        print(f"evidence={args.evidence_file}")

    print("BARRYFLIGHTS_LOCAL_MCP=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
