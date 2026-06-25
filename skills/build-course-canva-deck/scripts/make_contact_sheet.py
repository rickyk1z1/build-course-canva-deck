#!/usr/bin/env python3
"""Create a labeled contact sheet from rendered slide images."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from html import escape

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def write_svg_contact_sheet(files: list[Path], output: Path, *, cols: int, thumb_width: int, gap: int) -> Path:
    cols = max(1, cols)
    thumb_height = round(thumb_width * 9 / 16)
    label_height = 34
    card_height = thumb_height + label_height
    rows = math.ceil(len(files) / cols)
    width = cols * thumb_width + (cols + 1) * gap
    height = rows * card_height + (rows + 1) * gap
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#D8D2CC"/>',
    ]
    for index, path in enumerate(files):
        x = gap + (index % cols) * (thumb_width + gap)
        y = gap + (index // cols) * (card_height + gap)
        lines.append(f'<rect x="{x}" y="{y}" width="{thumb_width}" height="{card_height}" fill="#FFFFFF"/>')
        lines.append(
            f'<text x="{x + 10}" y="{y + 22}" font-family="Arial, sans-serif" '
            f'font-size="14" fill="#1C1C1C">{index + 1:02d}  {escape(path.stem)}</text>'
        )
        lines.append(
            f'<image href="{escape(path.resolve().as_uri())}" x="{x}" y="{y + label_height}" '
            f'width="{thumb_width}" height="{thumb_height}" preserveAspectRatio="xMidYMid meet"/>'
        )
    lines.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=560)
    parser.add_argument("--gap", type=int, default=20)
    args = parser.parse_args()

    files = sorted(
        [
            path for path in args.input_dir.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            and "montage" not in path.stem.lower()
            and "contact-sheet" not in path.stem.lower()
        ],
        key=natural_key,
    )
    if not files:
        raise SystemExit("no slide images found")
    if Image is None or args.output.suffix.lower() == ".svg":
        output = args.output if args.output.suffix.lower() == ".svg" else args.output.with_suffix(".svg")
        print(write_svg_contact_sheet(
            files,
            output,
            cols=args.cols,
            thumb_width=args.thumb_width,
            gap=args.gap,
        ))
        return 0
    font = ImageFont.load_default()
    cards: list[Image.Image] = []
    for index, path in enumerate(files, start=1):
        image = Image.open(path).convert("RGB")
        height = round(image.height * args.thumb_width / image.width)
        image = image.resize((args.thumb_width, height), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (args.thumb_width, height + 34), "white")
        card.paste(image, (0, 34))
        ImageDraw.Draw(card).text((10, 10), f"{index:02d}  {path.stem}", fill="#1C1C1C", font=font)
        cards.append(card)
    cols = max(1, args.cols)
    rows = math.ceil(len(cards) / cols)
    row_height = max(card.height for card in cards)
    width = cols * args.thumb_width + (cols + 1) * args.gap
    height = rows * row_height + (rows + 1) * args.gap
    sheet = Image.new("RGB", (width, height), "#D8D2CC")
    for index, card in enumerate(cards):
        x = args.gap + (index % cols) * (args.thumb_width + args.gap)
        y = args.gap + (index // cols) * (row_height + args.gap)
        sheet.paste(card, (x, y))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
