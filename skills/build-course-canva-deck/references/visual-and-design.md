# Visual and design

This reference covers structural page layouts, per-slide teaching visuals, source-image priority, generated-image teaching specificity, and template fidelity. Template fidelity here means the template's **colors, fonts, type scale, alignment axes, spacing, density, color mass, and layout language reproduced as editable composition** — not copying Canva's own vector/shape elements and not forcing every element into square blocks. There is no native-element reuse in this skill.

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
  "instant_takeaway": ""
}
```

Allowed `asset_type`: `source-image`, `redrawn-source-image`, `generated-image`, `editable-diagram`, `editable-table`, `text-only-exception`. `integration` must be `knowledge-page`; reject `standalone-stage`, `asset-list`, `production-note`. Every normal knowledge slide needs a teaching visual or a justified text-only exception.

## Structural layout system

Use fixed layout families for deck structure and varied layout families for section content:

- `lesson-overview`: exactly one total-introduction page after the optional cover. It previews the lesson problem and the ordered second-level sections.
- `section-cover`: exactly one page for each second-level source heading/root child, before its section content. All section-cover pages use the same family so learners feel chapter boundaries. Its small text is an overview of the section's direct child/third-level headings, not the section's conclusion.
- `summary`: exactly one final page, visually distinct from the overview and section covers, consolidating the course.
- Normal knowledge pages inside a section may vary (`image-*`, `comparison`, `table`, `roadmap`, `light`, `dark`, `orange`, etc.) according to the content relationship.

Do not treat structural pages as interchangeable pacing slides. A section-cover is not a place to teach descendant detail; it names the section and previews the upcoming third-level knowledge points. Do not write the section's conclusion, takeaway, or value promise in the small text. A normal knowledge page must not replace or impersonate the section-cover.

## Source image priority

Source images are authoritative teaching units, not a moodboard.

1. Reuse source case images when the source already contains a concrete example.
2. If a source image is low-resolution or too dense, redraw it cleaner without changing the example logic.
3. Use one teachable source case per slide by default. A slide may use two or three source images only for an explicit comparison or a source-ordered sequence; four or more should be split across pages.
4. Account for every non-thumbnail source image as used, redrawn, or omitted with a concrete reason. Do not omit a usable case image merely to shorten the deck.
5. Keep source images inside knowledge pages with a learner-facing caption that says what to inspect, not where the image came from.

## Generated images

Generate text-free case images for abstract, metaphor-heavy, or image-poor branches that become clearer with a concrete scene. Decide by teaching need, not by a quota. Route order: `gpt-image-2` first; built-in `imagegen` if GPT Image 2 is unavailable or fails; deterministic SVG/PPT diagram or redrawn source visual only if both fail or an editable diagram teaches better. Save final assets into the course asset folder.

Every generated case image must start from the knowledge point. In `visual_plan` and the matching `course.image_generation_tasks` item, record:

- `knowledge_anchor`: the source concept, claim, contrast, misconception, or metaphor the image must make visible;
- `observable_teaching_detail`: the concrete object, action, state, before/after change, or decision point in the picture that lets a zero-basis learner recognize the point;
- `instant_takeaway`: the one-sentence understanding a zero-basis learner should get before the instructor explains.

These three fields are **human-readable judgment cues**, not length-checked fields. The script does not measure them; the storyboard worker and director use them to decide whether the image teaches, and the non-regression checklist verifies it on the rendered page. If you cannot name a concrete `observable_teaching_detail` and `instant_takeaway`, do not generate — choose an editable diagram, split the page, or ask for a clearer example. After generation, inspect the image at slide size and ask: "what visible detail teaches this slide's point, and what should a learner grasp in three seconds?" If the answer is only mood, palette, or a generic scene, regenerate or replace.

Prefer vivid teaching scenes (before/after contrast, wrong/right choice, visible consequence, physical analogy, concrete workflow artifact) over a generic person at a desk, floating icons, abstract arrows, or decorative dashboards. Keep generated images free of baked-in Chinese text, UI labels, watermarks, and slogans; all labels, arrows, and captions stay editable slide text.

Use `editable-diagram` or `editable-table` instead of generation for arrows, chains, comparisons, label-heavy structures, and factual grids that must stay editable.

## Template fidelity (layout language first)

The selected Canva template is the visual source for **palette, typography, type scale, alignment axes, spacing, density, color mass, and image treatment** — reproduced as editable PPT/Canva composition. The deck fails when it only borrows the palette while ignoring the template's type scale, axes, spacing, and image discipline. It also fails when it becomes a generic slide deck with only the template colors applied.

Default profile for `DAHM5fsVEB0` (record an equivalent `course.design_profile` for any other template before authoring):

- Canvas 16:9, 1280x720 local / 1920x1080 Canva.
- Black `#1C1C1C`, Orange `#FC6736`, Cream `#F2EBE3`, White `#FFFFFF`.
- Title font Canva `站酷高端黑体` (local `站酷高端黑`); secondary `思源黑体-细体` (local `思源黑体 CN Light`); body `字由点字烈黑`; decorative `思源黑体-粗体` (local `思源黑体 CN Bold`).

Composition: large flat color fields, strong typography, disciplined image crops, clear axes, and intentional negative space. Treat the template as a layout language: inspect the template contact sheet and choose a template-like composition for each slide, adapting ideas from one or more template pages while keeping structure, density, title axis, color mass, and image treatment native to the template. Do not overfit to element shape: the original template may inspire blocks, bands, offsets, large fields, image crops, or open space, but the goal is a coordinated overall layout, not square boxes everywhere. Avoid rounded card grids, pills, badges, button-like labels, heavy borders, and dashboard styling unless a user-supplied template clearly uses them. Keep one dominant focus per slide and deliberate breathing room.

Typography discipline: body text ≥16 pt; captions/tertiary ≥15 pt; never 12–13 pt for content the learner must read. Ordinary titles ≥36 pt (short titles usually 46–58 pt; only long Chinese titles step toward 36–40 pt); avoid single-character title wraps. If a page needs tiny text to fit, split the slide or reduce copy rather than shrinking. If the content occupies only the upper half or one corner of the page, rebuild the composition instead of accepting empty imbalance; useful breathing room is intentional, but unfilled or top-heavy pages fail.

Layout rhythm: for long decks, use fixed structural families for `lesson-overview`, `section-cover`, and `summary`, then vary image side, color field (light/dark/accent), comparison, table, roadmap, close-reading, and statement layouts inside each section while keeping the same template language. Choose layouts by content relationship, not by mechanically alternating colors. Do not let section content collapse into one repeated two-column pattern, and do not let a long middle section become mostly plain light pages. This rhythm is verified by the director against the contact sheet and the non-regression checklist, not by numeric repetition thresholds.

## Layout bank

`cover`, `lesson-overview`, `section-cover`, `roadmap`, `light`, `dark`, `orange`/`accent`, `image-left`/`image-right` (+ `-dark`, `-orange`/`-accent` variants), `comparison`, `table`, `summary`. Use `lesson-overview`, `section-cover`, and `summary` only for their structural roles. Use `comparison`/`table`/two-panel only when the relationship is real and named in learner-facing labels. Use `table` family as an occasional pacing tool, not the default way to fit several points; if several adjacent nodes all seem to need it, split, summarize, or convert one to a flow/statement/image-evidence page.

## Before build

For every knowledge slide verify: a concrete visual plan mapped to a source node; the visual is actually on the slide; the slide explains the image for learners; the image integrates with the node's text rather than replacing it; text/visual balance leaves room for readable evidence and a useful visual; all labels are editable slide text; generated images are concrete teaching scenes, not abstract placeholders; the left footer names the current second-level knowledge framework on normal content pages; no production words (`PDF`, `原稿`, `来源文档`, `图旁注明`, `制作说明`) appear.
