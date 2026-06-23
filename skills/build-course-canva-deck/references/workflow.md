# End-to-end workflow

## Output workspace

Keep scratch files outside the user's project. Put durable deliverables in `<source-parent>/<course-stem>-课件产物/` unless the user chooses another location:

- `<course-stem>-屏显稿.md`
- `<course-stem>-录课讲稿.md`
- `<course-stem>-Canva导入稿.pptx`
- `curriculum-context.json`
- `课程体系关联说明.md`
- `canva-access.json`
- `assets/`
- `qa-report.json`
- `canva-design.txt`

Never overwrite source files.

## Source intake

1. Enumerate all supplied files and compute hashes.
2. Resolve the authoritative source with the user if more than one could control content.
3. Extract text, hierarchy, order, and embedded images.
4. Render PDFs and inspect their visual hierarchy. A long mind-map PDF often encodes hierarchy through position and connectors that text extraction loses.
5. Ask the user to choose `细纲` or `粗纲`; never recommend or infer a mode.
6. Search the workspace for the overall curriculum map and neighboring lessons. Create `curriculum-context.json`; ask only when the course position cannot be discovered.
7. Record the explicit mode reply in the source map.

Supported deterministic extraction routes:

- `.xmind`: parse `content.json` or legacy `content.xml`, retaining topic order and resources.
- `.opml` / `.mm`: parse XML outline order.
- `.docx`: read paragraph styles and extract `word/media`.
- `.md` / `.txt`: preserve heading and list order.
- `.pdf`: extract page text and images, then visually reconstruct hierarchy.

If scan quality or connectors are unreadable, stop and request a clearer export. Do not guess.

## Content modeling

Create a coverage ledger with one row per included source node:

`source node -> slide number -> treatment -> visual -> status`

Build `deck-spec.json` with this minimum shape:

```json
{
  "course": {
    "title": "课程标题",
    "audience": "零基础自媒体创作者",
    "outline_mode": "detailed",
    "authoritative_source": "/absolute/path",
    "template_design_id": "DAHM5fsVEB0",
    "explicit_exclusions": [],
    "curriculum_context": {
      "system_name": "自媒体与视频剪辑课程体系",
      "module": "模块名称",
      "course_role": "本课负责解决的问题",
      "prerequisite_lessons": [],
      "next_lessons": [],
      "shared_terms": {},
      "neighbor_topics": [],
      "excluded_neighbor_topics": []
    }
  },
  "slides": [
    {
      "number": 1,
      "section": "章节",
      "title": "直接陈述结论的标题",
      "layout": "cover",
      "screen": {
        "explanation": "学员可独立读懂的解释",
        "bullets": [],
        "caption": "",
        "blocks": []
      },
      "speaker_notes": "仅供录课口述",
      "visuals": [],
      "visual_plan": {
        "teaching_role": "what the visual helps the learner understand",
        "source_node_id": "n0001",
        "asset_type": "editable-diagram",
        "integration": "knowledge-page",
        "description": "student-facing visual idea",
        "generation_route": "",
        "prompt_brief": "",
        "labels_as_slide_text": true,
        "exception_reason": ""
      },
      "source_node_ids": ["n0001"],
      "added_content": [],
      "scope_check": {"status": "within-branch", "branch_node_id": "n0001"}
    }
  ]
}
```

Allowed layouts: `cover`, `roadmap`, `light`, `dark`, `orange`, `image-left`, `image-right`, `comparison`, `table`, `summary`.

For sparse mode, every `added_content` item must contain:

```json
{
  "text": "新增教学细则",
  "source_node_id": "n0012",
  "kind": "definition",
  "relevance": "direct",
  "evidence_urls": ["https://official.example/source"]
}
```

Allowed kinds: `definition`, `cause`, `relationship`, `example`, `misconception`, `boundary`. Any item marked `adjacent`, `low`, or `out-of-scope` must be removed.

## Authoring and visuals

- Preserve source order before optimizing narrative transitions.
- Align the deck with the overall curriculum role, prerequisites, shared terminology, and downstream lessons.
- Keep neighboring lessons' primary teaching tasks out of this deck; record a handoff instead of duplicating them.
- Give each knowledge slide one explanation paragraph and usually 3-5 concrete points.
- Keep a page readable without narration; use notes only for delivery rhythm.
- Read `visual-system.md` before visual work.
- Build a visual plan per knowledge slide; do not create a separate learner-facing page that only lists future case images.
- Use embedded source visuals before generating replacements.
- Redraw source visuals only to improve readability; preserve their teaching logic.
- Generate illustrations without baked-in text. Add labels as editable slide text.
- When a knowledge node needs a richer bitmap case image, use the available `imagegen` skill/tool path if it is present in the environment; if the visual is a simple relationship, process, table, or label-heavy diagram, prefer editable PPTX/Canva shapes instead.
- Use an image as 30-45% of a knowledge page, not as the whole lesson.
- Every source screenshot or generated diagram must have learner-facing interpretation in the same slide's caption or nearby body text.

## Build and delivery

1. Run the content audit before building.
2. Build the PPTX and export per-slide PNG and layout JSON.
3. Inspect the montage and every flagged slide at full size.
4. Run the final audit against both `deck-spec.json` and the PPTX XML.
5. Run the Canva access preflight described in `canva-delivery.md`; do not import if the active connector cannot access the chosen template/reference route.
6. Import the PPTX into Canva as a new presentation.
7. Verify page count, all rich text, font mapping, images, and page previews.
8. Show one final complete review to the user.
9. Commit Canva draft edits only after explicit approval.
10. Re-read the saved design and return its edit link.
