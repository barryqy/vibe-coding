from __future__ import annotations

from typing import Protocol


class ScenarioLike(Protocol):
    mode: str
    next_player: str
    board: tuple[str, ...]


def run_tictactoe(scenario: ScenarioLike) -> int:
    print("TICTACTOE_PLAY=ready")
    print(f"mode={scenario.mode}")
    print("TICTACTOE_PLAY=not-implemented")
    print("reason=OpenCode will replace run_tictactoe in dojo_app/tictactoe_play.py")
    return 1
