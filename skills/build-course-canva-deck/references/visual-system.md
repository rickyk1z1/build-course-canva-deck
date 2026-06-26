# Visual system for course decks

## Goal

Visuals are teaching devices, not a separate production checklist. The final Canva deck must show each case image or example diagram on the knowledge page where it helps the learner understand the concept.

Do not make learner-facing slides that say "next we will make these images", "reuse PDF images", "source screenshot", or similar production notes. Those belong only in internal files.

## Slide-level visual plan

Before building the PPTX, every normal knowledge slide must include a short `visual_plan` in `deck-spec.json`. This plan exists so the director can judge the page, not so the worker can fill a form:

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
3. Give every normal knowledge page a visual bridge when it helps the learner understand the node. The visual may be a source image, redrawn source visual, generated teaching case, editable diagram, editable table, or a deliberate text-only exception.
4. Prefer `generated-image` through `gpt-image-2` for rich case illustrations and demonstration illustrations, especially familiar-object metaphors, before/after scenes, physical analogies, and abstract concepts that need a concrete picture.
5. Use `editable-diagram` or `editable-table` only when the visual is mainly arrows, chains, comparisons, labels, or table-like information that must stay editable.
6. Keep all technical labels as editable slide text. Generated images should contain no baked-in Chinese text.

## Source image granularity

Source images are part of the authoritative teaching material, not a loose moodboard. When the outline contains reference images or case images, build a source-image coverage ledger before authoring:

```json
{
  "source_image_id": "img003",
  "status": "used",
  "slide_numbers": [8],
  "treatment": "single-case",
  "reason": "teaches association through a concrete lantern/scene example"
}
```

Every non-thumbnail source image must appear exactly once in `course.source_image_coverage` as `used` or `omitted`. Omitted images require a concrete reason such as duplicate, unreadable, decorative, or out-of-scope. Do not omit a usable case image merely to shorten the deck.

Use one teachable case image per slide by default. A slide may include up to three source image IDs only when one of these is true:

- the original source image file is already a single author-made composite, so `source_image_ids` contains one image ID even though the picture has multiple subcases;
- the source explicitly asks the learner to compare two images side by side, and `case_granularity` is `explicit-comparison`;
- two or three source images form a source-ordered teaching sequence that the instructor can explain on one page, and `case_granularity` is `multi-case-sequence`;
- the images are unreadable alone and are redrawn into a cleaner single teaching visual while preserving the source's original grouping.

Do not create a new collage that combines more than three independent source images into one slide. Four or more source images hides examples the instructor may need to explain one by one, makes captions generic, and treats cases as decoration instead of teaching evidence. If several source images support one branch, add slides and preserve the source order.

For two or three independent source images on one slide, the page must prove readability before PPT generation:

- `visual_plan.image_area_ratio`: total image area should normally be at least `0.45` and no more than `0.72`;
- `visual_plan.min_source_image_area_ratio`: the smallest source image must normally occupy at least `0.12` of the slide area;
- `visual_plan.text_area_ratio`: text should normally stay at or below `0.38`;
- captions and body text must identify what to inspect in each image, not summarize all images generically.

Each image-based slide must record:

- `visual_plan.source_image_ids`: source image IDs used on that slide, or an empty list for generated/editable visuals;
- `visual_plan.case_granularity`: `single-case`, `explicit-comparison`, `multi-case-sequence`, `source-authored-composite`, `redrawn-single`, or `not-source-image`;
- `visual_plan.case_grouping_reason`: required when more than one source image ID appears on a slide, and must explain why the images belong together instead of on separate pages.

## Image generation capability

Use this route order when a node needs a richer raster case image, such as a realistic object analogy, a textured scene, a before/after visual, or a non-text illustration that would be weak as simple shapes:

1. `gpt-image-2` first.
2. Built-in `imagegen` only if GPT Image 2 is unavailable, fails, or the user explicitly asks for it.
3. Local SVG/PPT diagram, redrawn source visual, or other deterministic fallback only if both GPT Image 2 and built-in imagegen are unavailable/failed, or if the director changes the visual decision because an editable diagram teaches better.

An image-generation review is mandatory for every deck, but it is a teaching decision, not a quota.

When workers are used, the 视觉分镜师 owns the planning layer and the 总导演 owns the execution layer. The planning layer is staged: `visual-triage` identifies source-image reuse, visual asset types, generated-image candidates, and capacity risks; `visual-finalize` completes template references, native motifs, layout checks, and only the approved `image_generation_tasks`. Native motif planning may only reference template elements/groups/frames that can be copied atomically; if the current Canva route only supports whole-page duplication, record native reuse as blocked instead of planning a motif. Long decks may be split into contiguous visual-plan parts under the same `storyboard-designer` role state. The 总导演 executes approved tasks, saves selected assets into the course asset folder, records asset paths or fallbacks, and connects the assets to `deck-spec.json`. Workers must not call image-generation tools or save final image assets.

Execution rule: if `course.image_generation_tasks` contains planned generated cases or a slide has `visual_plan.imagegen_priority: "preferred"`, the director must read the `gpt-image-2` skill and attempt GPT Image 2 before local PPTX build. If GPT Image 2 fails, attempt built-in `imagegen` unless it is unavailable in the current environment. Do not replace planned rich case images with local SVG/PPT diagrams merely because deterministic fallback is faster. If both generation routes fail or are unavailable, record route-by-route attempts, command/tool layer, affected slide numbers, and the chosen fallback in `course.image_generation_review`; then use the fallback only where it still teaches the node.

If the outline already contains many case images, inspect and reuse those source cases first wherever they directly teach the current node. Record `source_case_priority: "source-first"` and `reused_source_slide_numbers` in `course.image_generation_review`. After that source-case pass, identify text-heavy or abstract pages that have no source image and would become clearer with a generated teaching case. For source-rich decks, generated pages are required by teaching need, not by a quota: add them when the remaining non-source-image pages need richer visual cases, and skip them when source cases plus editable diagrams already make the deck visually teachable. A deck with no source reuse record or no completed review fails director review; a deck with no generated pages can pass only when `generated_slide_numbers` is an empty list and `generated_bypass_reason` explains why no remaining text-heavy or abstract page needs a generated case.

If the outline is image-poor, treat concrete teaching visuals as a primary build input rather than a late decoration. These may be generated images or editable diagrams/tables, depending on what teaches the node best. This applies in both `细纲` and `粗纲`. Image-poor means any of the following:

- no usable non-thumbnail case images;
- fewer than six usable non-thumbnail case images in a long deck;
- usable case images cover less than roughly one third of normal knowledge slides;
- a detailed outline has dense screen copy or many abstract concepts, but source visuals are too sparse to keep the deck from becoming mostly text.

For image-poor decks:

- Set `course.image_generation_review.source_case_image_count` to the count of usable non-thumbnail source case images; use `0` only when none exist.
- For long image-poor decks, give every major abstract branch at least one concrete visual bridge unless that branch is clearer as a text-led table or process diagram.
- Generate images for source metaphors, physical analogies, before/after misconceptions, and abstract mindset pages where a learner benefits from seeing a concrete scene.
- Use editable diagrams instead of generated images only for relationship maps, process chains, comparison structures, tables, and label-heavy visuals that must stay fully editable.
- Do not describe the image-poor plan as "a small number of generated images" unless the deck itself is short and mostly table/process content.
- Record selected generated slide numbers, route-by-route attempts, concrete bypass reasons, and deterministic fallbacks in `course.image_generation_review` so the decision is understandable before PPT generation.
- Record the executable task list in `course.image_generation_tasks` when generated illustrations are planned.
- SVG/PPT fallback diagrams are acceptable for relationship maps and label-heavy visuals, but they do not replace a planned rich bitmap teaching case unless GPT Image 2 was attempted and failed or the director changes the visual decision with a concrete teaching reason.

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

## Concrete teaching image standard

Generated images must make the learner understand the knowledge point faster. A picture is rejected even if it is visually polished when it is only abstract decoration, generic icons, arbitrary geometric blocks, or a vague "workflow-looking" graphic.

For process lessons, the knowledge point may be a workflow, but the image must show concrete artifacts from that workflow: a script page, shooting setup, media bins, editing timeline, subtitle/audio controls, platform version variants, title/cover board, publish checklist, analytics dashboard, or next-video planning loop. Do not use disconnected arrows, boxes, circles, or decorative abstract shapes as the main image.

Before building the PPTX, inspect generated images at slide size and ask: "Could a zero-basis learner explain why this exact image belongs on this exact slide?" If not, regenerate or replace it before Canva import.

## Required composition

- A case image is an illustration inside a knowledge page, not the whole page.
- A case image is also not a thumbnail in a collage. If the instructor must explain the case, give it readable space and a dedicated learner-facing interpretation.
- The page remains teaching-led: title, explanation, source-preserving points, and visual interpretation stay visible.
- On illustrated knowledge slides, keep a clear balance between text, visual, and breathing room. If the source text needs more space, split into more slides instead of shrinking the visual into a token illustration or shrinking text until it is unreadable.
- Captions explain what to look at, not where the image came from.
- Do not use decorative stock images unless they directly teach the node.

## Detailed outline mode

For `细纲`, visuals may clarify, crop, relabel, or redraw the source's examples, but must not add new technical content, workflows, or unrelated scenarios.

If the source says "编码像快递打包", the visual should show content, packing method, box/container, and unpacking at a conceptual level. Do not add advanced proxy workflows, software settings, or technical branches absent from the source.

## Sparse outline mode

For `粗纲`, generated examples can be richer, but each visual must still map to one original node. Add visual detail vertically inside the branch: definition, relation, familiar analogy, common confusion, or boundary.

Reject a visual if explaining it requires a new topic branch or a neighboring course. For example, an encoding-format visual may compare "packing method" and "file box", but should not drift into editing software button operations.

For `细纲` or `粗纲` with image-poor source material, prefer generated metaphor images for the original outline's own analogies and mindset claims, because the deck otherwise becomes an expanded text outline. In `细纲`, the generated image may visualize an existing metaphor, example, contrast, or claim, but must not add new technical branches. In `粗纲`, the generated image may support vertical expansion inside the original branch. Keep generated images text-free and put all labels in editable slide text. Use enough generated images that each major abstract branch has at least one concrete visual bridge, while still keeping every image mapped to an original node.

## Review checklist

For every knowledge slide, verify:

- Does the slide have a concrete visual plan mapped to a source node?
- Is `visual_applicability` justified by teaching need rather than by a visual quota?
- Was the image-generation review completed when the source has enough case images, did it reuse source cases first, and were suitable text-heavy/abstract pages supplemented instead of leaving all visuals as source reuse?
- Does `course.source_image_coverage` account for every non-thumbnail source image, and are usable case images mapped to readable slides?
- Does every source-image slide list `visual_plan.source_image_ids`, keep independent source images to three or fewer, and prove that multi-image pages remain readable?
- Is the visual actually on the slide, or represented by editable diagram/table shapes?
- Does the slide explain the image for learners?
- Is the image integrated with the current node's text rather than replacing it?
- Does the text/visual balance leave enough space for readable source evidence and a useful visual?
- Are all labels editable slide text?
- Do generated images record their generation route and prompt brief in `visual_plan`?
- Are generated images concrete teaching scenes or cases rather than abstract placeholders?
- Are there any production words such as `PDF`, `原稿`, `来源文档`, `图旁注明`, or `制作说明`? If yes, fail.
