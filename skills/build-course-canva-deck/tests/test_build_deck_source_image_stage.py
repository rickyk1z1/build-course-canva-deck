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
    for phrase in [
        "function imageDimensions",
        "function containFillRatio",
        "function caseImagePanels",
        "caseTextMode",
        "supporting-text",
    ]:
        if phrase not in source:
            raise AssertionError(f"case-image pages must adapt to source image footprint, missing {phrase}")

    match = re.search(
        r"const imageFrame = \{ left: \d+, top: \d+, width: (\d+), height: (\d+),",
        source,
    )
    if not match:
        raise AssertionError("caseImageStageLayout must declare a numeric shared imageFrame")
    width, height = map(int, match.groups())
    if width * height < MIN_CASE_STAGE_AREA:
        raise AssertionError(
            f"case image stage is too small: {width}x{height}={width * height}, "
            f"expected at least {int(MIN_CASE_STAGE_AREA)}"
        )

    helper_body = source.split("function caseImageStageLayout", 1)[1].split("function addExplanation", 1)[0]
    if "function insetPosition" not in source:
        raise AssertionError("case-image stage must have an inset helper for inner breathing room")
    if "const contentPosition = insetPosition(imageFrame" not in helper_body or "imageContentPosition:" not in helper_body or "contentPosition" not in helper_body:
        raise AssertionError("case-image stage must render images inside an inset content area")
    for phrase in [
        "function caseImageStageInset",
        "plan.case_stage_inner_padding",
        "composition.case_stage_inner_padding",
        "proportionalDefault",
    ]:
        if phrase not in source:
            raise AssertionError(f"case-image breathing room must be design-adjustable, missing {phrase}")
    if "const renderImagePosition = imageContentPosition || imagePosition" not in source:
        raise AssertionError("image rendering must use the inset content area when present")
    if "caseImagePanels(renderImagePosition" not in source:
        raise AssertionError("case-image multi-image panels must use adaptive panels from the inset content area")
    if "splitImagePanels(renderImagePosition" not in source:
        raise AssertionError("ordinary multi-image panels must still split the chosen image render area")
    if "perImagePanelBackgrounds: false" not in helper_body:
        raise AssertionError("case-image stage must not draw separate backing rectangles under each image")
    if "textPanel: null" not in helper_body:
        raise AssertionError("case-image stage must not draw a separate text backing panel over the image")
    if "multiImageArrangement: composition.multi_image_arrangement" not in helper_body:
        raise AssertionError("visual plans must be able to request a specific multi-image arrangement")
    for phrase in [
        "function caseTextPlacement",
        "composition.case_text_placement",
        "supporting_text_placement",
        "bottom-band",
        "top-band",
        "side-right",
        "side-left",
        "function caseStageTextLayout",
    ]:
        if phrase not in source:
            raise AssertionError(f"case-image supporting text must support varied in-stage placements, missing {phrase}")
    if "small_source_image_strategy" not in helper_body:
        raise AssertionError("small source images must trigger an adaptive supporting-text strategy")
    if "singleFillRatio < 0.48" not in helper_body:
        raise AssertionError("case-image stage must detect when a contain-fit single image leaves too much empty space")

    if "if (perImagePanelBackgrounds)" not in source:
        raise AssertionError("multi-image panel backing must be conditional, not unconditional")
    if 'caseTextMode === "supporting-text"' not in source:
        raise AssertionError("small case-image pages must be allowed to render supporting learner text outside the image")
    if "caseTextMode === \"supporting-text\" ? 3" not in source:
        raise AssertionError("supporting text on case-image pages must stay compact")

    print("case image stage builder regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
