#!/usr/bin/env python3
"""Regression tests for source-node density QA."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_deck.py"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def template_reference() -> dict[str, Any]:
    return {
        "page": 7,
        "layout_features": ["right-side visual anchor", "narrow text column"],
        "adaptation": "fit the explanation and visible points into the referenced composition before build",
    }


def visual_plan(node_id: str) -> dict[str, Any]:
    return {
        "source_node_id": node_id,
        "asset_type": "editable-diagram",
        "integration": "knowledge-page",
        "description": "dense mapping diagnostic diagram",
        "teaching_role": "shows why the branch must be split for learners",
        "visual_applicability": "required",
        "imagegen_priority": "not-needed",
        "imagegen_bypass_reason": "simple structure is clearer as editable shapes",
        "text_area_ratio": 0.4,
        "labels_as_slide_text": True,
        "template_reference": template_reference(),
    }


def coverage_treatments(node_ids: list[str]) -> list[dict[str, str]]:
    return [
        {
            "source_node_id": node_id,
            "coverage_status": "preserved",
            "screen_evidence": f"visible-{node_id}",
            "coverage_note": "carried into learner-facing copy without compression",
        }
        for node_id in node_ids
    ]


class AuditDeckDensityTest(unittest.TestCase):
    def run_audit(self, deck: dict[str, Any], source: dict[str, Any]) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            deck_path = temp / "deck-spec.json"
            source_path = temp / "source-map.json"
            report_path = temp / "qa-report.json"
            write_json(deck_path, deck)
            write_json(source_path, source)

            result = subprocess.run(
                [
                    sys.executable,
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
                check=False,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            return result, report

    def test_detailed_mode_rejects_overcompressed_source_mapping(self) -> None:
        nodes = [
            {"id": f"n{index:04d}", "title": f"Node {index}", "order": index, "include": True}
            for index in range(1, 27)
        ]
        source = {
            "outline_mode": "detailed",
            "mode_declared_by_user": True,
            "nodes": nodes,
            "images": [],
        }
        deck = {
            "course": {
                "title": "Density regression",
                "audience": "course creators",
                "outline_mode": "detailed",
                "curriculum_context": {
                    "system_name": "Course system",
                    "module": "QA",
                    "course_role": "Verify source coverage density",
                    "excluded_neighbor_topics": [],
                },
            },
            "slides": [
                {
                    "number": 1,
                    "title": "Density regression",
                    "layout": "cover",
                    "screen": {"explanation": "", "bullets": [], "caption": "", "blocks": []},
                    "visuals": [],
                    "visual_plan": {"template_reference": template_reference()},
                    "source_node_ids": ["n0001"],
                    "added_content": [],
                },
                {
                    "number": 2,
                    "title": "A dense branch needs more learner pages",
                    "layout": "roadmap",
                    "screen": {
                        "explanation": "This page intentionally maps too many source nodes so the audit must reject it.",
                        "bullets": [
                            "One branch contains many separate teaching points.",
                            "A single slide cannot preserve the original detail.",
                            "The deck should split the branch in source order.",
                            "Source coverage cannot be hidden in metadata.",
                        ],
                        "caption": "",
                        "blocks": [],
                    },
                    "visuals": [],
                    "visual_plan": visual_plan("n0002"),
                    "source_node_ids": [f"n{index:04d}" for index in range(2, 27)],
                    "added_content": [],
                },
            ],
        }

        result, report = self.run_audit(deck, source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("over-compresses source coverage", "\n".join(report["errors"]))

    def test_mapped_source_nodes_require_visible_coverage_treatments(self) -> None:
        nodes = [
            {"id": f"n{index:04d}", "title": f"Node {index}", "order": index, "include": True}
            for index in range(1, 6)
        ]
        source = {
            "outline_mode": "detailed",
            "mode_declared_by_user": True,
            "nodes": nodes,
            "images": [],
        }
        deck = {
            "course": {
                "title": "Treatment regression",
                "audience": "course creators",
                "outline_mode": "detailed",
                "curriculum_context": {
                    "system_name": "Course system",
                    "module": "QA",
                    "course_role": "Verify source node treatment evidence",
                    "excluded_neighbor_topics": [],
                },
            },
            "slides": [
                {
                    "number": 1,
                    "title": "visible-n0001",
                    "layout": "cover",
                    "screen": {"explanation": "visible-n0001", "bullets": [], "caption": "", "blocks": []},
                    "visuals": [],
                    "visual_plan": {"template_reference": template_reference()},
                    "source_node_ids": ["n0001"],
                    "added_content": [],
                },
                {
                    "number": 2,
                    "title": "Each mapped source node needs visible evidence",
                    "layout": "roadmap",
                    "screen": {
                        "explanation": "This page names visible-n0002 and visible-n0003 as preserved source content.",
                        "bullets": [
                            "visible-n0002 is carried into the learner-facing page.",
                            "visible-n0003 is carried into the learner-facing page.",
                            "visible-n0004 is carried into the learner-facing page.",
                            "visible-n0005 is carried into the learner-facing page.",
                        ],
                        "caption": "",
                        "blocks": [],
                    },
                    "visuals": [],
                    "visual_plan": visual_plan("n0002"),
                    "source_node_ids": ["n0002", "n0003", "n0004", "n0005"],
                    "added_content": [],
                },
            ],
        }

        result, report = self.run_audit(deck, source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_node_treatments", "\n".join(report["errors"]))

    def test_reasonable_mapping_with_visible_treatments_passes(self) -> None:
        nodes = [
            {"id": f"n{index:04d}", "title": f"Node {index}", "order": index, "include": True}
            for index in range(1, 6)
        ]
        source = {
            "outline_mode": "detailed",
            "mode_declared_by_user": True,
            "nodes": nodes,
            "images": [],
        }
        deck = {
            "course": {
                "title": "Treatment pass",
                "audience": "course creators",
                "outline_mode": "detailed",
                "curriculum_context": {
                    "system_name": "Course system",
                    "module": "QA",
                    "course_role": "Verify accepted treatment evidence",
                    "excluded_neighbor_topics": [],
                },
            },
            "slides": [
                {
                    "number": 1,
                    "title": "visible-n0001",
                    "layout": "cover",
                    "screen": {"explanation": "visible-n0001", "bullets": [], "caption": "", "blocks": []},
                    "visuals": [],
                    "visual_plan": {"template_reference": template_reference()},
                    "source_node_ids": ["n0001"],
                    "source_node_treatments": coverage_treatments(["n0001"]),
                    "added_content": [],
                },
                {
                    "number": 2,
                    "title": "Each mapped source node has visible evidence",
                    "layout": "roadmap",
                    "screen": {
                        "explanation": "This page names visible-n0002 and visible-n0003 as preserved source content.",
                        "bullets": [
                            "visible-n0002 is carried into the learner-facing page.",
                            "visible-n0003 is carried into the learner-facing page.",
                            "visible-n0004 is carried into the learner-facing page.",
                            "visible-n0005 is carried into the learner-facing page.",
                        ],
                        "caption": "",
                        "blocks": [],
                    },
                    "visuals": [],
                    "visual_plan": visual_plan("n0002"),
                    "source_node_ids": ["n0002", "n0003", "n0004", "n0005"],
                    "source_node_treatments": coverage_treatments(["n0002", "n0003", "n0004", "n0005"]),
                    "added_content": [],
                },
            ],
        }

        result, report = self.run_audit(deck, source)

        self.assertEqual(result.returncode, 0, report["errors"])
        self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
