#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import signal
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / ".lab-state" / "agent-prompts"
PROMPT_FILE = PROMPT_DIR / "real-coding-task.md"
TTY_SAFE_ENV = "AGENT_CODE_TTY_SAFE"
KNOWN_TOOL_DIRS = [
    "~/.local/bin",
    "~/.opencode/bin",
    "~/.bun/bin",
]

CODING_PROMPT = """Context:
You are helping with the Vibe Coding 101 dojo repo. Read AGENTS.md and docs/quality-bar.md first.

Goal:
Build BarryBot, a tiny prompt-and-answer agent that can use the lab LLM route when it is available.

Allowed files:
- dojo_app/barrybot.py
- tests/test_barrybot.py

Implementation:
- In dojo_app/barrybot.py, add:
  def route_from_env() -> dict[str, str]
  def build_messages(prompt: str) -> list[dict[str, str]]
  def redact_sensitive_text(text: str) -> str
  def ask_barrybot(prompt: str) -> str
- Prefer BARRYBOT_LLM_* env vars, then VIBE_LLM_*, then DevNet LLM_*.
- Use the OpenAI-compatible /chat/completions shape when a model route exists.
- Fall back to a deterministic local answer when no model route exists.
- Redact obvious API keys, SSN-shaped values, and email addresses from the final answer.

Tests:
- In tests/test_barrybot.py, test empty prompt rejection, message shape, route selection, deterministic fallback, and redaction.
- Do not call a real network endpoint in tests.

Verification:
Run this command before you stop:

python3 scripts/quality_gate.py

Output:
Summarize the files changed and the verification result.
"""
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def add_tool_dirs_to_path() -> None:
    paths = [os.path.expanduser(path) for path in KNOWN_TOOL_DIRS]
    os.environ["PATH"] = os.pathsep.join([*paths, os.environ.get("PATH", "")])


def log(line: str) -> None:
    print(line, flush=True)


def clean_output(text: str) -> str:
    text = ANSI_RE.sub("", text)
    return "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)


def print_captured_output(text: str) -> None:
    lines = clean_output(text).splitlines()
    if not lines:
        return

    log("AGENT_CODE_TOOL_OUTPUT=begin")
    if len(lines) > 80:
        log(f"... omitted {len(lines) - 80} earlier lines ...")
        lines = lines[-80:]
    for line in lines:
        print(line, flush=True)
    log("AGENT_CODE_TOOL_OUTPUT=end")


def rerun_away_from_tty(argv: list[str]) -> int | None:
    if os.getenv(TTY_SAFE_ENV) == "1" or not sys.stdout.isatty():
        return None

    out_path = ROOT / ".lab-state" / "agent-code-output.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env[TTY_SAFE_ENV] = "1"

    with out_path.open("w", encoding="utf-8") as out:
        process = subprocess.Popen(
            [sys.executable, __file__, *argv],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            text=True,
        )
        rc = process.wait()

    print(out_path.read_text(encoding="utf-8"), end="", flush=True)
    return rc


def run(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 240,
    capture: bool = False,
) -> int:
    try:
        process = subprocess.Popen(
            cmd,
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"RUN_STATUS=error:{exc.__class__.__name__}")
        return 1

    try:
        if capture:
            output, _ = process.communicate(timeout=timeout)
            print_captured_output(output or "")
            return process.returncode
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        log("RUN_STATUS=timeout")
        try:
            os.killpg(process.pid, signal.SIGTERM)
            if capture:
                output, _ = process.communicate(timeout=5)
                print_captured_output(output or "")
            else:
                process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if capture:
                try:
                    output, _ = process.communicate(timeout=5)
                    print_captured_output(output or "")
                except subprocess.TimeoutExpired:
                    pass
        return 1


def write_prompt() -> Path:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_FILE.write_text(CODING_PROMPT, encoding="utf-8")
    return PROMPT_FILE


def expected_change_ready() -> bool:
    bot_py = (ROOT / "dojo_app/barrybot.py").read_text(encoding="utf-8")
    tests_py = (ROOT / "tests/test_barrybot.py").read_text(encoding="utf-8")
    return "def ask_barrybot" in bot_py and "test_redacts_sensitive_values" in tests_py


def apply_guided_patch() -> None:
    bot_path = ROOT / "dojo_app/barrybot.py"
    tests_path = ROOT / "tests/test_barrybot.py"

    bot_path.write_text(
        '''from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


SYSTEM_PROMPT = (
    "You are BarryBot, a concise Cisco SE demo assistant. "
    "Answer the user directly, avoid secrets, and keep the response practical."
)
LAB_CONTEXT = [
    "The lab uses Codex CLI and OpenCode with a supplied DevNet model route.",
    "The repo check command is python3 scripts/quality_gate.py.",
    "DefenseClaw is introduced later to scan risky agent skills and extensions.",
]
SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{12,}"),
    re.compile(r"\\bAKIA[0-9A-Z]{16}\\b"),
    re.compile(r"\\b\\d{3}-\\d{2}-\\d{4}\\b"),
    re.compile(r"\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b"),
]


def route_from_env() -> dict[str, str]:
    routes = [
        ("barrybot", "BARRYBOT_LLM_BASE_URL", "BARRYBOT_LLM_API_KEY", "BARRYBOT_LLM_MODEL"),
        ("custom", "VIBE_LLM_BASE_URL", "VIBE_LLM_API_KEY", "VIBE_LLM_MODEL"),
        ("devnet", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"),
    ]

    for name, url_key, key_key, model_key in routes:
        base_url = os.getenv(url_key, "").rstrip("/")
        api_key = os.getenv(key_key, "")
        if base_url and api_key:
            return {
                "name": name,
                "base_url": base_url,
                "api_key": api_key,
                "model": os.getenv(model_key, "gpt-4o"),
            }

    return {"name": "deterministic", "base_url": "", "api_key": "", "model": "local-fallback"}


def build_messages(prompt: str) -> list[dict[str, str]]:
    clean = prompt.strip()
    if not clean:
        raise ValueError("prompt cannot be empty")

    context = "\\n".join(f"- {item}" for item in LAB_CONTEXT)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Lab context:\\n{context}\\n\\nQuestion: {clean}"},
    ]


def redact_sensitive_text(text: str) -> str:
    clean = text
    for pattern in SENSITIVE_PATTERNS:
        clean = pattern.sub("[redacted]", clean)
    return clean


def fallback_answer(prompt: str) -> str:
    clean = prompt.strip()
    if not clean:
        raise ValueError("prompt cannot be empty")

    return (
        "BarryBot local answer: keep the prompt small, check the model route, "
        f"then run python3 scripts/quality_gate.py. Question heard: {clean}"
    )


def call_model(route: dict[str, str], prompt: str, timeout: int = 20) -> str:
    payload = {
        "model": route["model"],
        "messages": build_messages(prompt),
        "temperature": 0.2,
        "max_tokens": 300,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{route['base_url']}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {route['api_key']}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    return content if isinstance(content, str) else str(content)


def ask_barrybot(prompt: str) -> str:
    route = route_from_env()
    if route["name"] == "deterministic":
        return redact_sensitive_text(fallback_answer(prompt))

    try:
        answer = call_model(route, prompt)
    except (OSError, KeyError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        answer = fallback_answer(prompt)
    return redact_sensitive_text(answer)
''',
        encoding="utf-8",
    )

    tests_path.write_text(
        '''import os
import unittest
from unittest import mock

from dojo_app import barrybot


class BarryBotTests(unittest.TestCase):
    def test_build_messages_requires_prompt(self):
        with self.assertRaises(ValueError):
            barrybot.build_messages("   ")

    def test_build_messages_includes_identity_and_context(self):
        messages = barrybot.build_messages("What is an agent?")

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("BarryBot", messages[0]["content"])
        self.assertIn("Lab context", messages[1]["content"])

    def test_route_prefers_barrybot_env(self):
        env = {
            "BARRYBOT_LLM_BASE_URL": "http://127.0.0.1:9999/v1",
            "BARRYBOT_LLM_API_KEY": "local",
            "BARRYBOT_LLM_MODEL": "gpt-4o",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            route = barrybot.route_from_env()

        self.assertEqual(route["name"], "barrybot")
        self.assertEqual(route["model"], "gpt-4o")

    def test_fallback_answer_mentions_repo_check(self):
        answer = barrybot.ask_barrybot("How do I verify?")

        self.assertIn("python3 scripts/quality_gate.py", answer)

    def test_redacts_sensitive_values(self):
        text = "sk-thisIsFakeButLongEnough user@example.com 111-22-3333 AKIA1111111111111111"  # lab-scanner: ignore

        clean = barrybot.redact_sensitive_text(text)

        self.assertNotIn("sk-thisIsFake", clean)
        self.assertNotIn("user@example.com", clean)  # lab-scanner: ignore
        self.assertNotIn("111-22-3333", clean)  # lab-scanner: ignore
        self.assertNotIn("AKIA1111111111111111", clean)  # lab-scanner: ignore


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


def print_diff() -> int:
    log("AGENT_CODE_DIFF=begin")
    rc = run(["git", "diff", "--", "dojo_app/barrybot.py", "tests/test_barrybot.py"], timeout=20)
    log("AGENT_CODE_DIFF=end")
    return rc


def codex_home() -> Path:
    return ROOT / ".lab-state" / "codex" / "home"


def codex_config() -> Path:
    return codex_home() / "config.toml"


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
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
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
            "vibe-coding-barrybot",
            CODING_PROMPT,
        ],
        env=env,
        timeout=25,
        capture=True,
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


def run_codex() -> int:
    add_tool_dirs_to_path()
    if not shutil.which("codex"):
        log("AGENT_CODE_TASK=skipped")
        log("reason=codex is not installed")
        return 0

    setup_rc = run([sys.executable, "scripts/setup_codex_devnet.py"], timeout=20)
    if setup_rc != 0:
        return setup_rc

    if not codex_config().exists():
        log("AGENT_CODE_TASK=skipped")
        log("reason=No Codex DevNet provider is configured")
        return 0

    shim_rc = run([sys.executable, "scripts/devnet_codex_shim.py", "--ensure"], timeout=20)
    if shim_rc != 0:
        return shim_rc

    prompt_file = write_prompt()
    env = dict(os.environ)
    env["CODEX_HOME"] = str(codex_home())
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"

    log("AGENT_CODE_TASK=starting")
    log("tool=codex")
    log(f"prompt_file={prompt_file.relative_to(ROOT)}")
    rc = run(
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
            "workspace-write",
            "--color",
            "never",
            CODING_PROMPT,
        ],
        env=env,
        timeout=35,
        capture=True,
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
        stdin=subprocess.DEVNULL,
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
    parser.add_argument("--tool", choices=["opencode", "codex", "claude"], default="codex")
    parser.add_argument("--print-prompt", action="store_true")
    args = parser.parse_args(argv)

    if args.print_prompt:
        path = write_prompt()
        log(f"AGENT_CODE_PROMPT={path.relative_to(ROOT)}")
        print(CODING_PROMPT, flush=True)
        return 0

    rerun_rc = rerun_away_from_tty(argv)
    if rerun_rc is not None:
        return rerun_rc

    if args.tool == "opencode":
        return run_opencode()
    if args.tool == "codex":
        return run_codex()
    return run_claude()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
