#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
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


def audit(temp: Path, deck: Path, source: Path, *, expect: int = 0) -> dict:
    report = temp / f"{deck.stem}-report.json"
    run(
        [sys.executable, str(SCRIPTS / "audit_deck.py"), "--deck-spec", str(deck), "--source-map", str(source), "--report", str(report)],
        expect=expect,
    )
    return json.loads(report.read_text(encoding="utf-8"))


def valid_template_motif(kind: str = "visual-anchor") -> dict:
    return {
        "kind": kind,
        "canva_asset_id": "MAEeKPWZP8I",
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
        },
        "canva_replacement": {
            "mode": "replace_placeholder",
            "match_strategy": "after Canva import, match the local preview proxy by page index and recorded motif_box, then replace it",
            "fallback": "delete the local proxy and insert the native Canva asset at the same recorded box",
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
            "native_motif": "planned" if number in {1, 8} else "none",
            "local_ppt_decision": "按参考模板页先确定文字列宽、视觉区和 motif 位置，再生成本地 PPT。",
        }
        for number in range(1, 17)
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
    cover["visual_plan"]["template_motif"] = valid_template_motif("hero-right")
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
        if index == 6:
            slide["layout"] = "image-right"
            slide["visuals"] = [{"path": "assets/generated/case.png", "alt": "生成案例图"}]
            slide["visual_plan"]["asset_type"] = "generated-image"
            slide["visual_plan"]["generation_route"] = "gpt-image-2"
            slide["visual_plan"]["imagegen_priority"] = "preferred"
            slide["visual_plan"]["prompt_brief"] = "具体课程场景的无文字教学案例图"
        if index == 8:
            slide["visual_plan"]["template_motif"] = valid_template_motif("visual-anchor")
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
        missing_motif_replacement["slides"][0]["visual_plan"]["template_motif"] = {
            "kind": "hero-right",
            "canva_asset_id": "MAEeKPWZP8I",
            "local_preview_path": "assets/template-grainy-star.png",
            "reference_template_page": 1,
            "placement_basis": "参考模板右侧中心主视觉，左侧文字栏收窄并提前断行。",
            "replaces_modules": ["cover-orange", "cover-focus"],
            "local_ppt_layout": {
                "coordinate_space": "1280x720",
                "text_column_width": 560,
                "title_break_strategy": "manual wrap before PPT generation",
                "motif_box": {"left": 680, "top": 60, "width": 600, "height": 600},
                "native_canva_scale": 1.5,
            },
            "collision_check": {
                "status": "clear",
                "notes": "本地 PPT 预览中主视觉不覆盖标题、正文、页脚和页码。",
            },
        }
        missing_motif_replacement_path.write_text(json.dumps(missing_motif_replacement, ensure_ascii=False), encoding="utf-8")
        motif_replacement_report = audit(temp, missing_motif_replacement_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("replace_placeholder" in error for error in motif_replacement_report["errors"])

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

        builder_source = (SCRIPTS / "build_deck.mjs").read_text(encoding="utf-8")
        assert "titleLength > 30 ? 36 : titleLength > 24 ? 40 : titleLength > 18 ? 46 : 58" in builder_source
        assert "numbered && !point.head ? 26 : 16" in builder_source
        assert "compact ? 16 : 17" in builder_source
        assert "text.length > 150 ? 16 : text.length > 105 ? 17 : 18" in builder_source
        assert "size: 15,\n    color: dark ? C.white : C.black" in builder_source

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

    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
