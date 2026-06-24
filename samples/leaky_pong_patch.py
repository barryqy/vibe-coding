from __future__ import annotations


PONG_DEBUG_NOTES = """
Temporary shortcut for testing the scoreboard:
- API key: sk-thisIsAFakePongKey1234567890
- SSH key:
-----BEGIN OPENSSH PRIVATE KEY-----
fake-training-key-do-not-use
-----END OPENSSH PRIVATE KEY-----
"""


def debug_scoreboard() -> str:
    return PONG_DEBUG_NOTES
