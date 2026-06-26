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


def write_fake_artifact_tool(workspace: Path) -> None:
    package_dir = workspace / "node_modules" / "@oai" / "artifact-tool"
    package_dir.mkdir(parents=True)
    (workspace / "package.json").write_text('{"private":true}\n', encoding="utf-8")
    (package_dir / "package.json").write_text(
        '{"name":"@oai/artifact-tool","type":"module","main":"index.mjs"}\n',
        encoding="utf-8",
    )
    (package_dir / "index.mjs").write_text(
        r'''
import fs from "node:fs/promises";

class Slide {
  constructor() {
    this.background = {};
    this._shapes = [];
    this._images = [];
    this.shapes = {
      items: this._shapes,
      add: (shape) => {
        const record = { ...shape, textValue: "", textStyle: {} };
        Object.defineProperty(record, "text", {
          get() {
            return { value: this.textValue, style: this.textStyle };
          },
          set(value) {
            this.textValue = String(value || "");
          },
        });
        this._shapes.push(record);
        return record;
      },
    };
    this.images = {
      items: this._images,
      add: (image) => {
        this._images.push(image);
        return image;
      },
    };
  }

  async export({ format }) {
    if (format !== "layout") return { text: async () => "" };
    return {
      text: async () => JSON.stringify({
        shapes: this._shapes.map((shape) => ({
          name: shape.name || "",
          position: shape.position || {},
          text: shape.textValue || "",
        })),
        images: this._images.map((image) => ({ alt: image.alt || "", position: image.position || {} })),
      }),
    };
  }
}

class PresentationImpl {
  constructor() {
    this.slides = {
      items: [],
      add: () => {
        const slide = new Slide();
        this.slides.items.push(slide);
        return slide;
      },
    };
  }

  async export() {
    return { arrayBuffer: async () => new ArrayBuffer(0) };
  }

  async inspect() {
    return { ndjson: "" };
  }
}

export const Presentation = {
  create() {
    return new PresentationImpl();
  },
};

export const PresentationFile = {
  async exportPptx() {
    return {
      async save(outputPath) {
        await fs.writeFile(outputPath, "fake pptx");
      },
    };
  },
};
'''.lstrip(),
        encoding="utf-8",
    )


def source_treatment(node_id: str, evidence: str, *, status: str = "preserved") -> dict:
    return {
        "source_node_id": node_id,
        "coverage_status": status,
        "screen_evidence": evidence,
        "coverage_note": "synthetic fixture keeps the mapped source node visible through this learner-facing phrase.",
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
    course["template_style_atlas"] = [
        {
            "id": "hero-cover",
            "source_template_pages": [1],
            "geometry": "large dark field with signature hero motif",
            "best_for": "course opening and section statements",
            "capacity_limits": "short title and one supporting phrase",
            "renderer_layouts": ["cover"],
        },
        {
            "id": "image-evidence",
            "source_template_pages": [6, 9],
            "geometry": "image slot paired with concise interpretation",
            "best_for": "source case image or generated teaching case",
            "capacity_limits": "one image plus three to four points",
            "renderer_layouts": ["image-right", "image-left-dark", "image-right-dark"],
        },
        {
            "id": "flow-roadmap",
            "source_template_pages": [2, 5],
            "geometry": "large color field with grouped route modules",
            "best_for": "process, sequence, or branch orientation",
            "capacity_limits": "three to four groups before splitting",
            "renderer_layouts": ["roadmap"],
        },
        {
            "id": "dense-index",
            "source_template_pages": [3, 18],
            "geometry": "compact module grid for occasional enumerations",
            "best_for": "short sibling list with peer items",
            "capacity_limits": "two to three columns with short labels",
            "renderer_layouts": ["table"],
        },
        {
            "id": "comparison-strip",
            "source_template_pages": [12],
            "geometry": "two strong fields with meaningful labels",
            "best_for": "real comparison or before-after contrast",
            "capacity_limits": "two sides and up to three points per side",
            "renderer_layouts": ["comparison"],
        },
        {
            "id": "accent-case",
            "source_template_pages": [8, 10, 14],
            "geometry": "accent field with structural visual anchor",
            "best_for": "memorable case, analogy, or transition",
            "capacity_limits": "one anchor image and short explanation",
            "renderer_layouts": ["image-left-accent", "image-right-accent"],
        },
    ]
    style_families = [
        "hero-cover",
        "image-evidence", "image-evidence", "flow-roadmap", "flow-roadmap",
        "dense-index", "flow-roadmap", "dense-index", "accent-case",
        "flow-roadmap", "image-evidence", "flow-roadmap", "dense-index",
        "comparison-strip", "accent-case", "hero-cover",
    ]
    course["template_page_mapping"] = [
        {
            "slide_number": number,
            "template_reference": f"page {((number - 1) % 8) + 1}",
            "template_style_family": style_families[number - 1],
            "layout_family": "cover" if number == 1 else "knowledge",
            "native_motif": "planned" if number in {1, 8, 10, 12} else "none",
            "content_fit_reason": "当前节点内容关系适合该模板结构家族，能保留讲解重点和视觉节奏。",
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
        "generated_bypass_reason": "",
        "gpt_image_2_attempts": [
            {
                "status": "success",
                "slide_numbers": [6],
                "asset_dir": "assets/generated",
                "notes": "fixture records successful GPT Image 2 generation before PPT build",
            }
        ],
        "rationale": "源图充足但仍补一张文字较多页面的教学案例图。",
    }
    course["image_generation_tasks"] = [
        {
            "slide_number": 6,
            "generation_route": "gpt-image-2",
            "knowledge_anchor": "节点 6 的文字较多，需要用一个具体场景呈现核心判断。",
            "observable_teaching_detail": "画面中学员能看到一个明确的操作前后状态差异，从而理解该节点的判断。",
            "instant_takeaway": "零基础学员能立刻看懂这个节点会改变画面结果和判断方式。",
            "template_style_bridge": "延续所选模板的高对比色块、清晰主体和留白标签区，让图片嵌入页面而不突兀。",
            "status": "success",
            "final_asset_path": "assets/generated/case.png",
        }
    ]
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
    cover["source_node_treatments"] = [source_treatment("n0001", "编码与格式", status="section-heading")]
    cover["visual_plan"]["source_node_id"] = "n0001"
    cover["visual_plan"]["layout_variant"] = "hero-cover"
    cover["visual_plan"]["template_motif"] = valid_template_motif("hero-right", source_page=1, source_element_id="template-star-hero")
    cover["visual_plan"]["template_motif"]["local_ppt_layout"]["motif_box"] = {"left": 700, "top": 70, "width": 560, "height": 560}

    layouts = [
        "comparison", "image-left-dark", "roadmap", "roadmap",
        "table", "roadmap", "table", "image-left-accent",
        "roadmap", "image-right-dark", "roadmap", "table",
        "comparison", "image-right-accent",
    ]
    variants = [
        "two-panel", "dark-spotlight", "index-grid", "poster-panel",
        "comparison-strip", "split-image", "close-reading", "wide-case-band",
        "gallery-strip", "center-anchor", "poster-panel", "split-image",
        "comparison-strip", "two-panel",
    ]
    rendered_patterns = [
        "balanced-two-panel-comparison",
        "dark-image-evidence-split",
        "full-field-branch-map",
        "accent-poster-principle",
        "compact-index-grid",
        "flow-roadmap-modules",
        "close-reading-table",
        "accent-wide-case-band",
        "gallery-evidence-strip",
        "center-anchor-statement",
        "side-poster-modules",
        "light-split-evidence",
        "comparison-strip",
        "accent-two-panel-case",
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
        slide["source_node_treatments"] = [source_treatment(node_id, slide["title"], status="clarified")]
        slide["scope_check"] = {"status": "within-branch", "branch_node_id": node_id}
        slide["visual_plan"]["source_node_id"] = node_id
        slide["visual_plan"]["template_reference"] = {
            "page": ((index - 1) % 8) + 1,
            "style_family": style_families[index - 1],
            "layout_features": ["varied template page family", "stable visual/text relationship"],
            "adaptation": "根据参考模板页调整图文区域、标题宽度和信息块位置后再生成本地 PPT。",
        }
        slide["visual_plan"]["template_style_family"] = style_families[index - 1]
        slide["visual_plan"]["layout_variant"] = variants[index - 2]
        slide["visual_plan"]["rendered_pattern"] = rendered_patterns[index - 2]
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
            slide["visual_plan"]["knowledge_anchor"] = "节点 6 的文字较多，需要用一个具体场景呈现核心判断。"
            slide["visual_plan"]["observable_teaching_detail"] = "画面中学员能看到一个明确的操作前后状态差异，从而理解该节点的判断。"
            slide["visual_plan"]["instant_takeaway"] = "零基础学员能立刻看懂这个节点会改变画面结果和判断方式。"
            slide["visual_plan"]["template_style_bridge"] = "延续所选模板的高对比色块、清晰主体和留白标签区，让图片嵌入页面而不突兀。"
        if index in {8, 10, 12}:
            slide["visual_plan"]["template_motif"] = valid_template_motif(
                "visual-anchor",
                source_page=((index - 1) % 3) + 2,
                source_element_id=f"template-anchor-{index}",
            )
        slides.append(slide)

    summary = json.loads(json.dumps(base["slides"][-1], ensure_ascii=False))
    summary["number"] = 16
    summary["title"] = "节点 16 的总结式标题"
    summary["layout"] = "summary"
    summary["source_node_ids"] = ["n0016"]
    summary["source_node_treatments"] = [source_treatment("n0016", summary["title"], status="clarified")]
    summary["scope_check"] = {"status": "within-branch", "branch_node_id": "n0016"}
    summary["visual_plan"]["source_node_id"] = "n0016"
    summary["visual_plan"]["layout_variant"] = "summary-blocks"
    slides.append(summary)
    base["slides"] = slides
    deck_path = temp / "source-rich-long-deck.json"
    deck_path.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    return deck_path, source_path


def write_layout_rich_builder_spec(temp: Path) -> Path:
    slides = []
    patterns = [
        ("roadmap", "full-field-branch-map", "流程页解释", "流程阶段"),
        ("orange", "accent-statement-visual-band", "结论页解释", "结论动作"),
        ("light", "side-rail-modules", "侧栏页解释", "检查动作"),
    ]
    for number, (layout, pattern, explanation, heading) in enumerate(patterns, start=1):
        slides.append({
            "number": number,
            "section": "TEST",
            "title": f"模板多版式参考 {number}",
            "layout": layout,
            "screen": {
                "explanation": f"{explanation}，用于验证构建器能按模板参考页形成不同几何结构。",
                "bullets": [f"{heading}一", f"{heading}二", f"{heading}三"],
                "caption": "",
                "blocks": [],
            },
            "visuals": [],
            "visual_plan": {
                "source_node_id": f"n{number:04d}",
                "asset_type": "editable-diagram",
                "integration": "knowledge-page",
                "description": "template reference geometry",
                "teaching_role": "shows template-driven layout variety",
                "visual_applicability": "required",
                "imagegen_priority": "not-needed",
                "imagegen_bypass_reason": "editable template structure is clearer here",
                "text_area_ratio": 0.42,
                "labels_as_slide_text": True,
                "layout_variant": pattern,
                "rendered_pattern": pattern,
                "template_style_family": pattern,
                "template_reference": {
                    "page": number + 2,
                    "style_family": pattern,
                    "layout_features": ["template geometry family", "distinct thumbnail pattern"],
                    "adaptation": "Use the selected template page family to produce a visibly different local PPT geometry.",
                },
                "diagram_elements": [{"kind": "module", "label": pattern}],
            },
            "source_node_ids": [f"n{number:04d}"],
            "source_node_treatments": [source_treatment(f"n{number:04d}", f"模板多版式参考 {number}")],
            "added_content": [],
            "scope_check": {"status": "within-branch", "branch_node_id": f"n{number:04d}"},
        })
    spec = {
        "course": {
            "title": "Builder layout variety regression",
            "audience": "course creators",
            "outline_mode": "detailed",
            "curriculum_context": {"system_name": "Course", "module": "Builder", "course_role": "Verify builder layout variety"},
        },
        "slides": slides,
    }
    spec_path = temp / "layout-rich-builder-spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    return spec_path


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
        assert by_text["编码是整理和压缩视频数据的打包手法。"]["source_path"] == "编码与格式 > 编码 > 编码是整理和压缩视频数据的打包手法。"
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

        backstage_copy_path = temp / "backstage-copy.json"
        backstage_copy = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        backstage_copy["slides"][1]["screen"]["explanation"] = (
            "本页顺序：1 父节点 / 2 子节点。这里故意把制作证据写进画面，用于验证审计拦截。"
        )
        backstage_copy_path.write_text(json.dumps(backstage_copy, ensure_ascii=False), encoding="utf-8")
        backstage_copy_report = audit(temp, backstage_copy_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("forbidden learner-facing text" in error for error in backstage_copy_report["errors"])

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

        whole_page_motif_path = temp / "whole-page-motif.json"
        whole_page_motif = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        whole_page_motif["slides"][0]["visual_plan"]["template_motif"] = valid_template_motif(
            "hero-right",
            source_page=1,
            source_element_id="template-star-hero",
        )
        whole_page_motif["slides"][0]["visual_plan"]["template_motif"]["local_ppt_layout"]["motif_box"] = {"left": 680, "top": 60, "width": 600, "height": 600}
        whole_page_motif["slides"][0]["visual_plan"]["template_motif"]["canva_replacement"]["source_copy_strategy"] = (
            "duplicate page from the template and paste page into the final course deck"
        )
        whole_page_motif_path.write_text(json.dumps(whole_page_motif, ensure_ascii=False), encoding="utf-8")
        whole_page_motif_report = audit(temp, whole_page_motif_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("whole template page" in error or "whole-template-page" in error for error in whole_page_motif_report["errors"])

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

        generated_missing_teaching_detail_path = temp / "source-rich-generated-missing-teaching-detail.json"
        generated_missing_teaching_detail = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        for slide in generated_missing_teaching_detail["slides"]:
            if slide.get("visual_plan", {}).get("asset_type") == "generated-image":
                slide["visual_plan"].pop("knowledge_anchor", None)
                slide["visual_plan"].pop("observable_teaching_detail", None)
                slide["visual_plan"].pop("instant_takeaway", None)
        for task in generated_missing_teaching_detail["course"]["image_generation_tasks"]:
            task.pop("knowledge_anchor", None)
            task.pop("observable_teaching_detail", None)
            task.pop("instant_takeaway", None)
        generated_missing_teaching_detail_path.write_text(json.dumps(generated_missing_teaching_detail, ensure_ascii=False), encoding="utf-8")
        generated_missing_teaching_detail_report = audit(
            temp,
            generated_missing_teaching_detail_path,
            source_rich_long_source_path,
            expect=1,
        )
        assert any(
            "knowledge_anchor" in error or "observable_teaching_detail" in error or "instant_takeaway" in error
            for error in generated_missing_teaching_detail_report["errors"]
        )

        blocked_native_reuse_path = temp / "source-rich-blocked-native-reuse.json"
        blocked_native_reuse = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        blocked_native_reuse["course"]["template_native_element_inventory"] = []
        blocked_native_reuse["course"]["template_native_reuse_status"] = {
            "status": "blocked-no-atomic-copy",
            "reason": "当前 Canva 路由只能导入 PPTX，不能原子级复制模板里的矢量、形状或组合元素，所以本轮不声明原生 motif 复用。",
        }
        for item in blocked_native_reuse["course"]["template_page_mapping"]:
            item["native_motif"] = "blocked-no-atomic-copy"
        for slide in blocked_native_reuse["slides"]:
            slide.get("visual_plan", {}).pop("template_motif", None)
        blocked_native_reuse_path.write_text(json.dumps(blocked_native_reuse, ensure_ascii=False), encoding="utf-8")
        blocked_native_reuse_report = audit(temp, blocked_native_reuse_path, source_rich_long_source_path, expect=1)
        assert any("blocked-no-atomic-copy" in error for error in blocked_native_reuse_report["errors"])

        approved_blocked_native_reuse_path = temp / "source-rich-approved-blocked-native-reuse.json"
        approved_blocked_native_reuse = json.loads(json.dumps(blocked_native_reuse, ensure_ascii=False))
        approved_blocked_native_reuse["course"]["native_template_fallback_approved_by_user"] = True
        approved_blocked_native_reuse_path.write_text(json.dumps(approved_blocked_native_reuse, ensure_ascii=False), encoding="utf-8")
        approved_blocked_native_reuse_report = audit(temp, approved_blocked_native_reuse_path, source_rich_long_source_path)
        assert approved_blocked_native_reuse_report["ok"], approved_blocked_native_reuse_report["errors"]

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

        fake_workspace = temp / "fake-artifact-workspace"
        fake_workspace.mkdir()
        write_fake_artifact_tool(fake_workspace)
        layout_builder_spec = write_layout_rich_builder_spec(temp)
        layout_builder_output = temp / "layout-rich-builder.pptx"
        run([
            "node",
            str(SCRIPTS / "build_deck.mjs"),
            "--spec",
            str(layout_builder_spec),
            "--output",
            str(layout_builder_output),
            "--workspace",
            str(fake_workspace),
        ])
        layout_shape_names = "\n".join(
            "\n".join(shape.get("name", "") for shape in json.loads(path.read_text(encoding="utf-8")).get("shapes", []))
            for path in sorted((fake_workspace / "layout").glob("slide-*.json"))
        )
        assert "flow-node-" in layout_shape_names
        assert "statement-field-" in layout_shape_names
        assert "side-rail-" in layout_shape_names

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

        no_generated_with_bypass_path = temp / "source-rich-no-generated-with-bypass.json"
        no_generated_with_bypass = json.loads(source_rich_long_deck_path.read_text(encoding="utf-8"))
        no_generated_with_bypass["course"]["image_generation_review"]["generated_slide_numbers"] = []
        no_generated_with_bypass["course"]["image_generation_review"]["candidates_considered"] = 0
        no_generated_with_bypass["course"]["image_generation_review"]["generated_bypass_reason"] = (
            "源案例图已经覆盖主要演示页，剩余抽象页使用可编辑对比图和流程图更清晰，因此不需要额外位图生成。"
        )
        for slide in no_generated_with_bypass["slides"]:
            if slide["visual_plan"].get("asset_type") == "generated-image":
                slide["layout"] = "comparison"
                slide["visuals"] = []
                slide["visual_plan"]["asset_type"] = "editable-diagram"
                slide["visual_plan"]["source_image_ids"] = []
                slide["visual_plan"]["case_granularity"] = "not-source-image"
                slide["visual_plan"]["generation_route"] = ""
                slide["visual_plan"]["prompt_brief"] = ""
                slide["visual_plan"]["imagegen_priority"] = "not-needed"
                slide["visual_plan"]["imagegen_bypass_reason"] = "该页用可编辑对比图比位图更容易承载标签和讲解关系。"
        no_generated_with_bypass_path.write_text(json.dumps(no_generated_with_bypass, ensure_ascii=False), encoding="utf-8")
        no_generated_with_bypass_report = audit(temp, no_generated_with_bypass_path, source_rich_long_source_path)
        assert no_generated_with_bypass_report["ok"]

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

        generic_block_label_path = temp / "generic-block-label.json"
        generic_block_label = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        generic_block_label["slides"][1]["screen"]["blocks"][0]["heading"] = "结构顺序 A"
        generic_block_label["slides"][1]["screen"]["blocks"][1]["heading"] = "结构顺序 B"
        generic_block_label_path.write_text(json.dumps(generic_block_label, ensure_ascii=False), encoding="utf-8")
        generic_block_label_report = audit(temp, generic_block_label_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("generic or meaningless block label" in error for error in generic_block_label_report["errors"])

        hierarchy_flattened_path = temp / "hierarchy-flattened.json"
        hierarchy_flattened = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        hierarchy_flattened["slides"][1]["source_node_ids"] = ["n0002", "n0003"]
        hierarchy_flattened["slides"][1]["source_node_treatments"] = [
            source_treatment("n0002", "编码负责按照一套规则整理和压缩这些数据", status="clarified"),
            source_treatment("n0003", "格式可以理解为装视频数据的文件箱子", status="clarified"),
        ]
        hierarchy_flattened["slides"][1]["screen"]["explanation"] += " 格式可以理解为装视频数据的文件箱子。"
        hierarchy_flattened["slides"][1]["scope_check"] = {"status": "within-branch", "branch_node_id": "n0002"}
        hierarchy_flattened_path.write_text(json.dumps(hierarchy_flattened, ensure_ascii=False), encoding="utf-8")
        hierarchy_flattened_report = audit(temp, hierarchy_flattened_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("flattens source hierarchy" in error for error in hierarchy_flattened_report["errors"])

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
