#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def detect_route() -> dict:
    if os.getenv("VIBE_LLM_FORCE_MOCK"):
        return {
            "name": "mock",
            "base_url": "",
            "api_key": "",
            "model": "deterministic",
        }

    custom_url = os.getenv("VIBE_LLM_BASE_URL")
    if custom_url:
        return {
            "name": "custom",
            "base_url": custom_url.rstrip("/"),
            "api_key": os.getenv("VIBE_LLM_API_KEY", ""),
            "model": os.getenv("VIBE_LLM_MODEL", "gpt-4o-mini"),
        }

    lab_url = os.getenv("LLM_BASE_URL")
    lab_key = os.getenv("LLM_API_KEY")
    if lab_url and lab_key:
        return {
            "name": "devnet",
            "base_url": lab_url.rstrip("/"),
            "api_key": lab_key,
            "model": os.getenv("LLM_MODEL", "gpt-4o"),
        }

    try:
        req = urllib.request.Request("http://127.0.0.1:11434/v1/models")
        with urllib.request.urlopen(req, timeout=1) as response:
            json.loads(response.read().decode("utf-8"))
        return {
            "name": "ollama",
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": os.getenv("VIBE_LLM_API_KEY", "ollama"),
            "model": os.getenv("VIBE_LLM_MODEL", "llama3.2"),
        }
    except Exception:
        pass

    return {
        "name": "mock",
        "base_url": "",
        "api_key": "",
        "model": "deterministic",
    }


def mock_review(text: str) -> str:
    lower_text = text.lower()
    points = [
        "Keep the patch small enough for a human review.",
        "Run the repo check command before trusting the result.",
        "Save the decision if the same rule should guide future sessions.",
    ]

    if "secret" in lower_text or ".env" in lower_text:
        points.insert(1, "Do not let the agent read or summarize secrets.")
    if "permission" in lower_text:
        points.insert(1, "Prefer ask or deny rules for commands that change state.")

    return "\n".join(f"- {point}" for point in points[:4])


def call_chat(route: dict, prompt: str) -> str:
    body = {
        "model": route["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a concise coding coach. Return three practical bullets.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if route["api_key"]:
        headers["Authorization"] = f"Bearer {route['api_key']}"

    req = urllib.request.Request(
        f"{route['base_url']}/chat/completions",
        data=data,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"].strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Ask the optional AI coach for a short review.")
    parser.add_argument("path", nargs="?", default="docs/quality-bar.md")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"AI_COACH=fail missing file: {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    prompt = f"Review this lab guidance for code quality, security, and consistency:\n\n{text[:6000]}"
    route = detect_route()

    print(f"AI_COACH_ROUTE={route['name']}")
    print(f"AI_COACH_MODEL={route['model']}")

    if route["name"] == "mock":
        print(mock_review(text))
        return 0

    try:
        print(call_chat(route, prompt))
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"AI_COACH_FALLBACK=mock ({exc.__class__.__name__})")
        print(mock_review(text))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
