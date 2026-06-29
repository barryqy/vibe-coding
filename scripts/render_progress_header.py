#!/usr/bin/env python3
"""Generate per-page progress-bar PNGs and refresh lab markdown headers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - author-time dependency
    raise SystemExit(
        "Pillow is required to render progress PNGs. "
        "Install with: python3 -m pip install pillow"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
LAB_SOURCE = ROOT.parent / "llabsource-vibe-coding"
CONFIG = LAB_SOURCE / "config.json"
LABS = LAB_SOURCE / "labs"
ASSETS = LABS / "assets" / "progress"
START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"

WIDTH = 1120
HEIGHT = 64
TOTAL_MODULES = 9
STOPS = list(range(1, TOTAL_MODULES + 1))

PART1 = list(range(1, 6))
PART2 = list(range(6, 10))

COLORS = {
    "card": "#f8f9fa",
    "border": "#dee2e6",
    "title": "#212529",
    "muted": "#6c757d",
    "track1": "#0d6efd",
    "track2": "#198754",
    "track_bg": "#ced4da",
    "stop_done_fg": "#ffffff",
    "stop_done_bg": "#0d6efd",
    "stop_done2_bg": "#198754",
    "stop_future_bg": "#ffffff",
    "stop_future_border": "#adb5bd",
    "stop_future_fg": "#6c757d",
    "stop_active_ring": "#0a58ca",
    "stop_active2_ring": "#146c43",
}


def module_index_from_name(name: str) -> int:
    match = re.match(r"(\d+)-", name)
    return int(match.group(1)) if match else 0


def short_label(index: int) -> str:
    return {
        0: "Intro",
        1: "Codex",
        2: "MCP",
        3: "Memory",
        4: "Maze",
        5: "OpenCode",
        6: "Darkside",
        7: "DefenseClaw",
        8: "Risky MCP",
        9: "Wrap-up",
    }.get(index, f"M{index}")


def load_fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    candidates = [
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 13),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", 11),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 13),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 11),
    ]
    bold = regular = None
    for path, size in candidates:
        if not Path(path).exists():
            continue
        if "Bold" in path and bold is None:
            bold = ImageFont.truetype(path, size)
        elif "Bold" not in path and regular is None:
            regular = ImageFont.truetype(path, size)
    if bold and regular:
        return bold, regular
    default = ImageFont.load_default()
    return default, default


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def track_color(stop: int) -> str:
    return COLORS["track1"] if stop in PART1 else COLORS["track2"]


def stop_fill(current: int, stop: int) -> tuple[str, str, str, int]:
    """Return fill, text color, ring color, radius for a subway stop."""
    if current and stop < current:
        fill = COLORS["stop_done2_bg"] if stop in PART2 else COLORS["stop_done_bg"]
        return fill, COLORS["stop_done_fg"], fill, 11
    if stop == current:
        ring = COLORS["stop_active2_ring"] if stop in PART2 else COLORS["stop_active_ring"]
        fill = COLORS["stop_done2_bg"] if stop in PART2 else COLORS["stop_done_bg"]
        return fill, COLORS["stop_done_fg"], ring, 14
    return COLORS["stop_future_bg"], COLORS["stop_future_fg"], COLORS["stop_future_border"], 10


def render_png(current: int, output_path: Path) -> None:
    title_font, stop_font = load_fonts()
    pct = int(round((current / TOTAL_MODULES) * 100)) if current else 0
    part_name = (
        "Part 1 — Vibe Coding"
        if current in PART1 or current == 0
        else "Part 2 — Securing AI Agents"
    )
    module_line = f"Module {current} of {TOTAL_MODULES}" if current else "Lab overview"
    caption = f"{part_name} · {module_line}"

    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    margin = 12
    draw.rounded_rectangle(
        (4, 4, WIDTH - 4, HEIGHT - 4),
        radius=10,
        fill=COLORS["card"],
        outline=COLORS["border"],
        width=1,
    )

    draw.text((margin, 10), caption, fill=COLORS["title"], font=title_font)
    pct_text = f"{pct}%"
    draw.text((WIDTH - margin - text_width(draw, pct_text, stop_font), 12), pct_text, fill=COLORS["muted"], font=stop_font)

    track_y = 40
    left = margin + 8
    right = WIDTH - margin - 8
    span = right - left
    if len(STOPS) > 1:
        step = span / (len(STOPS) - 1)
    else:
        step = 0
    centers = [int(left + step * i) for i in range(len(STOPS))]

    for i in range(len(centers) - 1):
        x1, x2 = centers[i], centers[i + 1]
        stop_a, stop_b = STOPS[i], STOPS[i + 1]
        if current and stop_b <= current:
            color = COLORS["track2"] if stop_b in PART2 else COLORS["track1"]
        elif current and stop_a < current:
            color = COLORS["track2"] if stop_b in PART2 else COLORS["track1"]
        else:
            color = COLORS["track_bg"]
        draw.line((x1, track_y, x2, track_y), fill=color, width=4)

    for stop, cx in zip(STOPS, centers):
        fill, fg, ring, radius = stop_fill(current, stop)
        draw.ellipse((cx - radius, track_y - radius, cx + radius, track_y + radius), fill=fill, outline=ring, width=2)
        num = str(stop)
        num_w = text_width(draw, num, stop_font)
        draw.text((cx - num_w // 2, track_y - 6), num, fill=fg, font=stop_font)

    # Part boundary tick between stops 5 and 6
    if len(centers) >= 6:
        bx = (centers[4] + centers[5]) // 2
        draw.line((bx, track_y - 14, bx, track_y + 14), fill=COLORS["muted"], width=1)
        draw.text((bx - 14, track_y - 26), "P2", fill=COLORS["muted"], font=stop_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)


def build_header(current: int) -> str:
    png_name = f"progress-{current:02d}.png"
    part_name = (
        "Part 1 — Vibe Coding"
        if current in PART1 or current == 0
        else "Part 2 — Securing AI Agents"
    )
    module_line = f"Module {current} of {TOTAL_MODULES}" if current else "Lab overview"
    alt = f"Lab progress — {part_name}, {module_line}"
    return (
        f"{START}\n"
        f"![{alt}](assets/progress/{png_name})\n"
        f"{END}"
    )


def update_file(path: Path, header: str) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(text):
        new_text = pattern.sub(header, text, count=1)
    else:
        new_text = header + "\n\n" + text.lstrip("\n")
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labs-dir", type=Path, default=LABS)
    parser.add_argument("--assets-dir", type=Path, default=ASSETS)
    args = parser.parse_args()

    items = json.loads(CONFIG.read_text(encoding="utf-8"))["items"]
    changed = 0
    for item in items:
        rel = item["content"].replace("labs/", "")
        path = args.labs_dir / rel
        if not path.exists():
            print(f"skip missing {path}")
            continue
        idx = module_index_from_name(rel)
        png_path = args.assets_dir / f"progress-{idx:02d}.png"
        render_png(idx, png_path)
        print(f"rendered {png_path.name}")
        if update_file(path, build_header(idx)):
            changed += 1
            print(f"updated {path.name}")
    print(f"PROGRESS_HEADERS={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
