#!/usr/bin/env python3
"""Regression test: generated-image pages must prove the required route chain."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


AUDIT = Path(__file__).resolve().parents[1] / "scripts" / "audit_deck.py"


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def base_source() -> dict:
    return {
        "outline_mode": "sparse",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": "n1", "order": 1, "parent_id": None, "text": "root", "include": True},
            {"id": "n2", "order": 2, "parent_id": "n1", "text": "chapter", "include": True},
            {"id": "n3", "order": 3, "parent_id": "n2", "text": "point", "include": True},
        ],
        "images": [],
    }


def base_deck() -> dict:
    return {
        "course": {
            "outline_mode": "sparse",
            "curriculum_context": {
                "system_name": "test",
                "module": "test",
                "course_role": "test",
                "excluded_neighbor_topics": [],
            },
            "chapter_spine": [{"source_node_id": "n2", "title": "chapter"}],
            "image_generation_tasks": [
                {
                    "slide": 3,
                    "route": "user-provided",
                    "asset_path": "assets/generated/local-fallback.png",
                    "knowledge_anchor": "point",
                    "observable_teaching_detail": "visible contrast",
                    "instant_takeaway": "point",
                    "case_visual_map": [
                        {"screen_evidence": "visible point", "visible_detail": "visible contrast"}
                    ],
                }
            ],
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
                "layout": "image-right",
                "title": "point",
                "source_node_ids": ["n3"],
                "framework_progress_label": "chapter",
                "screen": {
                    "explanation": "visible point",
                    "bullets": ["visible point"],
                    "caption": "visible point",
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
                    {"source_node_id": "n3", "coverage_status": "visualized", "screen_evidence": "visible point"}
                ],
                "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
                "visual_plan": {
                    "asset_type": "generated-image",
                    "integration": "knowledge-page",
                    "source_node_id": "n3",
                    "source_image_ids": [],
                    "labels_as_slide_text": True,
                    "generation_route": "user-provided",
                    "knowledge_anchor": "point",
                    "observable_teaching_detail": "visible contrast",
                    "instant_takeaway": "point",
                    "case_visual_map": [
                        {"screen_evidence": "visible point", "visible_detail": "visible contrast"}
                    ],
                },
                "visuals": [{"path": "assets/generated/local-fallback.png", "alt": "case"}],
                "added_content": [
                    {
                        "source_node_id": "n3",
                        "kind": "example",
                        "relevance": "direct",
                        "evidence_urls": ["https://example.com"],
                    }
                ],
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


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_path = root / "source.json"
        deck_path = root / "deck.json"
        report_path = root / "report.json"
        write(source_path, base_source())
        invalid_user_provided = base_deck()
        write(deck_path, invalid_user_provided)
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
        if result.returncode == 0:
            raise AssertionError(result.stdout)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if not any("user-provided route is only valid" in err for err in report["errors"]):
            raise AssertionError(report)

        diagram_clearer = base_deck()
        slide = diagram_clearer["slides"][2]
        task = diagram_clearer["course"]["image_generation_tasks"][0]
        slide["visual_plan"].update(
            {
                "generation_route": "deterministic-svg",
                "fallback_reason_type": "diagram-clearer",
                "fallback_reason": "本页教学对象是可控关系图；确定性 SVG 比模型图更清楚。",
            }
        )
        task.update(
            {
                "route": "deterministic-svg",
                "fallback_reason_type": "diagram-clearer",
                "fallback_reason": "本页教学对象是可控关系图；确定性 SVG 比模型图更清楚。",
            }
        )
        write(deck_path, diagram_clearer)
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
        if result.returncode != 0:
            raise AssertionError(report_path.read_text(encoding="utf-8"))
    print("generated image route audit regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
