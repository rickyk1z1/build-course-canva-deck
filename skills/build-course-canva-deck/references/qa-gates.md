# Quality gates

## Source gate

- One authoritative source is explicitly selected.
- A user-declared mode is recorded; mode is never inferred.
- Node IDs are unique and ordered.
- Parent nodes precede children.
- Embedded images and unreadable regions are accounted for.

## Content gate

- `curriculum_context` identifies the overall system, module, and this lesson's role.
- Shared terminology matches existing lessons.
- Prerequisite knowledge is only recapped as needed; neighboring lessons are not duplicated.
- Every included source node maps to at least one slide.
- Slide source-node order is monotonic.
- Detailed mode contains no added-content records.
- Sparse additions map to original nodes, use allowed addition kinds, have `direct` relevance, and include evidence URLs.
- Sparse additions do not create new branches or enter neighboring workflows.
- Visible content contains none of the curriculum context's `excluded_neighbor_topics`.
- User examples and metaphors are preserved.

## Learner-facing gate

Scan titles, explanations, bullets, captions, and visible block text. Reject:

- `PDF`, `原稿`, `来源文档`, `制作说明`, `图旁注明`;
- `详细讲稿`, `预计讲解时间`, `视觉说明`, `对应节点`;
- prompts, TODOs, lorem ipsum, placeholders, and tool tokens;
- `Genji 是真想教会你`.

Production metadata may exist in internal notes, but never in visible screen fields or PPTX slide XML.

## Visual gate

- Every normal knowledge slide has a `visual_plan` mapped to a source node.
- Every knowledge branch that can use a case image or demonstration image has one; exceptions must be explicit and justified.
- `visual_plan.integration` is `knowledge-page`; production-stage lists are rejected.
- The visual is actually represented in the slide as a source image, redrawn source image, generated image, editable diagram, or editable table.
- Slides with source or generated images use `image-left`, `image-right`, or another layout that visibly places the image inside the knowledge page.
- Visuals have learner-facing interpretation in the same slide.
- Generated images contain no baked-in Chinese text; labels are editable slide text.
- Generated image plans include a generation route and prompt brief; `gpt-image-2` is the preferred route for rich bitmap examples when available, while editable diagrams remain preferred for label-heavy teaching graphics.
- Generated images must be concrete teaching scenes, cases, or demonstrations. Abstract geometry, generic icon collages, and decorative workflow-looking placeholders fail even if they are visually polished.
- Illustrated knowledge slides target about 40% text area; pages needing more text should split rather than shrink the visual.
- Full-deck contact-sheet inspection must check template fidelity and layout variety: the deck should follow the Canva template language and avoid a long run of identical page layouts.
- Every slide records `visual_plan.template_reference` naming the reference template page/family, at least two inherited layout features, and the adaptation decision used before local PPT generation.
- For decks longer than 12 pages, automated layout rhythm checks must reject:
  - more than 60% of normal knowledge pages using the same layout family;
  - fewer than three background color modes across normal knowledge pages;
  - more than four consecutive normal knowledge pages with the same layout family or the same background color mode;
  - a middle section dominated by plain light `image-left` / `image-right` pages.
- `text-only-exception` is allowed only for cover, transition, summary, or a clearly justified non-visual page.
- No slide may present case images as a future task list instead of using them to teach the current node.

## Slide gate

- No question-only or keyword-only knowledge pages.
- Every normal knowledge slide has a complete explanation and 3-5 useful points.
- Images are accompanied by interpretation and do not replace the page's knowledge text.
- Body text is at least 16 pt; ordinary titles are at least 35 pt.
- No unintended overlap, clipping, title wrapping, broken connectors, or missing images.
- Page numbers, headers, fonts, and visual tokens are consistent.
- The full rendered contact sheet and any flagged page are inspected.

## Canva gate

- Canva access preflight is recorded in `canva-access.json`.
- If the canonical template is inaccessible, an accessible duplicate or explicit browser fallback approval is recorded before import.
- Canva page count equals the PPTX page count.
- Every page has been previewed.
- Rich-text scan contains zero forbidden terms.
- The original template remains unchanged.
- Draft changes are committed only after explicit user approval.
- Saved design is re-read and verified before delivery.
