from __future__ import annotations

import argparse
from dataclasses import dataclass


WIDTH = 32
HEIGHT = 9
PADDLE_SIZE = 3
DEFAULT_MOVES = "stay,stay,stay,stay,s,w,s,w"


@dataclass(frozen=True)
class GameState:
    human_y: int = 3
    cpu_y: int = 3
    ball_x: int = 5
    ball_y: int = 4
    ball_dx: int = -1
    ball_dy: int = 0
    human_score: int = 0
    cpu_score: int = 0


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def move_delta(move: str) -> int:
    cleaned = move.strip().lower()
    if cleaned in {"w", "up", "u"}:
        return -1
    if cleaned in {"s", "down", "d"}:
        return 1
    return 0


def paddle_cells(top: int) -> set[int]:
    return set(range(top, top + PADDLE_SIZE))


def cpu_step(cpu_y: int, ball_y: int) -> int:
    middle = cpu_y + PADDLE_SIZE // 2
    if ball_y < middle:
        return clamp(cpu_y - 1, 0, HEIGHT - PADDLE_SIZE)
    if ball_y > middle:
        return clamp(cpu_y + 1, 0, HEIGHT - PADDLE_SIZE)
    return cpu_y


def next_state(state: GameState, move: str) -> GameState:
    human_y = clamp(state.human_y + move_delta(move), 0, HEIGHT - PADDLE_SIZE)
    cpu_y = cpu_step(state.cpu_y, state.ball_y)

    ball_x = state.ball_x + state.ball_dx
    ball_y = state.ball_y + state.ball_dy
    ball_dx = state.ball_dx
    ball_dy = state.ball_dy
    human_score = state.human_score
    cpu_score = state.cpu_score

    if ball_y <= 0 or ball_y >= HEIGHT - 1:
        ball_dy *= -1
        ball_y = clamp(ball_y, 0, HEIGHT - 1)

    if ball_x <= 1:
        if ball_y in paddle_cells(human_y):
            ball_x = 2
            ball_dx = 1
            human_score += 1
        else:
            cpu_score += 1
            ball_x, ball_y, ball_dx, ball_dy = WIDTH // 2, HEIGHT // 2, 1, -1

    if ball_x >= WIDTH - 2:
        if ball_y in paddle_cells(cpu_y):
            ball_x = WIDTH - 3
            ball_dx = -1
            cpu_score += 1
        else:
            human_score += 1
            ball_x, ball_y, ball_dx, ball_dy = WIDTH // 2, HEIGHT // 2, -1, 1

    return GameState(human_y, cpu_y, ball_x, ball_y, ball_dx, ball_dy, human_score, cpu_score)


def draw_frame(state: GameState, turn: int, move: str) -> str:
    rows = ["+" + "-" * WIDTH + "+"]
    human = paddle_cells(state.human_y)
    cpu = paddle_cells(state.cpu_y)

    for y in range(HEIGHT):
        line = [" "] * WIDTH
        if y in human:
            line[0] = "|"
        if y in cpu:
            line[-1] = "|"
        if 0 <= state.ball_x < WIDTH and y == state.ball_y:
            line[state.ball_x] = "o"
        rows.append("|" + "".join(line) + "|")

    rows.append("+" + "-" * WIDTH + "+")
    rows.append(f"turn={turn} move={move or 'stay'}  you={state.human_score} cpu={state.cpu_score}")
    rows.append("controls=w up, s down, enter stay  lesson=no-secrets-in-games")
    return "\n".join(rows)


def parse_moves(raw: str) -> list[str]:
    moves = [part.strip() for part in raw.split(",") if part.strip()]
    return moves or ["stay"]


def run_scripted_match(moves: list[str]) -> None:
    state = GameState()
    print("BARRYPONG=ready")
    print("mode=scripted-human-vs-cpu")

    for turn, move in enumerate(moves, start=1):
        state = next_state(state, move)
        print(f"FRAME={turn}")
        print(draw_frame(state, turn, move))

    print("BARRYPONG=pass")
    print("NEXT: python3 scripts/check_repo.py")


def run_interactive_match(turns: int) -> None:
    state = GameState()
    print("BARRYPONG=ready")
    print("mode=interactive-human-vs-cpu")
    print("controls=w up, s down, enter stay, q quit")
    print("FRAME=0")
    print(draw_frame(state, 0, "ready"))

    for turn in range(1, turns + 1):
        print(f"Turn {turn} move [w/s/enter/q]: ", end="")
        try:
            move = input().strip().lower()
        except EOFError:
            print("BARRYPONG_INPUT=closed")
            move = "stay"
        if move == "q":
            break
        state = next_state(state, move)
        print(f"FRAME={turn}")
        print(draw_frame(state, turn, move or "stay"))

    print("BARRYPONG=pass")
    print("NEXT: python3 scripts/check_repo.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play a tiny terminal Pong match.")
    parser.add_argument("--moves", default=DEFAULT_MOVES, help="Comma-separated moves: w,s,stay")
    parser.add_argument("--play", action="store_true", help="Ask for one move per turn")
    parser.add_argument("--turns", type=int, default=8, help="Interactive turns")
    args = parser.parse_args(argv)

    if args.play:
        run_interactive_match(clamp(args.turns, 1, 20))
    else:
        run_scripted_match(parse_moves(args.moves))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
