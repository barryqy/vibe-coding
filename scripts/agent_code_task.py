#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / ".lab-state" / "agent-prompts"
PROMPT_FILE = PROMPT_DIR / "real-coding-task.md"
KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
    "~/.claude/bin",
    "~/.claude/local",
]

CODING_PROMPT = """Context:
You are helping with the Vibe Coding 101 dojo repo. Read AGENTS.md and docs/quality-bar.md first.

Goal:
Make a real, small code change. Add a helper that lists only high-priority tasks that are still open.

Allowed files:
- dojo_app/tasks.py
- tests/test_tasks.py

Implementation:
- In dojo_app/tasks.py, add:
  def list_high_priority_open_tasks(tasks: list[dict]) -> list[dict]
- Return copies of matching task dictionaries, like list_tasks does.
- A matching task has priority == "high" and done is false.
- Do not change existing public functions.

Tests:
- In tests/test_tasks.py, import the new helper.
- Add a unit test that creates a high open task, a high completed task, and a normal open task.
- Assert that only the high open task is returned.

Verification:
Run this command before you stop:

python3 scripts/quality_gate.py

Output:
Summarize the files changed and the verification result.
"""


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


def log(line: str) -> None:
    print(line, flush=True)


def run(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 240) -> int:
    try:
        process = subprocess.Popen(
            cmd,
            cwd=ROOT,
            env=env,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"RUN_STATUS=error:{exc.__class__.__name__}")
        return 1

    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        log("RUN_STATUS=timeout")
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return 1


def write_prompt() -> Path:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_FILE.write_text(CODING_PROMPT, encoding="utf-8")
    return PROMPT_FILE


def expected_change_ready() -> bool:
    tasks_py = (ROOT / "dojo_app/tasks.py").read_text(encoding="utf-8")
    tests_py = (ROOT / "tests/test_tasks.py").read_text(encoding="utf-8")
    return "def list_high_priority_open_tasks" in tasks_py and "list_high_priority_open_tasks" in tests_py


def apply_guided_patch() -> None:
    tasks_path = ROOT / "dojo_app/tasks.py"
    tests_path = ROOT / "tests/test_tasks.py"

    tasks_py = tasks_path.read_text(encoding="utf-8")
    if "def list_high_priority_open_tasks" not in tasks_py:
        marker = "\n\ndef summarize(tasks: list[dict]) -> dict:\n"
        helper = '''

def list_high_priority_open_tasks(tasks: list[dict]) -> list[dict]:
    found = []
    for task in tasks:
        if task.get("done"):
            continue
        if task.get("priority") != "high":
            continue
        found.append(dict(task))
    return found
'''
        tasks_py = tasks_py.replace(marker, helper + marker, 1)
        tasks_path.write_text(tasks_py, encoding="utf-8")

    tests_py = tests_path.read_text(encoding="utf-8")
    tests_changed = False
    import_block = "\n".join(tests_py.split("\n", 5)[0:5])
    if "list_high_priority_open_tasks" not in import_block:
        tests_py = tests_py.replace(
            "from dojo_app.tasks import add_task, complete_task, list_tasks, summarize\n",
            "from dojo_app.tasks import add_task, complete_task, list_high_priority_open_tasks, list_tasks, summarize\n",
            1,
        )
        tests_changed = True

    if "test_list_high_priority_open_tasks_filters_done_and_normal_priority" not in tests_py:
        marker = "\n    def test_summarize_counts_status(self):\n"
        test_case = '''
    def test_list_high_priority_open_tasks_filters_done_and_normal_priority(self):
        tasks = []
        high_open = add_task(tasks, "fix customer bug", priority="high")
        high_done = add_task(tasks, "ship demo", priority="high")
        add_task(tasks, "clean up notes", priority="normal")
        complete_task(tasks, high_done["id"])

        found = list_high_priority_open_tasks(tasks)

        self.assertEqual(found, [high_open])
        self.assertIsNot(found[0], high_open)
'''
        tests_py = tests_py.replace(marker, test_case + marker, 1)
        tests_changed = True

    if tests_changed:
        tests_path.write_text(tests_py, encoding="utf-8")


def print_diff() -> int:
    log("AGENT_CODE_DIFF=begin")
    rc = run(["git", "diff", "--", "dojo_app/tasks.py", "tests/test_tasks.py"], timeout=20)
    log("AGENT_CODE_DIFF=end")
    return rc


def run_opencode() -> int:
    add_tool_dirs_to_path()
    if not shutil.which("opencode"):
        log("AGENT_CODE_TASK=skipped")
        log("reason=opencode is not installed")
        return 0

    setup_rc = run([sys.executable, "scripts/setup_opencode_devnet.py"], timeout=20)
    if setup_rc != 0:
        return setup_rc

    config = ROOT / ".lab-state" / "opencode-devnet.json"
    if not config.exists():
        log("AGENT_CODE_TASK=skipped")
        log("reason=No OpenCode provider is configured")
        return 0

    shim_rc = run([sys.executable, "scripts/devnet_openai_shim.py", "--ensure"], timeout=20)
    if shim_rc != 0:
        return shim_rc

    prompt_file = write_prompt()
    env = dict(os.environ)
    env["OPENCODE_CONFIG"] = str(config)
    env.setdefault("OPENCODE_DISABLE_AUTOUPDATE", "true")
    env.setdefault("OPENCODE_DISABLE_LSP_DOWNLOAD", "true")

    log("AGENT_CODE_TASK=starting")
    log(f"prompt_file={prompt_file.relative_to(ROOT)}")
    rc = run(
        [
            "opencode",
            "run",
            "--dangerously-skip-permissions",
            "--agent",
            "build",
            "--model",
            f"devnet/{os.getenv('LLM_MODEL', 'gpt-4o')}",
            "--file",
            "AGENTS.md",
            "--file",
            "docs/quality-bar.md",
            "--title",
            "vibe-coding-real-code",
            CODING_PROMPT,
        ],
        env=env,
        timeout=25,
    )
    log(f"AGENT_CODE_TOOL_RC={rc}")

    print_diff()
    if rc == 0 and expected_change_ready():
        log("AGENT_CODE_APPLY=agent-edit")
    else:
        log("AGENT_CODE_APPLY=guided-patch")
        log("reason=The provider did not complete file edits in this lab run.")
        apply_guided_patch()
        print_diff()

    log("AGENT_CODE_VERIFY=starting")
    verify_rc = run([sys.executable, "scripts/quality_gate.py"], timeout=120)
    if verify_rc != 0:
        return verify_rc

    log("AGENT_CODE_TASK=pass")
    return 0


def run_claude() -> int:
    add_tool_dirs_to_path()
    if not shutil.which("claude"):
        log("AGENT_CODE_TASK=skipped")
        log("reason=claude is not installed")
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
        log("AGENT_CODE_TASK=skipped")
        log("reason=Claude Code is installed but not signed in")
        log("next_step=claude auth login")
        return 0

    prompt_file = write_prompt()
    log("AGENT_CODE_TASK=starting")
    log(f"prompt_file={prompt_file.relative_to(ROOT)}")
    rc = run(["claude", "-p", "--max-turns", "8", CODING_PROMPT], timeout=240)
    if rc != 0:
        return rc
    print_diff()
    return run([sys.executable, "scripts/quality_gate.py"], timeout=120)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Let a coding agent make a small real patch.")
    parser.add_argument("--tool", choices=["opencode", "claude"], default="opencode")
    parser.add_argument("--print-prompt", action="store_true")
    args = parser.parse_args(argv)

    if args.print_prompt:
        path = write_prompt()
        log(f"AGENT_CODE_PROMPT={path.relative_to(ROOT)}")
        print(CODING_PROMPT, flush=True)
        return 0

    if args.tool == "opencode":
        return run_opencode()
    return run_claude()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
