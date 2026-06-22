#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    value = text.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "decision"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a small second-brain decision note.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--why", required=True)
    parser.add_argument("--evidence", default="python3 scripts/check_repo.py")
    args = parser.parse_args()

    folder = Path(".second-brain/decisions")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{date.today().isoformat()}-{slugify(args.title)}.md"

    body = f"""---
type: decision
status: active
---

# {args.title}

## Decision

{args.title}

## Why It Matters

{args.why}

## Evidence

- {args.evidence}
"""
    path.write_text(body, encoding="utf-8")

    print("SECOND_BRAIN_NOTE=created")
    print(f"path={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

