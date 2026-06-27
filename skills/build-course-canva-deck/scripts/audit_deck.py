#!/usr/bin/env python3
"""Audit deck-spec, source coverage, scope records, and optional PPTX text.

This audit is a deterministic guard for structural hard errors only. It does
NOT judge teaching quality, layout rhythm, or whether a generated image teaches
its point; those are the director's learner review (see
references/non-regression-checklist.md). The script deliberately avoids length
thresholds and magic ratios so that agents design human-readable courseware
instead of filling fields to pass a number.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


# Backstage / production words that must never reach learner-facing slide text.
FORBIDDEN = [
    "PDF", "原稿", "来源文档", "制作说明", "图旁注明", "详细讲稿",
    "预计讲解时间", "视觉说明", "对应节点", "Genji 是真想教会你",
    "lorem ipsum", "TODO", "[TODO", "{{", "}}", "turn0", "ref_id",
    "本页顺序", "本页内容", "本页对应", "本页覆盖", "来源路径", "源路径",
    "source path", "source_node", "screen_evidence", "coverage_note",
]
IMAGE_LAYOUTS = {
    "image-left", "image-right",
    "image-left-dark", "image-right-dark",
    "image-left-orange", "image-right-orange",
    "image-left-accent", "image-right-accent",
}
STRUCTURAL_LAYOUTS = {"lesson-overview", "section-cover", "summary"}
UNMAPPED_ALLOWED_LAYOUTS = {"cover", "summary"}
KNOWLEDGE_LAYOUTS = {"roadmap", "light", "dark", "orange", "accent", *IMAGE_LAYOUTS, "comparison", "table"}
CONTENT_LAYOUTS = { *STRUCTURAL_LAYOUTS, *KNOWLEDGE_LAYOUTS }
ALLOWED_LAYOUTS = {"cover", *CONTENT_LAYOUTS}
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
VISUAL_LAYOUTS = {*IMAGE_LAYOUTS, "comparison", "table", "roadmap"}
FORBIDDEN_VISUAL_INTEGRATIONS = {"standalone-stage", "asset-list", "production-note", "later", "future-task"}
GENERATED_IMAGE_ROUTES = {"gpt-image-2", "imagegen", "user-provided"}
SOURCE_COVERAGE_STATUSES = {
    "preserved",
    "clarified",
    "visualized",
    "restructured",
    "section-heading",
}
GENERIC_BLOCK_LABELS = {
    "a", "b",
    "对比a", "对比b",
    "结构顺序a", "结构顺序b",
    "方案a", "方案b",
    "要点a", "要点b",
    "重点a", "重点b",
    "模块a", "模块b",
    "路径a", "路径b",
    "顺序a", "顺序b",
    "左侧", "右侧",
}


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


def normalized_match_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def pptx_text(path: Path) -> tuple[int, list[str], str]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        names.sort(key=lambda name: int(re.search(r"(\d+)", Path(name).stem).group(1)))
        slide_texts: list[str] = []
        for name in names:
            xml = archive.read(name).decode("utf-8", errors="replace")
            texts = [html.unescape(value) for value in re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.S)]
            slide_texts.append("\n".join(texts))
        return len(names), slide_texts, "\n".join(slide_texts)


def normalized_label(value: Any) -> str:
    return re.sub(r"[\s_\-—:：|｜/]+", "", str(value or "")).lower()


def is_generic_block_label(value: Any) -> bool:
    label = normalized_label(value)
    if not label:
        return True
    if label in GENERIC_BLOCK_LABELS:
        return True
    return bool(re.fullmatch(r"(对比|结构顺序|方案|要点|重点|模块|路径|顺序)[a-bａ-ｂ]?", label))


def ancestors_for(node_id: str, parent_by_id: dict[str, str | None]) -> list[str]:
    ancestors: list[str] = []
    current = parent_by_id.get(node_id)
    seen: set[str] = set()
    while current and current not in seen:
        ancestors.append(current)
        seen.add(current)
        current = parent_by_id.get(current)
    return ancestors


def top_section_for(node_id: str, root_id: str | None, parent_by_id: dict[str, str | None]) -> str | None:
    if not root_id or node_id == root_id:
        return None
    current = node_id
    seen: set[str] = set()
    while current and current not in seen:
        parent = parent_by_id.get(current)
        if parent == root_id:
            return current
        seen.add(current)
        current = parent or ""
    return None


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
    source_images = [
        image for image in source.get("images", [])
        if isinstance(image, dict) and "thumbnail" not in str(image.get("path", "")).lower()
    ]
    source_image_ids = {image.get("id") for image in source_images if image.get("id")}
    source_ids = {node.get("id") for node in source_nodes}
    source_order = {node.get("id"): node.get("order") for node in source_nodes}
    source_text_by_id = {
        str(node.get("id")): str(node.get("text") or node.get("title") or "")
        for node in source_nodes
    }
    parent_by_id = {
        str(node.get("id")): (str(node.get("parent_id")) if node.get("parent_id") else None)
        for node in source_nodes
    }
    ancestor_ids_by_id = {
        node_id: ancestors_for(node_id, parent_by_id)
        for node_id in source_text_by_id
    }
    root_ids = [
        str(node.get("id"))
        for node in sorted(source_nodes, key=lambda item: item.get("order", 0))
        if not node.get("parent_id")
    ]
    root_id = root_ids[0] if root_ids else None
    top_section_ids = [
        str(node.get("id"))
        for node in sorted(source_nodes, key=lambda item: item.get("order", 0))
        if root_id and str(node.get("parent_id") or "") == root_id
    ]

    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("deck-spec slides must be non-empty")
        slides = []
    expected_numbers = list(range(1, len(slides) + 1))
    actual_numbers = [slide.get("number") for slide in slides]
    if actual_numbers != expected_numbers:
        errors.append("slide numbers must be contiguous and match list order")

    if slides:
        non_cover_slides = [
            (index, slide)
            for index, slide in enumerate(slides, start=1)
            if slide.get("layout") != "cover"
        ]
        if not non_cover_slides or non_cover_slides[0][1].get("layout") != "lesson-overview":
            errors.append("first non-cover slide must use lesson-overview layout")
        if slides[-1].get("layout") != "summary":
            errors.append("final slide must use summary layout")

        overview_count = sum(1 for slide in slides if slide.get("layout") == "lesson-overview")
        if overview_count != 1:
            errors.append("deck must contain exactly one lesson-overview slide")
        summary_count = sum(1 for slide in slides if slide.get("layout") == "summary")
        if summary_count != 1:
            errors.append("deck must contain exactly one summary slide")

        seen_sections: list[str] = []
        seen_section_set: set[str] = set()
        for index, slide in enumerate(slides, start=1):
            layout = slide.get("layout", "light")
            node_ids = [str(value) for value in (slide.get("source_node_ids") or [])]
            if layout == "section-cover":
                if len(node_ids) != 1 or node_ids[0] not in top_section_ids:
                    errors.append(f"slide {index} section-cover must map exactly one top-level source section")
                    continue
                section_id = node_ids[0]
                expected_section = top_section_ids[len(seen_sections)] if len(seen_sections) < len(top_section_ids) else None
                if section_id in seen_section_set:
                    errors.append(f"slide {index} repeats section-cover for top-level source section {section_id}")
                elif expected_section and section_id != expected_section:
                    errors.append(
                        f"slide {index} section-cover breaks top-level source section order: "
                        f"expected {expected_section}, got {section_id}"
                    )
                seen_sections.append(section_id)
                seen_section_set.add(section_id)
                continue
            if layout in {"cover", "lesson-overview", "summary"}:
                continue
            slide_sections = {
                top_section_for(node_id, root_id, parent_by_id)
                for node_id in node_ids
                if node_id in source_ids
            }
            for section_id in sorted(value for value in slide_sections if value):
                if section_id not in seen_section_set:
                    errors.append(
                        f"slide {index} shows content before section-cover for top-level source section {section_id}"
                    )
        for section_id in top_section_ids:
            if section_id not in seen_section_set:
                errors.append(f"missing section-cover for top-level source section {section_id}")

    mapped: list[str] = []
    previous_min_order = 0
    exclusions = [str(value) for value in course.get("explicit_exclusions", [])]
    exclusions.extend(str(value) for value in curriculum.get("excluded_neighbor_topics", []))

    for index, slide in enumerate(slides, start=1):
        label = f"slide {index}"
        layout = slide.get("layout", "light")
        if layout not in ALLOWED_LAYOUTS:
            errors.append(f"{label} uses unsupported layout: {layout}")
        text = visible_text(slide)
        lower = text.lower()
        for term in FORBIDDEN:
            if term.lower() in lower:
                errors.append(f"{label} contains forbidden learner-facing text: {term}")
        for term in exclusions:
            if term and term.lower() in lower:
                errors.append(f"{label} contains an explicit out-of-scope term: {term}")

        title = str(slide.get("title", "")).strip()
        if layout != "cover" and not title:
            errors.append(f"{label} must have a learner-facing title")
        elif layout != "cover" and title.endswith(("?", "？")):
            warnings.append(f"{label} uses a question-style title; director should verify the answer is visible on the same page")

        slide_visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}

        screen = slide.get("screen") or {}
        if layout in CONTENT_LAYOUTS:
            explanation = str(screen.get("explanation", "")).strip()
            bullets = screen.get("bullets") or []
            blocks = screen.get("blocks") or []
            if not isinstance(blocks, list):
                errors.append(f"{label} screen.blocks must be a list when provided")
                blocks = []
            block_headings: list[str] = []
            for block_index, block in enumerate(blocks, start=1):
                if not isinstance(block, dict):
                    errors.append(f"{label} screen.blocks[{block_index}] must be an object")
                    continue
                heading = str(block.get("heading", "")).strip()
                block_headings.append(heading)
                if is_generic_block_label(heading):
                    errors.append(
                        f"{label} uses a generic or meaningless block label: {heading or '<empty>'}"
                    )
                items = block.get("items")
                if not isinstance(items, list) or not any(str(item).strip() for item in items):
                    errors.append(f"{label} block {heading or block_index} must contain visible learner-facing items")
            if layout in {"comparison", "table"}:
                meaningful_headings = [
                    heading for heading in block_headings
                    if heading and not is_generic_block_label(heading)
                ]
                if len(meaningful_headings) < 2:
                    errors.append(
                        f"{label} uses {layout} layout without at least two meaningful block headings; "
                        "do not create arbitrary A/B comparison or table structures"
                    )
                if len(set(normalized_label(heading) for heading in meaningful_headings)) != len(meaningful_headings):
                    errors.append(f"{label} repeats equivalent block headings in a structured layout")
            if not explanation:
                errors.append(f"{label} lacks a self-contained learner explanation")

            if layout in KNOWLEDGE_LAYOUTS:
                visual_plan = slide.get("visual_plan")
                if not isinstance(visual_plan, dict):
                    errors.append(f"{label} lacks a slide-level visual_plan")
                    visual_plan = {}
                asset_type = str(visual_plan.get("asset_type", "")).strip()
                integration = str(visual_plan.get("integration", "")).strip()
                plan_node = visual_plan.get("source_node_id")
                if asset_type not in VISUAL_ASSET_TYPES:
                    errors.append(f"{label} visual_plan.asset_type is unsupported")
                if integration != "knowledge-page" or integration in FORBIDDEN_VISUAL_INTEGRATIONS:
                    errors.append(f"{label} visual_plan must integrate the visual into the knowledge page")
                if plan_node not in source_ids:
                    errors.append(f"{label} visual_plan.source_node_id must map to an original source node")
                if visual_plan.get("labels_as_slide_text") is not True and asset_type != "text-only-exception":
                    errors.append(f"{label} visual labels must be editable slide text")
                visuals = slide.get("visuals") or []
                if asset_type in IMAGE_ASSET_TYPES:
                    if not visuals:
                        errors.append(f"{label} visual_plan uses an image asset but slide.visuals is empty")
                    if layout not in IMAGE_LAYOUTS | {"comparison"}:
                        errors.append(f"{label} image assets must use an image-integrated layout")
                    if not screen.get("caption"):
                        errors.append(f"{label} image asset lacks learner-facing visual interpretation")
                if asset_type in {"source-image", "redrawn-source-image"}:
                    visual_source_image_ids = visual_plan.get("source_image_ids")
                    if not isinstance(visual_source_image_ids, list) or not visual_source_image_ids:
                        errors.append(f"{label} source-image visual must list visual_plan.source_image_ids")
                        visual_source_image_ids = []
                    else:
                        unknown_images = [
                            str(image_id) for image_id in visual_source_image_ids
                            if image_id not in source_image_ids
                        ]
                        if unknown_images:
                            errors.append(
                                f"{label} visual_plan.source_image_ids contains unknown source images: "
                                + ", ".join(unknown_images[:8])
                            )
                    if len(visual_source_image_ids) > 3:
                        errors.append(
                            f"{label} combines {len(visual_source_image_ids)} independent source images; "
                            "source-image slides may use at most 3 readable source images"
                        )
                if asset_type == "generated-image":
                    route = str(visual_plan.get("generation_route", "")).strip()
                    if route not in GENERATED_IMAGE_ROUTES:
                        errors.append(f"{label} generated image must record a supported generation route")
                if asset_type == "text-only-exception" and layout in IMAGE_LAYOUTS | {"comparison"}:
                    errors.append(f"{label} uses an image/comparison layout but declares a text-only visual exception")

        node_ids = slide.get("source_node_ids") or []
        if not node_ids and layout not in UNMAPPED_ALLOWED_LAYOUTS:
            errors.append(f"{label} has no source-node mapping")
        scope = slide.get("scope_check") or {}
        branch_node_id = str(scope.get("branch_node_id", "")).strip()
        if layout in KNOWLEDGE_LAYOUTS:
            if not isinstance(scope, dict) or scope.get("status") != "within-branch" or not branch_node_id:
                errors.append(f"{label} must record scope_check.status within-branch and a branch_node_id")
            elif branch_node_id not in source_ids:
                errors.append(f"{label} scope_check.branch_node_id is not an original source node")
            else:
                for node_id in [str(value) for value in node_ids if str(value) in source_ids]:
                    if branch_node_id != node_id and branch_node_id not in ancestor_ids_by_id.get(node_id, []):
                        errors.append(
                            f"{label} flattens source hierarchy: branch {branch_node_id} is not an ancestor "
                            f"of mapped node {node_id}"
                        )

        treatment_ids: list[str] = []
        treatments = slide.get("source_node_treatments")
        if not node_ids and layout in UNMAPPED_ALLOWED_LAYOUTS:
            treatments = []
        elif not isinstance(treatments, list) or not treatments:
            errors.append(
                f"{label} must include source_node_treatments proving every mapped source node "
                "is present in learner-facing copy"
            )
        else:
            normalized_slide_text = normalized_match_text(text)
            node_id_values = [str(node_id) for node_id in node_ids]
            evidence_seen: dict[str, str] = {}
            previous_evidence_position = -1
            for treatment_index, item in enumerate(treatments, start=1):
                prefix = f"{label} source_node_treatments[{treatment_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                treatment_node_id = str(item.get("source_node_id", "")).strip()
                treatment_ids.append(treatment_node_id)
                if treatment_node_id not in node_id_values:
                    errors.append(f"{prefix} maps {treatment_node_id or 'empty'} outside source_node_ids")
                coverage_status = str(item.get("coverage_status", "")).strip()
                if coverage_status not in SOURCE_COVERAGE_STATUSES:
                    errors.append(
                        f"{prefix} coverage_status must be one of "
                        + ", ".join(sorted(SOURCE_COVERAGE_STATUSES))
                    )
                if layout == "section-cover" and coverage_status != "section-heading":
                    errors.append(f"{prefix} section-cover coverage_status must be section-heading")
                evidence = str(item.get("screen_evidence", "")).strip()
                normalized_evidence = normalized_match_text(evidence)
                if not normalized_evidence:
                    errors.append(f"{prefix} must include a concrete screen_evidence phrase")
                elif normalized_evidence not in normalized_slide_text:
                    errors.append(
                        f"{prefix} screen_evidence is not found in visible title, explanation, bullets, caption, or blocks"
                    )
                else:
                    previous_node_id = evidence_seen.get(normalized_evidence)
                    if previous_node_id and source_text_by_id.get(previous_node_id) != source_text_by_id.get(treatment_node_id):
                        errors.append(
                            f"{prefix} repeats screen_evidence already used for source node {previous_node_id}; "
                            "distinct source nodes need distinct learner-facing evidence"
                        )
                    evidence_seen[normalized_evidence] = treatment_node_id
                    evidence_position = normalized_slide_text.find(normalized_evidence)
                    if evidence_position < previous_evidence_position:
                        errors.append(
                            f"{prefix} screen_evidence appears out of source order in visible slide text: {evidence}"
                        )
                    previous_evidence_position = max(previous_evidence_position, evidence_position)
            if treatment_ids != [str(node_id) for node_id in node_ids]:
                errors.append(f"{label} source_node_treatments must match source_node_ids exactly and in order")

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
    duplicates = sorted({node_id for node_id in mapped if mapped.count(node_id) > 1})
    if duplicates:
        errors.append(f"source coverage maps nodes more than once: {', '.join(duplicates[:12])}")
    mapped_orders = [source_order[node_id] for node_id in mapped if node_id in source_order]
    if mapped_orders != sorted(mapped_orders):
        errors.append("source-node mappings are not monotonic across slides")

    pptx_slides = None
    if args.pptx:
        pptx_slides, pptx_slide_texts, text = pptx_text(args.pptx)
        if pptx_slides != len(slides):
            errors.append(f"PPTX page count {pptx_slides} does not match deck-spec {len(slides)}")
        lower = text.lower()
        for term in FORBIDDEN:
            if term.lower() in lower:
                errors.append(f"PPTX contains forbidden visible text: {term}")
        for index, slide in enumerate(slides, start=1):
            if index > len(pptx_slide_texts):
                continue
            normalized_pptx_slide_text = normalized_match_text(pptx_slide_texts[index - 1])
            treatments = slide.get("source_node_treatments")
            if not isinstance(treatments, list):
                continue
            for treatment_index, item in enumerate(treatments, start=1):
                if not isinstance(item, dict):
                    continue
                evidence = str(item.get("screen_evidence", "")).strip()
                if not normalized_match_text(evidence):
                    continue
                if normalized_match_text(evidence) not in normalized_pptx_slide_text:
                    errors.append(
                        f"slide {index} source_node_treatments[{treatment_index}] "
                        "screen_evidence is not found in the built PPTX slide text: "
                        f"{evidence}"
                    )

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
