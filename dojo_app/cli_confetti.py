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
ALT_SCREEN_ON = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"
CURSOR_HOME = "\033[1;1H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
SOLVED_TEXT = "MAZE SOLVED!"
DEFAULT_DURATION = 5.6


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
    display_text = SOLVED_TEXT[:width]
    title_col = max(0, (width - len(display_text)) // 2)
    title = (
        f"{COLORS['bold']}{COLORS['green']}{display_text}{RESET}"
        if use_color
        else display_text
    )
    rows[title_row][title_col] = title
    for offset in range(1, len(display_text)):
        if title_col + offset < width:
            rows[title_row][title_col + offset] = ""

    return "\r\n".join("".join(row) for row in rows)


def celebrate(
    stream: TextIO | None = None,
    duration: float = DEFAULT_DURATION,
    fps: int = 12,
    seed: int | None = None,
) -> None:
    target = stream or sys.stdout
    is_tty = bool(getattr(target, "isatty", lambda: False)())
    if not is_tty or os.getenv("TERM") == "dumb":
        print("* + *  MAZE SOLVED!  * + *", file=target)
        return

    terminal = shutil.get_terminal_size(fallback=(60, 20))
    width = max(1, min(terminal.columns - 1, 60))
    height = max(1, min(terminal.lines - 2, 16))
    rng = random.Random(seed)
    particles = [_new_particle(rng, width, height) for _ in range(max(18, width // 2))]
    deadline = time.monotonic() + max(0.0, duration)
    frame_delay = 1 / max(1, fps)
    first_frame = True

    target.write(f"{ALT_SCREEN_ON}{HIDE_CURSOR}")
    try:
        while first_frame or time.monotonic() < deadline:
            first_frame = False
            target.write(CURSOR_HOME)
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
    finally:
        target.write(f"{SHOW_CURSOR}{ALT_SCREEN_OFF}")

    target.write(f"* + *  {SOLVED_TEXT}  * + *\r\n")
    target.flush()
