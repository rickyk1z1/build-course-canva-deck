# End-to-end workflow

## Output workspace

Keep scratch files outside the user's project. Put durable deliverables in `<source-parent>/<course-stem>-课件产物/` unless the user chooses another location:

- `<course-stem>-屏显稿.md`
- `<course-stem>-录课讲稿.md`
- `<course-stem>-Canva导入稿.pptx`
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
6. Record the explicit reply in the source map.

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
    "explicit_exclusions": []
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
- Give each knowledge slide one explanation paragraph and usually 3-5 concrete points.
- Keep a page readable without narration; use notes only for delivery rhythm.
- Use embedded source visuals before generating replacements.
- Generate illustrations without baked-in text. Add labels as editable slide text.
- Use an image as 30-45% of a knowledge page, not as the whole lesson.

## Build and delivery

1. Run the content audit before building.
2. Build the PPTX and export per-slide PNG and layout JSON.
3. Inspect the montage and every flagged slide at full size.
4. Run the final audit against both `deck-spec.json` and the PPTX XML.
5. Import the PPTX into Canva as a new presentation.
6. Verify page count, all rich text, font mapping, images, and page previews.
7. Show one final complete review to the user.
8. Commit Canva draft edits only after explicit approval.
9. Re-read the saved design and return its edit link.
