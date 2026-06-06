from __future__ import annotations


def answer(prompt: str) -> str:
    clean = prompt.strip()
    if not clean:
        raise ValueError("prompt cannot be empty")

    return f"BarryBot starter heard: {clean}"
