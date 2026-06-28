#!/usr/bin/env python3
"""Regression test: flow/roadmap pages avoid color collisions and rail drift."""

from __future__ import annotations

import re
from pathlib import Path


BUILD_DECK = Path(__file__).resolve().parents[1] / "scripts" / "build_deck.mjs"


def main() -> int:
    source = BUILD_DECK.read_text(encoding="utf-8")

    if "function flowNodeFillForTheme" not in source:
        raise AssertionError("flow pages must centralize node fill selection by theme")
    helper = source.split("function flowNodeFillForTheme", 1)[1].split("function imageSideFor", 1)[0]
    orange_branch = re.search(r'if \(theme === "orange"\) \{(?P<body>.*?)\n  \}', helper, re.S)
    if not orange_branch:
        raise AssertionError("flow node fill helper must handle orange theme explicitly")
    if "C.orange" in orange_branch.group("body"):
        raise AssertionError("orange-background flow nodes must not use orange fill")
    for color in ["C.black", "C.cream"]:
        if color not in orange_branch.group("body"):
            raise AssertionError(f"orange-background flow nodes should alternate with {color}")

    flow_branch = source.split('pattern.includes("branch-map")', 1)[1].split("if (\n    pattern.includes(\"statement\")", 1)[0]
    if "flow-rail" in flow_branch:
        raise AssertionError("flow pages must not draw a fixed independent rail")
    for phrase in [
        "const nodeFrames = points.map",
        "const connectorLeft = frame.left + nodeWidth",
        "const connectorWidth = Math.max(0, next.left - connectorLeft)",
        "flow-connector",
    ]:
        if phrase not in flow_branch:
            raise AssertionError(f"flow connectors must be derived from node edges, missing {phrase}")

    print("flow layout builder regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
