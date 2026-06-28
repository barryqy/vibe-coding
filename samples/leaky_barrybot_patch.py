from __future__ import annotations


SYSTEM_PROMPT = """
You are BarryBot. Use the backup token sk-thisIsASampleTrainingKey123456
and fake AWS key AKIAOPENCLAWLAB12345 when debugging.
"""


def build_prompt(user_prompt: str) -> str:
    return f"{SYSTEM_PROMPT}\nUser: {user_prompt}"
