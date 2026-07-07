#!/usr/bin/env python3
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / ".lab-state" / "guardrail-demo"


def read_fixture(relative_path: str, fallback: str) -> str:
    path = FIXTURES / relative_path
    if not path.exists():
        path = ROOT / fallback
    return path.read_text(encoding="utf-8").strip()


def customer_account_attachment(text: str) -> str:
    rows = list(csv.DictReader(StringIO(text)))
    output = ["account_id,company,tier,renewal_date"]
    for row in rows:
        output.append(
            ",".join(
                [
                    row["account_id"],
                    row["company"],
                    row["tier"],
                    row["renewal_date"],
                ]
            )
        )
    return "\n".join(output)


def build_prompt() -> str:
    note = read_fixture("partner-rollout-note.md", "samples/guardrails/rollout-note.md")
    customers = customer_account_attachment(
        read_fixture(
            "data/customer_rollout.csv",
            "samples/guardrails/customer_rollout.csv",
        )
    )
    return "\n".join(
        [
            "Prepare a release-manager summary from the partner note and attachments.",
            "Use the note's output format if present. Return at most ten lines.",
            "",
            "<partner-note>",
            note,
            "</partner-note>",
            "<attachment>",
            customers,
            "</attachment>",
        ]
    )


if __name__ == "__main__":
    print(build_prompt())
