# Visual system for course decks

## Goal

Visuals are teaching devices, not a separate production checklist. The final Canva deck must show each case image or example diagram on the knowledge page where it helps the learner understand the concept.

Do not make learner-facing slides that say "next we will make these images", "reuse PDF images", "source screenshot", or similar production notes. Those belong only in internal files.

## Slide-level visual plan

Before building the PPTX, every normal knowledge slide must include a `visual_plan` in `deck-spec.json`:

```json
{
  "teaching_role": "what this visual helps the learner understand",
  "source_node_id": "n0012",
  "asset_type": "source-image",
  "integration": "knowledge-page",
  "description": "student-facing visual idea, without production wording",
  "visual_applicability": "required",
  "imagegen_priority": "preferred",
  "imagegen_bypass_reason": "",
  "generation_route": "",
  "prompt_brief": "",
  "text_area_ratio": 0.4,
  "labels_as_slide_text": true,
  "exception_reason": ""
}
```

Allowed `asset_type` values:

- `source-image`: extracted original image or screenshot from the authoritative source.
- `redrawn-source-image`: source visual rebuilt for readability while preserving its logic.
- `generated-image`: new text-free illustration generated for a missing visual, preferably with GPT Image 2.
- `editable-diagram`: Canva/PPTX shapes, arrows, simple icons, comparison blocks, or process chain.
- `editable-table`: source table or comparison rebuilt as editable slide text.
- `text-only-exception`: allowed only for cover, transition, summary, or a slide where an image would reduce clarity; must include `exception_reason`.

`integration` must be `knowledge-page`. Reject `standalone-stage`, `asset-list`, `production-note`, or anything that means the image is not actually used in the learner page.

## Priority order

1. Extract and reuse source case images when the source already contains a concrete example.
2. If the source image is low resolution or too dense, redraw it as a cleaner Canva-readable visual without changing the example logic.
3. For every knowledge branch that can be taught with a case image or demonstration image, create one. Treat this as required by default, not optional decoration.
4. Prefer `generated-image` through `gpt-image-2` for rich case illustrations and demonstration illustrations, especially familiar-object metaphors, before/after scenes, physical analogies, and abstract concepts that need a concrete picture.
5. Use `editable-diagram` or `editable-table` only when the visual is mainly arrows, chains, comparisons, labels, or table-like information that must stay editable.
6. Keep all technical labels as editable slide text. Generated images should contain no baked-in Chinese text.

## Image generation capability

Use `gpt-image-2` as the preferred route when a node needs a richer raster case image, such as a realistic object analogy, a textured scene, a before/after visual, or a non-text illustration that would be weak as simple shapes. Use the built-in `imagegen` route only when GPT Image 2 is unavailable, fails, or the user explicitly asks for it.

Do not force raster generation for visuals that are better as editable instructional graphics:

- Use `editable-diagram` for arrows, chains, tables, comparisons, labels, and shape-based teaching diagrams.
- Use `generated-image` with `generation_route: "gpt-image-2"` when a bitmap illustration will make the concept easier to understand.
- If GPT Image 2 is bypassed for a knowledge slide that could otherwise use an illustration, record `imagegen_priority: "not-needed"` plus a concrete `imagegen_bypass_reason`.
- If GPT Image 2 is unavailable in the current environment, record `imagegen_priority: "unavailable"` and use the best deterministic fallback; do not leave the page without a visual.
- Keep the generated image free of Chinese text, UI labels, watermarks, and decorative slogans.
- Put all labels, arrows, captions, and explanations in editable slide text.
- Save final project-bound generated images into the course asset folder; do not leave them only in a default generation directory.
- Record a short `prompt_brief` in `visual_plan` so the image intent can be audited without exposing production prompts on slides.

If GPT Image 2 and image generation are unavailable or fail, use the best deterministic fallback that still teaches the node: editable SVG/PPTX diagram, redrawn source image, or user-supplied image. Do not replace a needed case visual with an empty text-only slide.

## Concrete teaching image gate

Generated images must make the learner understand the knowledge point faster. A picture is rejected even if it is visually polished when it is only abstract decoration, generic icons, arbitrary geometric blocks, or a vague "workflow-looking" graphic.

For process lessons, the knowledge point may be a workflow, but the image must show concrete artifacts from that workflow: a script page, shooting setup, media bins, editing timeline, subtitle/audio controls, platform version variants, title/cover board, publish checklist, analytics dashboard, or next-video planning loop. Do not use disconnected arrows, boxes, circles, or decorative abstract shapes as the main image.

Before building the PPTX, inspect generated images at slide size and ask: "Could a zero-basis learner explain why this exact image belongs on this exact slide?" If not, regenerate or replace it before Canva import.

## Required composition

- A case image is an illustration inside a knowledge page, not the whole page.
- The page remains text-led: title, explanation, 3-5 points, and visual interpretation stay visible.
- On illustrated knowledge slides, target about 40% text area, 50% visual area, and 10% breathing room. If the source text needs more space, split into more slides instead of shrinking the visual into a token illustration.
- Captions explain what to look at, not where the image came from.
- Do not use decorative stock images unless they directly teach the node.

## Detailed outline mode

For `细纲`, visuals may clarify, crop, relabel, or redraw the source's examples, but must not add new technical content, workflows, or unrelated scenarios.

If the source says "编码像快递打包", the visual should show content, packing method, box/container, and unpacking at a conceptual level. Do not add advanced proxy workflows, software settings, or technical branches absent from the source.

## Sparse outline mode

For `粗纲`, generated examples can be richer, but each visual must still map to one original node. Add visual detail vertically inside the branch: definition, relation, familiar analogy, common confusion, or boundary.

Reject a visual if explaining it requires a new topic branch or a neighboring course. For example, an encoding-format visual may compare "packing method" and "file box", but should not drift into editing software button operations.

## QA checklist

For every knowledge slide, verify:

- Does the slide have a concrete visual plan mapped to a source node?
- Is `visual_applicability` marked required for every knowledge branch that can use a case or demonstration image?
- Is the visual actually on the slide, or represented by editable diagram/table shapes?
- Does the slide explain the image for learners?
- Is the image integrated with the current node's text rather than replacing it?
- Is the text area around 40% on illustrated knowledge slides?
- Are all labels editable slide text?
- Do generated images record their generation route and prompt brief in `visual_plan`?
- Are generated images concrete teaching scenes or cases rather than abstract placeholders?
- Are there any production words such as `PDF`, `原稿`, `来源文档`, `图旁注明`, or `制作说明`? If yes, fail.
