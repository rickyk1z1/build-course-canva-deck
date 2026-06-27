#!/usr/bin/env python3
"""Regression test: case-image pages are rendered image-first, not as small cards."""

from __future__ import annotations

import re
from pathlib import Path


BUILD_DECK = Path(__file__).resolve().parents[1] / "scripts" / "build_deck.mjs"
SLIDE_AREA = 1280 * 720
MIN_CASE_STAGE_AREA = SLIDE_AREA * 0.60


def main() -> int:
    source = BUILD_DECK.read_text(encoding="utf-8")

    if "function caseImageStageLayout" not in source:
        raise AssertionError("build_deck.mjs must have a case-image-specific stage layout")
    if "function isCaseImageItem" not in source:
        raise AssertionError("build_deck.mjs must detect case-image pages before layout execution")
    if not re.search(r"generated-image", source):
        raise AssertionError("generated-image pages must use the same case-image stage as source images")

    match = re.search(
        r"imagePosition:\s*\{\s*left:\s*\d+,\s*top:\s*\d+,\s*width:\s*(\d+),\s*height:\s*(\d+)\s*\}",
        source,
    )
    if not match:
        raise AssertionError("caseImageStageLayout must declare imagePosition with numeric width/height")
    width, height = map(int, match.groups())
    if width * height < MIN_CASE_STAGE_AREA:
        raise AssertionError(
            f"case image stage is too small: {width}x{height}={width * height}, "
            f"expected at least {int(MIN_CASE_STAGE_AREA)}"
        )

    helper_body = source.split("function caseImageStageLayout", 1)[1].split("function addExplanation", 1)[0]
    if "perImagePanelBackgrounds: false" not in helper_body:
        raise AssertionError("case-image stage must not draw separate backing rectangles under each image")
    if "textPanel: null" not in helper_body:
        raise AssertionError("case-image stage must not draw a separate text backing panel over the image")

    if "if (perImagePanelBackgrounds)" not in source:
        raise AssertionError("multi-image panel backing must be conditional, not unconditional")
    if "if (!caseImagePage)" not in source:
        raise AssertionError("case-image pages must not render explanation/bullets over the image stage")

    print("case image stage builder regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
