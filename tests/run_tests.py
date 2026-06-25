#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "build-course-canva-deck"
SCRIPTS = SKILL / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"


def run(command: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != expect:
        print("COMMAND:", " ".join(command))
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        raise AssertionError(f"expected exit {expect}, got {result.returncode}")
    return result


def audit(temp: Path, deck: Path, source: Path, *, expect: int = 0, canva_motif_report: Path | None = None) -> dict:
    report = temp / f"{deck.stem}-report.json"
    command = [
        sys.executable, str(SCRIPTS / "audit_deck.py"),
        "--deck-spec", str(deck),
        "--source-map", str(source),
        "--report", str(report),
    ]
    if canva_motif_report:
        command.extend(["--canva-motif-report", str(canva_motif_report)])
    run(
        command,
        expect=expect,
    )
    return json.loads(report.read_text(encoding="utf-8"))


PNG_FIXTURES = [
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC",
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGNk+M8AAwIBAUlQJ+IAAAAASUVORK5CYII=",
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGNgYPgPAAEDAQDqXc6EAAAAAElFTkSuQmCC",
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGNgoBMAAABpAAGlzzfEAAAAAElFTkSuQmCC",
]


def write_png_assets(asset_dir: Path, count: int = 4) -> list[str]:
    asset_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for index, raw in enumerate(PNG_FIXTURES[:count], start=1):
        path = asset_dir / f"case-{index}.png"
        path.write_bytes(base64.b64decode(raw))
        paths.append(str(path.relative_to(asset_dir.parent)))
    return paths


def pptx_media_count(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        return len([name for name in archive.namelist() if name.startswith("ppt/media/")])


def valid_template_motif(
    kind: str = "visual-anchor",
    *,
    source_page: int = 1,
    source_element_id: str = "template-star-small",
) -> dict:
    return {
        "kind": kind,
        "native_element_ref": {
            "source_design_id": "DAHM5fsVEB0",
            "source_page": source_page,
            "source_element_id": source_element_id,
            "source_element_type": "vector",
            "source_element_role": "template-native visual motif",
            "copied_from_existing_template": True,
        },
        "local_preview_path": "assets/template-motif-preview.png",
        "reference_template_page": 1,
        "placement_basis": "参考模板主视觉区域，在本地 PPT 阶段预留稳定位置并检查文字避让。",
        "replaces_modules": ["template-visual-anchor"],
        "local_ppt_layout": {
            "coordinate_space": "1280x720",
            "text_column_width": 560,
            "title_break_strategy": "wrap before PPT generation",
            "motif_box": {"left": 720, "top": 120, "width": 420, "height": 420},
            "native_canva_scale": 1.5,
            "protected_zones": [
                {"name": "title", "left": 72, "top": 58, "width": 600, "height": 128},
                {"name": "body", "left": 72, "top": 215, "width": 560, "height": 360},
                {"name": "footer", "left": 72, "top": 682, "width": 360, "height": 24},
                {"name": "page-number", "left": 1170, "top": 675, "width": 48, "height": 30},
            ],
        },
        "canva_replacement": {
            "mode": "copy_template_element",
            "match_strategy": "after Canva import, match the local preview proxy by page index and recorded motif_box before deleting it",
            "source_copy_strategy": "copy the recorded existing vector element from the chosen Canva template page and paste it into the imported deck at the recorded box",
            "fallback": "stop and request browser fallback or an accessible duplicate template; do not use a searched library asset",
        },
        "collision_check": {
            "status": "clear",
            "notes": "本地 PPT 预览中 motif 不覆盖标题、正文、页脚或页码。",
        },
    }


def write_source_rich_long_fixture(temp: Path) -> tuple[Path, Path]:
    source = {
        "schema_version": 1,
        "authoritative": True,
        "authoritative_source": "tests/fixtures/source-rich-outline.md",
        "source_type": "md",
        "source_sha256": "fixture",
        "outline_mode": "detailed",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": f"n{number:04d}", "order": number, "parent_id": None if number == 1 else "n0001", "depth": 0 if number == 1 else 1, "kind": "topic", "text": f"节点 {number}", "include": True}
            for number in range(1, 17)
        ],
        "images": [
            {"id": f"img{number:03d}", "path": f"assets/case-{number}.png", "sha256": f"img{number}"}
            for number in range(1, 9)
        ],
    }
    source_path = temp / "source-rich-long-source.json"
    source_path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")

    base = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
    course = base["course"]
    course["outline_mode"] = "detailed"
    course["template_page_mapping"] = [
        {
            "slide_number": number,
            "template_reference": f"page {((number - 1) % 8) + 1}",
            "layout_family": "cover" if number == 1 else "knowledge",
            "native_motif": "planned" if number in {1, 8, 10, 12} else "none",
            "local_ppt_decision": "按参考模板页先确定文字列宽、视觉区和 motif 位置，再生成本地 PPT。",
        }
        for number in range(1, 17)
    ]
    course["template_native_element_inventory"] = [
        {
            "source_design_id": "DAHM5fsVEB0",
            "source_page": 1,
            "source_element_id": "template-star-hero",
            "source_element_type": "vector",
            "visual_role": "cover hero star motif",
            "usable_layout_families": ["cover", "hero-cover"],
        },
        {
            "source_design_id": "DAHM5fsVEB0",
            "source_page": 3,
            "source_element_id": "template-anchor-8",
            "source_element_type": "vector",
            "visual_role": "small section anchor motif",
            "usable_layout_families": ["dark-spotlight", "center-anchor"],
        },
        {
            "source_design_id": "DAHM5fsVEB0",
            "source_page": 2,
            "source_element_id": "template-anchor-10",
            "source_element_type": "shape",
            "visual_role": "side rail accent shape",
            "usable_layout_families": ["image-right-dark", "poster-panel"],
        },
        {
            "source_design_id": "DAHM5fsVEB0",
            "source_page": 4,
            "source_element_id": "template-anchor-12",
            "source_element_type": "group",
            "visual_role": "native grouped corner motif",
            "usable_layout_families": ["comparison-strip", "two-panel"],
        },
    ]
    course["image_generation_review"] = {
        "status": "completed",
        "source_case_priority": "source-first",
        "source_case_image_count": 8,
        "reused_source_slide_numbers": [2, 3, 4],
        "generated_after_source_review": True,
        "generated_slide_numbers": [6],
        "candidates_considered": 3,
        "rationale": "源图充足但仍补一张文字较多页面的教学案例图。",
    }
    course["source_image_coverage"] = [
        {
            "source_image_id": f"img{number:03d}",
            "status": "used" if number in {2, 3, 4} else "omitted",
            "slide_numbers": [number] if number in {2, 3, 4} else [],
            "treatment": "single-case" if number in {2, 3, 4} else "omitted-duplicate",
            "reason": "fixture source case is shown as a readable single-case slide"
            if number in {2, 3, 4}
            else "fixture image intentionally omitted because this synthetic source-rich test only needs enough images to exercise coverage gates",
        }
        for number in range(1, 9)
    ]
    course["page_design_review"] = {
        "status": "completed",
        "reference_method": "对照选定 Canva 模板 contact sheet 和 page-design-quality.md 完成页面设计复核。",
        "checked_dimensions": ["title-scale", "alignment", "proximity", "contrast", "image-caption", "contact-sheet"],
        "contact_sheet_reviewed": True,
        "issues_fixed": ["converted generic bullets into information groups"],
        "residual_risk": "fixture only records the review gate, visual quality is checked in real deck renders",
    }

    cover = json.loads(json.dumps(base["slides"][0], ensure_ascii=False))
    cover["number"] = 1
    cover["source_node_ids"] = ["n0001"]
    cover["visual_plan"]["source_node_id"] = "n0001"
    cover["visual_plan"]["layout_variant"] = "hero-cover"
    cover["visual_plan"]["template_motif"] = valid_template_motif("hero-right", source_page=1, source_element_id="template-star-hero")
    cover["visual_plan"]["template_motif"]["local_ppt_layout"]["motif_box"] = {"left": 700, "top": 70, "width": 560, "height": 560}

    layouts = [
        "comparison", "image-left-dark", "roadmap", "image-right-orange",
        "table", "image-right", "comparison", "image-left-accent",
        "image-left-dark", "image-right-dark", "image-right-orange", "image-left",
        "comparison", "image-right-accent",
    ]
    variants = [
        "two-panel", "dark-spotlight", "index-grid", "poster-panel",
        "comparison-strip", "split-image", "close-reading", "wide-case-band",
        "gallery-strip", "center-anchor", "poster-panel", "split-image",
        "comparison-strip", "two-panel",
    ]
    slides = [cover]
    source_slide = base["slides"][1]
    for index, layout in enumerate(layouts, start=2):
        node_id = f"n{index:04d}"
        slide = json.loads(json.dumps(source_slide, ensure_ascii=False))
        slide["number"] = index
        slide["layout"] = layout
        slide["title"] = f"节点 {index} 的结论式标题"
        slide["source_node_ids"] = [node_id]
        slide["visual_plan"]["source_node_id"] = node_id
        slide["visual_plan"]["template_reference"] = {
            "page": ((index - 1) % 8) + 1,
            "layout_features": ["varied template page family", "stable visual/text relationship"],
            "adaptation": "根据参考模板页调整图文区域、标题宽度和信息块位置后再生成本地 PPT。",
        }
        slide["visual_plan"]["layout_variant"] = variants[index - 2]
        if index in {2, 3, 4}:
            slide["layout"] = "image-right" if index % 2 == 0 else "image-left-dark"
            slide["visuals"] = [{"path": f"assets/case-{index}.png", "alt": "源案例图"}]
            slide["visual_plan"]["asset_type"] = "source-image"
            slide["visual_plan"]["source_image_ids"] = [f"img{index:03d}"]
            slide["visual_plan"]["case_granularity"] = "single-case"
            slide["visual_plan"]["case_grouping_reason"] = ""
        if index == 6:
            slide["layout"] = "image-right"
            slide["visuals"] = [{"path": "assets/generated/case.png", "alt": "生成案例图"}]
            slide["visual_plan"]["asset_type"] = "generated-image"
            slide["visual_plan"]["source_image_ids"] = []
            slide["visual_plan"]["case_granularity"] = "not-source-image"
            slide["visual_plan"]["case_grouping_reason"] = ""
            slide["visual_plan"]["generation_route"] = "gpt-image-2"
            slide["visual_plan"]["imagegen_priority"] = "preferred"
            slide["visual_plan"]["prompt_brief"] = "具体课程场景的无文字教学案例图"
        if index in {8, 10, 12}:
            slide["visual_plan"]["template_motif"] = valid_template_motif(
                "visual-anchor",
                source_page=((index - 1) % 3) + 2,
                source_element_id=f"template-anchor-{index}",
            )
        slides.append(slide)

    summary = json.loads(json.dumps(base["slides"][-1], ensure_ascii=False))
    summary["number"] = 16
    summary["source_node_ids"] = ["n0016"]
    summary["visual_plan"]["source_node_id"] = "n0016"
    summary["visual_plan"]["layout_variant"] = "summary-blocks"
    slides.append(summary)
    base["slides"] = slides
    deck_path = temp / "source-rich-long-deck.json"
    deck_path.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    return deck_path, source_path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="course-canva-skill-") as raw:
        temp = Path(raw)

        # Source extraction preserves order and refuses to infer outline mode.
        source_map = temp / "source-map.json"
        run([sys.executable, str(SCRIPTS / "extract_source.py"), "--input", str(FIXTURES / "detailed-outline.md"), "--output", str(source_map)])
        extracted = json.loads(source_map.read_text(encoding="utf-8"))
        assert extracted["outline_mode"] is None
        assert extracted["requires_user_outline_mode"] is True
        by_text = {node["text"]: node for node in extracted["nodes"]}
        assert by_text["编码是整理和压缩视频数据的打包手法。"]["parent_id"] == by_text["编码"]["id"]
        assert by_text["格式是承装视频数据的文件箱子。"]["parent_id"] == by_text["格式"]["id"]
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(source_map), "--require-mode"], expect=1)
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(source_map), "--mode", "detailed", "--write", "--require-mode"])

        txt_outline = temp / "outline.txt"
        txt_outline.write_text("一、父节点\n  1. 子节点\n  2. 子节点二\n二、父节点二\n", encoding="utf-8")
        txt_map = temp / "txt-source-map.json"
        run([sys.executable, str(SCRIPTS / "extract_source.py"), "--input", str(txt_outline), "--output", str(txt_map)])
        txt_nodes = json.loads(txt_map.read_text(encoding="utf-8"))["nodes"]
        assert txt_nodes[1]["parent_id"] == txt_nodes[0]["id"]
        assert txt_nodes[2]["parent_id"] == txt_nodes[0]["id"]

        # Modern XMind parsing works and also leaves mode unset.
        xmind = temp / "fixture.xmind"
        with zipfile.ZipFile(xmind, "w") as archive:
            archive.writestr("content.json", json.dumps([{"rootTopic": {"title": "根节点", "children": {"attached": [{"title": "子节点"}]}}}], ensure_ascii=False))
        xmind_map = temp / "xmind-map.json"
        run([sys.executable, str(SCRIPTS / "extract_source.py"), "--input", str(xmind), "--output", str(xmind_map)])
        assert [node["text"] for node in json.loads(xmind_map.read_text(encoding="utf-8"))["nodes"]] == ["根节点", "子节点"]

        # Detailed baseline passes; added content does not.
        detailed = audit(temp, FIXTURES / "deck-spec-detailed.json", FIXTURES / "source-map-detailed.json")
        assert detailed["ok"]
        missing_curriculum_path = temp / "missing-curriculum.json"
        missing_curriculum = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        del missing_curriculum["course"]["curriculum_context"]
        missing_curriculum_path.write_text(json.dumps(missing_curriculum, ensure_ascii=False), encoding="utf-8")
        curriculum_report = audit(temp, missing_curriculum_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("curriculum_context" in error for error in curriculum_report["errors"])
        detailed_bad_path = temp / "detailed-added.json"
        detailed_bad = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        detailed_bad["slides"][1]["added_content"] = [{"text": "额外流程"}]
        detailed_bad_path.write_text(json.dumps(detailed_bad, ensure_ascii=False), encoding="utf-8")
        assert not audit(temp, detailed_bad_path, FIXTURES / "source-map-detailed.json", expect=1)["ok"]

        missing_visual_path = temp / "missing-visual-plan.json"
        missing_visual = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        del missing_visual["slides"][1]["visual_plan"]
        missing_visual_path.write_text(json.dumps(missing_visual, ensure_ascii=False), encoding="utf-8")
        missing_visual_report = audit(temp, missing_visual_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("visual_plan" in error for error in missing_visual_report["errors"])

        missing_motif_placement_path = temp / "missing-motif-placement.json"
        missing_motif_placement = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        missing_motif_placement["slides"][0]["visual_plan"]["template_motif"] = {
            "kind": "hero-right",
            "canva_asset_id": "MAEeKPWZP8I",
            "replaces_modules": ["cover-orange", "cover-focus"],
        }
        missing_motif_placement_path.write_text(json.dumps(missing_motif_placement, ensure_ascii=False), encoding="utf-8")
        motif_report = audit(temp, missing_motif_placement_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("template_motif" in error for error in motif_report["errors"])

        missing_motif_replacement_path = temp / "missing-motif-replacement.json"
        missing_motif_replacement = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        missing_motif_replacement["slides"][0]["visual_plan"]["template_motif"] = valid_template_motif(
            "hero-right",
            source_page=1,
            source_element_id="template-star-hero",
        )
        missing_motif_replacement["slides"][0]["visual_plan"]["template_motif"]["local_ppt_layout"]["motif_box"] = {"left": 680, "top": 60, "width": 600, "height": 600}
        del missing_motif_replacement["slides"][0]["visual_plan"]["template_motif"]["canva_replacement"]
        missing_motif_replacement_path.write_text(json.dumps(missing_motif_replacement, ensure_ascii=False), encoding="utf-8")
        motif_replacement_report = audit(temp, missing_motif_replacement_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("copy_template_element" in error for error in motif_replacement_report["errors"])

        non_template_motif_path = temp / "non-template-motif.json"
        non_template_motif = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        non_template_motif["slides"][0]["visual_plan"]["template_motif"] = valid_template_motif(
            "hero-right",
            source_page=1,
            source_element_id="template-star-hero",
        )
        non_template_motif["slides"][0]["visual_plan"]["template_motif"]["local_ppt_layout"]["motif_box"] = {"left": 680, "top": 60, "width": 600, "height": 600}
        non_template_motif["slides"][0]["visual_plan"]["template_motif"]["native_element_ref"]["source_design_id"] = "MAEeKPWZP8I"
        non_template_motif_path.write_text(json.dumps(non_template_motif, ensure_ascii=False), encoding="utf-8")
        non_template_motif_report = audit(temp, non_template_motif_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("chosen template" in error for error in non_template_motif_report["errors"])

        overlapping_motif_path = temp / "overlapping-motif.json"
        overlapping_motif = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        overlapping_motif["slides"][0]["visual_plan"]["template_motif"] = valid_template_motif(
            "visual-anchor",
            source_page=2,
            source_element_id="template-anchor-overlap",
        )
        overlapping_motif["slides"][0]["visual_plan"]["template_motif"]["local_ppt_layout"]["motif_box"] = {"left": 100, "top": 80, "width": 320, "height": 180}
        overlapping_motif_path.write_text(json.dumps(overlapping_motif, ensure_ascii=False), encoding="utf-8")
        overlapping_motif_report = audit(temp, overlapping_motif_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("overlaps protected zone" in error for error in overlapping_motif_report["errors"])

        canva_report_deck_path = temp / "canva-report-deck.json"
        canva_report_deck = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        canva_report_deck["slides"][0]["visual_plan"]["template_motif"] = valid_template_motif(
            "visual-anchor",
            source_page=1,
            source_element_id="template-star-small",
        )
        canva_report_deck_path.write_text(json.dumps(canva_report_deck, ensure_ascii=False), encoding="utf-8")
        bad_canva_report_path = temp / "bad-canva-native-motif-report.json"
        bad_canva_report_path.write_text(json.dumps([
            {
                "slide_number": 1,
                "source_design_id": "DAHM5fsVEB0",
                "source_page": 1,
                "source_element_id": "template-star-small",
                "final_status": "proxy_only",
            }
        ], ensure_ascii=False), encoding="utf-8")
        bad_canva_report = audit(
            temp,
            canva_report_deck_path,
            FIXTURES / "source-map-detailed.json",
            expect=1,
            canva_motif_report=bad_canva_report_path,
        )
        assert any("proxy_only" in error for error in bad_canva_report["errors"])
        good_canva_report_path = temp / "good-canva-native-motif-report.json"
        good_canva_report_path.write_text(json.dumps([
            {
                "slide_number": 1,
                "source_design_id": "DAHM5fsVEB0",
                "source_page": 1,
                "source_element_id": "template-star-small",
                "final_status": "verified",
            }
        ], ensure_ascii=False), encoding="utf-8")
        good_canva_report = audit(
            temp,
            canva_report_deck_path,
            FIXTURES / "source-map-detailed.json",
            canva_motif_report=good_canva_report_path,
        )
        assert good_canva_report["ok"]

        image_not_integrated_path = temp / "image-not-integrated.json"
        image_not_integrated = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        image_not_integrated["slides"][1]["layout"] = "light"
        image_not_integrated["slides"][1]["visual_plan"]["asset_type"] = "source-image"
        image_not_integrated["slides"][1]["visuals"] = []
        image_not_integrated_path.write_text(json.dumps(image_not_integrated, ensure_ascii=False), encoding="utf-8")
        image_report = audit(temp, image_not_integrated_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("image asset" in error or "image-integrated layout" in error for error in image_report["errors"])

        generated_missing_route_path = temp / "generated-missing-route.json"
        generated_missing_route = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        generated_missing_route["slides"][1]["layout"] = "image-right"
        generated_missing_route["slides"][1]["visuals"] = [{"path": "example.png", "alt": "案例图"}]
        generated_missing_route["slides"][1]["visual_plan"]["asset_type"] = "generated-image"
        generated_missing_route_path.write_text(json.dumps(generated_missing_route, ensure_ascii=False), encoding="utf-8")
        generated_route_report = audit(temp, generated_missing_route_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("generation route" in error or "prompt brief" in error for error in generated_route_report["errors"])

        generated_wrong_route_path = temp / "generated-wrong-route.json"
        generated_wrong_route = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        generated_wrong_route["slides"][1]["layout"] = "image-right"
        generated_wrong_route["slides"][1]["visuals"] = [{"path": "example.png", "alt": "案例图"}]
        generated_wrong_route["slides"][1]["visual_plan"]["asset_type"] = "generated-image"
        generated_wrong_route["slides"][1]["visual_plan"]["generation_route"] = "imagegen"
        generated_wrong_route["slides"][1]["visual_plan"]["imagegen_priority"] = "preferred"
        generated_wrong_route["slides"][1]["visual_plan"]["prompt_brief"] = "具体课程场景插图"
        generated_wrong_route_path.write_text(json.dumps(generated_wrong_route, ensure_ascii=False), encoding="utf-8")
        generated_wrong_route_report = audit(temp, generated_wrong_route_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("gpt-image-2" in error for error in generated_wrong_route_report["errors"])

        repetitive_layout_path = temp / "repetitive-layout.json"
        repetitive_layout = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        repeated = [repetitive_layout["slides"][0]]
        source_slide = repetitive_layout["slides"][1]
        for number in range(2, 16):
            clone = json.loads(json.dumps(source_slide, ensure_ascii=False))
            clone["number"] = number
            clone["layout"] = "image-right" if number % 2 == 0 else "image-left"
            repeated.append(clone)
        final_slide = json.loads(json.dumps(repetitive_layout["slides"][-1], ensure_ascii=False))
        final_slide["number"] = 16
        repeated.append(final_slide)
        repetitive_layout["slides"] = repeated
        repetitive_layout_path.write_text(json.dumps(repetitive_layout, ensure_ascii=False), encoding="utf-8")
        repetitive_layout_report = audit(temp, repetitive_layout_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("layout rhythm" in error for error in repetitive_layout_report["errors"])

        repetitive_template_reference_path = temp / "repetitive-template-reference.json"
        repetitive_template_reference = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        varied_layouts = [
            "image-right", "image-left-dark", "comparison", "image-right-orange",
            "light", "dark", "image-left-accent", "table", "orange", "image-right-dark",
            "comparison", "image-left", "dark", "image-right-accent",
        ]
        repeated = [repetitive_template_reference["slides"][0]]
        source_slide = repetitive_template_reference["slides"][1]
        for offset, layout in enumerate(varied_layouts, start=2):
            clone = json.loads(json.dumps(source_slide, ensure_ascii=False))
            clone["number"] = offset
            clone["layout"] = layout
            clone["visual_plan"]["template_reference"] = {
                "page": 4,
                "layout_features": ["same rectangular grid", "same text and visual split"],
                "adaptation": "故意重复同一个模板页族，用于验证整套版式多样性会被拦截。",
            }
            repeated.append(clone)
        final_slide = json.loads(json.dumps(repetitive_template_reference["slides"][-1], ensure_ascii=False))
        final_slide["number"] = len(repeated) + 1
        repeated.append(final_slide)
        repetitive_template_reference["slides"] = repeated
        repetitive_template_reference_path.write_text(json.dumps(repetitive_template_reference, ensure_ascii=False), encoding="utf-8")
        repetitive_template_reference_report = audit(temp, repetitive_template_reference_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("template reference variety" in error for error in repetitive_template_reference_report["errors"])

        source_rich_long_deck_path, source_rich_long_source_path = write_source_rich_long_fixture(temp)
        source_rich_long_report = audit(temp, source_rich_long_deck_path, source_rich_long_source_path)
        assert source_rich_long_report["ok"]

        repeated_native_motif_path = temp / "source-rich-repeated-native-motif.json"
        repeated_native_motif = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        for slide in repeated_native_motif["slides"]:
            motif = slide.get("visual_plan", {}).get("template_motif")
            if isinstance(motif, dict):
                motif["native_element_ref"]["source_page"] = 1
                motif["native_element_ref"]["source_element_id"] = "same-template-star"
        repeated_native_motif_path.write_text(json.dumps(repeated_native_motif, ensure_ascii=False), encoding="utf-8")
        repeated_native_motif_report = audit(temp, repeated_native_motif_path, source_rich_long_source_path, expect=1)
        assert any("too repetitive" in error for error in repeated_native_motif_report["errors"])

        builder_source = (SCRIPTS / "build_deck.mjs").read_text(encoding="utf-8")
        assert "titleLength > 30 ? 36 : titleLength > 24 ? 40 : titleLength > 18 ? 46 : 58" in builder_source
        assert "numbered && !point.head ? 26 : 16" in builder_source
        assert "compact ? 16 : 17" in builder_source
        assert "text.length > 150 ? 16 : text.length > 105 ? 17 : 18" in builder_source
        assert "size: 15,\n    color: dark ? C.white : C.black" in builder_source

        # Builder must render every declared image, including multi-source image pages and comparison visuals.
        image_asset_dir = temp / "builder-assets" / "assets"
        image_paths = write_png_assets(image_asset_dir, 4)
        image_deck = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        image_deck["slides"][1]["layout"] = "image-right"
        image_deck["slides"][1]["visuals"] = [
            {"path": image_paths[0], "alt": "源案例图 1"},
            {"path": image_paths[1], "alt": "源案例图 2"},
            {"path": image_paths[2], "alt": "源案例图 3"},
        ]
        image_deck["slides"][1]["visual_plan"]["asset_type"] = "source-image"
        image_deck["slides"][1]["visual_plan"]["source_image_ids"] = ["img001", "img002", "img003"]
        image_deck["slides"][1]["visual_plan"]["case_granularity"] = "multi-case-sequence"
        image_deck["slides"][1]["visual_plan"]["case_grouping_reason"] = "三张源图按原始顺序展示同一分支的递进案例，教师可在一页中逐张讲解。"
        image_deck["slides"][1]["visual_plan"]["text_area_ratio"] = 0.36
        image_deck["slides"][1]["visual_plan"]["image_area_ratio"] = 0.56
        image_deck["slides"][1]["visual_plan"]["min_source_image_area_ratio"] = 0.16
        image_deck["slides"][2]["layout"] = "comparison"
        image_deck["slides"][2]["visuals"] = [{"path": image_paths[3], "alt": "对比案例图"}]
        image_deck_path = temp / "builder-assets" / "deck-spec.json"
        image_deck_path.write_text(json.dumps(image_deck, ensure_ascii=False), encoding="utf-8")
        image_workspace = temp / "builder-workspace"
        image_output = temp / "builder-assets" / "image-deck.pptx"
        run([
            "node", str(SCRIPTS / "build_deck.mjs"),
            "--spec", str(image_deck_path),
            "--output", str(image_output),
            "--workspace", str(image_workspace),
        ])
        assert pptx_media_count(image_output) >= 4

        # A dense source node may be split across consecutive slides when the split is declared.
        split_deck = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        continuation = json.loads(json.dumps(split_deck["slides"][1], ensure_ascii=False))
        continuation["number"] = 3
        continuation["title"] = "编码还需要单独解释体积和播放压力"
        continuation["source_coverage_kind"] = "split-continuation"
        continuation["source_split_reason"] = "同一源节点包含两个需要分开讲解的教学单位，拆页后仍保持原节点顺序。"
        split_deck["slides"][2]["number"] = 4
        split_deck["slides"] = [split_deck["slides"][0], split_deck["slides"][1], continuation, split_deck["slides"][2]]
        split_deck_path = temp / "split-source-node.json"
        split_deck_path.write_text(json.dumps(split_deck, ensure_ascii=False), encoding="utf-8")
        split_report = audit(temp, split_deck_path, FIXTURES / "source-map-detailed.json")
        assert split_report["ok"]

        # PDF hierarchy checks must be explicitly recorded before source validation can pass in PDF mode.
        pdf_map = json.loads((FIXTURES / "source-map-detailed.json").read_text(encoding="utf-8"))
        pdf_map["source_type"] = "pdf"
        pdf_map["outline_mode"] = None
        pdf_map["mode_declared_by_user"] = False
        pdf_map_path = temp / "pdf-source-map.json"
        pdf_map_path.write_text(json.dumps(pdf_map, ensure_ascii=False), encoding="utf-8")
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(pdf_map_path), "--require-pdf-visual-check"], expect=1)
        run([
            sys.executable, str(SCRIPTS / "validate_source_map.py"), str(pdf_map_path),
            "--pdf-visual-check", "--mode", "detailed", "--write", "--require-mode", "--require-pdf-visual-check",
        ])

        missing_mapping_path = temp / "source-rich-missing-mapping.json"
        missing_mapping = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        del missing_mapping["course"]["template_page_mapping"]
        missing_mapping_path.write_text(json.dumps(missing_mapping, ensure_ascii=False), encoding="utf-8")
        missing_mapping_report = audit(temp, missing_mapping_path, source_rich_long_source_path, expect=1)
        assert any("template_page_mapping" in error for error in missing_mapping_report["errors"])

        missing_generated_path = temp / "source-rich-missing-generated.json"
        missing_generated = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        missing_generated["course"]["image_generation_review"]["generated_slide_numbers"] = []
        for slide in missing_generated["slides"]:
            if slide["visual_plan"].get("asset_type") == "generated-image":
                slide["visual_plan"]["asset_type"] = "source-image"
                slide["visual_plan"]["generation_route"] = ""
                slide["visual_plan"]["prompt_brief"] = ""
        missing_generated_path.write_text(json.dumps(missing_generated, ensure_ascii=False), encoding="utf-8")
        missing_generated_report = audit(temp, missing_generated_path, source_rich_long_source_path, expect=1)
        assert any("generated" in error or "image_generation_review" in error for error in missing_generated_report["errors"])

        missing_source_priority_path = temp / "source-rich-missing-source-priority.json"
        missing_source_priority = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        missing_source_priority["course"]["image_generation_review"]["source_case_priority"] = "generated-first"
        missing_source_priority["course"]["image_generation_review"]["reused_source_slide_numbers"] = []
        missing_source_priority_path.write_text(json.dumps(missing_source_priority, ensure_ascii=False), encoding="utf-8")
        missing_source_priority_report = audit(temp, missing_source_priority_path, source_rich_long_source_path, expect=1)
        assert any("source_case_priority" in error or "reused_source_slide_numbers" in error for error in missing_source_priority_report["errors"])

        source_collage_path = temp / "source-rich-collage.json"
        source_collage = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        source_collage["slides"][1]["visual_plan"]["source_image_ids"] = ["img002", "img003", "img004", "img005"]
        source_collage["slides"][1]["visual_plan"]["case_granularity"] = "explicit-comparison"
        source_collage["slides"][1]["visual_plan"]["case_grouping_reason"] = "故意把多个独立源图塞进同一页，用于验证审计会阻止案例拼图。"
        source_collage_path.write_text(json.dumps(source_collage, ensure_ascii=False), encoding="utf-8")
        source_collage_report = audit(temp, source_collage_path, source_rich_long_source_path, expect=1)
        assert any("at most 3" in error or "independent source images" in error for error in source_collage_report["errors"])

        source_three_images_path = temp / "source-rich-three-images.json"
        source_three_images = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        source_three_images["slides"][1]["visual_plan"]["source_image_ids"] = ["img002", "img003", "img004"]
        source_three_images["slides"][1]["visuals"] = [
            {"path": "assets/case-2.png", "alt": "源案例图 2"},
            {"path": "assets/case-3.png", "alt": "源案例图 3"},
            {"path": "assets/case-4.png", "alt": "源案例图 4"},
        ]
        source_three_images["slides"][1]["visual_plan"]["case_granularity"] = "multi-case-sequence"
        source_three_images["slides"][1]["visual_plan"]["case_grouping_reason"] = "三张源图按原始顺序展示同一分支的递进案例，教师可在一页中逐张讲解。"
        source_three_images["slides"][1]["visual_plan"]["text_area_ratio"] = 0.36
        source_three_images["slides"][1]["visual_plan"]["image_area_ratio"] = 0.56
        source_three_images["slides"][1]["visual_plan"]["min_source_image_area_ratio"] = 0.16
        source_three_images_path.write_text(json.dumps(source_three_images, ensure_ascii=False), encoding="utf-8")
        source_three_images_report = audit(temp, source_three_images_path, source_rich_long_source_path)
        assert source_three_images_report["ok"]

        missing_page_design_path = temp / "source-rich-missing-page-design.json"
        missing_page_design = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        del missing_page_design["course"]["page_design_review"]
        missing_page_design_path.write_text(json.dumps(missing_page_design, ensure_ascii=False), encoding="utf-8")
        missing_page_design_report = audit(temp, missing_page_design_path, source_rich_long_source_path, expect=1)
        assert any("page_design_review" in error for error in missing_page_design_report["errors"])

        # Sparse direct expansion passes.
        sparse = audit(temp, FIXTURES / "deck-spec-sparse.json", FIXTURES / "source-map-sparse.json")
        assert sparse["ok"]

        # Low-relevance software operation and backstage wording both fail.
        sparse_bad_path = temp / "sparse-out-of-scope.json"
        sparse_bad = json.loads((FIXTURES / "deck-spec-sparse.json").read_text(encoding="utf-8"))
        sparse_bad["slides"][1]["screen"]["bullets"].append("进入剪辑软件操作界面")
        sparse_bad["slides"][1]["added_content"].append({
            "text": "剪辑软件操作", "source_node_id": "n0002", "kind": "example",
            "relevance": "low", "evidence_urls": ["https://example.com"],
        })
        sparse_bad_path.write_text(json.dumps(sparse_bad, ensure_ascii=False), encoding="utf-8")
        bad_report = audit(temp, sparse_bad_path, FIXTURES / "source-map-sparse.json", expect=1)
        assert any("out-of-scope" in error or "not directly relevant" in error for error in bad_report["errors"])

        backstage_path = temp / "backstage.json"
        backstage = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        backstage["slides"][1]["screen"]["explanation"] += " 在 PDF 中这样描述。"
        backstage_path.write_text(json.dumps(backstage, ensure_ascii=False), encoding="utf-8")
        backstage_report = audit(temp, backstage_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("PDF" in error for error in backstage_report["errors"])

        unsupported_layout_path = temp / "unsupported-layout.json"
        unsupported_layout = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        unsupported_layout["slides"][1]["layout"] = "bad-layout"
        unsupported_layout["slides"][1]["screen"]["explanation"] += " TODO"
        unsupported_layout["slides"][1]["source_node_ids"].append(unsupported_layout["slides"][1]["source_node_ids"][0])
        unsupported_layout_path.write_text(json.dumps(unsupported_layout, ensure_ascii=False), encoding="utf-8")
        unsupported_layout_report = audit(temp, unsupported_layout_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("unsupported layout" in error for error in unsupported_layout_report["errors"])
        assert any("TODO" in error for error in unsupported_layout_report["errors"])
        assert any("more than once" in error for error in unsupported_layout_report["errors"])

        empty_editable_path = temp / "empty-editable-visual.json"
        empty_editable = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        empty_editable["slides"][1]["layout"] = "comparison"
        empty_editable["slides"][1]["screen"]["bullets"] = []
        empty_editable["slides"][1]["screen"]["blocks"] = []
        empty_editable["slides"][1]["visuals"] = []
        empty_editable["slides"][1]["visual_plan"]["asset_type"] = "editable-diagram"
        empty_editable["slides"][1]["visual_plan"]["imagegen_priority"] = "not-needed"
        empty_editable["slides"][1]["visual_plan"]["imagegen_bypass_reason"] = "该页是关系结构图，更适合可编辑形状。"
        empty_editable_path.write_text(json.dumps(empty_editable, ensure_ascii=False), encoding="utf-8")
        empty_editable_report = audit(temp, empty_editable_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("editable visual" in error for error in empty_editable_report["errors"])

        # Contact-sheet helper works with generated PNGs.
        try:
            from PIL import Image
        except ImportError:
            Image = None
        if Image:
            image_dir = temp / "images"
            image_dir.mkdir()
            for number in range(1, 4):
                Image.new("RGB", (320, 180), (number * 40, 30, 20)).save(image_dir / f"slide-{number:02d}.png")
            output = temp / "contact-sheet.jpg"
            run([sys.executable, str(SCRIPTS / "make_contact_sheet.py"), "--input-dir", str(image_dir), "--output", str(output)])
            assert output.exists() and output.stat().st_size > 0

        svg_image_dir = temp / "svg-images"
        svg_asset_paths = write_png_assets(svg_image_dir, 3)
        for index, relative in enumerate(svg_asset_paths, start=1):
            (svg_image_dir / f"slide-{index:02d}.png").write_bytes((svg_image_dir.parent / relative).read_bytes())
        svg_output = temp / "contact-sheet.svg"
        run([sys.executable, str(SCRIPTS / "make_contact_sheet.py"), "--input-dir", str(svg_image_dir), "--output", str(svg_output)])
        assert "<svg" in svg_output.read_text(encoding="utf-8")

    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
