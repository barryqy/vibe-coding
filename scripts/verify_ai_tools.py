#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import os


KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
    "~/.claude/bin",
    "~/.claude/local",
]


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, exc.__class__.__name__
    output = (result.stdout or result.stderr).strip()
    return result.returncode, output.splitlines()[0] if output else ""


def version(name: str, args: list[str]) -> str:
    path = shutil.which(name)
    if not path:
        return "not-installed"
    rc, output = run([name, *args])
    return output if rc == 0 and output else path


def main() -> int:
    add_tool_dirs_to_path()
    print("AI_TOOL_CHECK=ready")
    print(f"claude_path={shutil.which('claude') or 'not-installed'}")
    print(f"claude_version={version('claude', ['--version'])}")

    if shutil.which("claude"):
        rc, output = run(["claude", "auth", "status", "--text"])
        print(f"claude_auth={'ready' if rc == 0 else 'needs-login'}")
        if output:
            print(f"claude_auth_message={output}")
        if rc != 0:
            print("claude_next=claude auth login")
    else:
        print("claude_auth=not-installed")

    print(f"opencode_path={shutil.which('opencode') or 'not-installed'}")
    print(f"opencode_version={version('opencode', ['--version'])}")

    if shutil.which("opencode"):
        rc, output = run(["opencode", "auth", "list"])
        print(f"opencode_auth={'configured' if rc == 0 else 'not-configured'}")
        if output:
            print(f"opencode_auth_message={output}")
        print("opencode_next=python3 scripts/setup_opencode_devnet.py")
    else:
        print("opencode_auth=not-installed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
