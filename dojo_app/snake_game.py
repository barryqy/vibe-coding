from __future__ import annotations


WIDTH = 18
HEIGHT = 7
SNAKE = [(4, 3), (3, 3), (2, 3)]
FOOD = (12, 3)


def move_snake(step: int) -> list[tuple[int, int]]:
    dx = step % 5
    return [(x + dx, y) for x, y in SNAKE]


def draw_frame(step: int) -> str:
    snake = move_snake(step)
    head = snake[0]
    body = set(snake[1:])
    rows = ["+" + "-" * WIDTH + "+"]

    for y in range(HEIGHT):
        line = []
        for x in range(WIDTH):
            if (x, y) == head:
                line.append("@")
            elif (x, y) in body:
                line.append("o")
            elif (x, y) == FOOD:
                line.append("*")
            else:
                line.append(" ")
        rows.append("|" + "".join(line) + "|")

    rows.append("+" + "-" * WIDTH + "+")
    rows.append(f"score={step}  lesson=do-not-hide-keys-in-games")
    return "\n".join(rows)


def main() -> None:
    print("SNAKE_GAME=ready")
    for step in range(4):
        print(f"FRAME={step + 1}")
        print(draw_frame(step))
    print("SNAKE_GAME=pass")
    print("NEXT: python3 scripts/check_repo.py")


if __name__ == "__main__":
    main()
