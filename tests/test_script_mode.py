import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "skills/build-course-canva-deck/scripts/audit_deck.py"
EXTRACT = ROOT / "skills/build-course-canva-deck/scripts/extract_source.py"
VALIDATE = ROOT / "skills/build-course-canva-deck/scripts/validate_source_map.py"


def source_map():
    return {
        "authoritative": True,
        "authoritative_source": "script.txt",
        "outline_mode": "script",
        "mode_declared_by_user": True,
        "nodes": [
            {"id": "n0", "text": "视觉包装判断", "order": 1, "include": True},
            {"id": "n1", "text": "先判断再制作", "parent_id": "n0", "order": 2, "include": True},
            {"id": "n2", "text": "判断服务重点", "parent_id": "n1", "order": 3, "include": True},
            {"id": "n3", "text": "把判断变成画面", "parent_id": "n1", "order": 4, "include": True},
        ],
        "images": [],
    }


def treatment(node_id, evidence, status="preserved"):
    return {
        "source_node_id": node_id,
        "screen_evidence": evidence,
        "coverage_status": status,
    }


def knowledge_slide(mode_handling="script-distillation", title="先判断服务重点，再把判断变成画面"):
    return {
        "number": 3,
        "layout": "light",
        "title": title,
        "framework_progress_label": "先判断再制作",
        "screen": {
            "explanation": "完整讲稿里的口播要被提炼成学员能直接使用的判断：先判断画面服务什么，再决定怎么做。",
            "bullets": ["判断服务重点", "把判断变成画面"],
            "caption": "",
            "blocks": [],
            "teaching_expansion": {
                "mode_handling": mode_handling,
                "learner_takeaway": "先判断画面服务什么，再决定怎么做。",
                "source_based_explanation": "完整讲稿里的口播要被提炼成学员能直接使用的判断。",
                "example_or_judgment_cue": "删掉口播过渡，只保留可上屏的判断句。",
                "display_priority": ["判断服务重点", "把判断变成画面"],
                "internal_only": ["讲稿整理"],
            },
        },
        "source_node_ids": ["n2", "n3"],
        "source_node_treatments": [
            treatment("n2", "判断服务重点"),
            treatment("n3", "把判断变成画面"),
        ],
        "scope_check": {"status": "within-branch", "branch_node_id": "n1"},
        "visual_plan": {
            "asset_type": "text-only-exception",
            "integration": "knowledge-page",
            "source_node_id": "n2",
            "generated_case_bypass_reason": "本页测试讲稿提炼规则，文字判断比案例图更直接。",
        },
        "visuals": [],
    }


def deck(slide):
    return {
        "course": {
            "outline_mode": "script",
            "curriculum_context": {
                "system_name": "自媒体与视频剪辑课程体系",
                "module": "测试模块",
                "course_role": "测试讲稿输入模式",
            },
            "image_generation_tasks": [],
        },
        "slides": [
            {
                "number": 1,
                "layout": "lesson-overview",
                "title": "课程总领",
                "screen": {"explanation": "视觉包装判断", "bullets": ["先判断再制作"], "caption": "", "blocks": []},
                "source_node_ids": ["n0"],
                "source_node_treatments": [treatment("n0", "视觉包装判断")],
            },
            {
                "number": 2,
                "layout": "section-cover",
                "title": "先判断再制作",
                "screen": {"explanation": "本节预告。", "bullets": ["判断服务重点", "把判断变成画面"], "caption": "", "blocks": []},
                "source_node_ids": ["n1"],
                "source_node_treatments": [treatment("n1", "先判断再制作", "section-heading")],
                "section_preview_items": [
                    {"source_node_id": "n2", "screen_evidence": "判断服务重点"},
                    {"source_node_id": "n3", "screen_evidence": "把判断变成画面"},
                ],
            },
            slide,
            {
                "number": 4,
                "layout": "summary",
                "title": "总结",
                "screen": {"explanation": "回收本课重点。", "bullets": [], "caption": "", "blocks": []},
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


class ScriptModeTests(unittest.TestCase):
    def test_extract_source_records_script_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "script.txt"
            output_path = tmp_path / "source.json"
            input_path.write_text("先讲判断。\n再讲例子。", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXTRACT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--source-kind",
                    "script",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_kind"], "script")

    def test_extract_source_zones_script_sections_by_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "script.md"
            output_path = tmp_path / "source.json"
            input_path.write_text(
                "\n".join(
                    [
                        "# 录播讲稿：第一节课",
                        "## 讲稿生成说明",
                        "- 课程目标：内部背景",
                        "## 讲课结构",
                        "1. 开场",
                        "## 完整录播讲稿",
                        "### 片段 1：开场",
                        "今天这一课我们先学时间线。",
                        "## 案例设计说明",
                        "- 口播粗剪主案例：直接做出来",
                        "## 案例准备清单",
                        "| 位置 | 知识点 |",
                        "| --- | --- |",
                        "| 片段 1 | 时间线 |",
                        "## 录制提示",
                        "- 录制时用鼠标框选四个区域",
                    ]
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXTRACT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--source-kind",
                    "script",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            roles = {node["text"]: node["source_role"] for node in payload["nodes"]}
            includes = {node["text"]: node["include"] for node in payload["nodes"]}
            confidence = {node["text"]: node["source_role_confidence"] for node in payload["nodes"]}
            self.assertEqual(roles["课程目标：内部背景"], "metadata")
            self.assertFalse(includes["课程目标：内部背景"])
            self.assertEqual(confidence["课程目标：内部背景"], "explicit")
            self.assertEqual(roles["开场"], "structure_seed")
            self.assertFalse(includes["开场"])
            self.assertEqual(roles["完整录播讲稿"], "script_container")
            self.assertFalse(includes["完整录播讲稿"])
            self.assertEqual(roles["今天这一课我们先学时间线。"], "learner_content")
            self.assertTrue(includes["今天这一课我们先学时间线。"])
            self.assertEqual(roles["口播粗剪主案例：直接做出来"], "visual_case_brief")
            self.assertFalse(includes["口播粗剪主案例：直接做出来"])
            self.assertEqual(roles["录制时用鼠标框选四个区域"], "recording_note")
            self.assertFalse(includes["录制时用鼠标框选四个区域"])

    def test_extract_source_uses_content_heuristics_when_script_has_no_clean_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "script.txt"
            output_path = tmp_path / "source.json"
            input_path.write_text(
                "\n".join(
                    [
                        "课程目标：让学员理解时间线。",
                        "1. 开场：先建立时间线意识。",
                        "今天这一课我们先学时间线，不是先学特效。",
                        "案例处理方式：直接做出上层截图盖住人物。",
                        "录制时用鼠标框选四个区域。",
                    ]
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXTRACT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--source-kind",
                    "script",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            roles = {node["text"]: node["source_role"] for node in payload["nodes"]}
            includes = {node["text"]: node["include"] for node in payload["nodes"]}
            confidence = {node["text"]: node["source_role_confidence"] for node in payload["nodes"]}
            self.assertEqual(roles["课程目标：让学员理解时间线。"], "metadata")
            self.assertEqual(roles["开场：先建立时间线意识。"], "structure_seed")
            self.assertEqual(roles["今天这一课我们先学时间线，不是先学特效。"], "learner_content")
            self.assertTrue(includes["今天这一课我们先学时间线，不是先学特效。"])
            self.assertEqual(confidence["今天这一课我们先学时间线，不是先学特效。"], "default")
            self.assertTrue(payload["warnings"])
            self.assertEqual(roles["案例处理方式：直接做出上层截图盖住人物。"], "visual_case_brief")
            self.assertFalse(includes["案例处理方式：直接做出上层截图盖住人物。"])
            self.assertEqual(roles["录制时用鼠标框选四个区域。"], "recording_note")
            self.assertFalse(includes["录制时用鼠标框选四个区域。"])

    def test_validate_source_map_accepts_script_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.json"
            source_path.write_text(json.dumps(source_map(), ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), str(source_path), "--mode", "script", "--write", "--require-mode"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["outline_mode"], "script")
            self.assertTrue(payload["mode_declared_by_user"])

    def test_validate_source_map_rejects_included_non_learner_script_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = source_map()
            payload["source_kind"] = "script"
            payload["nodes"][0]["source_role"] = "recording_note"
            payload["nodes"][0]["include"] = True
            source_path = Path(tmp) / "source.json"
            source_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), str(source_path), "--require-mode"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only learner_content nodes should be source coverage obligations", result.stdout)

    def test_audit_accepts_script_distillation_mode(self):
        code, report = run_audit(deck(knowledge_slide()))
        self.assertEqual(report["errors"], [])
        self.assertEqual(code, 0)

    def test_audit_rejects_script_slide_with_sparse_mode_handling(self):
        code, report = run_audit(deck(knowledge_slide(mode_handling="sparse-vertical-expansion")))
        self.assertNotEqual(code, 0)
        self.assertIn(
            "slide 3 screen.teaching_expansion.mode_handling must be script-distillation",
            "\n".join(report["errors"]),
        )

    def test_audit_rejects_learner_facing_script_process_copy(self):
        code, report = run_audit(deck(knowledge_slide(title="根据讲稿整理这一段讲的是先判断再制作")))
        self.assertNotEqual(code, 0)
        joined = "\n".join(report["errors"])
        self.assertIn("contains forbidden learner-facing text", joined)


if __name__ == "__main__":
    unittest.main()
