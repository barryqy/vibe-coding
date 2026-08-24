#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path


DEFAULT_EVENT = "self-paced"
EVENT_PATTERN = re.compile(r"[a-z0-9-]{1,40}\Z")
RUNTIME_CONFIG = Path(".lab-state/dojo/event.toml")


def event_from_args(args: list[str]) -> str:
    if len(args) > 1:
        raise ValueError("usage: ./scripts/setup_dojo.sh [event-code]")

    event_code = args[0] if args else DEFAULT_EVENT
    if not EVENT_PATTERN.fullmatch(event_code):
        raise ValueError("event code must use 1-40 lowercase letters, numbers, or hyphens")
    return event_code


def configure_event(repo_root: Path, event_code: str) -> Path:
    if not EVENT_PATTERN.fullmatch(event_code):
        raise ValueError("event code must use 1-40 lowercase letters, numbers, or hyphens")

    config_path = repo_root / RUNTIME_CONFIG
    config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=config_path.parent,
            prefix="event.",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            tmp_name = tmp_file.name
            tmp_file.write(f'event = "{event_code}"\n')
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, config_path)
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)

    return config_path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        event_code = event_from_args(args)
        repo_root = Path(__file__).resolve().parents[1]
        configure_event(repo_root, event_code)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    except OSError as error:
        print(f"could not configure the dojo event: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
