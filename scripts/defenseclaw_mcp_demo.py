#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCAL_HOME = ROOT / ".lab-state" / "defenseclaw" / "home"
LOCAL_CLI = ROOT / ".lab-state" / "defenseclaw" / ".venv" / "bin" / "defenseclaw"
INSTALLER = ROOT / "scripts" / "install_defenseclaw_cli.sh"
RISKY_MCP = ROOT / "samples" / "mcp" / "workspace-admin-bridge.py"


def run(cmd: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.setdefault("NO_COLOR", "1")
    env.setdefault("CLICOLOR", "0")
    env.setdefault("DEFENSECLAW_HOME", str(LOCAL_HOME))
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )


def ensure_defenseclaw() -> str:
    if LOCAL_CLI.exists():
        return str(LOCAL_CLI)

    found = shutil.which("defenseclaw")
    if found:
        return found

    result = run([str(INSTALLER)], timeout=240)
    if result.returncode != 0:
        print(result.stdout.rstrip())
        print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(result.returncode)

    if LOCAL_CLI.exists():
        return str(LOCAL_CLI)

    found = shutil.which("defenseclaw")
    if found:
        return found

    print("DEFENSECLAW_INSTALL=failed", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    cli = ensure_defenseclaw()
    python_bin = ROOT / ".venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    result = run(
        [
            cli,
            "mcp",
            "set",
            "workspace_admin",
            "--command",
            str(python_bin),
            "--args",
            f'["{RISKY_MCP}"]',
            "--transport",
            "stdio",
        ],
        timeout=120,
    )
    combined = "\n".join(part for part in [result.stdout, result.stderr] if part)
    marker_words = ("refusing to scan", "HIGH", "CRITICAL", "block", "reject")

    if result.returncode == 0:
        print(combined.rstrip())
        print("DEFENSECLAW_MCP_ADMISSION=unexpected-allowed")
        return 1

    if not any(word.lower() in combined.lower() for word in marker_words):
        print(combined.rstrip())
        print("DEFENSECLAW_MCP_ADMISSION=unexpected-result")
        return 1

    print("DEFENSECLAW_MCP_ADMISSION=blocked")
    print("DEFENSECLAW_MCP=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
