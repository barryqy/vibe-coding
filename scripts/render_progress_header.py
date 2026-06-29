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
HEIGHT = 300
TOTAL_MODULES = 9

PART1 = list(range(1, 6))
PART2 = list(range(6, 10))

COLORS = {
    "card": "#f8f9fa",
    "border": "#dee2e6",
    "title": "#212529",
    "muted": "#6c757d",
    "pill_bg": "#e9ecef",
    "pill_fg": "#495057",
    "pill_border": "#ced4da",
    "active_bg": "#0d6efd",
    "active_fg": "#ffffff",
    "active_border": "#0a58ca",
    "meter_bg": "#e9ecef",
    "meter_fill": "#0d6efd",
    "meter_text": "#495057",
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


def load_fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold_path = next((p for p in candidates if "Bold" in p and Path(p).exists()), None)
    regular_path = next(
        (p for p in candidates if "Bold" not in p and Path(p).exists()),
        None,
    )
    if bold_path and regular_path:
        return (
            ImageFont.truetype(bold_path, 24),
            ImageFont.truetype(regular_path, 16),
            ImageFont.truetype(regular_path, 15),
        )
    default = ImageFont.load_default()
    return default, default, default


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def draw_pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    *,
    active: bool,
    font: ImageFont.ImageFont,
) -> int:
    padding_x = 16
    padding_y = 8
    text_w = text_width(draw, label, font)
    w = text_w + padding_x * 2
    h = 34
    radius = h // 2
    bg = COLORS["active_bg"] if active else COLORS["pill_bg"]
    fg = COLORS["active_fg"] if active else COLORS["pill_fg"]
    border = COLORS["active_border"] if active else COLORS["pill_border"]
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=bg, outline=border, width=2)
    draw.text((x + padding_x, y + padding_y - 2), label, fill=fg, font=font)
    return w


def draw_meter(draw: ImageDraw.ImageDraw, x: int, y: int, pct: int, font: ImageFont.ImageFont) -> None:
    bar_w = WIDTH - 80
    bar_h = 12
    fill_w = max(0, min(bar_w, int(bar_w * pct / 100)))
    draw.rounded_rectangle((x, y, x + bar_w, y + bar_h), radius=6, fill=COLORS["meter_bg"])
    if fill_w:
        draw.rounded_rectangle((x, y, x + fill_w, y + bar_h), radius=6, fill=COLORS["meter_fill"])
    draw.text((x, y + 20), f"{pct}% complete", fill=COLORS["meter_text"], font=font)


def render_png(current: int, output_path: Path) -> None:
    title_font, section_font, pill_font = load_fonts()
    pct = int(round((current / TOTAL_MODULES) * 100)) if current else 0
    part_name = (
        "Part 1 — Vibe Coding"
        if current in PART1 or current == 0
        else "Part 2 — Securing AI Agents"
    )
    module_line = f"Module {current} of {TOTAL_MODULES}" if current else "Lab overview"
    title = f"{part_name} · {module_line}"

    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    margin = 24
    draw.rounded_rectangle(
        (8, 8, WIDTH - 8, HEIGHT - 8),
        radius=16,
        fill=COLORS["card"],
        outline=COLORS["border"],
        width=2,
    )

    y = margin
    draw.text((margin, y), title, fill=COLORS["title"], font=title_font)
    y += 40

    draw.text((margin, y), "Part 1 — Vibe Coding (Modules 1–5)", fill=COLORS["muted"], font=section_font)
    y += 28
    x = margin
    for num in PART1:
        label = f"{num} {short_label(num)}"
        w = draw_pill(draw, x, y, label, active=(num == current), font=pill_font)
        x += w + 10
    y += 52

    draw.text((margin, y), "Part 2 — Securing AI Agents (Modules 6–9)", fill=COLORS["muted"], font=section_font)
    y += 28
    x = margin
    for num in PART2:
        label = f"{num} {short_label(num)}"
        w = draw_pill(draw, x, y, label, active=(num == current), font=pill_font)
        x += w + 10
    y += 52

    draw_meter(draw, margin, y, pct, section_font)

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
