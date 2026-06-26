#!/usr/bin/env python3
"""Regression tests for source-node density audit rules."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_deck.py"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_pptx(path: Path, slide_texts: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        for index, text in enumerate(slide_texts, start=1):
            runs = "".join(f"<a:t>{line}</a:t>" for line in text.splitlines())
            archive.writestr(f"ppt/slides/slide{index}.xml", f"<p:sld>{runs}</p:sld>")


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


STYLE_ATLAS = [
    {
        "id": "section-roadmap",
        "source_template_pages": [2, 5],
        "geometry": "large field with grouped branch modules",
        "best_for": "section orientation and concept grouping",
        "capacity_limits": "three to four branches before splitting",
        "renderer_layouts": ["roadmap"],
    },
    {
        "id": "dark-evidence",
        "source_template_pages": [9, 17],
        "geometry": "dark field with one strong evidence slot",
        "best_for": "case evidence with short interpretation",
        "capacity_limits": "one visual and three points only",
        "renderer_layouts": ["image-left-dark", "image-right-dark"],
    },
    {
        "id": "meaningful-compare",
        "source_template_pages": [12],
        "geometry": "two strong fields with balanced labels",
        "best_for": "real contrast between two decisions",
        "capacity_limits": "two sides with up to three items",
        "renderer_layouts": ["comparison"],
    },
    {
        "id": "dense-index",
        "source_template_pages": [3, 18],
        "geometry": "compact grid with clear grouped modules",
        "best_for": "occasional dense enumerations",
        "capacity_limits": "two to three columns, no long paragraph",
        "renderer_layouts": ["table"],
    },
    {
        "id": "accent-statement",
        "source_template_pages": [8, 10],
        "geometry": "accent color field with statement and support",
        "best_for": "memorable principle or transition",
        "capacity_limits": "one statement and two support points",
        "renderer_layouts": ["orange", "image-right-orange"],
    },
    {
        "id": "plain-explain",
        "source_template_pages": [6, 14],
        "geometry": "light field with title axis and evidence group",
        "best_for": "compact explanation with supporting points",
        "capacity_limits": "one paragraph plus four points",
        "renderer_layouts": ["light", "image-left"],
    },
]


def style_reference(style: dict[str, Any]) -> dict[str, Any]:
    return {
        "page": style["source_template_pages"][0],
        "family": style["id"],
        "style_family": style["id"],
        "layout_features": ["template title axis", "structured color field"],
        "adaptation": f"Use {style['id']} geometry because the content relationship fits this template structure family.",
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


def long_deck_with_style_sequence(style_ids: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes = [
        {
            "id": f"n{index:04d}",
            "title": f"Node {index}",
            "order": index,
            "parent_id": None if index == 1 else "n0001",
            "include": True,
        }
        for index in range(1, 17)
    ]
    source = {
        "outline_mode": "detailed",
        "mode_declared_by_user": True,
        "nodes": nodes,
        "images": [],
    }
    styles = {item["id"]: item for item in STYLE_ATLAS}
    layout_by_style = {
        "section-roadmap": "roadmap",
        "dark-evidence": "image-left-dark",
        "meaningful-compare": "comparison",
        "dense-index": "table",
        "accent-statement": "image-right-orange",
        "plain-explain": "image-left",
    }
    slides: list[dict[str, Any]] = [
        {
            "number": 1,
            "title": "visible-n0001",
            "layout": "cover",
            "screen": {"explanation": "visible-n0001", "bullets": [], "caption": "", "blocks": []},
            "visuals": [],
            "visual_plan": {"template_reference": style_reference(styles["accent-statement"])},
            "source_node_ids": ["n0001"],
            "source_node_treatments": coverage_treatments(["n0001"]),
            "added_content": [],
            "scope_check": {"status": "within-branch", "branch_node_id": "n0001"},
        }
    ]
    mapping = [
        {
            "slide_number": 1,
            "template_reference": "accent-statement",
            "template_style_family": "accent-statement",
            "layout_family": "cover",
            "content_fit_reason": "The cover introduces the lesson with a strong template statement field.",
            "local_ppt_decision": "Render as a course cover while keeping the template title axis.",
        }
    ]
    for offset, style_id in enumerate(style_ids, start=2):
        node_id = f"n{offset:04d}"
        style = styles[style_id]
        layout = layout_by_style[style_id]
        blocks = [
            {"heading": "问题判断", "items": [f"visible-{node_id} appears in a meaningful block"]},
            {"heading": "处理动作", "items": ["Use this structure because it matches the teaching relationship"]},
        ]
        slides.append(
            {
                "number": offset,
                "title": f"Slide {offset} carries visible-{node_id}",
                "layout": layout,
                "screen": {
                    "explanation": f"This learner-facing explanation preserves visible-{node_id} and states the core idea clearly.",
                    "bullets": [f"visible-{node_id} is the preserved source evidence.", "A second point keeps the page readable."],
                    "caption": "The visual group explains how to read this structure." if layout.startswith("image") or layout == "comparison" else "",
                    "blocks": blocks,
                },
                "visuals": [],
                "visual_plan": {
                    "source_node_id": node_id,
                    "asset_type": "editable-diagram",
                    "integration": "knowledge-page",
                    "description": f"{style_id} teaching diagram",
                    "teaching_role": "Shows why the selected template structure fits this point",
                    "visual_applicability": "required",
                    "imagegen_priority": "not-needed",
                    "imagegen_bypass_reason": "Editable structure is clearer than generated imagery",
                    "text_area_ratio": 0.45,
                    "labels_as_slide_text": True,
                    "template_style_family": style_id,
                    "layout_variant": style_id,
                    "template_reference": style_reference(style),
                    "diagram_elements": [{"kind": "module", "label": style_id}],
                },
                "source_node_ids": [node_id],
                "source_node_treatments": coverage_treatments([node_id]),
                "added_content": [],
                "scope_check": {"status": "within-branch", "branch_node_id": "n0001"},
            }
        )
        mapping.append(
            {
                "slide_number": offset,
                "template_reference": style_id,
                "template_style_family": style_id,
                "layout_family": layout,
                "content_fit_reason": f"The source point fits {style_id} because the content relationship matches the style capacity.",
                "local_ppt_decision": f"Render with {layout} so the planned {style_id} geometry is visible.",
            }
        )
    deck = {
        "course": {
            "title": "Template rhythm regression",
            "audience": "course creators",
            "outline_mode": "detailed",
            "curriculum_context": {
                "system_name": "Course system",
                "module": "Audit",
                "course_role": "Verify template rhythm",
                "excluded_neighbor_topics": [],
            },
            "template_style_atlas": STYLE_ATLAS,
            "template_page_mapping": mapping,
            "template_native_reuse_status": {
                "status": "not-needed",
                "reason": "This regression focuses on editable template structure families, not native motifs.",
            },
            "template_native_element_inventory": [],
            "image_generation_review": {
                "status": "completed",
                "source_case_image_count": 0,
                "generated_slide_numbers": [],
                "generated_bypass_reason": "Editable diagrams and structure-family mapping carry the visual bridge in this regression deck.",
                "candidates_considered": 0,
            },
            "source_image_coverage": [],
            "page_design_review": {
                "status": "completed",
                "checked_dimensions": ["title-scale", "alignment", "proximity", "contrast", "image-caption", "contact-sheet"],
                "contact_sheet_reviewed": True,
                "reference_method": "Compared the long-deck rhythm against the template style atlas before build.",
                "issues_fixed": ["Adjusted repeated style families before import."],
            },
        },
        "slides": slides,
    }
    return deck, source


def long_deck_with_generated_fallback(include_route_evidence: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    deck, source = long_deck_with_style_sequence([
        "section-roadmap",
        "dark-evidence",
        "meaningful-compare",
        "dense-index",
        "accent-statement",
        "plain-explain",
        "section-roadmap",
        "dark-evidence",
        "meaningful-compare",
        "dense-index",
        "accent-statement",
        "plain-explain",
        "section-roadmap",
        "dark-evidence",
        "meaningful-compare",
    ])
    slide = deck["slides"][1]
    slide["layout"] = "image-left"
    slide["visuals"] = [{"kind": "image", "path": "/tmp/fallback.png"}]
    slide["screen"]["caption"] = "This generated case image is interpreted for the learner."
    slide["visual_plan"]["asset_type"] = "generated-image"
    slide["visual_plan"]["generation_route"] = "user-provided"
    slide["visual_plan"]["imagegen_priority"] = "unavailable"
    slide["visual_plan"]["prompt_brief"] = "text-free concrete teaching case"
    deck["course"]["image_generation_tasks"] = [
        {
            "slide_number": 2,
            "route": "user-provided",
            "status": "local_deterministic_fallback",
            "final_asset_path": "/tmp/fallback.png",
        }
    ]
    deck["course"]["image_generation_review"]["generated_slide_numbers"] = [2]
    deck["course"]["image_generation_review"]["fallback_slide_numbers"] = [2]
    deck["course"]["image_generation_review"]["candidates_considered"] = 1
    deck["course"]["image_generation_review"]["generated_bypass_reason"] = (
        "Local fallback was used after checking generation routes for this regression case."
    )
    if include_route_evidence:
        deck["course"]["image_generation_review"]["gpt_image_2_attempts"] = [
            {
                "status": "failed",
                "slide_numbers": [2],
                "error_layer": "codex-cli",
                "notes": "GPT Image 2 generation failed in this regression case.",
            }
        ]
        deck["course"]["image_generation_review"]["imagegen_attempts"] = [
            {
                "status": "failed",
                "slide_numbers": [2],
                "error_layer": "imagegen-tool",
                "notes": "Built-in imagegen failed in this regression case.",
            }
        ]
    return deck, source


class AuditDeckDensityTest(unittest.TestCase):
    def run_audit(self, deck: dict[str, Any], source: dict[str, Any]) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            deck_path = temp / "deck-spec.json"
            source_path = temp / "source-map.json"
            report_path = temp / "mechanical-audit-report.json"
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

    def run_audit_with_pptx(
        self,
        deck: dict[str, Any],
        source: dict[str, Any],
        slide_texts: list[str],
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            deck_path = temp / "deck-spec.json"
            source_path = temp / "source-map.json"
            report_path = temp / "mechanical-audit-report.json"
            pptx_path = temp / "deck.pptx"
            write_json(deck_path, deck)
            write_json(source_path, source)
            write_pptx(pptx_path, slide_texts)

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
                    "--pptx",
                    str(pptx_path),
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
                    "module": "Audit",
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
            {
                "id": f"n{index:04d}",
                "title": f"Node {index}",
                "order": index,
                "parent_id": None if index == 1 else "n0001",
                "include": True,
            }
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
                    "module": "Audit",
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
            {
                "id": f"n{index:04d}",
                "title": f"Node {index}",
                "order": index,
                "parent_id": None if index == 1 else "n0001",
                "include": True,
            }
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
                    "module": "Audit",
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
                    "scope_check": {"status": "within-branch", "branch_node_id": "n0001"},
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
                    "scope_check": {"status": "within-branch", "branch_node_id": "n0001"},
                },
            ],
        }

        result, report = self.run_audit(deck, source)

        self.assertEqual(result.returncode, 0, report["errors"])
        self.assertTrue(report["ok"])

    def test_pptx_slide_text_must_contain_each_source_evidence(self) -> None:
        nodes = [
            {"id": f"n{index:04d}", "title": f"Node {index}", "order": index, "include": True}
            for index in range(1, 4)
        ]
        source = {
            "outline_mode": "detailed",
            "mode_declared_by_user": True,
            "nodes": nodes,
            "images": [],
        }
        deck = {
            "course": {
                "title": "Rendered evidence regression",
                "audience": "course creators",
                "outline_mode": "detailed",
                "curriculum_context": {
                    "system_name": "Course system",
                    "module": "Audit",
                    "course_role": "Verify rendered source evidence",
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
                    "title": "Rendered page carries all evidence",
                    "layout": "roadmap",
                    "screen": {
                        "explanation": "This page claims visible-n0002 and visible-n0003 are present.",
                        "bullets": [
                            "visible-n0002 appears in the spec.",
                            "visible-n0003 appears in the spec.",
                            "A third point keeps the page valid.",
                        ],
                        "caption": "",
                        "blocks": [],
                    },
                    "visuals": [],
                    "visual_plan": visual_plan("n0002"),
                    "source_node_ids": ["n0002", "n0003"],
                    "source_node_treatments": coverage_treatments(["n0002", "n0003"]),
                    "added_content": [],
                },
            ],
        }

        result, report = self.run_audit_with_pptx(
            deck,
            source,
            [
                "visible-n0001",
                "Rendered page carries all evidence\nvisible-n0002",
            ],
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("built PPTX slide text", "\n".join(report["errors"]))

    def test_distinct_source_nodes_cannot_reuse_the_same_evidence(self) -> None:
        nodes = [
            {"id": f"n{index:04d}", "text": f"Node {index}", "order": index, "include": True}
            for index in range(1, 4)
        ]
        source = {
            "outline_mode": "detailed",
            "mode_declared_by_user": True,
            "nodes": nodes,
            "images": [],
        }
        deck = {
            "course": {
                "title": "Duplicate evidence regression",
                "audience": "course creators",
                "outline_mode": "detailed",
                "curriculum_context": {
                    "system_name": "Course system",
                    "module": "Audit",
                    "course_role": "Reject generic repeated evidence",
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
                    "title": "A generic heading cannot cover details",
                    "layout": "roadmap",
                    "screen": {
                        "explanation": "generic-evidence is visible but too generic for two different nodes.",
                        "bullets": [
                            "generic-evidence",
                            "A second point keeps the page valid.",
                            "A third point keeps the page valid.",
                        ],
                        "caption": "",
                        "blocks": [],
                    },
                    "visuals": [],
                    "visual_plan": visual_plan("n0002"),
                    "source_node_ids": ["n0002", "n0003"],
                    "source_node_treatments": [
                        {
                            "source_node_id": "n0002",
                            "coverage_status": "preserved",
                            "screen_evidence": "generic-evidence",
                            "coverage_note": "carried into learner-facing copy",
                        },
                        {
                            "source_node_id": "n0003",
                            "coverage_status": "preserved",
                            "screen_evidence": "generic-evidence",
                            "coverage_note": "carried into learner-facing copy",
                        },
                    ],
                    "added_content": [],
                },
            ],
        }

        result, report = self.run_audit(deck, source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repeats screen_evidence", "\n".join(report["errors"]))

    def test_visible_evidence_order_must_follow_source_order(self) -> None:
        nodes = [
            {"id": f"n{index:04d}", "text": f"Node {index}", "order": index, "include": True}
            for index in range(1, 4)
        ]
        source = {
            "outline_mode": "detailed",
            "mode_declared_by_user": True,
            "nodes": nodes,
            "images": [],
        }
        deck = {
            "course": {
                "title": "Evidence order regression",
                "audience": "course creators",
                "outline_mode": "detailed",
                "curriculum_context": {
                    "system_name": "Course system",
                    "module": "Audit",
                    "course_role": "Reject visible evidence order drift",
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
                    "title": "Visible order must match source order",
                    "layout": "roadmap",
                    "screen": {
                        "explanation": "The slide text mentions visible-n0003 before visible-n0002.",
                        "bullets": [
                            "visible-n0003 appears first.",
                            "visible-n0002 appears second.",
                            "A third point keeps the page valid.",
                        ],
                        "caption": "",
                        "blocks": [],
                    },
                    "visuals": [],
                    "visual_plan": visual_plan("n0002"),
                    "source_node_ids": ["n0002", "n0003"],
                    "source_node_treatments": coverage_treatments(["n0002", "n0003"]),
                    "added_content": [],
                },
            ],
        }

        result, report = self.run_audit(deck, source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("out of source order", "\n".join(report["errors"]))

    def test_long_deck_rejects_repeated_template_style_family(self) -> None:
        deck, source = long_deck_with_style_sequence(["dense-index"] * 15)

        result, report = self.run_audit(deck, source)

        errors = "\n".join(report["errors"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("template style variety", errors)
        self.assertIn("composition variety", errors)

    def test_long_deck_accepts_template_style_atlas_rhythm(self) -> None:
        deck, source = long_deck_with_style_sequence([
            "section-roadmap",
            "dark-evidence",
            "meaningful-compare",
            "dense-index",
            "accent-statement",
            "plain-explain",
            "section-roadmap",
            "dark-evidence",
            "meaningful-compare",
            "dense-index",
            "accent-statement",
            "plain-explain",
            "section-roadmap",
            "dark-evidence",
            "meaningful-compare",
        ])

        result, report = self.run_audit(deck, source)

        self.assertEqual(result.returncode, 0, report["errors"])
        self.assertTrue(report["ok"])

    def test_generated_image_fallback_requires_route_chain_evidence(self) -> None:
        deck, source = long_deck_with_generated_fallback(include_route_evidence=False)

        result, report = self.run_audit(deck, source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gpt-image-2 -> imagegen -> fallback", "\n".join(report["errors"]))

    def test_generated_image_fallback_passes_with_route_chain_evidence(self) -> None:
        deck, source = long_deck_with_generated_fallback(include_route_evidence=True)

        result, report = self.run_audit(deck, source)

        self.assertEqual(result.returncode, 0, report["errors"])
        self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
