#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import signal
import shutil
import subprocess


KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
]
ANSI_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\].*?(?:\x07|\x1b\\))")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


def clean_cli_text(text: str) -> str:
    plain = ANSI_RE.sub("", text)
    return CONTROL_RE.sub("", plain)


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    env = dict(os.environ)
    env.setdefault("NO_COLOR", "1")
    env.setdefault("CLICOLOR", "0")
    env.setdefault("CI", "1")
    env.setdefault("TERM", "dumb")
    try:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        return 1, exc.__class__.__name__

    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate(timeout=2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return 1, "TimeoutExpired"

    output = clean_cli_text(output or "").strip()
    return process.returncode, output.splitlines()[0] if output else ""


def version(name: str, args: list[str]) -> str:
    path = shutil.which(name)
    if not path:
        return "not-installed"
    rc, output = run([name, *args])
    return output if rc == 0 and output else path


def main() -> int:
    add_tool_dirs_to_path()
    print("AI_TOOL_CHECK=ready")
    print(f"codex_path={shutil.which('codex') or 'not-installed'}")
    print(f"codex_version={version('codex', ['--version'])}")
    if shutil.which("codex"):
        print("codex_auth=not-required-for-devnet-shim")
        print("codex_next=python3 scripts/setup_codex_devnet.py")
    else:
        print("codex_auth=not-installed")

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
