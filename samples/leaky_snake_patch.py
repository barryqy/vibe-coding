from __future__ import annotations


SNAKE_DEBUG_NOTES = """
Temporary shortcut for testing the scoreboard:
- API key: sk-thisIsAFakeSnakeKey1234567890
- SSH key:
-----BEGIN OPENSSH PRIVATE KEY-----
fake-training-key-do-not-use
-----END OPENSSH PRIVATE KEY-----
"""


def debug_scoreboard() -> str:
    return SNAKE_DEBUG_NOTES
