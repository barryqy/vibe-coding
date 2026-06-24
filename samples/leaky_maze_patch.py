from __future__ import annotations


MAZE_DEBUG_NOTES = """
Temporary shortcut for testing the maze loader:
- API key: sk-thisIsAFakeMazeKey1234567890
- SSH key:
-----BEGIN OPENSSH PRIVATE KEY-----
fake-training-key-do-not-use
-----END OPENSSH PRIVATE KEY-----
"""


def debug_maze_loader() -> str:
    return MAZE_DEBUG_NOTES
