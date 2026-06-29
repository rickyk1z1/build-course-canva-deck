#!/usr/bin/env python3
"""Regression test: no-source pages cannot all bypass generated case images."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path


AUDIT = Path(__file__).resolve().parents[1] / "scripts" / "audit_deck.py"


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def source_map() -> dict:
    nodes = [
        {"id": "n1", "order": 1, "parent_id": None, "text": "root", "include": True},
        {"id": "n2", "order": 2, "parent_id": "n1", "text": "chapter", "include": True},
    ]
    for offset in range(4):
        nodes.append(
            {
                "id": f"n{offset + 3}",
                "order": offset + 3,
                "parent_id": "n2",
                "text": f"point {offset + 1}",
                "include": True,
            }
        )
    return {
        "outline_mode": "detailed",
        "mode_declared_by_user": True,
        "nodes": nodes,
        "images": [],
    }


def teaching_expansion(text: str) -> dict:
    return {
        "mode_handling": "detailed-clarification",
        "learner_takeaway": text,
        "source_based_explanation": text,
        "example_or_judgment_cue": text,
        "display_priority": [text],
        "internal_only": [],
    }


def knowledge_slide(number: int, node_id: str, title: str, bypass: str) -> dict:
    return {
        "number": number,
        "layout": "light",
        "title": title,
        "source_node_ids": [node_id],
        "framework_progress_label": "chapter",
        "screen": {
            "explanation": f"{title} uses a visible operation path.",
            "bullets": [f"{title} path"],
            "caption": "",
            "blocks": [],
            "teaching_expansion": teaching_expansion(title),
        },
        "source_node_treatments": [
            {"source_node_id": node_id, "coverage_status": "clarified", "screen_evidence": title}
        ],
        "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
        "visual_plan": {
            "asset_type": "editable-diagram",
            "integration": "knowledge-page",
            "source_node_id": node_id,
            "source_image_ids": [],
            "labels_as_slide_text": True,
            "layout_variant": "side-rail",
            "generated_case_bypass_reason": bypass,
        },
        "visuals": [],
    }


def deck(bypasses: list[str]) -> dict:
    slides = [
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
            "screen": {
                "explanation": "chapter",
                "bullets": ["agenda 1", "agenda 2", "agenda 3", "agenda 4"],
                "caption": "",
                "blocks": [],
            },
            "section_preview_items": [
                {"source_node_id": "n3", "screen_evidence": "agenda 1"},
                {"source_node_id": "n4", "screen_evidence": "agenda 2"},
                {"source_node_id": "n5", "screen_evidence": "agenda 3"},
                {"source_node_id": "n6", "screen_evidence": "agenda 4"},
            ],
            "source_node_treatments": [
                {"source_node_id": "n2", "coverage_status": "section-heading", "screen_evidence": "chapter"}
            ],
            "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
        },
    ]
    for offset, bypass in enumerate(bypasses):
        slides.append(knowledge_slide(offset + 3, f"n{offset + 3}", f"point {offset + 1}", bypass))
    slides.append(
        {
            "number": 7,
            "layout": "summary",
            "title": "summary",
            "source_node_ids": [],
            "screen": {"explanation": "done", "bullets": [], "caption": "", "blocks": []},
            "source_node_treatments": [],
            "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
        }
    )
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
        "slides": slides,
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
        generic = deck(["本页是连续源节点整理，使用可编辑结构图比表格更适配当前信息量。"] * 4)
        report = run_audit(root, generic)
        if report["ok"]:
            raise AssertionError(report)
        if not any("generic generated_case_bypass_reason" in err for err in report["errors"]):
            raise AssertionError(report)

        specific_reasons = [
            "point 1 的操作路径需要保留快捷键、步骤和顺序， editable diagram 比生成场景图更清楚。",
            "point 2 的参数关系需要保留分类和轴， editable diagram 比生成场景图更清楚。",
            "point 3 的流程顺序需要逐步读， editable diagram 比生成场景图更清楚。",
            "point 4 的表格矩阵需要可编辑标签， editable diagram 比生成场景图更清楚。",
        ]
        all_bypass = deck(specific_reasons)
        report = run_audit(root, all_bypass)
        if report["ok"]:
            raise AssertionError(report)
        if not any("but no generated-image slides/image_generation_tasks" in err for err in report["errors"]):
            raise AssertionError(report)

        mixed = deck(specific_reasons)
        generated = mixed["slides"][2]
        generated["layout"] = "image-right"
        generated["screen"]["caption"] = "point 1 path"
        generated["visual_plan"].update(
            {
                "asset_type": "generated-image",
                "generation_route": "gpt-image-2",
                "generation_attempts": [
                    {"route": "gpt-image-2", "status": "success", "evidence": "saved asset"}
                ],
                "case_visual_map": [
                    {"screen_evidence": "point 1 path", "visible_detail": "step path"}
                ],
            }
        )
        generated["visuals"] = [{"path": "assets/generated/point-1.png", "alt": "point 1"}]
        mixed["course"]["image_generation_tasks"] = [
            {
                "slide": 3,
                "route": "gpt-image-2",
                "asset_path": "assets/generated/point-1.png",
                "generation_attempts": [
                    {"route": "gpt-image-2", "status": "success", "evidence": "saved asset"}
                ],
                "knowledge_anchor": "point 1",
                "observable_teaching_detail": "step path",
                "instant_takeaway": "point 1",
                "case_visual_map": [
                    {"screen_evidence": "point 1 path", "visible_detail": "step path"}
                ],
            }
        ]
        report = run_audit(root, mixed)
        if report["ok"]:
            raise AssertionError(report)
        if not any("only 1 generated-image slide" in err or "consecutive no-source non-generated run" in err for err in report["errors"]):
            raise AssertionError(report)

        second_generated = mixed["slides"][4]
        second_generated["layout"] = "image-right"
        second_generated["screen"]["caption"] = "point 3 path"
        second_generated["visual_plan"].update(
            {
                "asset_type": "generated-image",
                "generation_route": "gpt-image-2",
                "generation_attempts": [
                    {"route": "gpt-image-2", "status": "success", "evidence": "saved asset"}
                ],
                "case_visual_map": [
                    {"screen_evidence": "point 3 path", "visible_detail": "step path"}
                ],
            }
        )
        second_generated["visuals"] = [{"path": "assets/generated/point-3.png", "alt": "point 3"}]
        mixed["course"]["image_generation_tasks"].append(
            {
                "slide": 5,
                "route": "gpt-image-2",
                "asset_path": "assets/generated/point-3.png",
                "generation_attempts": [
                    {"route": "gpt-image-2", "status": "success", "evidence": "saved asset"}
                ],
                "knowledge_anchor": "point 3",
                "observable_teaching_detail": "step path",
                "instant_takeaway": "point 3",
                "case_visual_map": [
                    {"screen_evidence": "point 3 path", "visible_detail": "step path"}
                ],
            }
        )
        report = run_audit(root, mixed)
        if not report["ok"]:
            raise AssertionError(report)

    print("no-source generated-image gate regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
