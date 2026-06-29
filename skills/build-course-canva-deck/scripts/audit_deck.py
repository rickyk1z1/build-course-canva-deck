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
import math
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
    "源图", "挂载",
    "先知道整节课", "整节课怎么展开", "再进入每一节",
    "构建课件", "课件思路", "制作思路", "构建思路",
    "讲稿整理", "根据讲稿", "这一段讲的是", "本段讲的是",
    "source path", "source_node", "screen_evidence", "coverage_note",
]
ALLOWED_MODES = {"detailed", "sparse"}
TEACHING_EXPANSION_MODE = {
    "detailed": "detailed-clarification",
    "sparse": "sparse-vertical-expansion",
}
STATIC_FOOTER_TEXT = "线上录课课件"
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
GENERATED_IMAGE_ROUTES = {"gpt-image-2"}
GENERATION_ATTEMPT_STATUSES = {"success", "failed", "unavailable"}
NO_SOURCE_GENERATION_MIN_SLIDES = 4
NO_SOURCE_NON_GENERATED_RUN_MAX = 2
NO_SOURCE_GENERATED_SLIDES_PER = 3
ELLIPSIS_RE = re.compile(r"…|\.{3}")
SECTION_CUE_MAX_CHARS = 34
SECTION_CUE_LIST_MARK_RE = re.compile(r"[·•；;]|[、，,](?=.)")
GENERIC_GENERATED_CASE_BYPASS_PATTERNS = [
    "可编辑图解比模型场景图更清楚",
    "可编辑结构图比表格更适配",
    "使用可编辑结构图比表格更适配当前信息量",
    "本页教学对象是结构、关系或清单判断",
    "本页是连续源节点整理",
    "本页是单个源节点的操作判断",
    "生成场景图更准确",
    "生成案例图更准确",
    "更适配当前信息量",
]
BYPASS_STRUCTURE_TERMS = {
    "流程", "步骤", "顺序", "路径", "关系", "层级", "矩阵", "表格",
    "参数", "快捷键", "操作", "轴", "分类", "对比", "清单", "标签",
}
NEGATIVE_SCOPE_VERBS = "不(?:进入|讲|涉及|展开|复讲|教学|教|做)"
NEGATIVE_SCOPE_OBJECTS = (
    "软件|按钮|剪映|快捷键|关键帧|蒙版|调色|发布|复盘|拍摄|参数|导入|导出|"
    "时间线|效率工作流|HSL|LUT|完播率|点击率|留存曲线|A/B测试|AI"
)
COMPOSITE_IMAGE_MARKERS = {
    "composite",
    "composites",
    "montage",
    "contact-sheet",
    "contact_sheet",
    "collage",
    "stitched",
}
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


def learner_text_quality_errors(label: str, slide: dict[str, Any], text: str) -> list[str]:
    errors: list[str] = []
    if ELLIPSIS_RE.search(text):
        errors.append(
            f"{label} contains visible ellipsis/truncated learner copy; split/rewrite the slide "
            "instead of rendering clipped text"
        )
    screen = slide.get("screen") or {}
    block_headings: dict[str, str] = {}
    for block_index, block in enumerate(screen.get("blocks") or [], start=1):
        if not isinstance(block, dict):
            continue
        heading = str(block.get("heading", "")).strip()
        normalized = normalized_match_text(heading)
        if not normalized or len(normalized) < 2:
            continue
        previous = block_headings.get(normalized)
        if previous:
            errors.append(
                f"{label} repeats the same visible block/card heading ({heading}); "
                "merge the repeated idea or give each card a distinct learner-facing role"
            )
            break
        block_headings[normalized] = heading
    bullet_seen: dict[str, str] = {}
    for bullet in screen.get("bullets") or []:
        value = str(bullet.get("text") if isinstance(bullet, dict) else bullet).strip()
        normalized = normalized_match_text(value)
        if not normalized or len(normalized) < 4:
            continue
        previous = bullet_seen.get(normalized)
        if previous:
            errors.append(
                f"{label} repeats the same visible bullet ({value}); remove duplicate screen copy"
            )
            break
        bullet_seen[normalized] = value
    return errors


def section_cue_errors(label: str, cue: str) -> list[str]:
    errors: list[str] = []
    if ELLIPSIS_RE.search(cue):
        errors.append(
            f"{label} section-cover cue contains ellipsis/truncation: {cue}; "
            "use a short agenda label or split the section"
        )
    compact = normalized_match_text(cue)
    if len(compact) > SECTION_CUE_MAX_CHARS:
        errors.append(
            f"{label} section-cover cue is too content-heavy for a chapter divider: {cue}; "
            "section covers need compact agenda labels, not full knowledge statements"
        )
    if len(SECTION_CUE_LIST_MARK_RE.findall(cue)) >= 2 or cue.count("/") >= 3:
        errors.append(
            f"{label} section-cover cue looks like a dense list: {cue}; "
            "move the list to normal knowledge pages"
        )
    return errors


def negative_scope_leaks(text: str) -> list[str]:
    compact = normalized_match_text(text)
    pattern = re.compile(f"{NEGATIVE_SCOPE_VERBS}.{{0,16}}(?:{NEGATIVE_SCOPE_OBJECTS})", re.I)
    return [match.group(0) for match in pattern.finditer(compact)]


def generation_attempt_status(attempts: list[Any], route: str) -> str:
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        if str(attempt.get("route", "")).strip() == route:
            return str(attempt.get("status", "")).strip()
    return ""


def generation_attempt_errors(
    label: str,
    visual_plan: dict[str, Any],
    task: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    route = str(visual_plan.get("generation_route", "")).strip()
    if route not in GENERATED_IMAGE_ROUTES:
        return [f"{label} generated image must use generation_route gpt-image-2 only"]

    if not task:
        errors.append(f"{label} generated image must have a matching course.image_generation_tasks entry")
        task = {}
    elif str(task.get("route", "")).strip() != route:
        errors.append(f"{label} image_generation_tasks route must match visual_plan.generation_route")

    attempts = visual_plan.get("generation_attempts")
    if not isinstance(attempts, list) or not attempts:
        attempts = task.get("generation_attempts")
    if not isinstance(attempts, list) or not attempts:
        errors.append(f"{label} generated image must record a successful gpt-image-2 generation_attempt")
        attempts = []
    for index, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, dict):
            errors.append(f"{label} generation_attempts[{index}] must be an object")
            continue
        attempt_route = str(attempt.get("route", "")).strip()
        status = str(attempt.get("status", "")).strip()
        evidence = str(attempt.get("evidence", "")).strip()
        if attempt_route != "gpt-image-2":
            errors.append(
                f"{label} generation_attempts[{index}] must use gpt-image-2 only, "
                f"not {attempt_route or '<empty>'}"
            )
        if status not in GENERATION_ATTEMPT_STATUSES:
            errors.append(f"{label} generation_attempts[{index}] has unsupported status {status or '<empty>'}")
        if not evidence:
            errors.append(f"{label} generation_attempts[{index}] must record tool result, error, or reason")

    gpt_status = generation_attempt_status(attempts if isinstance(attempts, list) else [], "gpt-image-2")
    if gpt_status != "success":
        errors.append(f"{label} gpt-image-2 route requires a successful gpt-image-2 attempt")
    return errors


def generated_case_bypass_errors(label: str, slide: dict[str, Any], bypass: str) -> list[str]:
    """Reject generic no-source bypass copy that does not prove generation was considered."""
    errors: list[str] = []
    reason = str(bypass or "").strip()
    if not reason:
        return [f"{label} must explain why a generated case image would teach worse"]
    compact_reason = normalized_match_text(reason)
    generic_matches = [
        phrase for phrase in GENERIC_GENERATED_CASE_BYPASS_PATTERNS
        if normalized_match_text(phrase) in compact_reason
    ]
    if generic_matches:
        errors.append(
            f"{label} uses a generic generated_case_bypass_reason ({generic_matches[0]}); "
            "write a page-specific reason tied to the current visual structure"
        )
    title = str(slide.get("title") or "").strip()
    visible_points = visible_teaching_points(slide)
    anchors = [title, *visible_points]
    anchor_found = False
    for anchor in anchors:
        normalized_anchor = normalized_match_text(anchor)
        if normalized_anchor and (
            normalized_anchor in compact_reason or compact_reason in normalized_anchor
        ):
            anchor_found = True
            break
    if not anchor_found:
        errors.append(
            f"{label} generated_case_bypass_reason must name the current title or a visible teaching point; "
            "do not use deck-level visual-policy language"
        )
    if not any(term in reason for term in BYPASS_STRUCTURE_TERMS):
        errors.append(
            f"{label} generated_case_bypass_reason must identify the concrete structure "
            "(flow, sequence, relationship, axis, table, parameter, shortcut, operation path, etc.) "
            "that is clearer than a generated case image"
        )
    return errors


def visible_teaching_points(slide: dict[str, Any]) -> list[str]:
    screen = slide.get("screen") or {}
    points: list[str] = []
    for item in screen.get("bullets") or []:
        value = str(item.get("text") if isinstance(item, dict) else item).strip()
        if value:
            points.append(value)
    for block in screen.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        heading = str(block.get("heading", "")).strip()
        if heading and not is_generic_block_label(heading):
            points.append(heading)
        for item in block.get("items") or []:
            value = str(item.get("text") if isinstance(item, dict) else item).strip()
            if value:
                points.append(value)
    return points


def teaching_expansion_errors(label: str, screen: dict[str, Any], text: str, mode: str) -> list[str]:
    errors: list[str] = []
    expansion = screen.get("teaching_expansion")
    if not isinstance(expansion, dict):
        return [f"{label} lacks screen.teaching_expansion"]
    expected = TEACHING_EXPANSION_MODE.get(mode, "")
    actual = str(expansion.get("mode_handling", "")).strip()
    if expected and actual != expected:
        errors.append(f"{label} screen.teaching_expansion.mode_handling must be {expected}")
    for key in ("learner_takeaway", "source_based_explanation"):
        if not str(expansion.get(key, "")).strip():
            errors.append(f"{label} screen.teaching_expansion.{key} is required")
    display_priority = [
        str(value).strip()
        for value in expansion.get("display_priority", [])
        if str(value).strip()
    ] if isinstance(expansion.get("display_priority"), list) else []
    if not display_priority:
        errors.append(f"{label} screen.teaching_expansion.display_priority must list learner-facing phrases")
    else:
        normalized_text = normalized_match_text(text)
        if not any(normalized_match_text(phrase) in normalized_text for phrase in display_priority):
            errors.append(f"{label} does not render any screen.teaching_expansion.display_priority phrase")
    internal_only = expansion.get("internal_only", [])
    if isinstance(internal_only, list):
        normalized_text = normalized_match_text(text)
        for value in internal_only:
            phrase = normalized_match_text(value)
            if phrase and phrase in normalized_text:
                errors.append(f"{label} renders internal-only teaching/planning text: {value}")
    return errors


def normalized_match_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def reusable_content_phrases(slide: dict[str, Any]) -> list[tuple[str, str]]:
    phrases: list[tuple[str, str]] = []
    candidates = [str(slide.get("title") or "").strip()]
    candidates.extend(visible_teaching_points(slide))
    for item in slide.get("source_node_treatments") or []:
        if isinstance(item, dict):
            candidates.append(str(item.get("screen_evidence") or "").strip())
    seen: set[str] = set()
    for phrase in candidates:
        normalized = normalized_match_text(phrase)
        if not normalized or len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        phrases.append((normalized, phrase))
    return phrases


def section_cover_reuses_content(cover_normalized: str, normal_normalized: str) -> bool:
    if not cover_normalized or not normal_normalized:
        return False
    if normal_normalized in cover_normalized and cover_normalized != normal_normalized:
        return True
    return cover_normalized == normal_normalized and len(cover_normalized) >= 6


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


def layout_geometry_signature(slide: dict[str, Any]) -> tuple:
    """A coarse structural fingerprint of a content slide.

    This is intentionally not an aesthetic judgement. It only captures the
    handful of structural choices that, when repeated across many adjacent
    pages, mean the contact sheet will look the same: the layout family,
    whether the page carries a real image, the bullet count, and the block
    count. It exists to raise a warning so the director knows where to look,
    never to approve or fail a deck on a number.
    """
    screen = slide.get("screen") or {}
    visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}
    asset_type = str(visual_plan.get("asset_type", "")).strip()
    has_image = asset_type in IMAGE_ASSET_TYPES and bool(slide.get("visuals"))
    bullet_count = len([b for b in (screen.get("bullets") or []) if str(b).strip()])
    block_count = len([b for b in (screen.get("blocks") or []) if isinstance(b, dict)])
    return (
        str(slide.get("layout", "")),
        has_image,
        bullet_count,
        block_count,
    )


def ancestors_for(node_id: str, parent_by_id: dict[str, str | None]) -> list[str]:
    ancestors: list[str] = []
    current = parent_by_id.get(node_id)
    seen: set[str] = set()
    while current and current not in seen:
        ancestors.append(current)
        seen.add(current)
        current = parent_by_id.get(current)
    return ancestors


def section_for(node_id: str, section_ids: list[str], parent_by_id: dict[str, str | None]) -> str | None:
    section_set = set(section_ids)
    if node_id in section_set:
        return node_id
    current = node_id
    seen: set[str] = set()
    while current and current not in seen:
        if current in section_set:
            return current
        parent = parent_by_id.get(current)
        seen.add(current)
        current = parent or ""
    return None


def chapter_spine_ids(course: dict[str, Any], source_nodes: list[dict[str, Any]], root_id: str | None) -> tuple[list[str], bool]:
    raw = course.get("chapter_spine")
    if isinstance(raw, list) and raw:
        ids: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                value = item.get("source_node_id") or item.get("id")
            else:
                value = item
            if str(value or "").strip():
                ids.append(str(value).strip())
        return ids, True
    return [
        str(node.get("id"))
        for node in sorted(source_nodes, key=lambda item: item.get("order", 0))
        if root_id and str(node.get("parent_id") or "") == root_id
    ], False


def framework_progress_expected(
    layout: str,
    node_ids: list[str],
    section_ids: list[str],
    parent_by_id: dict[str, str | None],
    source_text_by_id: dict[str, str],
) -> str | None:
    if layout == "section-cover" and len(node_ids) == 1 and node_ids[0] in section_ids:
        return source_text_by_id.get(node_ids[0])
    mapped_section_ids = {
        section_for(node_id, section_ids, parent_by_id)
        for node_id in node_ids
        if node_id in source_text_by_id
    }
    mapped_section_ids = {section_id for section_id in mapped_section_ids if section_id}
    if len(mapped_section_ids) == 1:
        return source_text_by_id.get(next(iter(mapped_section_ids)))
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
    if mode not in ALLOWED_MODES or not source.get("mode_declared_by_user"):
        errors.append("outline mode was not explicitly declared by the user")
    if source.get("source_kind") == "script":
        errors.append("source_kind=script is not a valid authoritative source route; use the outline/XMind source map and keep lecture scripts as optional screen-copy reference")
    course = deck.get("course") or {}
    if course.get("outline_mode") != mode:
        errors.append("deck-spec mode does not match source-map mode")
    reference_script = course.get("reference_script")
    if reference_script is not None:
        if not isinstance(reference_script, dict):
            errors.append("course.reference_script must be an object when provided")
        else:
            if reference_script.get("authoritative") is not False:
                errors.append("course.reference_script.authoritative must be false")
            if str(reference_script.get("usage", "")).strip() != "screen-copy-reference-only":
                errors.append("course.reference_script.usage must be screen-copy-reference-only")
            if not str(reference_script.get("path") or reference_script.get("source") or "").strip():
                errors.append("course.reference_script must record the reference script path/source")
    curriculum = course.get("curriculum_context") or {}
    if not curriculum.get("system_name"):
        errors.append("curriculum_context.system_name is required")
    if not curriculum.get("module"):
        errors.append("curriculum_context.module is required")
    if not curriculum.get("course_role"):
        errors.append("curriculum_context.course_role is required")
    image_generation_tasks = course.get("image_generation_tasks") or []
    if not isinstance(image_generation_tasks, list):
        errors.append("course.image_generation_tasks must be a list when provided")
        image_generation_tasks = []
    image_generation_task_by_slide: dict[int, dict[str, Any]] = {}
    for task in image_generation_tasks:
        if not isinstance(task, dict):
            continue
        try:
            slide_number = int(task.get("slide"))
        except (TypeError, ValueError):
            continue
        image_generation_task_by_slide.setdefault(slide_number, task)

    source_nodes = [node for node in source.get("nodes", []) if node.get("include", True)]
    source_images = [
        image for image in source.get("images", [])
        if isinstance(image, dict) and "thumbnail" not in str(image.get("path", "")).lower()
    ]
    source_image_ids = {image.get("id") for image in source_images if image.get("id")}
    source_image_by_id = {
        str(image.get("id")): image
        for image in source_images
        if str(image.get("id") or "").strip()
    }
    used_source_image_ids: list[str] = []
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
    children_by_parent: dict[str, list[str]] = {}
    for node in sorted(source_nodes, key=lambda item: item.get("order", 0)):
        parent_id = str(node.get("parent_id") or "")
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(str(node.get("id")))
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
    top_section_ids, explicit_chapter_spine = chapter_spine_ids(course, source_nodes, root_id)
    if explicit_chapter_spine and not top_section_ids:
        errors.append("course.chapter_spine must contain at least one source_node_id")
    unknown_chapter_ids = [node_id for node_id in top_section_ids if node_id not in source_ids]
    if unknown_chapter_ids:
        errors.append(
            "course.chapter_spine contains unknown source nodes: "
            + ", ".join(unknown_chapter_ids[:12])
        )
    duplicate_chapter_ids = sorted({node_id for node_id in top_section_ids if top_section_ids.count(node_id) > 1})
    if duplicate_chapter_ids:
        errors.append(
            "course.chapter_spine repeats source nodes: "
            + ", ".join(duplicate_chapter_ids[:12])
        )
    chapter_orders = [source_order[node_id] for node_id in top_section_ids if node_id in source_order]
    if chapter_orders != sorted(chapter_orders):
        errors.append("course.chapter_spine must follow source order")
    for section_id in top_section_ids:
        for other_id in top_section_ids:
            if section_id == other_id:
                continue
            if section_id in ancestor_ids_by_id.get(other_id, []):
                errors.append(
                    f"course.chapter_spine contains overlapping chapters: {section_id} is an ancestor of {other_id}"
                )

    for image in source_images:
        image_id = str(image.get("id") or "").strip()
        anchor_id = str(image.get("source_node_id") or "").strip()
        if not image_id:
            errors.append("non-thumbnail source image is missing id")
            continue
        if not anchor_id:
            errors.append(
                f"non-thumbnail source image {image_id} is missing source_node_id; "
                "extract_source.py must preserve the XMind image topic anchor"
            )
        elif anchor_id not in source_ids:
            errors.append(
                f"non-thumbnail source image {image_id} has unknown source_node_id {anchor_id}"
            )

    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("deck-spec slides must be non-empty")
        slides = []
    expected_numbers = list(range(1, len(slides) + 1))
    actual_numbers = [slide.get("number") for slide in slides]
    if actual_numbers != expected_numbers:
        errors.append("slide numbers must be contiguous and match list order")

    normal_phrases_by_section: dict[str, list[tuple[int, str, str]]] = {}
    for phrase_slide_index, phrase_slide in enumerate(slides, start=1):
        if phrase_slide.get("layout") not in KNOWLEDGE_LAYOUTS:
            continue
        phrase_node_ids = [str(value) for value in (phrase_slide.get("source_node_ids") or [])]
        phrase_sections = {
            section_for(node_id, top_section_ids, parent_by_id)
            for node_id in phrase_node_ids
            if node_id in source_ids
        }
        phrase_sections = {section_id for section_id in phrase_sections if section_id}
        if len(phrase_sections) != 1:
            continue
        phrase_section_id = next(iter(phrase_sections))
        for normalized, raw in reusable_content_phrases(phrase_slide):
            normal_phrases_by_section.setdefault(phrase_section_id, []).append(
                (phrase_slide_index, normalized, raw)
            )

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
                    errors.append(f"slide {index} section-cover must map exactly one approved chapter node")
                    continue
                section_id = node_ids[0]
                expected_section = top_section_ids[len(seen_sections)] if len(seen_sections) < len(top_section_ids) else None
                if section_id in seen_section_set:
                    errors.append(f"slide {index} repeats section-cover for approved chapter node {section_id}")
                elif expected_section and section_id != expected_section:
                    errors.append(
                        f"slide {index} section-cover breaks approved chapter order: "
                        f"expected {expected_section}, got {section_id}"
                    )
                seen_sections.append(section_id)
                seen_section_set.add(section_id)
                direct_child_ids = children_by_parent.get(section_id, [])
                if direct_child_ids:
                    preview_items = slide.get("section_preview_items")
                    if not isinstance(preview_items, list) or not preview_items:
                        errors.append(
                            f"slide {index} section-cover must preview this section's immediate child source headings"
                        )
                    else:
                        normalized_slide_text = normalized_match_text(visible_text(slide))
                        preview_evidence: list[str] = []
                        preview_node_ids: list[str] = []
                        previous_preview_order = -1
                        for preview_index, item in enumerate(preview_items, start=1):
                            prefix = f"slide {index} section_preview_items[{preview_index}]"
                            if not isinstance(item, dict):
                                errors.append(f"{prefix} must be an object")
                                continue
                            raw_ids = item.get("source_node_ids")
                            if raw_ids is None:
                                raw_ids = [item.get("source_node_id")]
                            if not isinstance(raw_ids, list) or not raw_ids:
                                errors.append(f"{prefix} must cite immediate child source_node_id(s)")
                                continue
                            item_ids = [str(value) for value in raw_ids if str(value or "").strip()]
                            if not item_ids:
                                errors.append(f"{prefix} must cite immediate child source_node_id(s)")
                                continue
                            for child_id in item_ids:
                                if child_id not in direct_child_ids:
                                    errors.append(
                                        f"{prefix} maps {child_id} outside the section's immediate child headings"
                                    )
                                    continue
                                child_order = source_order.get(child_id, 0)
                                if child_order < previous_preview_order:
                                    errors.append(f"{prefix} breaks source order for section preview headings")
                                previous_preview_order = max(previous_preview_order, child_order)
                                preview_node_ids.append(child_id)
                            evidence = str(item.get("screen_evidence", "")).strip()
                            normalized_evidence = normalized_match_text(evidence)
                            if not normalized_evidence:
                                errors.append(f"{prefix} must include visible screen_evidence")
                            elif normalized_evidence not in normalized_slide_text:
                                errors.append(f"{prefix} screen_evidence is not visible on the section-cover slide")
                            else:
                                preview_evidence.append(normalized_evidence)
                        section_bullets = [
                            str(value.get("text") if isinstance(value, dict) else value).strip()
                            for value in (slide.get("screen") or {}).get("bullets", [])
                            if str(value.get("text") if isinstance(value, dict) else value).strip()
                        ]
                        for cue_index, cue in enumerate(
                            [*section_bullets, *[str(item.get("screen_evidence", "")).strip() for item in preview_items if isinstance(item, dict)]],
                            start=1,
                        ):
                            errors.extend(section_cue_errors(f"slide {index} cue {cue_index}", cue))
                        for bullet in [normalized_match_text(value) for value in section_bullets]:
                            if not any(bullet in evidence or evidence in bullet for evidence in preview_evidence):
                                errors.append(
                                    f"slide {index} section-cover bullets must be approved chapter child preview items, not conclusions"
                                )
                                break
                        cover_phrases = [
                            (normalized_match_text(cue), cue)
                            for cue in section_bullets
                            if normalized_match_text(cue)
                        ]
                        cover_phrases.extend(
                            (evidence, str(item.get("screen_evidence", "")).strip())
                            for evidence, item in [
                                (normalized_match_text(str(entry.get("screen_evidence", "")).strip()), entry)
                                for entry in preview_items
                                if isinstance(entry, dict)
                            ]
                            if evidence
                        )
                        for cover_normalized, cover_raw in cover_phrases:
                            for normal_slide, normal_normalized, normal_raw in normal_phrases_by_section.get(section_id, []):
                                if normal_slide <= index:
                                    continue
                                if section_cover_reuses_content(cover_normalized, normal_normalized):
                                    errors.append(
                                        f"slide {index} section-cover repeats normal knowledge-page learner copy "
                                        f"from slide {normal_slide}: {normal_raw}; use compact agenda cues on "
                                        "section covers and keep teachable statements for normal pages"
                                    )
                                    break
                continue
            if layout in {"cover", "lesson-overview", "summary"}:
                continue
            slide_sections = {
                section_for(node_id, top_section_ids, parent_by_id)
                for node_id in node_ids
                if node_id in source_ids
            }
            for section_id in sorted(value for value in slide_sections if value):
                if section_id not in seen_section_set:
                    errors.append(
                        f"slide {index} shows content before section-cover for approved chapter node {section_id}"
                    )
        for section_id in top_section_ids:
            if section_id not in seen_section_set:
                errors.append(f"missing section-cover for approved chapter node {section_id}")

    mapped: list[str] = []
    mapped_for_order: list[str] = []
    previous_min_order = 0
    exclusions = [str(value) for value in course.get("explicit_exclusions", [])]
    exclusions.extend(str(value) for value in curriculum.get("excluded_neighbor_topics", []))
    no_source_knowledge_slide_count = 0
    generated_image_slide_count = 0
    no_source_non_generated_slides: list[int] = []
    no_source_visual_events: list[tuple[int, str | None, bool]] = []

    for index, slide in enumerate(slides, start=1):
        label = f"slide {index}"
        layout = slide.get("layout", "light")
        if layout not in ALLOWED_LAYOUTS:
            errors.append(f"{label} uses unsupported layout: {layout}")
        text = visible_text(slide)
        errors.extend(learner_text_quality_errors(label, slide, text))
        lower = text.lower()
        for term in FORBIDDEN:
            if term.lower() in lower:
                errors.append(f"{label} contains forbidden learner-facing text: {term}")
        for term in exclusions:
            if term and term.lower() in lower:
                errors.append(f"{label} contains an explicit out-of-scope term: {term}")
        leaks = negative_scope_leaks(text)
        for leak in leaks:
            errors.append(
                f"{label} contains learner-facing negative scope wording: {leak}; "
                "course boundaries belong in curriculum metadata, not screen copy"
            )

        title = str(slide.get("title", "")).strip()
        if layout != "cover" and not title:
            errors.append(f"{label} must have a learner-facing title")
        elif layout != "cover" and title.endswith(("?", "？")):
            warnings.append(f"{label} uses a question-style title; director should verify the answer is visible on the same page")

        slide_visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}
        node_ids = [str(value) for value in (slide.get("source_node_ids") or [])]
        raw_framework_progress_label = slide.get("framework_progress_label", "")
        framework_progress_label = "" if raw_framework_progress_label is None else str(raw_framework_progress_label).strip()
        if normalized_match_text(framework_progress_label) == normalized_match_text(STATIC_FOOTER_TEXT):
            errors.append(f"{label} framework_progress_label must not be the static courseware footer")
        expected_progress = framework_progress_expected(
            layout,
            node_ids,
            top_section_ids,
            parent_by_id,
            source_text_by_id,
        )
        if layout in KNOWLEDGE_LAYOUTS and not framework_progress_label:
            errors.append(f"{label} must set framework_progress_label for the left footer")
        if layout in KNOWLEDGE_LAYOUTS:
            slide_section_ids = {
                section_for(node_id, top_section_ids, parent_by_id)
                for node_id in node_ids
                if node_id in source_ids
            }
            slide_section_ids = {section_id for section_id in slide_section_ids if section_id}
            if len(slide_section_ids) > 1:
                spanned = ", ".join(
                    sorted(source_text_by_id.get(section_id, section_id) for section_id in slide_section_ids)
                )
                errors.append(
                    f"{label} mixes content from multiple approved chapters on one knowledge page: {spanned}"
                )
        if framework_progress_label and expected_progress and framework_progress_label != expected_progress:
            errors.append(
                f"{label} framework_progress_label must be current approved chapter: {expected_progress}"
            )

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
                errors.extend(teaching_expansion_errors(label, screen, text, str(mode or "")))
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
                    case_visual_map = visual_plan.get("case_visual_map")
                    if not isinstance(case_visual_map, list) or not case_visual_map:
                        errors.append(
                            f"{label} image visual_plan must map visible case details to the slide's teaching points"
                        )
                    else:
                        map_evidence: list[str] = []
                        for map_index, map_item in enumerate(case_visual_map, start=1):
                            prefix = f"{label} visual_plan.case_visual_map[{map_index}]"
                            if not isinstance(map_item, dict):
                                errors.append(f"{prefix} must be an object")
                                continue
                            evidence = str(map_item.get("screen_evidence", "")).strip()
                            detail = str(map_item.get("visible_detail", "")).strip()
                            if not evidence:
                                errors.append(f"{prefix} must cite a visible slide teaching point")
                            elif normalized_match_text(evidence) not in normalized_match_text(text):
                                errors.append(f"{prefix} screen_evidence is not visible on the slide")
                            else:
                                map_evidence.append(normalized_match_text(evidence))
                            if not detail:
                                errors.append(f"{prefix} must describe the image detail that makes the point visible")
                        for point in visible_teaching_points(slide):
                            normalized_point = normalized_match_text(point)
                            if not normalized_point:
                                continue
                            if not any(normalized_point in evidence or evidence in normalized_point for evidence in map_evidence):
                                errors.append(
                                    f"{label} case_visual_map does not cover visible teaching point: {point}"
                                )
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
                        for image_id in visual_source_image_ids:
                            image = source_image_by_id.get(str(image_id))
                            if not image:
                                continue
                            anchor_id = str(image.get("source_node_id") or "").strip()
                            if not anchor_id or anchor_id not in source_ids:
                                continue
                            mapped_node_ids = [
                                str(value)
                                for value in node_ids
                                if str(value) in source_ids
                            ]
                            anchor_matches_slide = False
                            for mapped_node_id in mapped_node_ids:
                                if (
                                    anchor_id == mapped_node_id
                                    or mapped_node_id in ancestor_ids_by_id.get(anchor_id, [])
                                    or anchor_id in ancestor_ids_by_id.get(mapped_node_id, [])
                                ):
                                    anchor_matches_slide = True
                                    break
                            if not anchor_matches_slide:
                                errors.append(
                                    f"{label} uses source image {image_id} anchored to source node "
                                    f"{anchor_id} ({source_text_by_id.get(anchor_id, anchor_id)}) outside "
                                    "the slide's mapped source branch; source-image placement must follow "
                                    "the image's XMind node anchor"
                                )
                    visual_paths = [
                        str(visual.get("path") or visual.get("src") or "").lower()
                        for visual in visuals
                        if isinstance(visual, dict)
                    ]
                    if len(visual_source_image_ids) > 1:
                        if len(visuals) < len(visual_source_image_ids):
                            errors.append(
                                f"{label} combines {len(visual_source_image_ids)} source images into "
                                f"{len(visuals)} rendered visual asset(s); render source images as separate "
                                "large panels or split the page"
                            )
                        composite_paths = [
                            path for path in visual_paths
                            if any(marker in path for marker in COMPOSITE_IMAGE_MARKERS)
                        ]
                        if composite_paths:
                            errors.append(
                                f"{label} uses a composite/montage asset for multiple source images; "
                                "do not shrink source cases into a single stitched image"
                            )
                        visual_ids = [
                            str(visual.get("source_image_id") or "")
                            for visual in visuals
                            if isinstance(visual, dict) and str(visual.get("source_image_id") or "").strip()
                        ]
                        if len(visual_ids) != len(visual_source_image_ids):
                            errors.append(
                                f"{label} multi-source visuals must set one visuals[].source_image_id per rendered image"
                            )
                        elif sorted(visual_ids) != sorted(str(image_id) for image_id in visual_source_image_ids):
                            errors.append(
                                f"{label} visuals[].source_image_id must match visual_plan.source_image_ids"
                            )
                    if len(visual_source_image_ids) > 2 and not visual_plan.get("multi_image_readability_exception"):
                        errors.append(
                            f"{label} combines {len(visual_source_image_ids)} independent source images; "
                            "split the page unless a director readability exception proves each image remains large"
                        )
                    if layout in KNOWLEDGE_LAYOUTS and integration == "knowledge-page":
                        used_source_image_ids.extend(
                            str(image_id)
                            for image_id in visual_source_image_ids
                            if image_id in source_image_ids
                        )
                if asset_type == "generated-image":
                    generated_image_slide_count += 1
                    try:
                        slide_number = int(slide.get("number"))
                    except (TypeError, ValueError):
                        slide_number = -1
                    errors.extend(
                        generation_attempt_errors(
                            label,
                            visual_plan,
                            image_generation_task_by_slide.get(slide_number),
                        )
                    )
                if asset_type == "text-only-exception" and layout in IMAGE_LAYOUTS | {"comparison"}:
                    errors.append(f"{label} uses an image/comparison layout but declares a text-only visual exception")
                if asset_type == "text-only-exception":
                    bypass = str(
                        visual_plan.get("text_only_exception_reason")
                        or visual_plan.get("generated_case_bypass_reason")
                        or ""
                    ).strip()
                    if not bypass:
                        errors.append(
                            f"{label} text-only exception must explain why generated case image or diagram is not useful"
                        )
                if (
                    layout in KNOWLEDGE_LAYOUTS
                    and asset_type not in {"source-image", "redrawn-source-image"}
                    and not (isinstance(visual_plan.get("source_image_ids"), list) and visual_plan.get("source_image_ids"))
                ):
                    no_source_knowledge_slide_count += 1
                    slide_section_ids = {
                        section_for(node_id, top_section_ids, parent_by_id)
                        for node_id in node_ids
                        if node_id in source_ids
                    }
                    slide_section_ids = {section_id for section_id in slide_section_ids if section_id}
                    slide_section_key = next(iter(slide_section_ids)) if len(slide_section_ids) == 1 else None
                    no_source_visual_events.append((index, slide_section_key, asset_type == "generated-image"))
                    if asset_type != "generated-image":
                        no_source_non_generated_slides.append(index)
                        bypass = str(
                            visual_plan.get("text_only_exception_reason")
                            or visual_plan.get("generated_case_bypass_reason")
                            or visual_plan.get("no_generated_case_reason")
                            or ""
                        ).strip()
                        errors.extend(generated_case_bypass_errors(label, slide, bypass))

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
                if layout not in {"cover", "lesson-overview", "summary"}:
                    mapped_for_order.append(node_id)
        orders = sorted(source_order[node_id] for node_id in node_ids if node_id in source_order)
        if orders and layout not in {"cover", "lesson-overview", "summary"}:
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

    if source_image_ids:
        used_source_image_set = set(used_source_image_ids)
        missing_source_images = sorted(source_image_ids - used_source_image_set)
        if missing_source_images:
            errors.append(
                "non-thumbnail source images must be used or redrawn on knowledge pages; missing "
                f"{len(missing_source_images)} source image(s): "
                + ", ".join(missing_source_images[:20])
            )

        image_coverage = course.get("source_image_coverage")
        if not isinstance(image_coverage, list) or not image_coverage:
            errors.append("course.source_image_coverage must account for every non-thumbnail source image")
        else:
            coverage_by_id: dict[str, list[dict[str, Any]]] = {}
            for item in image_coverage:
                if not isinstance(item, dict):
                    errors.append("course.source_image_coverage entries must be objects")
                    continue
                image_id = str(item.get("source_image_id", "")).strip()
                if not image_id:
                    errors.append("course.source_image_coverage entry is missing source_image_id")
                    continue
                coverage_by_id.setdefault(image_id, []).append(item)
            coverage_missing = sorted(source_image_ids - set(coverage_by_id))
            if coverage_missing:
                errors.append(
                    "course.source_image_coverage is missing non-thumbnail source images: "
                    + ", ".join(coverage_missing[:20])
                )
            unknown_coverage = sorted(set(coverage_by_id) - source_image_ids)
            allowed_non_case_statuses = {"thumbnail_omitted", "system_omitted"}
            unexpected_coverage = [
                image_id for image_id in unknown_coverage
                if all(
                    str(item.get("status", "")).strip() not in allowed_non_case_statuses
                    for item in coverage_by_id[image_id]
                )
            ]
            if unexpected_coverage:
                errors.append(
                    "course.source_image_coverage contains unknown non-thumbnail source images: "
                    + ", ".join(unexpected_coverage[:20])
                )
            for image_id in sorted(source_image_ids):
                entries = coverage_by_id.get(image_id, [])
                accepted = False
                for item in entries:
                    status = str(item.get("status", "")).strip()
                    if status not in {"used", "redrawn"}:
                        errors.append(
                            f"course.source_image_coverage for {image_id} must be status used or redrawn; "
                            "non-thumbnail source images are presumed teaching case images"
                        )
                    if status in {"used", "redrawn"}:
                        accepted = True
                if accepted and image_id not in used_source_image_set:
                    errors.append(
                        f"course.source_image_coverage marks {image_id} as used/redrawn, "
                        "but no knowledge-page visual_plan.source_image_ids references it"
                    )

    if (
        no_source_knowledge_slide_count >= NO_SOURCE_GENERATION_MIN_SLIDES
        and generated_image_slide_count == 0
    ):
        errors.append(
            f"deck has {no_source_knowledge_slide_count} normal knowledge slides without source images "
            "but no generated-image slides/image_generation_tasks; run the generated case-image decision "
            "flow instead of bypassing every no-source page. Non-generated no-source slides include: "
            + ", ".join(str(value) for value in no_source_non_generated_slides[:20])
        )
    if no_source_knowledge_slide_count >= NO_SOURCE_GENERATION_MIN_SLIDES:
        required_generated = math.ceil(no_source_knowledge_slide_count / NO_SOURCE_GENERATED_SLIDES_PER)
        if generated_image_slide_count < required_generated:
            errors.append(
                f"deck has {no_source_knowledge_slide_count} normal knowledge slides without source images "
                f"but only {generated_image_slide_count} generated-image slide(s); need at least "
                f"{required_generated} generated case-image page(s) or split/reclassify no-source pages with "
                "specific per-page visual reasons"
            )

    run: list[int] = []
    run_section: str | None = None

    def flush_no_source_run() -> None:
        if len(run) > NO_SOURCE_NON_GENERATED_RUN_MAX:
            errors.append(
                f"slides {run[0]}-{run[-1]} are a consecutive no-source non-generated run "
                f"({len(run)} pages); after {NO_SOURCE_NON_GENERATED_RUN_MAX} such pages, create a "
                "generated case-image page or use a source/redrawn case image instead of continuing "
                "text/diagram-only bypasses"
            )

    event_by_slide = {slide_number: (section_key, generated) for slide_number, section_key, generated in no_source_visual_events}
    for index, slide in enumerate(slides, start=1):
        event = event_by_slide.get(index)
        if slide.get("layout") not in KNOWLEDGE_LAYOUTS or event is None or event[1] is True:
            flush_no_source_run()
            run = []
            run_section = None
            continue
        section_key, _generated = event
        if run and section_key == run_section:
            run.append(index)
        else:
            flush_no_source_run()
            run = [index]
            run_section = section_key
    flush_no_source_run()

    missing = [node_id for node_id in source_ids if node_id not in mapped]
    if missing:
        errors.append(f"source coverage is incomplete; missing {len(missing)} nodes: {', '.join(sorted(missing)[:12])}")
    duplicates = sorted({node_id for node_id in mapped if mapped.count(node_id) > 1})
    if duplicates:
        errors.append(f"source coverage maps nodes more than once: {', '.join(duplicates[:12])}")
    mapped_orders = [source_order[node_id] for node_id in mapped_for_order if node_id in source_order]
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
        if ELLIPSIS_RE.search(text):
            errors.append(
                "PPTX contains visible ellipsis/truncated learner copy; split or rewrite slides before delivery"
            )
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

    # Geometry-repetition signal: this is a warning, not a hard gate. The audit
    # cannot judge layout aesthetics, but it can flag where the contact sheet is
    # likely to look the same so the director knows to inspect those pages. We
    # only look at knowledge pages inside one section; structural families
    # (cover/overview/section-cover/summary) are supposed to repeat.
    run_start_index = 0
    run_signature: tuple | None = None
    run_length = 0
    current_section: str | None = None

    def flush_geometry_run(end_index_exclusive: int) -> None:
        if run_signature is not None and run_length >= 3:
            warnings.append(
                f"slides {run_start_index}-{end_index_exclusive - 1} share the same content-page "
                f"geometry ({run_length} pages: layout/image/bullet/block signature {run_signature}); "
                "director should confirm on the contact sheet that this is not repeated layout"
            )

    for index, slide in enumerate(slides, start=1):
        layout = slide.get("layout", "light")
        if layout not in KNOWLEDGE_LAYOUTS:
            flush_geometry_run(index)
            run_signature = None
            run_length = 0
            current_section = None
            continue
        node_ids = [str(value) for value in (slide.get("source_node_ids") or [])]
        slide_sections = {
            section_for(node_id, top_section_ids, parent_by_id)
            for node_id in node_ids
            if node_id in source_ids
        }
        slide_sections = {section_id for section_id in slide_sections if section_id}
        section_key = next(iter(slide_sections)) if len(slide_sections) == 1 else None
        signature = layout_geometry_signature(slide)
        if signature == run_signature and section_key == current_section and section_key is not None:
            run_length += 1
        else:
            flush_geometry_run(index)
            run_signature = signature
            run_length = 1
            run_start_index = index
            current_section = section_key
    flush_geometry_run(len(slides) + 1)

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
