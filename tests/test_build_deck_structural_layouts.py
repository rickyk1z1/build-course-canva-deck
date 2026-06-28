import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "skills/build-course-canva-deck/scripts/build_deck.mjs"


class StructuralLayoutBuildTests(unittest.TestCase):
    def test_builds_overview_section_cover_and_summary_layouts(self):
        if not shutil.which("node"):
            self.skipTest("node is not available")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec_path = tmp_path / "deck-spec.json"
            out_path = tmp_path / "deck.pptx"
            workspace = tmp_path / "workspace"
            spec_path.write_text(
                json.dumps(
                    {
                        "course": {
                            "design_profile": {},
                            "outline_mode": "sparse",
                        },
                        "slides": [
                            {
                                "number": 1,
                                "layout": "lesson-overview",
                                "section": "测试课程",
                                "title": "课程总领",
                                "screen": {
                                    "explanation": "先建立整节课的结构，再进入每个章节。",
                                    "bullets": ["第一节", "第二节"],
                                    "caption": "总领页负责让学员知道接下来怎么走。",
                                    "blocks": [],
                                },
                            },
                            {
                                "number": 2,
                                "layout": "section-cover",
                                "section": "测试课程",
                                "section_number": 1,
                                "title": "第一节",
                                "screen": {
                                    "explanation": "这一节先解决第一个核心问题。",
                                    "bullets": ["先判断问题", "再进入方法"],
                                    "caption": "",
                                    "blocks": [],
                                },
                            },
                            {
                                "number": 3,
                                "layout": "summary",
                                "section": "测试课程",
                                "title": "总结",
                                "screen": {
                                    "explanation": "最后把本课的核心结论收束成可复述的句子。",
                                    "bullets": ["先总领", "分章节展开", "最后总结"],
                                    "caption": "",
                                    "blocks": [],
                                },
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "node",
                    str(BUILD),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(out_path),
                    "--workspace",
                    str(workspace),
                    "--asset-dir",
                    str(tmp_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out_path.exists())
            self.assertEqual(len(list((workspace / "preview").glob("slide-*.png"))), 3)
            with zipfile.ZipFile(out_path) as pptx:
                slide_xml = "\n".join(
                    pptx.read(name).decode("utf-8", errors="replace")
                    for name in pptx.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
            self.assertNotIn("线上录课课件", slide_xml)

    def test_roadmap_layout_is_renderable_editable_diagram_without_extra_pattern(self):
        if not shutil.which("node"):
            self.skipTest("node is not available")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec_path = tmp_path / "deck-spec.json"
            out_path = tmp_path / "roadmap.pptx"
            workspace = tmp_path / "workspace"
            spec_path.write_text(
                json.dumps(
                    {
                        "course": {
                            "design_profile": {},
                            "outline_mode": "sparse",
                        },
                        "slides": [
                            {
                                "number": 1,
                                "layout": "roadmap",
                                "section": "测试课程",
                                "title": "按顺序判断包装重点",
                                "framework_progress_label": "包装判断",
                                "screen": {
                                    "explanation": "这页用路线图把判断顺序变成可复述的步骤。",
                                    "bullets": ["先看目标", "再看素材", "最后定风格"],
                                    "caption": "",
                                    "blocks": [],
                                    "teaching_expansion": {
                                        "mode_handling": "sparse-vertical-expansion",
                                        "learner_takeaway": "学员能按顺序判断包装重点。",
                                        "source_based_explanation": "把判断顺序拆成三个可执行步骤。",
                                        "example_or_judgment_cue": "先看目标,再看素材,最后定风格。",
                                        "display_priority": ["先看目标", "再看素材", "最后定风格"],
                                        "internal_only": [],
                                    },
                                },
                                "visual_plan": {
                                    "asset_type": "editable-diagram",
                                    "integration": "knowledge-page",
                                    "source_node_id": "n1",
                                    "labels_as_slide_text": True,
                                    "generated_case_bypass_reason": "本页教学对象是判断顺序,可编辑路线图比生成案例图更清楚。",
                                },
                                "visuals": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "node",
                    str(BUILD),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(out_path),
                    "--workspace",
                    str(workspace),
                    "--asset-dir",
                    str(tmp_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(out_path) as pptx:
                slide_xml = "\n".join(
                    pptx.read(name).decode("utf-8", errors="replace")
                    for name in pptx.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
            self.assertIn("flow-node-1-0", slide_xml)


if __name__ == "__main__":
    unittest.main()
