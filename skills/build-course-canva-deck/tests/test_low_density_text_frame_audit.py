#!/usr/bin/env python3
"""Regression test: sparse side-rail/modules pages cannot pass as diagrams."""

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


def deck(points: list[str], visuals: list[dict] | None = None) -> dict:
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
                    "bullets": points,
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
                "visuals": visuals or [],
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


def run_audit(root: Path, spec: dict) -> dict:
    source_path = root / "source.json"
    deck_path = root / "deck.json"
    report_path = root / "report.json"
    write(source_path, source_map())
    write(deck_path, spec)
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
        ],
        text=True,
        capture_output=True,
    )
    return json.loads(report_path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sparse = deck(["step one", "step two"])
        report = run_audit(root, sparse)
        if report["ok"]:
            raise AssertionError(report)
        if not any("creates empty card/rail space" in err for err in report["errors"]):
            raise AssertionError(report)

        dense = deck(["step one", "step two", "step three"])
        report = run_audit(root, dense)
        if not report["ok"]:
            raise AssertionError(report)

    print("low-density text-frame audit regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
