import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "skills/build-course-canva-deck/scripts/audit_deck.py"


def wrapper_source_map():
    """A source tree whose real chapters sit below a wrapper level.

    root(n0) is the lesson title. n1 is a framing/wrapper node (root child)
    that is NOT a chapter. The real teaching chapters are n2 and n5, both
    children of the wrapper n1 — i.e. depth 2, not root children.
    """
    return {
        "outline_mode": "detailed",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": "n0", "text": "你的视频为何留不住人", "order": 1, "include": True},
            {"id": "n1", "text": "课程框架问题", "parent_id": "n0", "order": 2, "include": True},
            {"id": "n2", "text": "选题方向规划", "parent_id": "n1", "order": 3, "include": True},
            {"id": "n3", "text": "选题方法", "parent_id": "n2", "order": 4, "include": True},
            {"id": "n4", "text": "选题误区", "parent_id": "n2", "order": 5, "include": True},
            {"id": "n5", "text": "内容结构", "parent_id": "n1", "order": 6, "include": True},
            {"id": "n6", "text": "开头钩子", "parent_id": "n5", "order": 7, "include": True},
            {"id": "n7", "text": "中段推进", "parent_id": "n5", "order": 8, "include": True},
        ],
        "images": [],
    }


def treatment(node_id, evidence, status="preserved"):
    return {
        "source_node_id": node_id,
        "screen_evidence": evidence,
        "coverage_status": status,
    }


def knowledge_slide(number, title, node_ids, branch, framework_progress_label, evidence=None):
    evidence = evidence or title
    return {
        "number": number,
        "layout": "light",
        "title": title,
        "section": "测试课",
        "framework_progress_label": framework_progress_label,
        "screen": {
            "explanation": evidence,
            "bullets": ["可读要点"],
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
            treatment(node_id, evidence if index == 0 else title)
            for index, node_id in enumerate(node_ids)
        ],
        "scope_check": {"status": "within-branch", "branch_node_id": branch},
        "visual_plan": {
            "asset_type": "text-only-exception",
            "integration": "knowledge-page",
            "source_node_id": node_ids[0],
            "labels_as_slide_text": True,
            "text_only_exception_reason": "结构测试夹具不验证案例图质量。",
        },
    }


def section_cover(number, title, section_id, preview):
    return {
        "number": number,
        "layout": "section-cover",
        "title": title,
        "section": "测试课",
        "screen": {
            "explanation": "本节预告。",
            "bullets": [item["screen_evidence"] for item in preview],
            "caption": "",
            "blocks": [],
        },
        "source_node_ids": [section_id],
        "source_node_treatments": [treatment(section_id, title, "section-heading")],
        "section_preview_items": preview,
    }


def overview(node_ids):
    return {
        "number": 1,
        "layout": "lesson-overview",
        "title": "课程总领",
        "screen": {
            "explanation": "你的视频为何留不住人？本课围绕课程框架问题展开。",
            "bullets": ["选题方向规划", "内容结构"],
            "caption": "",
            "blocks": [],
        },
        "source_node_ids": node_ids,
        "source_node_treatments": [
            treatment(node_id, "你的视频为何留不住人" if node_id == "n0" else "课程框架问题")
            for node_id in node_ids
        ],
    }


def summary():
    return {
        "number": 99,
        "layout": "summary",
        "title": "总结",
        "screen": {"explanation": "按章节回收本课重点。", "bullets": [], "caption": "", "blocks": []},
        "source_node_ids": [],
        "source_node_treatments": [],
    }


def deck(slides, chapter_spine=None):
    course = {
        "outline_mode": "detailed",
        "curriculum_context": {
            "system_name": "自媒体与视频剪辑课程体系",
            "module": "测试模块",
            "course_role": "测试章节识别",
        },
    }
    if chapter_spine is not None:
        course["chapter_spine"] = chapter_spine
    return {"course": course, "slides": slides}


def run_audit(deck_spec, source):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        deck_path = tmp_path / "deck.json"
        source_path = tmp_path / "source.json"
        report_path = tmp_path / "report.json"
        deck_path.write_text(json.dumps(deck_spec, ensure_ascii=False), encoding="utf-8")
        source_path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
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


def renumber(slides):
    for index, slide in enumerate(slides, start=1):
        slide["number"] = index
    return slides


class ChapterSpineAuditTests(unittest.TestCase):
    def test_accepts_deep_chapter_spine_below_a_wrapper_node(self):
        # Chapters are n2 and n5 (depth 2), wrapper n1 + root n0 covered on overview.
        slides = renumber([
            overview(["n0", "n1"]),
            section_cover(0, "选题方向规划", "n2", [
                {"source_node_id": "n3", "screen_evidence": "选题方法"},
                {"source_node_id": "n4", "screen_evidence": "选题误区"},
            ]),
            knowledge_slide(0, "选题方法", ["n3"], "n2", "选题方向规划"),
            knowledge_slide(0, "选题误区", ["n4"], "n2", "选题方向规划"),
            section_cover(0, "内容结构", "n5", [
                {"source_node_id": "n6", "screen_evidence": "开头钩子"},
                {"source_node_id": "n7", "screen_evidence": "中段推进"},
            ]),
            knowledge_slide(0, "开头钩子", ["n6"], "n5", "内容结构"),
            knowledge_slide(0, "中段推进", ["n7"], "n5", "内容结构"),
            summary(),
        ])
        code, report = run_audit(
            deck(slides, chapter_spine=["n2", "n5"]),
            wrapper_source_map(),
        )
        self.assertEqual(report["errors"], [])
        self.assertEqual(code, 0)

    def test_rejects_overlapping_chapter_spine(self):
        # n2 is an ancestor of n3; selecting both is an overlap error.
        slides = renumber([overview(["n0", "n1"]), summary()])
        code, report = run_audit(
            deck(slides, chapter_spine=["n2", "n3"]),
            wrapper_source_map(),
        )
        self.assertNotEqual(code, 0)
        self.assertIn(
            "course.chapter_spine contains overlapping chapters: n2 is an ancestor of n3",
            "\n".join(report["errors"]),
        )

    def test_rejects_chapter_spine_out_of_source_order(self):
        slides = renumber([overview(["n0", "n1"]), summary()])
        code, report = run_audit(
            deck(slides, chapter_spine=["n5", "n2"]),
            wrapper_source_map(),
        )
        self.assertNotEqual(code, 0)
        self.assertIn(
            "course.chapter_spine must follow source order",
            "\n".join(report["errors"]),
        )

    def test_rejects_chapter_spine_with_unknown_node(self):
        slides = renumber([overview(["n0", "n1"]), summary()])
        code, report = run_audit(
            deck(slides, chapter_spine=["n2", "n999"]),
            wrapper_source_map(),
        )
        self.assertNotEqual(code, 0)
        self.assertIn(
            "course.chapter_spine contains unknown source nodes: n999",
            "\n".join(report["errors"]),
        )

    def test_fallback_to_root_children_when_chapter_spine_absent(self):
        # No chapter_spine field -> audit falls back to root children (n1 only).
        # The wrapper n1 then must have its own section-cover; here we omit it
        # so the fallback path is observable via the missing-section-cover error.
        slides = renumber([overview(["n0"]), summary()])
        code, report = run_audit(
            deck(slides, chapter_spine=None),
            wrapper_source_map(),
        )
        self.assertNotEqual(code, 0)
        self.assertIn(
            "missing section-cover for approved chapter node n1",
            "\n".join(report["errors"]),
        )


if __name__ == "__main__":
    unittest.main()
