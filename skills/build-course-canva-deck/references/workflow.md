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
    "template_page_mapping": [
      {
        "slide_number": 1,
        "template_reference": "page 1 / cover hero-right",
        "layout_family": "cover",
        "native_motif": "hero-right grainy star previewed locally and replaced in Canva",
        "local_ppt_decision": "narrow title column before PPT generation so the motif has a stable right-side anchor"
      }
    ],
    "image_generation_review": {
      "status": "completed",
      "source_case_priority": "source-first",
      "source_case_image_count": 8,
      "reused_source_slide_numbers": [2, 4, 5, 9],
      "generated_after_source_review": true,
      "generated_slide_numbers": [6, 14],
      "candidates_considered": 4,
      "rationale": "source case images are used first where they directly teach the node; generated cases only supplement text-heavy or abstract pages"
    },
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
        "layout_variant": "center-anchor",
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

For decks longer than 12 pages, every normal knowledge slide must also set `visual_plan.layout_variant` before local PPT generation. This is the actual composition family the builder must render, not a retrospective description. Use concrete values such as `split-image`, `poster-panel`, `wide-case-band`, `center-anchor`, `gallery-strip`, `close-reading`, `index-grid`, `two-panel`, or another short stable family name. The full deck must distribute these variants across the selected template pages so the contact sheet does not collapse into repeated two-column pages.

For decks longer than 12 pages, build a template-page mapping table before PPT generation. The mapping must spread slides across multiple reference pages/page families from the selected template. Do not map most normal knowledge pages to one generic two-column reference. Automated QA rejects long decks with too few distinct template references, a dominant reference family, or long runs of the same reference.

For decks longer than 12 pages, `course.template_page_mapping` is required before local PPT generation. It must list every slide, the chosen template reference page/page family, the layout family, any native motif planned for that slide, and the local PPT decision that makes the chosen template composition work. Do not build the local PPT until this table exists.

For decks longer than 12 pages, Canva-native template element use is mandatory when the selected template contains reusable native motifs or structural assets. Plan these in `visual_plan.template_motif` before local PPT generation; use local raster preview proxies only to verify position, scale, collision, and contact-sheet rhythm. After Canva import, replace those proxies with the native Canva assets using the recorded `replace_placeholder` route. A long deck that uses only generic PPT shapes/images and no planned native template motif fails QA.

When the source contains enough concrete case images, still run an image-generation review before local PPT generation. Source images remain the first choice for nodes they directly teach. Record this priority explicitly in `course.image_generation_review.source_case_priority: "source-first"` and list `reused_source_slide_numbers`. Only after this source-case pass should text-heavy or abstract pages receive a small number of generated text-free case illustrations. Record `generated_after_source_review: true`; a source-rich long deck with no source reuse record, no generated-image pages, or no completed review fails QA.

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
- Run the image-generation review even when the outline already includes many source case images. Use source images where they directly teach the node, but generate a few extra case illustrations for text-heavy or abstract pages that need a more direct visual bridge.
- Generate illustrations without baked-in text. Add labels as editable slide text.
- Every knowledge branch that can use a case image or demonstration image should have one. Prefer `gpt-image-2` for rich bitmap case illustrations; use built-in `imagegen` only when GPT Image 2 is unavailable or explicitly requested. If the visual is a simple relationship, process, table, or label-heavy diagram, use editable PPTX/Canva shapes and record why raster generation was bypassed.
- On illustrated knowledge pages, keep text around 40% and visual content around 50%; split content into more slides when the text cannot fit cleanly.
- Every source screenshot or generated diagram must have learner-facing interpretation in the same slide's caption or nearby body text.
- Generated illustrations must be concrete teaching scenes or examples. Reject abstract geometric placeholders, generic icons, or decorative workflow-looking images that do not make the slide's knowledge point clearer.

## Build and delivery

1. Run the content audit before building.
2. Build the PPTX and export per-slide PNG and layout JSON.
   - Pass the external scratch directory as `--workspace`.
   - The workspace may provide its own `package.json` and `node_modules`; otherwise `build_deck.mjs` falls back to Codex's bundled primary runtime for `@oai/artifact-tool`.
   - If neither route can resolve `@oai/artifact-tool`, stop and initialize an isolated scratch Node workspace instead of changing the user's project dependencies.
3. Inspect the montage and every flagged slide at full size.
4. Run the final audit against both `deck-spec.json` and the PPTX XML.
5. Run the Canva access preflight described in `canva-delivery.md`; do not import if the active connector cannot access the chosen template/reference route.
6. Import the PPTX into Canva as a new presentation.
7. Verify page count, all rich text, font mapping, images, and page previews.
8. Show one final complete review to the user.
9. Commit Canva draft edits only after explicit approval.
10. Re-read the saved design and return its edit link.
