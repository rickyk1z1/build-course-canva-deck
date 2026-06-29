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
            {"id": "n1", "text": "第一节", "parent_id": "n0", "order": 2, "include": True},
            {"id": "n2", "text": "第一节内容", "parent_id": "n1", "order": 3, "include": True},
            {"id": "n3", "text": "第二节", "parent_id": "n0", "order": 4, "include": True},
            {"id": "n4", "text": "第二节内容", "parent_id": "n3", "order": 5, "include": True},
        ],
        "images": [],
    }


def treatment(node_id, evidence, status="preserved"):
    return {
        "source_node_id": node_id,
        "screen_evidence": evidence,
        "coverage_status": status,
    }


def slide(
    number,
    layout,
    title,
    node_ids=None,
    evidence=None,
    branch="n0",
    bullets=None,
    section_preview_items=None,
    framework_progress_label=None,
):
    evidence = evidence or title
    node_ids = node_ids or []
    result = {
        "number": number,
        "layout": layout,
        "title": title,
        "section": "测试课",
        "screen": {
            "explanation": evidence,
            "bullets": bullets or ["可读要点"],
            "caption": "",
            "blocks": [],
            "teaching_expansion": {
                "mode_handling": "detailed-clarification",
                "learner_takeaway": evidence,
                "source_based_explanation": evidence,
                "example_or_judgment_cue": "结构测试夹具。",
                "display_priority": [evidence],
                "internal_only": [],
            },
        },
        "source_node_ids": node_ids,
        "source_node_treatments": [
            treatment(
                node_id,
                evidence if index == 0 else title,
                "section-heading" if layout == "section-cover" else "preserved",
            )
            for index, node_id in enumerate(node_ids)
        ],
        "scope_check": {"status": "within-branch", "branch_node_id": branch},
        "visual_plan": {
            "asset_type": "text-only-exception",
            "integration": "knowledge-page",
            "source_node_id": node_ids[0] if node_ids else "n0",
            "labels_as_slide_text": True,
            "text_only_exception_reason": f"{title} 的结构测试页需要保留 {evidence} 的关系和顺序，文字清单比生成案例图更清楚。",
        },
    }
    if framework_progress_label is not None:
        result["framework_progress_label"] = framework_progress_label
    elif layout not in {"cover", "lesson-overview", "section-cover", "summary"}:
        result["framework_progress_label"] = "第一节"
    if section_preview_items is not None:
        result["section_preview_items"] = section_preview_items
    return result


def deck(slides):
    return {
        "course": {
            "outline_mode": "detailed",
            "curriculum_context": {
                "system_name": "自媒体与视频剪辑课程体系",
                "module": "测试模块",
                "course_role": "测试结构",
            },
        },
        "slides": slides,
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


class OutlineStructureAuditTests(unittest.TestCase):
    def test_rejects_flat_deck_without_overview_section_covers_and_final_summary(self):
        code, report = run_audit(
            deck(
                [
                    slide(1, "cover", "课程标题", ["n0"], "课程标题"),
                    slide(2, "light", "第一节内容", ["n1", "n2"], "第一节", branch="n1"),
                    slide(
                        3,
                        "light",
                        "第二节内容",
                        ["n3", "n4"],
                        "第二节",
                        branch="n3",
                        framework_progress_label="第二节",
                    ),
                ]
            )
        )
        self.assertNotEqual(code, 0)
        joined = "\n".join(report["errors"])
        self.assertIn("first non-cover slide must use lesson-overview layout", joined)
        self.assertIn("missing section-cover for approved chapter node n1", joined)
        self.assertIn("final slide must use summary layout", joined)

    def test_rejects_static_footer_and_requires_current_second_level_progress(self):
        slides = [
            slide(1, "lesson-overview", "课程总领", ["n0"], "课程标题"),
            slide(
                2,
                "section-cover",
                "第一节",
                ["n1"],
                "第一节",
                branch="n1",
                bullets=["第一节内容"],
                section_preview_items=[
                    {"source_node_id": "n2", "screen_evidence": "第一节内容"}
                ],
            ),
            slide(
                3,
                "light",
                "第一节内容",
                ["n2"],
                "第一节内容",
                branch="n1",
                framework_progress_label="线上录课课件",
            ),
            slide(
                4,
                "section-cover",
                "第二节",
                ["n3"],
                "第二节",
                branch="n3",
                bullets=["第二节内容"],
                section_preview_items=[
                    {"source_node_id": "n4", "screen_evidence": "第二节内容"}
                ],
            ),
            slide(
                5,
                "light",
                "第二节内容",
                ["n4"],
                "第二节内容",
                branch="n3",
                framework_progress_label="第二节",
            ),
            slide(6, "summary", "总结", [], "按章节回收本课重点"),
        ]
        code, report = run_audit(deck(slides))
        self.assertNotEqual(code, 0)
        joined = "\n".join(report["errors"])
        self.assertIn("slide 3 framework_progress_label must not be the static courseware footer", joined)
        self.assertIn("slide 3 framework_progress_label must be current approved chapter: 第一节", joined)

    def test_accepts_overview_then_each_section_cover_then_content_then_summary(self):
        slides = [
            slide(1, "lesson-overview", "课程总领", ["n0"], "课程标题"),
            slide(
                2,
                "section-cover",
                "第一节",
                ["n1"],
                "第一节",
                branch="n1",
                bullets=["第一节内容"],
                section_preview_items=[
                    {"source_node_id": "n2", "screen_evidence": "第一节内容"}
                ],
            ),
            slide(3, "light", "第一节内容", ["n2"], "第一节内容", branch="n1"),
            slide(
                4,
                "section-cover",
                "第二节",
                ["n3"],
                "第二节",
                branch="n3",
                bullets=["第二节内容"],
                section_preview_items=[
                    {"source_node_id": "n4", "screen_evidence": "第二节内容"}
                ],
            ),
            slide(
                5,
                "light",
                "第二节内容",
                ["n4"],
                "第二节内容",
                branch="n3",
                framework_progress_label="第二节",
            ),
            slide(6, "summary", "总结", [], "按章节回收本课重点"),
        ]
        code, report = run_audit(deck(slides))
        self.assertEqual(report["errors"], [])
        self.assertEqual(code, 0)

    def test_rejects_section_cover_without_third_level_preview_items(self):
        slides = [
            slide(1, "lesson-overview", "课程总领", ["n0"], "课程标题"),
            slide(
                2,
                "section-cover",
                "第一节",
                ["n1"],
                "第一节",
                branch="n1",
                bullets=["这一节先解决第一个核心问题"],
            ),
            slide(3, "light", "第一节内容", ["n2"], "第一节内容", branch="n1"),
            slide(
                4,
                "section-cover",
                "第二节",
                ["n3"],
                "第二节",
                branch="n3",
                bullets=["第二节内容"],
                section_preview_items=[
                    {"source_node_id": "n4", "screen_evidence": "第二节内容"}
                ],
            ),
            slide(
                5,
                "light",
                "第二节内容",
                ["n4"],
                "第二节内容",
                branch="n3",
                framework_progress_label="第二节",
            ),
            slide(6, "summary", "总结", [], "按章节回收本课重点"),
        ]
        code, report = run_audit(deck(slides))
        self.assertNotEqual(code, 0)
        self.assertIn(
            "slide 2 section-cover must preview this section's immediate child source headings",
            "\n".join(report["errors"]),
        )


if __name__ == "__main__":
    unittest.main()
