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
    "lorem ipsum", "TODO", "[TODO", "{{", "}}", "turn0", "ref_id",
]
IMAGE_LAYOUTS = {
    "image-left", "image-right",
    "image-left-dark", "image-right-dark",
    "image-left-orange", "image-right-orange",
    "image-left-accent", "image-right-accent",
}
KNOWLEDGE_LAYOUTS = {"roadmap", "light", "dark", "orange", "accent", *IMAGE_LAYOUTS, "comparison", "table", "summary"}
ALLOWED_LAYOUTS = {"cover", *KNOWLEDGE_LAYOUTS}
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
VISUAL_APPLICABILITY = {"required", "exception"}
IMAGEGEN_PRIORITY = {"preferred", "not-needed", "unavailable"}
TEMPLATE_MOTIF_KINDS = {"hero-right", "visual-anchor", "accent-motif", "background-motif", "frame-motif", "side-panel"}
TEMPLATE_NATIVE_ELEMENT_TYPES = {
    "vector",
    "shape",
    "line",
    "frame",
    "group",
    "background-shape",
    "native-vector",
    "native-shape",
    "native-group",
    "image-frame",
}
TEMPLATE_MOTIF_REPLACEMENT_MODES = {"copy_template_element", "replace_placeholder"}
VECTOR_COPY_ELEMENT_TYPES = {
    "vector",
    "shape",
    "line",
    "group",
    "background-shape",
    "native-vector",
    "native-shape",
    "native-group",
}
ALLOWED_SOURCE_GRANULARITY = {
    "single-case",
    "explicit-comparison",
    "multi-case-sequence",
    "source-authored-composite",
    "redrawn-single",
}
MULTI_SOURCE_GRANULARITY = {"explicit-comparison", "multi-case-sequence"}
SOURCE_NODE_DENSITY_LIMITS = {
    "detailed": 8,
    "sparse": 10,
}
SOURCE_COVERAGE_STATUSES = {
    "preserved",
    "clarified",
    "visualized",
    "restructured",
    "section-heading",
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


def pptx_text(path: Path) -> tuple[int, str]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        names.sort(key=lambda name: int(re.search(r"(\d+)", Path(name).stem).group(1)))
        texts: list[str] = []
        for name in names:
            xml = archive.read(name).decode("utf-8", errors="replace")
            texts.extend(html.unescape(value) for value in re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.S))
        return len(names), "\n".join(texts)


def layout_theme(layout: str) -> str:
    if layout in {"dark", "summary"} or layout.endswith("-dark"):
        return "dark"
    if layout in {"orange", "accent", "roadmap"} or layout.endswith("-orange") or layout.endswith("-accent"):
        return "orange"
    return "light"


def layout_family(layout: str) -> str:
    if layout.startswith("image-left") or layout.startswith("image-right"):
        return f"image-{layout_theme(layout)}"
    return layout


def template_reference_key(slide: dict[str, Any]) -> str:
    visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}
    reference = visual_plan.get("template_reference") if isinstance(visual_plan.get("template_reference"), dict) else {}
    value = reference.get("family") or reference.get("page") or reference.get("pages")
    if isinstance(value, list):
        value = ",".join(str(item) for item in value)
    return str(value or "").strip()


def composition_variant_key(slide: dict[str, Any]) -> str:
    visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}
    value = visual_plan.get("layout_variant") or visual_plan.get("composition_variant")
    if not value:
        reference = visual_plan.get("template_reference") if isinstance(visual_plan.get("template_reference"), dict) else {}
        value = reference.get("composition_family") or reference.get("layout_variant")
    return str(value or "").strip()


def structured_visual_content(screen: dict[str, Any], visual_plan: dict[str, Any], visuals: list[Any]) -> bool:
    if visuals:
        return True
    bullets = screen.get("bullets") or []
    if isinstance(bullets, list) and any(str(item).strip() for item in bullets):
        return True
    blocks = screen.get("blocks") or []
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if str(block.get("heading", "")).strip():
                return True
            items = block.get("items") or []
            if isinstance(items, list) and any(str(item).strip() for item in items):
                return True
    for key in ("diagram_elements", "table_rows", "shape_plan"):
        value = visual_plan.get(key)
        if isinstance(value, list) and value:
            return True
        if isinstance(value, dict) and value:
            return True
    return False


def max_run(values: list[str]) -> tuple[str, int]:
    best_value = ""
    best_count = 0
    current_value = ""
    current_count = 0
    for value in values:
        if value == current_value:
            current_count += 1
        else:
            current_value = value
            current_count = 1
        if current_count > best_count:
            best_value = current_value
            best_count = current_count
    return best_value, best_count


def numeric_box(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    required = ["left", "top", "width", "height"]
    if any(not isinstance(value.get(key), (int, float)) for key in required):
        return None
    return {key: float(value[key]) for key in required}


def boxes_overlap(first: dict[str, float], second: dict[str, float]) -> bool:
    return (
        first["left"] < second["left"] + second["width"]
        and first["left"] + first["width"] > second["left"]
        and first["top"] < second["top"] + second["height"]
        and first["top"] + first["height"] > second["top"]
    )


def template_motif_key(template_motif: dict[str, Any]) -> str:
    ref = template_motif.get("native_element_ref") if isinstance(template_motif.get("native_element_ref"), dict) else {}
    return ":".join(
        str(ref.get(key, "")).strip()
        for key in ("source_design_id", "source_page", "source_element_id")
        if str(ref.get(key, "")).strip()
    )


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
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("deck-spec slides must be non-empty")
        slides = []
    expected_numbers = list(range(1, len(slides) + 1))
    actual_numbers = [slide.get("number") for slide in slides]
    if actual_numbers != expected_numbers:
        errors.append("slide numbers must be contiguous and match list order")
    normal_knowledge = [
        slide for slide in slides
        if slide.get("layout") not in {"cover", "summary"} and (slide.get("layout", "light") in KNOWLEDGE_LAYOUTS)
    ]
    source_density_limit = SOURCE_NODE_DENSITY_LIMITS.get(str(mode))
    if source_density_limit and len(source_nodes) > 1:
        minimum_normal_slides = max(1, (len(source_nodes) - 2) // source_density_limit + 1)
        if len(normal_knowledge) < minimum_normal_slides:
            errors.append(
                f"{mode} mode is over-compressed: {len(source_nodes)} included source nodes "
                f"across {len(normal_knowledge)} normal knowledge slides; expected at least "
                f"{minimum_normal_slides} normal knowledge slides at the QA density limit "
                f"of {source_density_limit} source nodes per slide"
            )
    if len(normal_knowledge) > 12:
        template_page_mapping = course.get("template_page_mapping")
        if not isinstance(template_page_mapping, list) or len(template_page_mapping) != len(slides):
            errors.append(
                "course.template_page_mapping must list every slide before local PPT generation "
                "for decks longer than 12 pages"
            )
        else:
            mapped_slide_numbers = [item.get("slide_number") for item in template_page_mapping if isinstance(item, dict)]
            if mapped_slide_numbers != actual_numbers:
                errors.append("course.template_page_mapping slide_number values must match deck slide order")
            for item in template_page_mapping:
                if not isinstance(item, dict):
                    errors.append("course.template_page_mapping entries must be objects")
                    continue
                if not str(item.get("template_reference", "")).strip():
                    errors.append("course.template_page_mapping entries must include template_reference")
                if not str(item.get("layout_family", "")).strip():
                    errors.append("course.template_page_mapping entries must include layout_family")
                if len(str(item.get("local_ppt_decision", "")).strip()) < 20:
                    errors.append("course.template_page_mapping entries must include a concrete local_ppt_decision")
        template_native_element_inventory = course.get("template_native_element_inventory")
        inventory_keys: set[str] = set()
        if not isinstance(template_native_element_inventory, list) or not template_native_element_inventory:
            errors.append(
                "course.template_native_element_inventory must list reusable existing native elements "
                "from the selected Canva template before local PPT generation"
            )
        else:
            for item in template_native_element_inventory:
                if not isinstance(item, dict):
                    errors.append("course.template_native_element_inventory entries must be objects")
                    continue
                source_design_id = str(item.get("source_design_id", "")).strip()
                source_page = str(item.get("source_page", "")).strip()
                source_element_id = str(item.get("source_element_id", "")).strip()
                source_element_type = str(item.get("source_element_type", "")).strip()
                if not source_design_id or not source_page or not source_element_id:
                    errors.append("course.template_native_element_inventory entries must include source_design_id, source_page, and source_element_id")
                if source_element_type not in TEMPLATE_NATIVE_ELEMENT_TYPES:
                    errors.append("course.template_native_element_inventory source_element_type must describe a native vector/shape/group/frame element")
                if len(str(item.get("visual_role", "")).strip()) < 8:
                    errors.append("course.template_native_element_inventory entries must describe visual_role")
                inventory_keys.add(":".join([source_design_id, source_page, source_element_id]))
        families = [layout_family(str(slide.get("layout", "light"))) for slide in normal_knowledge]
        themes = [layout_theme(str(slide.get("layout", "light"))) for slide in normal_knowledge]
        family_counts = {family: families.count(family) for family in set(families)}
        dominant_family, dominant_count = max(family_counts.items(), key=lambda item: item[1])
        dominant_ratio = dominant_count / len(normal_knowledge)
        if dominant_ratio > 0.60:
            errors.append(
                f"layout rhythm is too repetitive: {dominant_family} covers "
                f"{dominant_count}/{len(normal_knowledge)} normal knowledge slides"
            )
        if len(set(themes)) < 3:
            errors.append("layout rhythm must use at least three background color modes across long decks")
        run_family, run_family_count = max_run(families)
        if run_family_count > 4:
            errors.append(f"layout rhythm has {run_family_count} consecutive {run_family} pages")
        run_theme, run_theme_count = max_run(themes)
        if run_theme_count > 4:
            errors.append(f"layout rhythm has {run_theme_count} consecutive {run_theme} background pages")
        plain_light_image_count = sum(1 for slide in normal_knowledge if slide.get("layout") in {"image-left", "image-right"})
        if plain_light_image_count / len(normal_knowledge) > 0.50:
            errors.append(
                "layout rhythm is dominated by plain light image-left/image-right pages; "
                "use dark and accent template-field image variants"
            )
        template_refs = [template_reference_key(slide) for slide in normal_knowledge]
        nonempty_refs = [ref for ref in template_refs if ref]
        distinct_refs = set(nonempty_refs)
        min_distinct_refs = min(6, max(3, len(normal_knowledge) // 4))
        if len(distinct_refs) < min_distinct_refs:
            errors.append(
                f"template reference variety is too low: uses {len(distinct_refs)} "
                f"reference pages/families across {len(normal_knowledge)} normal knowledge slides; "
                f"expected at least {min_distinct_refs}"
            )
        if nonempty_refs:
            ref_counts = {ref: nonempty_refs.count(ref) for ref in distinct_refs}
            dominant_ref, dominant_ref_count = max(ref_counts.items(), key=lambda item: item[1])
            if dominant_ref_count / len(normal_knowledge) > 0.40:
                errors.append(
                    f"template reference variety is too repetitive: {dominant_ref} covers "
                    f"{dominant_ref_count}/{len(normal_knowledge)} normal knowledge slides"
                )
            run_ref, run_ref_count = max_run(nonempty_refs)
            if run_ref_count > 3:
                errors.append(f"template reference variety has {run_ref_count} consecutive pages based on {run_ref}")
        variants = [composition_variant_key(slide) for slide in normal_knowledge]
        missing_variants = [
            str(slide.get("number"))
            for slide, variant in zip(normal_knowledge, variants)
            if not variant
        ]
        if missing_variants:
            errors.append(
                "long decks must record visual_plan.layout_variant for every normal knowledge slide; "
                f"missing slides: {', '.join(missing_variants[:12])}"
            )
        else:
            distinct_variants = set(variants)
            min_distinct_variants = min(7, max(4, len(normal_knowledge) // 4))
            if len(distinct_variants) < min_distinct_variants:
                errors.append(
                    f"composition variety is too low: uses {len(distinct_variants)} "
                    f"layout variants across {len(normal_knowledge)} normal knowledge slides; "
                    f"expected at least {min_distinct_variants}"
                )
            variant_counts = {variant: variants.count(variant) for variant in distinct_variants}
            dominant_variant, dominant_variant_count = max(variant_counts.items(), key=lambda item: item[1])
            if dominant_variant_count / len(normal_knowledge) > 0.35:
                errors.append(
                    f"composition variety is too repetitive: {dominant_variant} covers "
                    f"{dominant_variant_count}/{len(normal_knowledge)} normal knowledge slides"
                )
            run_variant, run_variant_count = max_run(variants)
            if run_variant_count > 2:
                errors.append(f"composition variety has {run_variant_count} consecutive pages using {run_variant}")
        template_motif_count = sum(
            1 for slide in slides
            if isinstance((slide.get("visual_plan") or {}).get("template_motif"), dict)
        )
        required_motifs = max(4, len(normal_knowledge) // 5)
        if template_motif_count < required_motifs:
            errors.append(
                f"long decks must plan Canva-native template motif use before local PPT generation; "
                f"found {template_motif_count}, expected at least {required_motifs}"
            )
        if template_motif_count >= 4:
            motif_keys = [
                template_motif_key((slide.get("visual_plan") or {}).get("template_motif") or {})
                for slide in slides
                if isinstance((slide.get("visual_plan") or {}).get("template_motif"), dict)
            ]
            nonempty_motif_keys = [key for key in motif_keys if key]
            if "inventory_keys" in locals() and inventory_keys:
                for key in nonempty_motif_keys:
                    if key not in inventory_keys:
                        errors.append(f"Canva-native template motif {key} is not listed in course.template_native_element_inventory")
            distinct_motif_keys = set(nonempty_motif_keys)
            if len(distinct_motif_keys) < 2:
                errors.append(
                    "Canva-native template motif use is too repetitive: long decks must reuse at least "
                    "two distinct existing template elements instead of placing the same element everywhere"
                )
            if nonempty_motif_keys:
                motif_key_counts = {key: nonempty_motif_keys.count(key) for key in distinct_motif_keys}
                dominant_motif_key, dominant_motif_count = max(motif_key_counts.items(), key=lambda item: item[1])
                if dominant_motif_count / len(nonempty_motif_keys) > 0.60:
                    errors.append(
                        f"Canva-native template motif use is too repetitive: template element "
                        f"{dominant_motif_key} appears on {dominant_motif_count}/{len(nonempty_motif_keys)} motif slides"
                    )
                run_motif_key, run_motif_count = max_run(nonempty_motif_keys)
                if run_motif_count > 2:
                    errors.append(
                        f"Canva-native template motif use has {run_motif_count} consecutive motif placements "
                        f"from the same template element {run_motif_key}"
                    )
        source_image_rich_threshold = max(6, (len(normal_knowledge) + 2) // 3)
        if len(source_images) >= source_image_rich_threshold:
            review = course.get("image_generation_review")
            source_image_coverage = course.get("source_image_coverage")
            generated_slides = [
                slide for slide in slides
                if (slide.get("visual_plan") or {}).get("asset_type") == "generated-image"
            ]
            source_case_slides = [
                slide for slide in slides
                if (slide.get("visual_plan") or {}).get("asset_type") in {"source-image", "redrawn-source-image"}
            ]
            required_generated = max(1, len(normal_knowledge) // 10)
            required_source_reuse = max(2, min(len(source_images), required_generated + 1))
            if not isinstance(review, dict) or review.get("status") != "completed":
                errors.append("source-rich long decks must complete course.image_generation_review before local PPT generation")
            elif review.get("source_case_priority") != "source-first":
                errors.append("course.image_generation_review must record source_case_priority as source-first")
            elif not isinstance(review.get("reused_source_slide_numbers"), list) or len(review.get("reused_source_slide_numbers")) < required_source_reuse:
                errors.append("course.image_generation_review must list enough reused_source_slide_numbers before generated additions")
            elif review.get("generated_after_source_review") is not True:
                errors.append("course.image_generation_review must confirm generated_after_source_review")
            elif not isinstance(review.get("generated_slide_numbers"), list) or not review.get("generated_slide_numbers"):
                errors.append("course.image_generation_review must list generated_slide_numbers for source-rich long decks")
            elif int(review.get("candidates_considered") or 0) < required_generated:
                errors.append("course.image_generation_review must consider candidate pages for generated teaching cases")
            if len(source_case_slides) < required_source_reuse:
                errors.append(
                    f"source-rich long decks must reuse source case images before generated additions; "
                    f"found {len(source_case_slides)}, expected at least {required_source_reuse}"
                )
            if len(generated_slides) < required_generated:
                errors.append(
                    f"source-rich long decks must include generated teaching case images; "
                    f"found {len(generated_slides)}, expected at least {required_generated}"
                )
            if not isinstance(source_image_coverage, list):
                errors.append("source-rich decks must include course.source_image_coverage for every non-thumbnail source image")
            else:
                coverage_by_id: dict[str, dict[str, Any]] = {}
                for item in source_image_coverage:
                    if not isinstance(item, dict):
                        errors.append("course.source_image_coverage entries must be objects")
                        continue
                    image_id = item.get("source_image_id")
                    if image_id in coverage_by_id:
                        errors.append(f"course.source_image_coverage repeats source image {image_id}")
                    if image_id:
                        coverage_by_id[str(image_id)] = item
                    if image_id not in source_image_ids:
                        errors.append(f"course.source_image_coverage references unknown source image {image_id}")
                    status = item.get("status")
                    if status not in {"used", "omitted"}:
                        errors.append(f"source image {image_id} coverage status must be used or omitted")
                    if status == "used":
                        slide_numbers = item.get("slide_numbers")
                        if not isinstance(slide_numbers, list) or not slide_numbers:
                            errors.append(f"source image {image_id} marked used but has no slide_numbers")
                        elif not all(number in actual_numbers for number in slide_numbers):
                            errors.append(f"source image {image_id} maps to an unknown slide number")
                        if not str(item.get("treatment", "")).strip():
                            errors.append(f"source image {image_id} marked used but has no treatment")
                    if status == "omitted" and len(str(item.get("reason", "")).strip()) < 12:
                        errors.append(f"source image {image_id} omitted without a concrete reason")
                missing_coverage = sorted(str(image_id) for image_id in source_image_ids if image_id not in coverage_by_id)
                if missing_coverage:
                    errors.append(
                        "course.source_image_coverage is missing source images: "
                        + ", ".join(missing_coverage[:12])
                    )
        else:
            review = course.get("image_generation_review")
            source_image_coverage = course.get("source_image_coverage")
            generated_slides = [
                slide for slide in slides
                if (slide.get("visual_plan") or {}).get("asset_type") == "generated-image"
            ]
            required_generated = max(4, (len(normal_knowledge) * 2 + 4) // 5)
            generation_unavailable = (
                isinstance(review, dict)
                and str(review.get("generation_route_status", "")).strip() == "unavailable"
            )
            if not isinstance(review, dict) or review.get("status") != "completed":
                errors.append("image-poor long decks must complete course.image_generation_review before local PPT generation")
            else:
                if int(review.get("source_case_image_count") or 0) != len(source_images):
                    errors.append(
                        "image-poor decks must record source_case_image_count as the usable "
                        f"non-thumbnail source image count ({len(source_images)})"
                    )
                if int(review.get("candidates_considered") or 0) < required_generated:
                    errors.append(
                        "image-poor decks must consider enough generated teaching-image candidates; "
                        f"expected at least {required_generated}"
                    )
                if not isinstance(review.get("generated_slide_numbers"), list):
                    errors.append("image-poor decks must list generated_slide_numbers or an unavailable fallback")
                elif not generation_unavailable and len(review.get("generated_slide_numbers")) < required_generated:
                    errors.append(
                        f"image-poor long decks should use generated teaching images substantially; "
                        f"found {len(review.get('generated_slide_numbers'))}, expected at least {required_generated}"
                    )
                if generation_unavailable:
                    fallbacks = review.get("fallback_slide_numbers")
                    if not isinstance(fallbacks, list) or len(fallbacks) < required_generated:
                        errors.append(
                            "when generation is unavailable, image-poor decks must list enough "
                            "fallback_slide_numbers using editable diagrams"
                        )
            if not generation_unavailable and len(generated_slides) < required_generated:
                errors.append(
                    f"image-poor long decks should render generated teaching-image slides; "
                    f"found {len(generated_slides)}, expected at least {required_generated}"
                )
            if source_images:
                if not isinstance(source_image_coverage, list):
                    errors.append("image-poor decks with source images must include course.source_image_coverage")
                else:
                    coverage_ids = {
                        item.get("source_image_id")
                        for item in source_image_coverage
                        if isinstance(item, dict)
                    }
                    missing_coverage = sorted(str(image_id) for image_id in source_image_ids if image_id not in coverage_ids)
                    if missing_coverage:
                        errors.append(
                            "course.source_image_coverage is missing image-poor source images: "
                            + ", ".join(missing_coverage[:12])
                        )
        design_review = course.get("page_design_review")
        required_design_dimensions = {"title-scale", "alignment", "proximity", "contrast", "image-caption", "contact-sheet"}
        if not isinstance(design_review, dict) or design_review.get("status") != "completed":
            errors.append("long decks must complete course.page_design_review before Canva import")
        else:
            checked = {str(item) for item in design_review.get("checked_dimensions", [])}
            missing_dimensions = sorted(required_design_dimensions - checked)
            if missing_dimensions:
                errors.append(
                    "course.page_design_review missing checked_dimensions: "
                    + ", ".join(missing_dimensions)
                )
            if design_review.get("contact_sheet_reviewed") is not True:
                errors.append("course.page_design_review must confirm contact_sheet_reviewed")
            if len(str(design_review.get("reference_method", "")).strip()) < 20:
                errors.append("course.page_design_review must record the reference design method")
            if not isinstance(design_review.get("issues_fixed"), list) or not design_review.get("issues_fixed"):
                errors.append("course.page_design_review must list design issues fixed before Canva import")

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
        if layout != "cover" and (not title or title.endswith(("?", "？"))):
            errors.append(f"{label} must use a conclusion-style title")
        slide_visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}
        template_reference = slide_visual_plan.get("template_reference") or {}
        if not isinstance(template_reference, dict):
            errors.append(f"{label} visual_plan.template_reference must describe the template layout source")
        else:
            reference_page = template_reference.get("page") or template_reference.get("pages")
            if not reference_page:
                errors.append(f"{label} visual_plan.template_reference must name the reference template page or page family")
            features = template_reference.get("layout_features")
            if not isinstance(features, list) or len([feature for feature in features if str(feature).strip()]) < 2:
                errors.append(f"{label} visual_plan.template_reference must list at least two inherited layout features")
            if len(str(template_reference.get("adaptation", "")).strip()) < 20:
                errors.append(f"{label} visual_plan.template_reference must explain how the template layout is adapted to this slide")
        if len(normal_knowledge) > 12 and slide in normal_knowledge and not composition_variant_key(slide):
            errors.append(f"{label} visual_plan.layout_variant must name the actual rendered composition family")
        template_motif = slide_visual_plan.get("template_motif")
        if isinstance(template_motif, dict):
            if template_motif.get("kind") not in TEMPLATE_MOTIF_KINDS:
                errors.append(f"{label} template_motif.kind is unsupported")
            if not template_motif.get("local_preview_path"):
                errors.append(f"{label} template_motif must provide local_preview_path for local PPT layout review")
            native_ref = template_motif.get("native_element_ref")
            if not isinstance(native_ref, dict):
                errors.append(f"{label} template_motif must provide native_element_ref for an existing element in the chosen Canva template")
                native_ref = {}
            source_design_id = str(native_ref.get("source_design_id", "")).strip()
            course_template_id = str(course.get("template_design_id", "")).strip()
            if not source_design_id:
                errors.append(f"{label} template_motif.native_element_ref.source_design_id is required")
            elif course_template_id and source_design_id != course_template_id:
                errors.append(
                    f"{label} template_motif must reuse an element from the chosen template {course_template_id}, "
                    f"not {source_design_id}"
                )
            if not isinstance(native_ref.get("source_page"), (int, float, str)) or not str(native_ref.get("source_page", "")).strip():
                errors.append(f"{label} template_motif.native_element_ref.source_page is required")
            if not str(native_ref.get("source_element_id", "")).strip():
                errors.append(f"{label} template_motif.native_element_ref.source_element_id is required")
            source_element_type = str(native_ref.get("source_element_type", "")).strip()
            if source_element_type not in TEMPLATE_NATIVE_ELEMENT_TYPES:
                errors.append(
                    f"{label} template_motif.native_element_ref.source_element_type must be a reusable native "
                    "template vector/shape/group/frame element"
                )
            if native_ref.get("copied_from_existing_template") is not True:
                errors.append(f"{label} template_motif.native_element_ref must confirm copied_from_existing_template: true")
            canva_asset_id = str(template_motif.get("canva_asset_id", "")).strip()
            if canva_asset_id and (
                canva_asset_id.lower().startswith("pending")
                or "inserted after import" in canva_asset_id.lower()
                or "canva native asset id" in canva_asset_id.lower()
            ):
                errors.append(f"{label} template_motif.canva_asset_id is still a placeholder, not a verified Canva native asset")
            replacement = template_motif.get("canva_replacement") or {}
            replacement_mode = replacement.get("mode") if isinstance(replacement, dict) else ""
            if not isinstance(replacement, dict) or replacement_mode not in TEMPLATE_MOTIF_REPLACEMENT_MODES:
                errors.append(f"{label} template_motif must use canva_replacement.mode copy_template_element or replace_placeholder")
            if source_element_type in VECTOR_COPY_ELEMENT_TYPES and replacement_mode != "copy_template_element":
                errors.append(
                    f"{label} template_motif reuses a native vector/shape/group element and must copy the existing "
                    "template element instead of replacing a proxy with a generic media asset"
                )
            if isinstance(replacement, dict) and len(str(replacement.get("match_strategy", "")).strip()) < 20:
                errors.append(f"{label} template_motif must record how the local preview proxy is matched after Canva import")
            if isinstance(replacement, dict) and replacement_mode == "copy_template_element" and len(str(replacement.get("source_copy_strategy", "")).strip()) < 20:
                errors.append(f"{label} template_motif must record canva_replacement.source_copy_strategy for copying the existing template element")
            if not isinstance(template_motif.get("replaces_modules"), list) or not template_motif.get("replaces_modules"):
                errors.append(f"{label} template_motif must list the structural modules it replaces")
            if len(str(template_motif.get("placement_basis", "")).strip()) < 20:
                errors.append(f"{label} template_motif must record a concrete placement basis")
            local_layout = template_motif.get("local_ppt_layout") or {}
            motif_box = local_layout.get("motif_box") if isinstance(local_layout, dict) else {}
            if not isinstance(local_layout, dict) or not isinstance(motif_box, dict):
                errors.append(f"{label} template_motif must record local_ppt_layout.motif_box before Canva import")
            else:
                required_numbers = ["left", "top", "width", "height"]
                missing = [key for key in required_numbers if not isinstance(motif_box.get(key), (int, float))]
                if missing:
                    errors.append(f"{label} template_motif local_ppt_layout.motif_box missing numeric {', '.join(missing)}")
                motif_box_numeric = numeric_box(motif_box)
                if motif_box_numeric:
                    allow_bleed = local_layout.get("allow_bleed") is True
                    if not allow_bleed and (
                        motif_box_numeric["left"] < 0
                        or motif_box_numeric["top"] < 0
                        or motif_box_numeric["left"] + motif_box_numeric["width"] > 1280
                        or motif_box_numeric["top"] + motif_box_numeric["height"] > 720
                    ):
                        errors.append(f"{label} template_motif motif_box must stay inside the 1280x720 canvas unless allow_bleed is true")
                if isinstance(local_layout.get("text_column_width"), (int, float)) and local_layout.get("text_column_width") > 720:
                    errors.append(f"{label} template_motif text column is too wide to reserve a clear motif area")
                elif not isinstance(local_layout.get("text_column_width"), (int, float)):
                    errors.append(f"{label} template_motif must record local_ppt_layout.text_column_width")
                if template_motif.get("kind") == "hero-right" and not missing:
                    center_x = motif_box["left"] + motif_box["width"] / 2
                    center_y = motif_box["top"] + motif_box["height"] / 2
                    if not (880 <= center_x <= 1100 and 260 <= center_y <= 460):
                        errors.append(f"{label} hero-right template_motif must be centered in the right visual field in local PPT coordinates")
                    if not (450 <= motif_box["width"] <= 720 and 450 <= motif_box["height"] <= 720):
                        errors.append(f"{label} hero-right template_motif must use a substantial but controlled right-side scale")
                protected_zones = local_layout.get("protected_zones")
                if not isinstance(protected_zones, list) or not protected_zones:
                    errors.append(f"{label} template_motif must record local_ppt_layout.protected_zones for title/body/footer/page-number collision checks")
                else:
                    motif_box_numeric = numeric_box(motif_box)
                    for zone in protected_zones:
                        if not isinstance(zone, dict):
                            errors.append(f"{label} template_motif protected_zones entries must be objects")
                            continue
                        zone_name = str(zone.get("name", "")).strip() or "unnamed"
                        zone_box = numeric_box(zone)
                        if not zone_box:
                            errors.append(f"{label} template_motif protected zone {zone_name} must include numeric left/top/width/height")
                            continue
                        if motif_box_numeric and boxes_overlap(motif_box_numeric, zone_box):
                            errors.append(f"{label} template_motif overlaps protected zone {zone_name}")
            collision = template_motif.get("collision_check") or {}
            if collision.get("status") != "clear" or len(str(collision.get("notes", "")).strip()) < 12:
                errors.append(f"{label} template_motif must record a clear collision check")
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
            if layout in IMAGE_LAYOUTS | {"comparison"} and not screen.get("caption"):
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
                if (
                    asset_type in {"editable-diagram", "editable-table"}
                    and layout in {"comparison", "table", "roadmap"}
                    and not structured_visual_content(screen, visual_plan, visuals)
                ):
                    errors.append(
                        f"{label} editable visual must be backed by visible blocks, visual elements, or diagram/table metadata"
                    )
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
                    case_granularity = str(visual_plan.get("case_granularity", "")).strip()
                    if case_granularity not in ALLOWED_SOURCE_GRANULARITY:
                        errors.append(f"{label} source-image visual must record a valid case_granularity")
                    if len(visual_source_image_ids) > 3:
                        errors.append(
                            f"{label} combines {len(visual_source_image_ids)} independent source images; "
                            "source-image slides may use at most 3 readable source images"
                        )
                    elif len(visual_source_image_ids) > 1:
                        if asset_type == "source-image" and len(visuals) < len(visual_source_image_ids):
                            errors.append(f"{label} multiple source images must have one visible visual entry per source image")
                        if case_granularity not in MULTI_SOURCE_GRANULARITY:
                            errors.append(f"{label} uses multiple source images but is not marked explicit-comparison or multi-case-sequence")
                        if len(str(visual_plan.get("case_grouping_reason", "")).strip()) < 20:
                            errors.append(f"{label} multiple source images require case_grouping_reason")
                        image_area_ratio = visual_plan.get("image_area_ratio")
                        if not isinstance(image_area_ratio, (int, float)):
                            errors.append(f"{label} multiple source images require visual_plan.image_area_ratio")
                        elif not 0.45 <= float(image_area_ratio) <= 0.72:
                            errors.append(f"{label} multiple source images must reserve 45%-72% slide area for images")
                        min_source_image_area_ratio = visual_plan.get("min_source_image_area_ratio")
                        if not isinstance(min_source_image_area_ratio, (int, float)):
                            errors.append(f"{label} multiple source images require visual_plan.min_source_image_area_ratio")
                        elif float(min_source_image_area_ratio) < 0.12:
                            errors.append(f"{label} smallest source image is too small to be readable")
                        if isinstance(text_area_ratio, (int, float)) and float(text_area_ratio) > 0.38:
                            errors.append(f"{label} text area is too large for a readable multi-source-image slide")
                if asset_type == "generated-image":
                    route = str(visual_plan.get("generation_route", "")).strip()
                    prompt_brief = str(visual_plan.get("prompt_brief", "")).strip()
                    if route not in GENERATED_IMAGE_ROUTES:
                        errors.append(f"{label} generated image must record a supported generation route")
                    if route != "gpt-image-2" and imagegen_priority != "unavailable":
                        errors.append(f"{label} generated image should use gpt-image-2 unless it is unavailable")
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
        if (
            source_density_limit
            and layout in KNOWLEDGE_LAYOUTS
            and layout != "summary"
            and len(node_ids) > source_density_limit
        ):
            errors.append(
                f"{label} over-compresses source coverage: maps {len(node_ids)} source nodes "
                f"in {mode} mode; split this branch into more learner pages instead of hiding "
                "source coverage in metadata"
            )
        treatment_ids: list[str] = []
        treatments = slide.get("source_node_treatments")
        if not isinstance(treatments, list) or not treatments:
            errors.append(
                f"{label} must include source_node_treatments proving every mapped source node "
                "is present in learner-facing copy"
            )
        else:
            normalized_slide_text = normalized_match_text(text)
            node_id_values = [str(node_id) for node_id in node_ids]
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
                evidence = str(item.get("screen_evidence", "")).strip()
                if len(normalized_match_text(evidence)) < 4:
                    errors.append(f"{prefix} must include a concrete screen_evidence phrase")
                elif normalized_match_text(evidence) not in normalized_slide_text:
                    errors.append(
                        f"{prefix} screen_evidence is not found in visible title, explanation, bullets, caption, or blocks"
                    )
                if len(str(item.get("coverage_note", "")).strip()) < 12:
                    errors.append(f"{prefix} must explain how the original node was preserved or clarified")
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
    duplicates = sorted({node_id for node_id in mapped if mapped.count(node_id) > 1})
    if duplicates:
        errors.append(f"source coverage maps nodes more than once: {', '.join(duplicates[:12])}")
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
            "source_density_limit": source_density_limit,
            "max_source_nodes_on_slide": max(
                (len(slide.get("source_node_ids") or []) for slide in slides),
                default=0,
            ),
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
