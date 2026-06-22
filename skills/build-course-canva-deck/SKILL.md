---
name: build-course-canva-deck
description: Turn a course outline or knowledge tree into a detailed, learner-facing, editable Canva recording deck using the fixed black-orange-cream template system. Use for PDF, XMind, DOCX, Markdown, TXT, OPML, or FreeMind inputs when Codex must preserve teaching order, distinguish a user-declared detailed outline from a user-declared sparse outline, create screen copy and separate lecture notes, prepare explanatory visuals, build and QA a PPTX, import it into Canva, and request final approval before saving.
---

# Build Course Canva Deck

Create a complete recording presentation from a course knowledge outline. Treat the accepted `影像基础参数` deck as the content-depth and visual-quality baseline, not as reusable subject matter.

## Non-negotiable checkpoint

1. Inspect every supplied source before authoring.
2. If sources conflict or overlap, ask the user to choose one authoritative source. Do not merge them by assumption.
3. After inspecting the authoritative source, ask the user to reply exactly with either `细纲` or `粗纲`.
4. Do not infer the mode from length, hierarchy, file type, or apparent detail. Do not proceed until the user chooses.
5. Record the choice in `source-map.json` with `validate_source_map.py --mode detailed|sparse --write`.

## Mode contract

- `细纲` / `detailed`: match the accepted `影像基础参数` deck's content depth. Preserve source order, examples, metaphors, claims, and scope. Improve teachability, wording, and visuals only. Do not add adjacent professional workflows.
- `粗纲` / `sparse`: produce content more detailed than the accepted baseline by adding definitions, causes, relationships, examples, common misconceptions, and necessary boundaries. Expand vertically inside existing branches only. Never create a new branch or follow a low-relevance tangent. Every addition must map to one original node and authoritative evidence.

Read [references/content-policy.md](references/content-policy.md) before writing either mode.

## Required workflow

1. Read [references/workflow.md](references/workflow.md) and create an external scratch workspace.
2. Run `scripts/extract_source.py` to create `source-map.json`. For PDFs, also render and visually inspect every relevant page; extracted text alone is not hierarchy evidence.
3. Complete the mandatory source and mode checkpoint above.
4. Build a source coverage matrix in source order. Include every valid node exactly once or intentionally map a tightly related group to one slide.
5. Create `deck-spec.json` using the schema in [references/workflow.md](references/workflow.md).
6. Write two separate layers:
   - learner-facing screen copy that can be understood without narration;
   - lecture notes for oral transitions and emphasis, never rendered on slides.
7. Reuse source examples and images first. Create new diagrams or text-free illustrations only when they materially improve comprehension.
8. Read [references/design-system.md](references/design-system.md), then build the editable PPTX with `scripts/build_deck.mjs` and `@oai/artifact-tool`.
9. Run `scripts/audit_deck.py`, render every slide, create a contact sheet, and fix all errors before Canva import.
10. Read [references/canva-delivery.md](references/canva-delivery.md), import the verified PPTX as a new Canva design, and leave template `DAHM5fsVEB0` unchanged.
11. Verify every Canva page, show the complete preview, and ask for one final approval. Save draft edits only after explicit approval.
12. Re-read the saved Canva design and confirm the forbidden-language count is zero before returning the final link.

## Hard boundaries

- Keep the source's teaching order.
- Use one teaching node per slide by default; add slides instead of shrinking body text below 16 pt.
- Put definitions, explanations, examples, and visual interpretation on the slide. Do not create question-only or keyword-only pages.
- Keep source images inside knowledge pages. Never let a screenshot or example image replace the lesson text.
- Preserve intuitive metaphors even when approximate. Ask before changing one that appears directionally wrong.
- Never display production language such as `PDF`, `原稿`, `来源文档`, `制作说明`, `图旁注明`, `详细讲稿`, or `预计讲解时间`.
- Never display prompts, placeholders, source-tracking labels, or `Genji 是真想教会你`.
- Keep research citations in the evidence ledger, not on slides unless the user requests citations.
- Do not modify or overwrite the original Canva template.

Read [references/qa-gates.md](references/qa-gates.md) before declaring any stage complete.

## Resources

- `scripts/extract_source.py`: extract a canonical source map from supported formats.
- `scripts/validate_source_map.py`: validate hierarchy and record the user-declared mode.
- `scripts/audit_deck.py`: enforce coverage, mode, scope, screen-copy, and PPTX text gates.
- `scripts/build_deck.mjs`: generate editable 16:9 slides in the fixed template language.
- `scripts/make_contact_sheet.py`: create a labeled full-deck review sheet.
- `assets/template-reference/`: immutable visual reference for Canva template `DAHM5fsVEB0`.
- `assets/golden-layouts/`: approved knowledge-page composition references.
