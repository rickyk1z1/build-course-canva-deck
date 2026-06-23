#!/usr/bin/env python3
"""Audit deck-spec, source coverage, scope records, and optional PPTX text."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


FORBIDDEN = [
    "PDF", "原稿", "来源文档", "制作说明", "图旁注明", "详细讲稿",
    "预计讲解时间", "视觉说明", "对应节点", "Genji 是真想教会你",
    "lorem ipsum", "[TODO", "{{", "}}", "turn0", "ref_id",
]
KNOWLEDGE_LAYOUTS = {"roadmap", "light", "dark", "orange", "image-left", "image-right", "comparison", "table", "summary"}
ALLOWED_ADDITION_KINDS = {"definition", "cause", "relationship", "example", "misconception", "boundary"}
VISUAL_ASSET_TYPES = {
    "source-image",
    "redrawn-source-image",
    "generated-image",
    "editable-diagram",
    "editable-table",
    "text-only-exception",
}
IMAGE_ASSET_TYPES = {"source-image", "redrawn-source-image", "generated-image"}
VISUAL_LAYOUTS = {"image-left", "image-right", "comparison", "table", "roadmap"}
FORBIDDEN_VISUAL_INTEGRATIONS = {"standalone-stage", "asset-list", "production-note", "later", "future-task"}
GENERATED_IMAGE_ROUTES = {"imagegen", "user-provided", "external-tool"}
VISUAL_APPLICABILITY = {"required", "exception"}
IMAGEGEN_PRIORITY = {"preferred", "not-needed", "unavailable"}


def flatten_text(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from flatten_text(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_text(item)


def visible_text(slide: dict[str, Any]) -> str:
    screen = slide.get("screen") or {}
    values = [slide.get("title", ""), screen.get("explanation", ""), screen.get("bullets", []), screen.get("caption", ""), screen.get("blocks", [])]
    return "\n".join(flatten_text(values))


def pptx_text(path: Path) -> tuple[int, str]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        names.sort(key=lambda name: int(re.search(r"(\d+)", Path(name).stem).group(1)))
        texts: list[str] = []
        for name in names:
            xml = archive.read(name).decode("utf-8", errors="replace")
            texts.extend(html.unescape(value) for value in re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.S))
        return len(names), "\n".join(texts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck-spec", required=True, type=Path)
    parser.add_argument("--source-map", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--pptx", type=Path)
    parser.add_argument("--layout-dir", type=Path)
    args = parser.parse_args()

    deck = json.loads(args.deck_spec.read_text(encoding="utf-8"))
    source = json.loads(args.source_map.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []
    mode = source.get("outline_mode")
    if mode not in {"detailed", "sparse"} or not source.get("mode_declared_by_user"):
        errors.append("outline mode was not explicitly declared by the user")
    course = deck.get("course") or {}
    if course.get("outline_mode") != mode:
        errors.append("deck-spec mode does not match source-map mode")
    curriculum = course.get("curriculum_context") or {}
    if not curriculum.get("system_name"):
        errors.append("curriculum_context.system_name is required")
    if not curriculum.get("module"):
        errors.append("curriculum_context.module is required")
    if not curriculum.get("course_role"):
        errors.append("curriculum_context.course_role is required")

    source_nodes = [node for node in source.get("nodes", []) if node.get("include", True)]
    source_ids = {node.get("id") for node in source_nodes}
    source_order = {node.get("id"): node.get("order") for node in source_nodes}
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("deck-spec slides must be non-empty")
        slides = []
    expected_numbers = list(range(1, len(slides) + 1))
    actual_numbers = [slide.get("number") for slide in slides]
    if actual_numbers != expected_numbers:
        errors.append("slide numbers must be contiguous and match list order")

    mapped: list[str] = []
    previous_min_order = 0
    exclusions = [str(value) for value in course.get("explicit_exclusions", [])]
    exclusions.extend(str(value) for value in curriculum.get("excluded_neighbor_topics", []))
    for index, slide in enumerate(slides, start=1):
        label = f"slide {index}"
        layout = slide.get("layout", "light")
        text = visible_text(slide)
        lower = text.lower()
        for term in FORBIDDEN:
            if term.lower() in lower:
                errors.append(f"{label} contains forbidden learner-facing text: {term}")
        for term in exclusions:
            if term and term.lower() in lower:
                errors.append(f"{label} contains an explicit out-of-scope term: {term}")
        title = str(slide.get("title", "")).strip()
        if layout != "cover" and (not title or title.endswith(("?", "？"))):
            errors.append(f"{label} must use a conclusion-style title")
        screen = slide.get("screen") or {}
        if layout in KNOWLEDGE_LAYOUTS:
            explanation = str(screen.get("explanation", "")).strip()
            bullets = screen.get("bullets") or []
            blocks = screen.get("blocks") or []
            point_count = len(bullets) + sum(len(block.get("items", [])) for block in blocks if isinstance(block, dict))
            if len(explanation) < 20:
                errors.append(f"{label} lacks a self-contained learner explanation")
            if layout not in {"table", "summary"} and not 3 <= point_count <= 5:
                errors.append(f"{label} should contain 3-5 structured learner-facing points")
            if layout in {"image-left", "image-right", "comparison"} and not screen.get("caption"):
                errors.append(f"{label} has a visual layout without learner-facing interpretation")
            if layout != "summary":
                visual_plan = slide.get("visual_plan")
                if not isinstance(visual_plan, dict):
                    errors.append(f"{label} lacks a slide-level visual_plan")
                    visual_plan = {}
                asset_type = str(visual_plan.get("asset_type", "")).strip()
                integration = str(visual_plan.get("integration", "")).strip()
                plan_node = visual_plan.get("source_node_id")
                description = str(visual_plan.get("description", "")).strip()
                role = str(visual_plan.get("teaching_role", "")).strip()
                visual_applicability = str(visual_plan.get("visual_applicability", "")).strip()
                imagegen_priority = str(visual_plan.get("imagegen_priority", "")).strip()
                if asset_type not in VISUAL_ASSET_TYPES:
                    errors.append(f"{label} visual_plan.asset_type is unsupported")
                if visual_applicability not in VISUAL_APPLICABILITY:
                    errors.append(f"{label} visual_plan.visual_applicability must be required or exception")
                if imagegen_priority not in IMAGEGEN_PRIORITY:
                    errors.append(f"{label} visual_plan.imagegen_priority is required")
                if integration != "knowledge-page" or integration in FORBIDDEN_VISUAL_INTEGRATIONS:
                    errors.append(f"{label} visual_plan must integrate the visual into the knowledge page")
                if plan_node not in source_ids:
                    errors.append(f"{label} visual_plan.source_node_id must map to an original source node")
                if len(description) < 8 or len(role) < 8:
                    errors.append(f"{label} visual_plan lacks a concrete teaching role or description")
                if visual_plan.get("labels_as_slide_text") is not True and asset_type != "text-only-exception":
                    errors.append(f"{label} visual labels must be editable slide text")
                if visual_applicability == "required" and asset_type == "text-only-exception":
                    errors.append(f"{label} requires a case or demonstration visual, but uses a text-only exception")
                text_area_ratio = visual_plan.get("text_area_ratio")
                if asset_type != "text-only-exception":
                    if not isinstance(text_area_ratio, (int, float)):
                        errors.append(f"{label} visual_plan.text_area_ratio is required for illustrated slides")
                    elif not 0.33 <= float(text_area_ratio) <= 0.48:
                        errors.append(f"{label} text area should stay around 40% on illustrated slides")
                visuals = slide.get("visuals") or []
                if asset_type in IMAGE_ASSET_TYPES:
                    if not visuals:
                        errors.append(f"{label} visual_plan uses an image asset but slide.visuals is empty")
                    if layout not in {"image-left", "image-right", "comparison"}:
                        errors.append(f"{label} image assets must use an image-integrated layout")
                    if not screen.get("caption"):
                        errors.append(f"{label} image asset lacks learner-facing visual interpretation")
                if asset_type == "generated-image":
                    route = str(visual_plan.get("generation_route", "")).strip()
                    prompt_brief = str(visual_plan.get("prompt_brief", "")).strip()
                    if route not in GENERATED_IMAGE_ROUTES:
                        errors.append(f"{label} generated image must record a supported generation route")
                    if route != "imagegen" and imagegen_priority != "unavailable":
                        errors.append(f"{label} generated image should use imagegen unless imagegen is unavailable")
                    if len(prompt_brief) < 12:
                        errors.append(f"{label} generated image must record a concrete prompt brief")
                if asset_type in {"editable-diagram", "editable-table"} and imagegen_priority == "preferred":
                    errors.append(f"{label} editable visual must explain why imagegen was not used")
                if imagegen_priority == "not-needed":
                    bypass_reason = str(visual_plan.get("imagegen_bypass_reason", "")).strip()
                    if len(bypass_reason) < 12:
                        errors.append(f"{label} imagegen bypass requires a concrete reason")
                if asset_type in {"editable-diagram", "editable-table"} and layout not in VISUAL_LAYOUTS:
                    errors.append(f"{label} editable visual assets should use a visible diagram/table/comparison layout")
                if asset_type == "text-only-exception":
                    reason = str(visual_plan.get("exception_reason", "")).strip()
                    if layout not in {"summary"} and len(reason) < 12:
                        errors.append(f"{label} text-only visual exception is not justified")
        node_ids = slide.get("source_node_ids") or []
        if not node_ids:
            errors.append(f"{label} has no source-node mapping")
        for node_id in node_ids:
            if node_id not in source_ids:
                errors.append(f"{label} maps unknown source node {node_id}")
            else:
                mapped.append(node_id)
        orders = sorted(source_order[node_id] for node_id in node_ids if node_id in source_order)
        if orders:
            if orders[0] < previous_min_order:
                errors.append(f"{label} breaks authoritative source order")
            previous_min_order = max(previous_min_order, orders[0])
        additions = slide.get("added_content") or []
        if mode == "detailed" and additions:
            errors.append(f"{label} adds content in detailed-outline mode")
        if mode == "sparse":
            scope = slide.get("scope_check") or {}
            if scope.get("status") != "within-branch" or scope.get("branch_node_id") not in source_ids:
                errors.append(f"{label} lacks a valid within-branch scope check")
            for addition_index, item in enumerate(additions, start=1):
                prefix = f"{label} addition {addition_index}"
                if item.get("source_node_id") not in source_ids:
                    errors.append(f"{prefix} is not mapped to an original node")
                if item.get("kind") not in ALLOWED_ADDITION_KINDS:
                    errors.append(f"{prefix} has an unsupported addition kind")
                if item.get("relevance") != "direct":
                    errors.append(f"{prefix} is not directly relevant to its branch")
                urls = item.get("evidence_urls") or []
                if not urls or not all(str(url).startswith("https://") for url in urls):
                    errors.append(f"{prefix} lacks authoritative HTTPS evidence")

    missing = [node_id for node_id in source_ids if node_id not in mapped]
    if missing:
        errors.append(f"source coverage is incomplete; missing {len(missing)} nodes: {', '.join(sorted(missing)[:12])}")
    mapped_orders = [source_order[node_id] for node_id in mapped if node_id in source_order]
    if mapped_orders != sorted(mapped_orders):
        errors.append("source-node mappings are not monotonic across slides")

    pptx_slides = None
    if args.pptx:
        pptx_slides, text = pptx_text(args.pptx)
        if pptx_slides != len(slides):
            errors.append(f"PPTX page count {pptx_slides} does not match deck-spec {len(slides)}")
        lower = text.lower()
        for term in FORBIDDEN:
            if term.lower() in lower:
                errors.append(f"PPTX contains forbidden visible text: {term}")

    if args.layout_dir and args.layout_dir.exists():
        for path in sorted(args.layout_dir.glob("*.json")):
            raw = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r'"(?:overflow|isOverflowing|textOverflow)"\s*:\s*true', raw, re.I):
                errors.append(f"layout reports overflow: {path.name}")
            if re.search(r'"(?:unintendedOverlap|overlapWarning)"\s*:\s*true', raw, re.I):
                errors.append(f"layout reports unintended overlap: {path.name}")

    report = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "mode": mode,
            "source_nodes": len(source_nodes),
            "mapped_nodes": len(set(mapped)),
            "slides": len(slides),
            "pptx_slides": pptx_slides,
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
