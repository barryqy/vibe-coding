#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / ".lab-state" / "agent-prompts"
PROMPT_FILE = PROMPT_DIR / "shared-quality-task.md"
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


TASK_PROMPT = """Context:
You are helping with the Vibe Coding 101 dojo repo. Read AGENTS.md and docs/quality-bar.md before proposing changes.

Goal:
Improve the tiny task tracker without making broad rewrites. Propose one small change: add a way to list only high-priority open tasks.

Constraints:
- Plan only. Do not edit files during this pass.
- Keep the public examples free of secrets and private data.
- Preserve the existing tests and app API unless you explain why they should change.
- Do not read .env, .env.*, secrets/, browser profiles, SSH keys, or cloud credentials.

Verification:
Before a patch can be trusted, the repo must pass:

python3 scripts/quality_gate.py

Memory:
If this becomes a real implementation decision, save it with scripts/make_second_brain_note.py.

Output:
Return a short plan with the files you would touch, the test you would add, and the verification command.
"""


def command_path(name: str) -> str:
    return shutil.which(name) or "not found"


def write_prompt() -> Path:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_FILE.write_text(TASK_PROMPT, encoding="utf-8")
    return PROMPT_FILE


def devnet_config() -> Path:
    return ROOT / ".lab-state" / "opencode-devnet.json"


def devnet_model() -> str:
    return os.getenv("LLM_MODEL", "gpt-4o")


def claude_command(prompt_file: Path) -> list[str]:
    prompt = prompt_file.read_text(encoding="utf-8")
    return [
        "claude",
        "-p",
        "--permission-mode",
        "plan",
        "--max-turns",
        "1",
        prompt,
    ]


def opencode_command(prompt_file: Path) -> list[str]:
    prompt = prompt_file.read_text(encoding="utf-8")
    cmd = [
        "opencode",
        "run",
        "--title",
        "vibe-coding-quality-loop",
        "--agent",
        "plan",
        "--file",
        "AGENTS.md",
        "--file",
        "docs/quality-bar.md",
    ]
    if devnet_config().exists():
        cmd.extend(["--model", f"devnet/{devnet_model()}"])
    cmd.append(prompt)
    return cmd


def shell_preview(tool: str, prompt_file: Path) -> str:
    rel_prompt = prompt_file.relative_to(ROOT)
    if tool == "claude":
        return f'claude -p --permission-mode plan --max-turns 1 "$(cat {rel_prompt})"'
    prefix = ""
    model = ""
    if devnet_config().exists():
        prefix = f"OPENCODE_CONFIG={devnet_config().relative_to(ROOT)} "
        model = f"--model devnet/{devnet_model()} "
    return f'{prefix}opencode run --title vibe-coding-quality-loop --agent plan {model}--file AGENTS.md --file docs/quality-bar.md "$(cat {rel_prompt})"'


def auth_ready(tool: str) -> tuple[bool, str]:
    if command_path(tool) == "not found":
        return False, "not-installed"

    if tool == "claude":
        cmd = ["claude", "auth", "status", "--text"]
    else:
        if devnet_config().exists():
            return True, "ready-devnet-config"
        cmd = ["opencode", "auth", "list"]

    try:
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=10, check=False)
    except subprocess.TimeoutExpired:
        return False, "auth-check-timeout"
    except OSError as exc:
        return False, f"auth-check-error:{exc.__class__.__name__}"

    if result.returncode == 0:
        return True, "ready"

    message = (result.stderr or result.stdout).strip().splitlines()
    detail = message[0] if message else "not-authenticated"
    return False, detail


def run_tool(tool: str, prompt_file: Path) -> int:
    ready, reason = auth_ready(tool)
    if not ready:
        print(f"{tool.upper()}_RUN=skipped")
        print(f"reason={reason}")
        return 0

    cmd = claude_command(prompt_file) if tool == "claude" else opencode_command(prompt_file)
    print(f"{tool.upper()}_RUN=starting")
    env = dict(os.environ)
    if tool == "opencode" and devnet_config().exists():
        env["OPENCODE_CONFIG"] = str(devnet_config())
        env.setdefault("OPENCODE_DISABLE_AUTOUPDATE", "true")
        env.setdefault("OPENCODE_DISABLE_LSP_DOWNLOAD", "true")
    result = subprocess.run(cmd, cwd=ROOT, env=env, text=True, timeout=120, check=False)
    print(f"{tool.upper()}_RUN_RC={result.returncode}")
    return 0 if result.returncode == 0 else result.returncode


def print_rules() -> None:
    print("AGENT_RULES=loaded")
    print("Claude Code reads CLAUDE.md and project settings under .claude/settings.json.")
    print("OpenCode reads AGENTS.md and combines configured instruction files from opencode.json.")
    print("Both tools should use the same verification command: python3 scripts/quality_gate.py")


def main(argv: list[str]) -> int:
    add_tool_dirs_to_path()
    parser = argparse.ArgumentParser(description="Compare Claude Code and OpenCode on the same scoped task.")
    parser.add_argument("--tool", choices=["both", "claude", "opencode"], default="both")
    parser.add_argument("--run", action="store_true", help="Run the selected tool only if it is installed and authenticated.")
    parser.add_argument("--show-rules", action="store_true", help="Print the rule files each tool uses.")
    args = parser.parse_args(argv)

    prompt_file = write_prompt()
    tools = ["claude", "opencode"] if args.tool == "both" else [args.tool]

    print("AGENT_COMPARE=ready")
    print(f"prompt_file={prompt_file.relative_to(ROOT)}")
    print(f"claude={command_path('claude')}")
    print(f"opencode={command_path('opencode')}")

    if args.show_rules:
        print_rules()

    for tool in tools:
        print(f"\n[{tool}]")
        print(f"command={shell_preview(tool, prompt_file)}")
        if args.run:
            rc = run_tool(tool, prompt_file)
            if rc != 0:
                return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
