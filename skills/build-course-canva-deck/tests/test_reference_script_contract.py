#!/usr/bin/env python3
"""Regression test: lecture scripts are optional references, not source modes."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
AUDIT = SKILL_DIR / "scripts" / "audit_deck.py"
EXTRACT = SKILL_DIR / "scripts" / "extract_source.py"
VALIDATE = SKILL_DIR / "scripts" / "validate_source_map.py"


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def source_map(source_kind: str = "outline") -> dict:
    return {
        "schema_version": 1,
        "authoritative": True,
        "authoritative_source": "lesson.xmind",
        "source_type": "xmind",
        "source_kind": source_kind,
        "outline_mode": "sparse",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": "n1", "order": 1, "parent_id": None, "depth": 0, "text": "root", "include": True},
            {"id": "n2", "order": 2, "parent_id": "n1", "depth": 1, "text": "chapter", "include": True},
            {"id": "n3", "order": 3, "parent_id": "n2", "depth": 2, "text": "point", "include": True},
        ],
        "images": [],
    }


def deck(reference_script: dict | None = None) -> dict:
    course = {
        "outline_mode": "sparse",
        "curriculum_context": {
            "system_name": "test",
            "module": "test",
            "course_role": "test",
            "excluded_neighbor_topics": [],
        },
        "chapter_spine": [{"source_node_id": "n2", "title": "chapter"}],
        "image_generation_tasks": [],
    }
    if reference_script is not None:
        course["reference_script"] = reference_script
    return {
        "course": course,
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
                    "explanation": "visible point",
                    "bullets": ["visible point"],
                    "caption": "",
                    "blocks": [],
                    "teaching_expansion": {
                        "mode_handling": "sparse-vertical-expansion",
                        "learner_takeaway": "visible point",
                        "source_based_explanation": "visible point",
                        "example_or_judgment_cue": "visible point",
                        "display_priority": ["visible point"],
                        "internal_only": [],
                    },
                },
                "source_node_treatments": [
                    {"source_node_id": "n3", "coverage_status": "clarified", "screen_evidence": "visible point"}
                ],
                "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
                "visual_plan": {
                    "asset_type": "text-only-exception",
                    "integration": "knowledge-page",
                    "source_node_id": "n3",
                    "source_image_ids": [],
                    "labels_as_slide_text": True,
                    "generated_case_bypass_reason": "visible point 是参考讲稿契约测试页，文字证据清单结构比生成案例图更清楚。",
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


def run_audit(root: Path, source: dict, spec: dict) -> tuple[int, dict]:
    source_path = root / "source.json"
    deck_path = root / "deck.json"
    report_path = root / "report.json"
    write(source_path, source)
    write(deck_path, spec)
    result = subprocess.run(
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
    return result.returncode, json.loads(report_path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = root / "script.md"
        output_path = root / "source.json"
        input_path.write_text("这是一段讲稿参考。", encoding="utf-8")
        extract_result = subprocess.run(
            [
                "python3",
                str(EXTRACT),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--source-kind",
                "script",
            ],
            text=True,
            capture_output=True,
        )
        if extract_result.returncode == 0:
            raise AssertionError("extract_source.py must not accept --source-kind script")

        write(output_path, source_map())
        validate_result = subprocess.run(
            ["python3", str(VALIDATE), str(output_path), "--mode", "script"],
            text=True,
            capture_output=True,
        )
        if validate_result.returncode == 0:
            raise AssertionError("validate_source_map.py must not accept --mode script")

        valid_reference = {
            "path": "/tmp/reference-script.md",
            "authoritative": False,
            "usage": "screen-copy-reference-only",
        }
        code, report = run_audit(root, source_map(), deck(valid_reference))
        if code != 0:
            raise AssertionError(report)

        code, report = run_audit(root, source_map("script"), deck(valid_reference))
        if code == 0:
            raise AssertionError(report)
        if not any("source_kind=script" in error for error in report["errors"]):
            raise AssertionError(report)

        invalid_reference = {"path": "/tmp/reference-script.md", "authoritative": True}
        code, report = run_audit(root, source_map(), deck(invalid_reference))
        if code == 0:
            raise AssertionError(report)
        if not any("reference_script" in error for error in report["errors"]):
            raise AssertionError(report)

    print("reference script contract regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
