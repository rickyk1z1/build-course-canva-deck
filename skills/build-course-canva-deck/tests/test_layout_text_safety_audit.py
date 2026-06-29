#!/usr/bin/env python3
"""Regression test: rendered explanatory text must use space safely."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


AUDIT = Path(__file__).resolve().parents[1] / "scripts" / "audit_deck.py"


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def source_map() -> dict:
    return {
        "outline_mode": "detailed",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": "n1", "order": 1, "parent_id": None, "text": "root", "include": True},
            {"id": "n2", "order": 2, "parent_id": "n1", "text": "chapter", "include": True},
            {"id": "n3", "order": 3, "parent_id": "n2", "text": "point", "include": True},
        ],
        "images": [],
    }


def teaching_expansion() -> dict:
    return {
        "mode_handling": "detailed-clarification",
        "learner_takeaway": "point",
        "source_based_explanation": "point explanation",
        "example_or_judgment_cue": "point cue",
        "display_priority": ["point"],
        "internal_only": [],
    }


def deck() -> dict:
    return {
        "course": {
            "outline_mode": "detailed",
            "curriculum_context": {
                "system_name": "test",
                "module": "test",
                "course_role": "test",
                "excluded_neighbor_topics": [],
            },
            "chapter_spine": [{"source_node_id": "n2", "title": "chapter"}],
            "image_generation_tasks": [],
        },
        "slides": [
            {
                "number": 1,
                "layout": "lesson-overview",
                "title": "root",
                "source_node_ids": ["n1"],
                "screen": {"explanation": "root", "bullets": ["chapter"], "caption": "", "blocks": []},
                "source_node_treatments": [
                    {"source_node_id": "n1", "coverage_status": "clarified", "screen_evidence": "root"}
                ],
                "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
            },
            {
                "number": 2,
                "layout": "section-cover",
                "title": "chapter",
                "source_node_ids": ["n2"],
                "screen": {"explanation": "chapter", "bullets": ["point"], "caption": "", "blocks": []},
                "section_preview_items": [{"source_node_id": "n3", "screen_evidence": "point"}],
                "source_node_treatments": [
                    {"source_node_id": "n2", "coverage_status": "section-heading", "screen_evidence": "chapter"}
                ],
                "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
            },
            {
                "number": 3,
                "layout": "light",
                "title": "point",
                "source_node_ids": ["n3"],
                "framework_progress_label": "chapter",
                "screen": {
                    "explanation": "point explanation",
                    "bullets": ["step one", "step two", "step three"],
                    "caption": "",
                    "blocks": [],
                    "teaching_expansion": teaching_expansion(),
                },
                "source_node_treatments": [
                    {"source_node_id": "n3", "coverage_status": "clarified", "screen_evidence": "point"}
                ],
                "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
                "visual_plan": {
                    "asset_type": "editable-diagram",
                    "integration": "knowledge-page",
                    "source_node_id": "n3",
                    "source_image_ids": [],
                    "labels_as_slide_text": True,
                    "layout_variant": "side-rail",
                    "generated_case_bypass_reason": "point 的操作路径需要保留快捷键、步骤和顺序，side-rail 结构比生成场景图更清楚。",
                },
                "visuals": [],
            },
            {
                "number": 4,
                "layout": "summary",
                "title": "summary",
                "source_node_ids": [],
                "screen": {"explanation": "done", "bullets": [], "caption": "", "blocks": []},
                "source_node_treatments": [],
                "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
            },
        ],
    }


def layout_element(name: str, bbox: list[int], font: int, lines: int = 1) -> dict:
    text = "当目标是一块会运动和透视变化的平面时，平面跟踪更适合。"
    return {
        "kind": "shape",
        "name": name,
        "bbox": bbox,
        "text": text,
        "textPreview": text,
        "resolvedFontSize": font,
        "textLayout": {"lineCount": lines},
    }


def run_audit(root: Path, layout_elements: list[dict]) -> dict:
    source_path = root / "source.json"
    deck_path = root / "deck.json"
    report_path = root / "report.json"
    layout_dir = root / "layout"
    layout_dir.mkdir(exist_ok=True)
    write(source_path, source_map())
    write(deck_path, deck())
    write(layout_dir / "slide-003.json", {"elements": layout_elements})
    subprocess.run(
        [
            "python3",
            str(AUDIT),
            "--deck-spec",
            str(deck_path),
            "--source-map",
            str(source_path),
            "--report",
            str(report_path),
            "--layout-dir",
            str(layout_dir),
        ],
        text=True,
        capture_output=True,
    )
    return json.loads(report_path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bottom_report = run_audit(root, [layout_element("caption-3", [72, 650, 900, 34], 15)])
        if bottom_report["ok"]:
            raise AssertionError(bottom_report)
        if not any("bottom safety zone" in err for err in bottom_report["errors"]):
            raise AssertionError(bottom_report)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        small_report = run_audit(root, [layout_element("explanation-3", [812, 210, 340, 112], 21, 3)])
        if small_report["ok"]:
            raise AssertionError(small_report)
        if not any("small explanation text leaves underused frame" in err for err in small_report["errors"]):
            raise AssertionError(small_report)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ok_report = run_audit(root, [
            layout_element("caption-3", [76, 607, 690, 35], 17),
            layout_element("explanation-3", [812, 210, 340, 180], 22, 4),
        ])
        if not ok_report["ok"]:
            raise AssertionError(ok_report)

    print("layout text safety audit regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
