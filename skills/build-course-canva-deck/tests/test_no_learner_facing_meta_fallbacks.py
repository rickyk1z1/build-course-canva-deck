#!/usr/bin/env python3
"""Regression test: the builder must not invent producer-facing screen copy."""

from __future__ import annotations

from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
BUILD_DECK = SKILL_DIR / "scripts" / "build_deck.mjs"
AUDIT_DECK = SKILL_DIR / "scripts" / "audit_deck.py"

FORBIDDEN_META_COPY = [
    "先知道整节课怎么展开，再进入每一节。",
    "整节课怎么展开",
    "构建课件",
    "课件思路",
    "制作思路",
]


def main() -> int:
    build_source = BUILD_DECK.read_text(encoding="utf-8")
    audit_source = AUDIT_DECK.read_text(encoding="utf-8")

    for phrase in FORBIDDEN_META_COPY:
        if phrase in build_source:
            raise AssertionError(f"build_deck.mjs must not inject learner-facing meta copy: {phrase}")

    if "const overviewCaption = String(screen.caption || \"\").trim();" not in build_source:
        raise AssertionError("lesson overview caption must come only from authored screen.caption")
    if "if (overviewCaption)" not in build_source:
        raise AssertionError("lesson overview caption block must be omitted when no learner caption is authored")
    if "NEGATIVE_SCOPE_RE" not in build_source:
        raise AssertionError("build_deck.mjs must reject learner-facing negative scope wording before rendering")
    if "generated_case_bypass_reason" not in build_source:
        raise AssertionError("build_deck.mjs must require a generated-image decision for no-source knowledge pages")
    if "function validateTeachingExpansion" not in build_source:
        raise AssertionError("build_deck.mjs must validate learner-facing teaching expansion before rendering")
    if "screen.teaching_expansion" not in build_source or "display_priority" not in build_source:
        raise AssertionError("build_deck.mjs must require visible teaching_expansion phrases for knowledge slides")
    if "function validateGeneratedImageRoute" not in build_source:
        raise AssertionError("build_deck.mjs must validate generated-image route chains before rendering")
    for phrase in [
        "gpt-image-2",
        "imagegen",
        "deterministic-svg",
        "fallback_reason_type",
        "diagram-clearer",
        "user_provided_asset",
        "user_asset_source",
    ]:
        if phrase not in build_source:
            raise AssertionError(f"build_deck.mjs must enforce generated-image route field: {phrase}")

    for phrase in ["整节课怎么展开", "构建课件", "课件思路", "制作思路"]:
        if phrase not in audit_source:
            raise AssertionError(f"audit_deck.py must reject leaked producer-facing phrase: {phrase}")

    print("learner-facing meta fallback regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
