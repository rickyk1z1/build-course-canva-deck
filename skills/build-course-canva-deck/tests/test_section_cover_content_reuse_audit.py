#!/usr/bin/env python3
"""Regression test: section covers stay agenda-only and cannot reuse content-page copy."""

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
            {"id": "n3", "order": 3, "parent_id": "n2", "text": "多轨道层级逻辑（上层盖下层）", "include": True},
        ],
        "images": [],
    }


def knowledge_slide() -> dict:
    return {
        "number": 3,
        "layout": "light",
        "title": "多轨道层级逻辑（上层盖下层）",
        "source_node_ids": ["n3"],
        "framework_progress_label": "chapter",
        "screen": {
            "explanation": "上层轨道会覆盖下层画面，先看层级再判断为什么被挡住。",
            "bullets": ["上层盖下层"],
            "caption": "",
            "blocks": [],
            "teaching_expansion": {
                "mode_handling": "detailed-clarification",
                "learner_takeaway": "上层盖下层",
                "source_based_explanation": "上层轨道会覆盖下层画面。",
                "example_or_judgment_cue": "画面不见时先看轨道层级。",
                "display_priority": ["上层盖下层"],
                "internal_only": [],
            },
        },
        "source_node_treatments": [
            {
                "source_node_id": "n3",
                "coverage_status": "clarified",
                "screen_evidence": "多轨道层级逻辑（上层盖下层）",
            }
        ],
        "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
        "visual_plan": {
            "asset_type": "editable-diagram",
            "integration": "knowledge-page",
            "source_node_id": "n3",
            "source_image_ids": [],
            "labels_as_slide_text": True,
            "layout_variant": "flow",
            "generated_case_bypass_reason": "多轨道层级逻辑（上层盖下层）需要保留层级关系和顺序，编辑图解比生成场景图更清楚。",
        },
        "visuals": [],
    }


def deck(section_bullet: str) -> dict:
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
                "screen": {"explanation": "chapter", "bullets": [section_bullet], "caption": "", "blocks": []},
                "section_preview_items": [{"source_node_id": "n3", "screen_evidence": section_bullet}],
                "source_node_treatments": [
                    {"source_node_id": "n2", "coverage_status": "section-heading", "screen_evidence": "chapter"}
                ],
                "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
            },
            knowledge_slide(),
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


def run_audit(root: Path, deck_spec: dict) -> dict:
    source_path = root / "source.json"
    deck_path = root / "deck.json"
    report_path = root / "report.json"
    write(source_path, source_map())
    write(deck_path, deck_spec)
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
        repeated = run_audit(root, deck("多轨道层级逻辑（上层盖下层） · 添加 / 删除 / 移动 / 分割 ..."))
        if repeated["ok"]:
            raise AssertionError(repeated)
        expected = [
            "section-cover repeats normal knowledge-page learner copy",
            "section-cover cue contains ellipsis",
            "section-cover cue looks like a dense list",
        ]
        for phrase in expected:
            if not any(phrase in err for err in repeated["errors"]):
                raise AssertionError(repeated)

        compact = run_audit(root, deck("轨道层级"))
        if not compact["ok"]:
            raise AssertionError(compact)

    print("section-cover content reuse audit regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
