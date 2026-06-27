import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "skills/build-course-canva-deck/scripts/audit_deck.py"


def source_map():
    return {
        "outline_mode": "detailed",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": "n0", "text": "课程标题", "order": 1, "include": True},
            {"id": "n1", "text": "内容结构", "parent_id": "n0", "order": 2, "include": True},
            {"id": "n2", "text": "先给判断", "parent_id": "n1", "order": 3, "include": True},
            {"id": "n3", "text": "再补背景", "parent_id": "n1", "order": 4, "include": True},
        ],
        "images": [],
    }


def treatment(node_id, evidence, status="preserved"):
    return {
        "source_node_id": node_id,
        "screen_evidence": evidence,
        "coverage_status": status,
    }


def base_slide(visual_plan):
    return {
        "number": 3,
        "layout": "image-left",
        "title": "先给判断，再补背景",
        "section": "测试课",
        "framework_progress_label": "内容结构",
        "screen": {
            "explanation": "开头要像回答急问题：先让观众知道值不值得看，再补必要背景。",
            "bullets": ["先给判断", "再补背景"],
            "caption": "画面要让学员直接看出两个步骤的差别。",
            "blocks": [],
        },
        "source_node_ids": ["n2", "n3"],
        "source_node_treatments": [
            treatment("n2", "先给判断"),
            treatment("n3", "再补背景"),
        ],
        "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
        "visual_plan": visual_plan,
        "visuals": [{"path": "placeholder.png", "alt": "案例图"}],
    }


def deck(slide):
    return {
        "course": {
            "outline_mode": "detailed",
            "curriculum_context": {
                "system_name": "自媒体与视频剪辑课程体系",
                "module": "测试模块",
                "course_role": "测试案例图",
            },
        },
        "slides": [
            {
                "number": 1,
                "layout": "lesson-overview",
                "title": "课程总领",
                "screen": {"explanation": "课程标题", "bullets": ["内容结构"], "caption": "", "blocks": []},
                "source_node_ids": ["n0"],
                "source_node_treatments": [treatment("n0", "课程标题")],
            },
            {
                "number": 2,
                "layout": "section-cover",
                "title": "内容结构",
                "screen": {"explanation": "本节预告。", "bullets": ["先给判断", "再补背景"], "caption": "", "blocks": []},
                "source_node_ids": ["n1"],
                "source_node_treatments": [treatment("n1", "内容结构", "section-heading")],
                "section_preview_items": [
                    {"source_node_id": "n2", "screen_evidence": "先给判断"},
                    {"source_node_id": "n3", "screen_evidence": "再补背景"},
                ],
            },
            slide,
            {
                "number": 4,
                "layout": "summary",
                "title": "总结",
                "screen": {"explanation": "按章节回收本课重点。", "bullets": [], "caption": "", "blocks": []},
                "source_node_ids": [],
                "source_node_treatments": [],
            },
        ],
    }


def run_audit(deck_spec):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        deck_path = tmp_path / "deck.json"
        source_path = tmp_path / "source.json"
        report_path = tmp_path / "report.json"
        deck_path.write_text(json.dumps(deck_spec, ensure_ascii=False), encoding="utf-8")
        source_path.write_text(json.dumps(source_map(), ensure_ascii=False), encoding="utf-8")
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
        return result.returncode, report


class VisualTeachingSpecificityTests(unittest.TestCase):
    def test_rejects_generated_case_image_without_mapping_visible_details_to_points(self):
        visual_plan = {
            "asset_type": "generated-image",
            "integration": "knowledge-page",
            "source_node_id": "n2",
            "labels_as_slide_text": True,
            "generation_route": "gpt-image-2",
            "knowledge_anchor": "开头先给判断，再补背景",
            "observable_teaching_detail": "餐厅顾客和服务员",
            "instant_takeaway": "开头要先回答值不值得看",
        }
        code, report = run_audit(deck(base_slide(visual_plan)))
        self.assertNotEqual(code, 0)
        self.assertIn("slide 3 image visual_plan must map visible case details to the slide's teaching points", "\n".join(report["errors"]))

    def test_rejects_text_only_exception_without_generated_case_image_bypass_reason(self):
        slide = base_slide(
            {
                "asset_type": "text-only-exception",
                "integration": "knowledge-page",
                "source_node_id": "n2",
                "labels_as_slide_text": True,
            }
        )
        slide["layout"] = "light"
        slide["visuals"] = []
        code, report = run_audit(deck(slide))
        self.assertNotEqual(code, 0)
        self.assertIn("slide 3 text-only exception must explain why generated case image or diagram is not useful", "\n".join(report["errors"]))

    def test_accepts_case_visual_map_covering_each_visible_teaching_point(self):
        visual_plan = {
            "asset_type": "generated-image",
            "integration": "knowledge-page",
            "source_node_id": "n2",
            "labels_as_slide_text": True,
            "generation_route": "gpt-image-2",
            "knowledge_anchor": "开头先给判断，再补背景",
            "observable_teaching_detail": "画面左侧是结论牌，右侧是背景资料被延后递出",
            "instant_takeaway": "先让观众判断值不值得看，再补背景",
            "case_visual_map": [
                {"screen_evidence": "先给判断", "visible_detail": "顾客先看到明确的结论牌"},
                {"screen_evidence": "再补背景", "visible_detail": "服务员把背景资料放在后面递出"},
            ],
        }
        code, report = run_audit(deck(base_slide(visual_plan)))
        self.assertEqual(report["errors"], [])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
