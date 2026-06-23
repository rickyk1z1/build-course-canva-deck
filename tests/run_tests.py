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


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="course-canva-skill-") as raw:
        temp = Path(raw)

        # Source extraction preserves order and refuses to infer outline mode.
        source_map = temp / "source-map.json"
        run([sys.executable, str(SCRIPTS / "extract_source.py"), "--input", str(FIXTURES / "detailed-outline.md"), "--output", str(source_map)])
        extracted = json.loads(source_map.read_text(encoding="utf-8"))
        assert extracted["outline_mode"] is None
        assert extracted["requires_user_outline_mode"] is True
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(source_map), "--require-mode"], expect=1)
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(source_map), "--mode", "detailed", "--write", "--require-mode"])

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
