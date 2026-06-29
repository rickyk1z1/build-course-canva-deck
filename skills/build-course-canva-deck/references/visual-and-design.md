# Visual and design

This reference covers structural page layouts, per-slide teaching visuals, source-image inclusion and node anchoring, case-image stage execution, generated-image teaching specificity, and template fidelity. Template fidelity here means the template's **colors, fonts, type scale, alignment axes, spacing, density, color mass, and layout language reproduced as editable composition** — not copying Canva's own vector/shape elements and not forcing every element into square blocks. There is no native-element reuse in this skill.

Visuals are teaching devices, not decoration and not a separate production checklist. The final deck shows each case image or example diagram on the knowledge page where it helps the learner understand the concept. Never put production notes ("next we will make these images", "reuse PDF images", "source screenshot") on a learner-facing slide; those belong only in internal files.

## Slide-level visual plan

Before building the PPTX, every normal knowledge slide includes a short `visual_plan` in `deck-spec.json`. It exists so the director can judge the page, not so a worker can fill a form:

```json
{
  "teaching_role": "what this visual helps the learner understand",
  "source_node_id": "n0012",
  "asset_type": "source-image",
  "integration": "knowledge-page",
  "description": "student-facing visual idea, without production wording",
  "labels_as_slide_text": true,
  "source_image_ids": [],
  "generation_route": "",
  "knowledge_anchor": "",
  "observable_teaching_detail": "",
  "instant_takeaway": "",
  "case_visual_map": [],
  "generated_case_bypass_reason": ""
}
```

Allowed `asset_type`: `source-image`, `redrawn-source-image`, `generated-image`, `editable-diagram`, `editable-table`, `text-only-exception`. `integration` must be `knowledge-page`; reject `standalone-stage`, `asset-list`, `production-note`. Every normal knowledge slide needs a teaching visual or a justified text-only exception.

## Per-slide visual asset decision

The visual pass is made per normal knowledge slide in two phases.

Phase 1 is the creative teaching draft. The storyboarder should first ask, "What would make this point clearest to a zero-basis learner?" and propose the strongest learner-facing page: concrete case image, before/after state, wrong/right example, metaphor, workflow artifact, editable relationship diagram, or table. Do not start by asking how to pass the audit, how to minimize generation work, or how to write a bypass reason. The draft may be ambitious; convergence will trim it.

Phase 2 is convergence. The director reviews the draft against source anchoring, generated-image route, empty-space risk, local no-source runs, contact-sheet geometry, and learner readability. Pages that became sparse side-rail/module cards, text-heavy diagrams, or abstract placeholders are revised with GPT Image 2 case images, source/redrawn images, denser editable structures, or split pages. Bypass reasons are accepted only after this creative pass has produced and rejected the stronger visual alternative for a page-specific reason.

Do not decide that "the deck already has enough images" and then leave image-less pages as text-heavy diagrams. For each normal knowledge slide:

1. If the source node has anchored source images, use or redraw those source images first.
2. If no anchored source image exists, default to asking what concrete case image would make the point visible to a zero-basis learner. Use `generated-image` for judgment examples, before/after states, wrong/right choices, metaphors, consequences, user reactions, visible workflow artifacts, or any point where a learner benefits from seeing the situation.
3. Use `editable-diagram` only when the teaching object is the relationship, sequence, hierarchy, axis, or label-heavy structure itself.
4. Use `editable-table` only for factual comparisons, grids, or category matrices that must remain editable.
5. Use `text-only-exception` only when a case image or diagram would make the point less clear; record the concrete bypass reason.

The final visual plan must leave a trace of this decision. For every normal knowledge slide without `source-image` / `redrawn-source-image`, record either a `generated-image` plan plus a matching `course.image_generation_tasks` entry, or a positive `generated_case_bypass_reason` explaining why `editable-diagram`, `editable-table`, or `text-only-exception` teaches better than a generated case image. The reason must be page-specific: it names the current title or visible teaching point and the exact structure (flow, sequence, relationship, axis, table, parameter, shortcut, operation path, etc.) that would become less clear as a generated case image. Generic bypass language such as "本页是连续源节点整理", "可编辑图解比模型场景图更清楚", or "更适配当前信息量" is not valid. The final audit rejects no-source knowledge pages that choose diagram/table/text-only without this reason. It also rejects long local bypass runs: after two consecutive no-source non-generated knowledge pages, the next no-source page must use a generated/source/redrawn case-image treatment or the visual plan must be redesigned. These checks belong to convergence, not to the first creative draft.

## Structural layout system

Use fixed layout families for deck structure and varied layout families for section content:

- `lesson-overview`: exactly one total-introduction page after the optional cover. It previews the lesson problem and the ordered approved chapter nodes from `course.chapter_spine`.
- `section-cover`: exactly one page for each approved chapter node, before its section content. All section-cover pages use the same family so learners feel chapter boundaries. Its small text is an overview of the chapter's direct child headings, not the section's conclusion.
- `summary`: exactly one final page, visually distinct from the overview and section covers, consolidating the course.
- Normal knowledge pages inside a section may vary (`image-*`, `comparison`, `table`, `roadmap`, `light`, `dark`, `orange`, etc.) according to the content relationship.

Do not treat structural pages as interchangeable pacing slides. A section-cover is not a place to teach descendant detail; it names the approved chapter and previews the upcoming child knowledge points with compact agenda cues. Do not write the section's conclusion, takeaway, value promise, dense child list, shortcut string, or any later normal-page title/evidence phrase in the small text. A normal knowledge page must not replace or impersonate the section-cover, and a section-cover must not pre-render normal page content.

## Source image inclusion

Source images are authoritative teaching units, not a moodboard or an optional asset pool. Every non-thumbnail source image extracted from the authoritative source is presumed to be a usable course case image. The source outline already says what each source image teaches: the image's attached XMind/source node is its authoritative teaching anchor. The director and visual storyboarder must read `source_node_id` / `source_path` from `source-map.json` and place the image on a knowledge page covering that node, an ancestor, or a descendant. If a non-thumbnail image lacks this anchor, stop and fix `extract_source.py` or the source extraction; do not visually infer where the image "probably belongs." Within that anchored branch, crop it, pair it with adjacent source images, sequence it, or redraw it if needed. They must not first score whether a source image is "strong enough" to include, and they must not omit it merely because another image seems clearer, because the deck would be shorter without it, or because the image appears visually similar to another source image.

1. Reuse source case images when the source already contains a concrete example.
2. If a source image is low-resolution or too dense, redraw it cleaner without changing the example logic.
3. Use one teachable source case per slide by default. Do not create a raster composite, contact-sheet strip, montage, collage, or stitched panel that shrinks several source images into one unreadable picture. If a single source image is inherently small, sparse, or a narrow UI fragment that cannot optically fill the stage even after sensible cropping, keep it as the main evidence but add learner-facing image interpretation or pair it with a second anchored image when the source relationship supports that. If two source images must appear together, place the original images inside one shared case-image stage with their own `visuals[].source_image_id`; keep learner text short enough that both images are inspectable at recording size. If three or more anchored images are needed, split pages unless the director records a readability exception and the rendered page proves each image remains large enough to inspect.
4. Account for every non-thumbnail source image as `used` or `redrawn` in `course.source_image_coverage`, and reference the original source image id from a normal knowledge page's `visual_plan.source_image_ids`. Audit fails if any non-thumbnail source image is not represented on a knowledge page, if it is placed outside its anchored source branch, or if multiple source images are hidden inside one composite asset.
5. Keep source images inside knowledge pages with a learner-facing caption that says what to inspect, not where the image came from.
6. Only true system artifacts such as mind-map thumbnails, page thumbnails, extraction previews, logos introduced by the export process, or corrupted unreadable files may be omitted. Mark those as `thumbnail_omitted` or `system_omitted`; ordinary case images from the source are not eligible for omission.

## Case image stage execution

Case image pages are `asset_type: source-image`, `redrawn-source-image`, or `generated-image`. They are not ordinary text-image pages. Layout execution starts by reserving the shared case-image stage, then fitting text around it.

1. The case-image stage should normally occupy at least 60% of the slide. 70%+ is allowed when the image is the teaching evidence. This target applies to the designed shared stage, not to forcing a small original image to stretch until it blurs or leaves awkward empty space. Do not invoke "text/visual balance", layout rhythm, or template fidelity to shrink a readable case image, but also do not leave a tiny contain-fit screenshot floating alone inside a huge blank field when image interpretation or a second anchored image would teach better.
2. Default case-image pages render only title and a short caption. When the actual contain-fit footprint of a source image leaves useful empty area in the reserved stage, or when the visual plan requests `supporting-text`, the layout may add compact explanation and up to three learner-facing points inside the same case-image stage. This is not a fixed side-rail rule: depending on the image proportions and real empty area, the supporting text may sit in a side lane, top/bottom band, corner, or other deliberate stage-internal text area. That text must interpret the image, stay outside the image's own panel, and never cover or compete with the case. Move longer explanation to adjacent non-image pages, compress it into a learner-facing caption, or split the teaching point. Do not add an opaque text backing panel on top of the image stage; if the text needs that much support, the page has too much text for a case-image layout.
3. The shared case-image stage is a field, not the image's exact bounding box. Render the white/cream/dark field first, then place the actual image area inside that field with optically sufficient breathing room on all four sides. The amount is a design decision: judge it against the field size, image crop, neighboring title/caption/footer, and the template's negative-space rhythm. A source or generated case image touching the stage edge is a layout execution failure because it breaks the field/image relationship, not because it violates a magic number. The visual plan may record a `case_stage_inner_padding` or `composition.case_stage_inner_padding` when a page needs a specific optical adjustment; the builder supplies proportional defaults and safety limits only to preserve the intended relationship.
4. One large case image per slide is the default. Two case images may share a slide only inside one shared large stage for a direct comparison/sequence, and the split panels must be calculated from the inset content area, not from the outer stage edge. Do not mechanically use equal horizontal panels when the source images have different proportions or visual density. Use asymmetric, staggered, vertical-stack, or main-plus-secondary arrangements so each image keeps its natural proportion and the pair reads as a composed teaching comparison. Equal side-by-side is only acceptable when the images have compatible proportions and the teaching relationship is explicitly parallel. Do not put separate white/cream backing cards under each image when a single shared stage can hold the images; those extra rectangles make the pictures read as small inserted cards rather than the teaching object.
5. A case-image page is acceptable when the image stage is the first visual focus and the learner can inspect the case before reading all text. It fails when the title, text panel, empty space, decorative backing shapes, or edge-to-edge image placement dominate and the case image becomes a dropped-in rectangle. It also fails when one small source image sits alone in a huge field with no interpretation, or when different-proportion images are forced into a stiff equal row. The good pattern is a large shared picture field with disciplined inner padding plus a short side note/caption or proportion-aware multi-image composition; the bad pattern is a normal slide layout with small pictures dropped into leftover rectangles.

## Composition judgment

The visual storyboarder and director must apply basic graphic-design judgment before the renderer runs. Layout is not solved by selecting a named template or by passing numeric checks. For each knowledge page, decide the dominant visual focus, supporting text hierarchy, main alignment axis, and negative-space relationship between title, image field, caption, footer, and page edge. Preserve consistent outer margins and intentional inner padding inside color fields; do not let images, text blocks, or diagram parts accidentally kiss the edge of their containing field. Uneven spacing is allowed only when it creates emphasis or follows the template's visual language; accidental edge contact, cramped corners, and unrelated gaps are failures.

For case-image pages, the director asks: does the image sit inside its stage like a deliberately mounted teaching example, or does it look pasted flush into a rectangle? If it looks pasted, fix the visual plan/layout before building. If a source image or source-image pair cannot visually carry the stage by itself, deliberately use the stage's empty area for image interpretation or choose an anchored second image instead of accepting empty imbalance. Do not push the main explanatory copy outside the stage into the page footer just because the image stage was reserved first. For multi-image case pages, use shared field geometry and consistent optical gutters, but allow different panel sizes, vertical offsets, side/top/bottom text areas, or main/secondary hierarchy when proportions differ; only align everything into an even row when the rendered images actually benefit from that parallel reading.

## Generated images

Generate text-free case images for no-source knowledge pages, abstract branches, metaphor-heavy branches, and image-poor branches that become clearer with a concrete scene. For plain text or diagram-heavy pages, default to asking whether a generated case image would let learners grasp the point faster; do not keep a page text-only or diagram-only merely because the source has no image or because other pages already use source images. Decide by teaching need, not by a quota, but the generated-image obligation is local: one generated image elsewhere in the deck never satisfies unrelated no-source pages. A section cannot run three consecutive no-source non-generated knowledge pages, and a deck with many no-source pages needs generated/source/redrawn case images distributed near the relevant teaching points. Generated case images inherit the case-image stage execution above: they are teaching evidence, not small decorative illustrations beside a text panel. The generated-image route is mandatory and singular: use `gpt-image-2` only. Do not use built-in `imagegen`, deterministic SVG/PPT fallback art, local drawings, or user-provided files as generated-image substitutes. Save final GPT Image 2 assets into the course asset folder.

Every `generated-image` page must record the executed `gpt-image-2` attempt in both `visual_plan` and the matching `course.image_generation_tasks` item. If `gpt-image-2` cannot produce the asset, do not mark the page as `generated-image`; redesign it as `editable-diagram`, `editable-table`, `source-image`, `redrawn-source-image`, or `text-only-exception` with a concrete generated-case bypass reason.

Required route fields:

```json
{
  "generation_route": "gpt-image-2",
  "generation_attempts": [
    {"route": "gpt-image-2", "status": "success", "evidence": "tool result or saved asset proof"}
  ]
}
```

Allowed route semantics:

- `gpt-image-2`: `generation_attempts` includes a successful `gpt-image-2` attempt.
- No other route is allowed for `asset_type: "generated-image"`.

If an editable diagram teaches better than model-generated imagery, do not label the page `generated-image`; use `editable-diagram` / `editable-table` and record `generated_case_bypass_reason`.

Every generated case image must start from the knowledge point. In `visual_plan` and the matching `course.image_generation_tasks` item, record:

- `knowledge_anchor`: the source concept, claim, contrast, misconception, or metaphor the image must make visible;
- `observable_teaching_detail`: the concrete object, action, state, before/after change, or decision point in the picture that lets a zero-basis learner recognize the point;
- `instant_takeaway`: the one-sentence understanding a zero-basis learner should get before the instructor explains.
- `case_visual_map`: a list mapping each visible teaching point, bullet, or enumerated item to the exact image detail that makes it visible, using `{ "screen_evidence": "...", "visible_detail": "..." }`.

These fields are **human-readable judgment cues**, not prompt decoration. The storyboard worker and director use them to decide whether the image teaches, and the non-regression checklist verifies it on the rendered page. If you cannot map the slide's visible points to concrete image details, the image is probably too generic. Regenerate, choose an editable diagram, split the page, or ask for a clearer example. After generation, inspect the image at slide size and ask: "can a learner see the page's enumerated ideas in the image before reading every bullet?" If the answer is only mood, palette, or a generic scene, regenerate or replace.

Prefer vivid teaching scenes (before/after contrast, wrong/right choice, visible consequence, physical analogy, concrete workflow artifact, or a scene where each enumerated idea has a visible object/action) over a generic person at a desk, floating icons, abstract arrows, or decorative dashboards. Keep generated images free of baked-in Chinese text, UI labels, watermarks, and slogans; all labels, arrows, and captions stay editable slide text.

Use `editable-diagram` or `editable-table` instead of generation for arrows, chains, comparisons, label-heavy structures, and factual grids that must stay editable. Use `text-only-exception` only when a concrete case image or diagram would genuinely make the point less clear; record `text_only_exception_reason` or `generated_case_bypass_reason`.

## Template fidelity (layout language first)

The selected Canva template is the visual source for **palette, typography, type scale, alignment axes, spacing, density, color mass, and image treatment** — reproduced as editable PPT/Canva composition. The deck fails when it only borrows the palette while ignoring the template's type scale, axes, spacing, and image discipline. It also fails when it becomes a generic slide deck with only the template colors applied.

Default profile for `DAHM5fsVEB0` (record an equivalent `course.design_profile` for any other template before authoring):

- Canvas 16:9, 1280x720 local / 1920x1080 Canva.
- Black `#1C1C1C`, Orange `#FC6736`, Cream `#F2EBE3`, White `#FFFFFF`.
- Title font Canva `站酷高端黑体` (local `站酷高端黑`); secondary `思源黑体-细体` (local `思源黑体 CN Light`); body `字由点字烈黑`; decorative `思源黑体-粗体` (local `思源黑体 CN Bold`).

Composition: large flat color fields, strong typography, disciplined image crops, clear axes, and intentional negative space. Treat the template as a layout language: inspect the template contact sheet and choose a template-like composition for each slide, adapting ideas from one or more template pages while keeping structure, density, title axis, color mass, and image treatment native to the template. Do not overfit to element shape: the original template may inspire blocks, bands, offsets, large fields, image crops, or open space, but the goal is a coordinated overall layout, not square boxes everywhere. Avoid rounded card grids, pills, badges, button-like labels, heavy borders, and dashboard styling unless a user-supplied template clearly uses them. Keep one dominant focus per slide and deliberate breathing room.

Typography discipline: body text ≥18 pt; captions/tertiary ≥17 pt; secondary headings, card headings, large list labels, side-rail statements, and other non-primary emphasis text normally ≥30 pt when they act as a local heading, or ≥24 pt when they act as a compact explanatory statement. Never use 12–13 pt for content the learner must read. Ordinary titles ≥36 pt (short titles usually 46–58 pt; only long Chinese titles step toward 36–40 pt); avoid single-character title wraps. If a page needs tiny text to fit, split the slide or reduce copy rather than shrinking. Text size must respond to actual text amount and frame size: a short explanatory paragraph in a tall/wide side area should grow to fill the frame optically, while a long paragraph should shrink only down to the minimum and then force a split/rewrite. Do not leave a large side text frame with 18–21 pt copy when 22–26 pt would fit. On case-image pages, reduce learner text before shrinking the image and allow a smaller title scale than ordinary statement pages if that preserves the image stage. Captions and image interpretation text must live inside the case-image stage's safe content area or another deliberate text area, not be pushed into the footer/safety zone by the reserved image stage. The renderer may choose side, top, bottom, or corner placement inside the stage; the skill should not force all supporting text to one fixed position. If the content occupies only the upper half or one corner of the page, rebuild the composition instead of accepting empty imbalance; useful breathing room is intentional, but a case-image page with a dominant large image is not considered imbalanced merely because the image uses most of the slide.

Layout rhythm: for long decks, use fixed structural families for `lesson-overview`, `section-cover`, and `summary`, then vary image side, color field (light/dark/accent), comparison, table, roadmap, close-reading, and statement layouts inside each section while keeping the same template language. Choose layouts by content relationship, not by mechanically alternating colors. Do not let section content collapse into one repeated two-column pattern, and do not let a long middle section become mostly plain light pages. This rhythm is verified by the director against the contact sheet and the non-regression checklist, not by numeric repetition thresholds.

## Layout bank

`cover`, `lesson-overview`, `section-cover`, `roadmap`, `light`, `dark`, `orange`/`accent`, `image-left`/`image-right` (+ `-dark`, `-orange`/`-accent` variants), `comparison`, `table`, `summary`. Use `lesson-overview`, `section-cover`, and `summary` only for their structural roles. Use `comparison`/`table`/two-panel only when the relationship is real and named in learner-facing labels. Use `table` family as an occasional pacing tool, not the default way to fit several points; if several adjacent nodes all seem to need it, split, summarize, or convert one to a flow/statement/image-evidence page.

## Before build

For every knowledge slide verify: a concrete visual plan mapped to a source node; the visual is actually on the slide; the slide explains the image for learners; image pages include `case_visual_map` so the image visibly supports the slide's enumerated points; the image integrates with the node's text rather than replacing it; text/visual balance means the image remains readable and the text is only enough to guide inspection, not that the slide must reserve equal area for text; all labels are editable slide text; generated images are concrete teaching scenes, not abstract placeholders; text-only pages have a concrete bypass reason; the left footer names the current approved chapter framework on normal content pages; no production words (`PDF`, `原稿`, `来源文档`, `图旁注明`, `制作说明`) appear. Before build, also verify that every case-image page (`source-image`, `redrawn-source-image`, or `generated-image`) is rendered inside a dominant shared case-image stage rather than as tiny cards, a composite montage, or a small illustration beside oversized text. For source images, additionally verify that every non-thumbnail source image id has an extracted `source_node_id`, appears in some normal knowledge page's `visual_plan.source_image_ids`, is placed within that image's anchored source branch, and is listed in `course.source_image_coverage` as `used` or `redrawn`.
