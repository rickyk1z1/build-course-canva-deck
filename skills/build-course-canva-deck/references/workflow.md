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
    "design_profile": {
      "profile_source": "default-bundled-template | chosen-canva-template",
      "template_design_id": "DAHM5fsVEB0",
      "reference_contact_sheet": "assets/template-reference/template-21-pages-contact-sheet.jpg",
      "colors": {
        "dark": "#1C1C1C",
        "accent": "#FC6736",
        "light": "#F2EBE3",
        "neutral": "#FFFFFF",
        "muted": "#6C6661"
      },
      "fonts": {
        "title": "站酷高端黑",
        "secondary": "思源黑体 CN Light",
        "body": "字由点字烈黑",
        "decorative": "思源黑体 CN Bold"
      },
      "layout_rhythm": {
        "required_modes": ["light", "dark", "accent"],
        "max_consecutive_same_mode": 4,
        "max_dominant_family_ratio": 0.6
      }
    },
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
        "visual_applicability": "required",
        "imagegen_priority": "preferred",
        "imagegen_bypass_reason": "",
        "generation_route": "",
        "prompt_brief": "",
        "text_area_ratio": 0.4,
        "labels_as_slide_text": true,
        "exception_reason": "",
        "template_reference": {
          "page": 7,
          "layout_features": ["right-side centered visual anchor", "narrow left text column", "high-contrast dark field"],
          "adaptation": "narrow or wrap the learner-facing text first, then keep the template's visual anchor position and scale"
        },
        "template_motif": {
          "kind": "hero-right",
          "canva_asset_id": "Canva native asset id inserted after import",
          "local_preview_path": "required local raster preview used in the PPTX before Canva import",
          "reference_template_page": 1,
          "placement_basis": "follow the template's large right-side centered motif; narrow the text column and wrap the title instead of pushing the motif into a corner",
          "replaces_modules": ["cover-orange", "cover-focus"],
          "local_ppt_layout": {
            "coordinate_space": "1280x720",
            "text_column_width": 560,
            "title_break_strategy": "manual or deterministic wrap before PPT generation",
            "motif_box": {"left": 680, "top": 60, "width": 600, "height": 600},
            "native_canva_scale": 1.5
          },
          "canva_replacement": {
            "mode": "replace_placeholder",
            "match_strategy": "after Canva import, match the local preview proxy by page index and motif_box position, then update_fill to canva_asset_id",
            "fallback": "delete the local preview proxy and insert the native Canva asset at the same scaled box; never overlay both"
          },
          "collision_check": {
            "status": "clear",
            "notes": "local PPT preview shows the motif does not cover title, explanation, footer, or page number"
          }
        }
      },
      "source_node_ids": ["n0001"],
      "added_content": [],
      "scope_check": {"status": "within-branch", "branch_node_id": "n0001"}
    }
  ]
}
```

Allowed layouts: `cover`, `roadmap`, `light`, `dark`, `orange`/`accent`, `image-left`, `image-right`, `image-left-dark`, `image-right-dark`, `image-left-orange`/`image-left-accent`, `image-right-orange`/`image-right-accent`, `comparison`, `table`, `summary`.

`visual_plan.template_motif` is not cover-specific. Use it on any slide that reuses a template-native Canva element or a distinctive template motif. The motif must be planned before PPTX generation:

- include a `local_preview_path` so the generated local PPTX/contact sheet previews the final intended position and scale;
- include `local_ppt_layout` with text column width, title/wrapping decision, and a 1280x720 `motif_box`;
- treat `canva_asset_id` as the native asset to insert after Canva import at the scaled coordinates, not as a reason to skip local PPT review;
- set `canva_replacement.mode` to `replace_placeholder`: the local preview proxy must be replaced with the native Canva asset, or deleted before inserting the native asset at the same box. It must never remain underneath an overlaid native asset;
- list the structural modules or regions the motif replaces. If the motif needs more space, narrow or move text modules in the PPT layout instead of drifting the motif into an arbitrary corner.

Every slide must include `visual_plan.template_reference`, even when it does not use a native Canva motif:

- `page` or `pages`: the chosen template page, template page family, or bundled reference layout being adapted;
- `layout_features`: at least two visible features inherited from that reference, such as title scale, image crop, color-field split, centered visual anchor, asymmetric grid, side rail, or caption position;
- `adaptation`: how the course text and visual evidence were fitted into that composition. If the text is long, describe the text-area change, title wrapping, slide split, or alternate template family chosen before building the PPTX.

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
- Every knowledge branch that can use a case image or demonstration image should have one. Prefer `gpt-image-2` for rich bitmap case illustrations; use built-in `imagegen` only when GPT Image 2 is unavailable or explicitly requested. If the visual is a simple relationship, process, table, or label-heavy diagram, use editable PPTX/Canva shapes and record why raster generation was bypassed.
- On illustrated knowledge pages, keep text around 40% and visual content around 50%; split content into more slides when the text cannot fit cleanly.
- Every source screenshot or generated diagram must have learner-facing interpretation in the same slide's caption or nearby body text.
- Generated illustrations must be concrete teaching scenes or examples. Reject abstract geometric placeholders, generic icons, or decorative workflow-looking images that do not make the slide's knowledge point clearer.

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
