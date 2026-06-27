from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


VALID_MODES = {"human-vs-computer", "human-vs-human"}
PLAYERS = {"X", "O"}
EMPTY = "."
BOARD_HEADER_RE = re.compile(r"^BOARD\s*:?\s*$", re.IGNORECASE)
KEY_VALUE_RE = re.compile(r"^(MODE|NEXT)\s*[:=]\s*(.+)$", re.IGNORECASE)
MODE_TEXT_RE = re.compile(r"human\s*[- ]?\s*vs\.?\s*[- ]?\s*(computer|human)", re.IGNORECASE)
NEXT_TEXT_RE = re.compile(r"\bnext\b[^XO]{0,40}\b([XO])\b", re.IGNORECASE)
DEFAULT_SCENARIO_TEXT = """MODE: human-vs-computer
NEXT: X
BOARD:
. . .
. . .
. . .
"""


@dataclass(frozen=True)
class Scenario:
    mode: str
    next_player: str
    board: tuple[str, ...]


def normalize_cell(token: str) -> str | None:
    value = token.strip().upper()
    if value in {"X", "O"}:
        return value
    if value in {".", "_", "-", "0"}:
        return EMPTY
    return None


def parse_board_row(line: str) -> str | None:
    raw = line.strip()
    if not raw:
        return None

    if "|" in raw:
        parts = [part.strip() for part in raw.split("|")]
    elif " " in raw:
        parts = [part.strip() for part in raw.split()]
    else:
        parts = list(raw)

    if len(parts) != 3:
        return None

    cells = []
    for part in parts:
        cell = normalize_cell(part)
        if cell is None:
            return None
        cells.append(cell)
    return "".join(cells)


def winner(board: tuple[str, ...]) -> str | None:
    wins = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )
    for a, b, c in wins:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return None


def board_full(board: tuple[str, ...]) -> bool:
    return EMPTY not in board


def validate_scenario(scenario: Scenario) -> None:
    if scenario.mode not in VALID_MODES:
        raise ValueError("mode must be human-vs-computer or human-vs-human")
    if scenario.next_player not in PLAYERS:
        raise ValueError("next player must be X or O")
    if len(scenario.board) != 9:
        raise ValueError("board must contain exactly nine cells")
    if set(scenario.board) - {EMPTY, "X", "O"}:
        raise ValueError("board cells must be X, O, or .")

    x_count = scenario.board.count("X")
    o_count = scenario.board.count("O")
    if o_count > x_count or x_count > o_count + 1:
        raise ValueError("board has an impossible move count")
    if winner(scenario.board) and not board_full(scenario.board):
        raise ValueError("scenario should start before a finished game")

    expected = "X" if x_count == o_count else "O"
    if scenario.next_player != expected:
        raise ValueError(f"next player should be {expected} for this board")


def expected_next_player(board: tuple[str, ...]) -> str:
    return "X" if board.count("X") == board.count("O") else "O"


def infer_mode(text: str) -> str:
    match = MODE_TEXT_RE.search(text)
    if not match:
        return ""
    opponent = match.group(1).lower()
    if opponent == "computer":
        return "human-vs-computer"
    return "human-vs-human"


def infer_next_player(text: str, board: tuple[str, ...]) -> str:
    match = NEXT_TEXT_RE.search(text)
    if match:
        return match.group(1).upper()
    return expected_next_player(board)


def parse_scenario(text: str) -> Scenario:
    mode = ""
    next_player = ""
    rows: list[str] = []
    in_board = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        key_match = KEY_VALUE_RE.match(line)
        if key_match:
            key = key_match.group(1).upper()
            value = key_match.group(2).strip()
            if key == "MODE":
                mode = value.lower()
            elif key == "NEXT":
                next_player = value.upper()
            continue
        if BOARD_HEADER_RE.match(line):
            in_board = True
            continue

        row = parse_board_row(line)
        if row and (in_board or len(rows) < 3):
            rows.append(row)
            if len(rows) == 3:
                in_board = False

    if len(rows) != 3:
        raise ValueError("scenario needs a 3x3 board")

    board = tuple("".join(rows))
    if not mode:
        mode = infer_mode(text)
    if not next_player:
        next_player = infer_next_player(text, board)

    scenario = Scenario(mode=mode, next_player=next_player, board=board)
    validate_scenario(scenario)
    return scenario


def format_scenario(scenario: Scenario) -> str:
    rows = [" ".join(scenario.board[index : index + 3]) for index in range(0, 9, 3)]
    return "\n".join(
        [
            f"MODE: {scenario.mode}",
            f"NEXT: {scenario.next_player}",
            "BOARD:",
            *rows,
            "",
        ]
    )


def load_scenario(path: str | None = None) -> Scenario:
    if not path:
        return parse_scenario(DEFAULT_SCENARIO_TEXT)
    return parse_scenario(Path(path).read_text(encoding="utf-8"))


def write_scenario(path: str, scenario: Scenario) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_scenario(scenario), encoding="utf-8")


def render_board(board: tuple[str, ...]) -> str:
    display = []
    for index, cell in enumerate(board):
        display.append(str(index + 1) if cell == EMPTY else cell)
    return "\n".join(
        [
            f" {display[0]} | {display[1]} | {display[2]} ",
            "---+---+---",
            f" {display[3]} | {display[4]} | {display[5]} ",
            "---+---+---",
            f" {display[6]} | {display[7]} | {display[8]} ",
        ]
    )


def run_scenario_check(scenario: Scenario) -> None:
    print("TICTACTOE_CHECK=ready")
    print(f"mode={scenario.mode}")
    print(f"next={scenario.next_player}")
    print(f"empty_cells={scenario.board.count(EMPTY)}")
    print("winner=none")
    print("TICTACTOE_CHECK=pass")


def run_static_scenario(scenario: Scenario) -> None:
    print("Tic-tac-toe starting board")
    print(f"Game mode: {scenario.mode.replace('-vs-', ' vs ')}")
    print(f"Next player: {scenario.next_player}")
    print("Open squares are numbered 1-9 for the next move.")
    print(render_board(scenario.board))
    print("Scenario is ready for play mode.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or play a tiny terminal tic-tac-toe scenario.")
    parser.add_argument("--scenario-file", help="File containing MODE, NEXT, and BOARD lines")
    parser.add_argument("--write-clean", help="Write the parsed scenario back in the tiny format")
    parser.add_argument("--check-only", action="store_true", help="Validate the scenario without playing")
    parser.add_argument("--play", action="store_true", help="Play from the scenario")
    args = parser.parse_args(argv)

    try:
        scenario = load_scenario(args.scenario_file)
    except (OSError, ValueError) as exc:
        marker = "TICTACTOE_CHECK=fail" if args.check_only else "TICTACTOE_BOARD=fail"
        print(marker)
        print(f"reason={exc}")
        return 1

    if args.write_clean:
        try:
            write_scenario(args.write_clean, scenario)
        except OSError as exc:
            print("TICTACTOE=fail")
            print(f"reason={exc}")
            return 1

    if args.check_only:
        run_scenario_check(scenario)
        return 0

    if args.play:
        from dojo_app.tictactoe_play import run_tictactoe

        return run_tictactoe(scenario)

    run_static_scenario(scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
