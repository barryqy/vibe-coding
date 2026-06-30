from __future__ import annotations

import argparse
import os
import re
import sys
from typing import TextIO


RESET = "\033[0m"
COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}

GOOD_WORDS = (
    "pass",
    "ok",
    "complete",
    "clean",
    "blocked",
    "observed",
    "inspected",
    "system-present",
    "bundled-codex",
    "already-present",
    "using-existing",
)
WORKING_WORDS = (
    "ready",
    "starting",
    "creating-venv",
    "installing-cli",
    "initializing-home",
    "upgrading-pip",
    "rebuilding-venv",
    "rebuilding-incomplete-venv",
)
WARN_WORDS = (
    "unknown",
    "not-reported",
    "not-found",
    "not-installed",
    "missing-dependency",
    "not-implemented",
    "check-output",
    "fallback",
    "note",
    "skipped",
    "budget-exhausted",
    "model-budget-exhausted",
    "rate_limit",
)
BAD_WORDS = (
    "fail",
    "failed",
    "unexpected",
    "missed",
    "flagged",
    "invalid",
    "error",
)
RISK_WORDS = (
    "akia",
    "aws_",
    "aws access key",
    "secret access key",
    "credential-shaped",
    "aws_credentials",
    "eval_marker",
    "shell_marker",
    "rce_marker",
    "stolen_",
    "local-files-written",
    "oops_",
    "shell=true",
    "eval(",
)
INJECTION_WORDS = (
    "launch is healthy",
    "no rollback trigger",
    "launch state:",
    "rollback condition:",
    "support channel:",
)


def color_enabled(stream: TextIO | None = None) -> bool:
    target = stream or sys.stdout
    force = os.getenv("DOJO_COLOR") or os.getenv("CLICOLOR_FORCE")
    if force and force not in {"0", "false", "False", "no"}:
        return True
    if os.getenv("NO_COLOR") or os.getenv("TERM") == "dumb":
        return False
    return bool(getattr(target, "isatty", lambda: False)())


def paint(text: str, color: str | None, stream: TextIO | None = None) -> str:
    if not color or not color_enabled(stream):
        return text

    code = COLORS.get(color)
    if not code:
        return text
    return f"{code}{text}{RESET}"


def _value_after_equals(line: str) -> str:
    if "=" not in line:
        return ""
    return line.split("=", 1)[1].strip().lower()


def status_color(line: str) -> str | None:
    text = line.strip()
    lower = text.lower()
    value = _value_after_equals(text)

    if text.startswith("[OK]"):
        return "green"
    if text.startswith("[FAIL]"):
        return "red"
    if re.match(r"^\[(critical|high)\]", lower):
        return "red"
    if re.match(r"^\[(medium)\]", lower):
        return "yellow"
    if re.match(r"^\[(low)\]", lower):
        return "cyan"
    if lower.startswith("scenario_group="):
        return "bold"
    if lower.startswith("risk=") or lower.startswith("recommended_gate="):
        return "yellow"
    if any(word in lower for word in INJECTION_WORDS):
        return "yellow"
    if lower.startswith("oops_") or "local-files-written" in lower:
        return "red"
    if any(word in lower for word in RISK_WORDS):
        return "yellow"

    if any(word in value for word in BAD_WORDS):
        return "red"
    if any(word in value for word in WARN_WORDS):
        return "yellow"
    if any(word in value for word in GOOD_WORDS):
        return "green"
    if any(word in value for word in WORKING_WORDS):
        return "cyan"

    if lower.startswith("next="):
        return "yellow"
    return None


def format_status(line: str, stream: TextIO | None = None) -> str:
    return paint(line, status_color(line), stream)


def print_status(line: str, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    print(format_status(line, target), file=target)


def print_color(text: str, color: str, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    print(paint(text, color, target), file=target)


def print_section(text: str, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    print(file=target)
    print(paint(text, "cyan", target), file=target)


def print_stream(source: TextIO | None = None, stream: TextIO | None = None) -> None:
    source = source or sys.stdin
    target = stream or sys.stdout
    for raw_line in source:
        print(format_status(raw_line.rstrip("\n"), target), file=target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print short colored lab messages.")
    parser.add_argument(
        "mode",
        choices=["status", "section", "stream", *COLORS.keys()],
        help="Use status for marker lines, section for headings, or an explicit color.",
    )
    parser.add_argument("text", nargs="*")
    args = parser.parse_args(argv)

    if args.mode == "stream":
        print_stream()
        return 0

    if not args.text:
        parser.error(f"{args.mode} requires text")

    text = " ".join(args.text)
    if args.mode == "status":
        print_status(text)
    elif args.mode == "section":
        print_section(text)
    else:
        print_color(text, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
