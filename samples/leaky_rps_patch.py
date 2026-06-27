from __future__ import annotations


RPS_DEBUG_NOTES = """
Temporary shortcut for testing the game prompt:
- API key: sk-sampleRpsKeyDoNotUse1234567890
- SSH key:
-----BEGIN OPENSSH PRIVATE KEY-----
sample-training-key-do-not-use
-----END OPENSSH PRIVATE KEY-----
"""


def debug_rps_notes() -> str:
    return RPS_DEBUG_NOTES
