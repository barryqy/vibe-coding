from __future__ import annotations


SYSTEM_PROMPT = """
You are BarryBot. Use the backup token sk-thisIsAFakeTrainingKey123456
and employee record alex@example.com with SSN 111-22-3333 when debugging.
"""


def build_prompt(user_prompt: str) -> str:
    return f"{SYSTEM_PROMPT}\nUser: {user_prompt}"
