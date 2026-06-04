#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from agent_compare import TASK_PROMPT, write_prompt


ROOT = Path(__file__).resolve().parents[1]
KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
]


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


def run(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 180) -> int:
    try:
        result = subprocess.run(cmd, cwd=ROOT, env=env, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        print("RUN_STATUS=timeout")
        return 1
    except OSError as exc:
        print(f"RUN_STATUS=error:{exc.__class__.__name__}")
        return 1
    return result.returncode


def prompt_for_first_result() -> str:
    return (
        "Read AGENTS.md and docs/quality-bar.md, then explain this dojo repo in five bullets. "
        "After that, propose one small beginner-friendly code change. "
        "Do not edit files. End with the exact verification command."
    )


def run_opencode() -> int:
    add_tool_dirs_to_path()
    if not shutil.which("opencode"):
        print("OPENCODE_FIRST_RESULT=skipped")
        print("reason=opencode is not installed")
        return 0

    config = ROOT / ".lab-state" / "opencode-devnet.json"
    if not config.exists():
        setup_rc = run([sys.executable, "scripts/setup_opencode_devnet.py"])
        if setup_rc != 0:
            return setup_rc

    if not config.exists():
        print("OPENCODE_FIRST_RESULT=skipped")
        print("reason=No OpenCode provider is configured")
        return 0

    shim_rc = run([sys.executable, "scripts/devnet_openai_shim.py", "--ensure"], timeout=20)
    if shim_rc != 0:
        return shim_rc

    env = dict(os.environ)
    env["OPENCODE_CONFIG"] = str(config)
    env.setdefault("OPENCODE_DISABLE_AUTOUPDATE", "true")
    env.setdefault("OPENCODE_DISABLE_LSP_DOWNLOAD", "true")

    model = os.getenv("LLM_MODEL", "gpt-4o")
    print("OPENCODE_FIRST_RESULT=starting")
    print(f"model=devnet/{model}")
    return run(
        [
            "opencode",
            "run",
            "--agent",
            "plan",
            "--model",
            f"devnet/{model}",
            "--file",
            "AGENTS.md",
            "--file",
            "docs/quality-bar.md",
            "--title",
            "vibe-coding-first-result",
            prompt_for_first_result(),
        ],
        env=env,
    )


def run_codex() -> int:
    add_tool_dirs_to_path()
    if not shutil.which("codex"):
        print("CODEX_FIRST_RESULT=skipped")
        print("reason=codex is not installed")
        return 0

    config = ROOT / ".lab-state" / "codex" / "home" / "config.toml"
    if not config.exists():
        setup_rc = run([sys.executable, "scripts/setup_codex_devnet.py"])
        if setup_rc != 0:
            return setup_rc

    if not config.exists():
        print("CODEX_FIRST_RESULT=skipped")
        print("reason=No Codex DevNet provider is configured")
        return 0

    shim_rc = run([sys.executable, "scripts/devnet_codex_shim.py", "--ensure"], timeout=20)
    if shim_rc != 0:
        return shim_rc

    env = dict(os.environ)
    env["CODEX_HOME"] = str(config.parent)
    env.setdefault("NO_COLOR", "1")
    env.setdefault("TERM", "dumb")

    model = os.getenv("LLM_MODEL", "gpt-4o")
    print("CODEX_FIRST_RESULT=starting")
    print(f"model=devnet/{model}")
    result = subprocess.run(
        [
            "codex",
            "exec",
            "--disable",
            "plugin_sharing",
            "--ephemeral",
            "--skip-git-repo-check",
            "--cd",
            str(ROOT),
            "--sandbox",
            "read-only",
            "--color",
            "never",
            prompt_for_first_result(),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    output = (result.stdout or "").strip()
    if output:
        print(output)
    if result.returncode != 0:
        print("CODEX_FIRST_RESULT=failed")
        detail = (result.stderr or "").strip().splitlines()
        if detail:
            print(f"reason={detail[-1]}")
    return result.returncode


def run_claude() -> int:
    add_tool_dirs_to_path()
    if not shutil.which("claude"):
        print("CLAUDE_FIRST_RESULT=skipped")
        print("reason=claude is not installed")
        return 0

    auth = subprocess.run(
        ["claude", "auth", "status", "--text"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    if auth.returncode != 0:
        print("CLAUDE_FIRST_RESULT=skipped")
        print("reason=Claude Code is installed but not signed in")
        print("next_step=claude auth login")
        return 0

    write_prompt()
    print("CLAUDE_FIRST_RESULT=starting")
    return run(
        [
            "claude",
            "-p",
            "--permission-mode",
            "plan",
            "--max-turns",
            "1",
            TASK_PROMPT,
        ]
    )


def main(argv: list[str]) -> int:
    add_tool_dirs_to_path()
    parser = argparse.ArgumentParser(description="Run the first beginner AI-agent result.")
    parser.add_argument("--tool", choices=["opencode", "codex", "claude"], default="codex")
    args = parser.parse_args(argv)

    if args.tool == "opencode":
        return run_opencode()
    if args.tool == "codex":
        return run_codex()
    return run_claude()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
