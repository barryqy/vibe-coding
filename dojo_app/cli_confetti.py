from __future__ import annotations

import os
import random
import shutil
import sys
import time
from typing import TextIO

from dojo_app.lab_output import COLORS, RESET, color_enabled


CONFETTI_CHARS = (".", "*", "+", "#", "@", "%")
CONFETTI_COLORS = ("red", "green", "yellow", "blue", "magenta", "cyan")
CLEAR_SCREEN = "\033[H\033[2J"
SOLVED_TEXT = "MAZE SOLVED!"


def _new_particle(rng: random.Random, width: int, height: int, above: bool = False):
    top = -height if above else 0
    return (
        rng.randrange(width),
        rng.randrange(top, height),
        rng.choice(CONFETTI_CHARS),
        rng.choice(CONFETTI_COLORS),
    )


def _draw_frame(width: int, height: int, particles, use_color: bool) -> str:
    rows = [[" "] * width for _ in range(height)]
    for x, y, char, color in particles:
        if y < 0 or y >= height:
            continue
        rows[y][x] = f"{COLORS[color]}{char}{RESET}" if use_color else char

    title_row = height // 2
    title_col = max(0, (width - len(SOLVED_TEXT)) // 2)
    title = f"{COLORS['bold']}{COLORS['green']}{SOLVED_TEXT}{RESET}" if use_color else SOLVED_TEXT
    rows[title_row][title_col] = title
    for offset in range(1, len(SOLVED_TEXT)):
        if title_col + offset < width:
            rows[title_row][title_col + offset] = ""

    return "\n".join("".join(row) for row in rows)


def celebrate(
    stream: TextIO | None = None,
    duration: float = 1.4,
    fps: int = 12,
    seed: int | None = None,
) -> None:
    target = stream or sys.stdout
    is_tty = bool(getattr(target, "isatty", lambda: False)())
    if not is_tty or os.getenv("TERM") == "dumb":
        print("* + *  MAZE SOLVED!  * + *", file=target)
        return

    terminal = shutil.get_terminal_size(fallback=(60, 20))
    width = max(32, min(terminal.columns, 80))
    height = max(8, min(terminal.lines - 2, 16))
    rng = random.Random(seed)
    particles = [_new_particle(rng, width, height) for _ in range(max(18, width // 2))]
    deadline = time.monotonic() + max(0.0, duration)
    frame_delay = 1 / max(1, fps)
    first_frame = True

    while first_frame or time.monotonic() < deadline:
        first_frame = False
        target.write(CLEAR_SCREEN)
        target.write(_draw_frame(width, height, particles, color_enabled(target)))
        target.flush()

        next_particles = []
        for x, y, char, color in particles:
            if y + 1 >= height:
                next_particles.append(_new_particle(rng, width, height, above=True))
            else:
                next_particles.append((x, y + 1, char, color))
        particles = next_particles

        if time.monotonic() < deadline:
            time.sleep(frame_delay)

    target.write("\n")
    target.flush()
