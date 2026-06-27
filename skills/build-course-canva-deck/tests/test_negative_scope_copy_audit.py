#!/usr/bin/env python3
"""Regression test: course-boundary exclusions must not become screen copy."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


AUDIT = Path(__file__).resolve().parents[1] / "scripts" / "audit_deck.py"


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = {
            "outline_mode": "sparse",
            "mode_declared_by_user": True,
            "nodes": [
                {"id": "n1", "order": 1, "parent_id": None, "text": "root", "include": True},
                {"id": "n2", "order": 2, "parent_id": "n1", "text": "chapter", "include": True},
                {"id": "n3", "order": 3, "parent_id": "n2", "text": "point", "include": True},
            ],
            "images": [],
        }
        deck = {
            "course": {
                "outline_mode": "sparse",
                "curriculum_context": {
                    "system_name": "test",
                    "module": "test",
                    "course_role": "test",
                    "excluded_neighbor_topics": ["剪映界面、按钮位置、时间线操作"],
                },
                "chapter_spine": [{"source_node_id": "n2", "title": "chapter"}],
            },
            "slides": [
                {
                    "number": 1,
                    "layout": "cover",
                    "title": "root",
                    "screen": {
                        "explanation": "positive learner value",
                        "bullets": ["先讲判断", "不进入软件按钮"],
                        "caption": "",
                        "blocks": [],
                    },
                    "source_node_ids": [],
                    "source_node_treatments": [],
                    "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
                },
                {
                    "number": 2,
                    "layout": "lesson-overview",
                    "title": "overview",
                    "source_node_ids": ["n1"],
                    "screen": {"explanation": "root", "bullets": ["chapter"], "caption": "", "blocks": []},
                    "source_node_treatments": [
                        {"source_node_id": "n1", "coverage_status": "clarified", "screen_evidence": "root"}
                    ],
                    "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
                },
                {
                    "number": 3,
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
                    "number": 4,
                    "layout": "light",
                    "title": "point",
                    "source_node_ids": ["n3"],
                    "framework_progress_label": "chapter",
                    "screen": {"explanation": "point", "bullets": ["visible idea"], "caption": "", "blocks": []},
                    "source_node_treatments": [
                        {"source_node_id": "n3", "coverage_status": "clarified", "screen_evidence": "point"}
                    ],
                    "scope_check": {"status": "within-branch", "branch_node_id": "n2"},
                    "visual_plan": {
                        "asset_type": "text-only-exception",
                        "integration": "knowledge-page",
                        "source_node_id": "n3",
                        "source_image_ids": [],
                        "labels_as_slide_text": True,
                        "case_visual_map": [],
                    },
                    "visuals": [],
                    "added_content": [
                        {
                            "source_node_id": "n3",
                            "kind": "definition",
                            "relevance": "direct",
                            "evidence_urls": ["https://example.com"],
                        }
                    ],
                },
                {
                    "number": 5,
                    "layout": "summary",
                    "title": "summary",
                    "source_node_ids": [],
                    "screen": {"explanation": "done", "bullets": [], "caption": "", "blocks": []},
                    "source_node_treatments": [],
                },
            ],
        }
        source_path = root / "source.json"
        deck_path = root / "deck.json"
        report_path = root / "report.json"
        write(source_path, source)
        write(deck_path, deck)
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
        if not any("negative scope wording" in err and "不进入软件按钮" in err for err in report["errors"]):
            raise AssertionError(report)
    print("negative scope copy audit regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
