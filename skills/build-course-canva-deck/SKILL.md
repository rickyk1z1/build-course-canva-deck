---
name: build-course-canva-deck
description: Turn a course outline or knowledge tree into a detailed, learner-facing, editable Canva recording deck that belongs to one coherent self-media, editing-mindset, and video-editing curriculum. Use for PDF, XMind, DOCX, Markdown, TXT, OPML, or FreeMind inputs when Codex must preserve teaching order, distinguish a user-declared detailed outline from a user-declared sparse outline, align terminology and scope with neighboring courses, create screen copy and separate lecture notes, prepare explanatory visuals, build and QA a PPTX, import it into Canva, and request final approval before saving.
---

# Build Course Canva Deck

Create a complete recording presentation from a course knowledge outline. Treat the accepted `影像基础参数` deck as the content-depth and visual-quality baseline, not as reusable subject matter. Treat the Canva template as configurable: use the bundled `DAHM5fsVEB0` profile only when the user has not supplied a different template.

## Non-negotiable checkpoint

1. Inspect every supplied source before authoring.
2. If sources conflict or overlap, ask the user to choose one authoritative source. Do not merge them by assumption.
3. After inspecting the authoritative source, ask the user to reply exactly with either `细纲` or `粗纲`.
4. Do not infer the mode from length, hierarchy, file type, or apparent detail. Do not proceed until the user chooses.
5. Record the choice in `source-map.json` with `validate_source_map.py --mode detailed|sparse --write`. For PDF sources, also pass `--pdf-visual-check` after rendering and visually inspecting the page hierarchy.

Before authoring, read [references/curriculum-system.md](references/curriculum-system.md). Discover the existing curriculum map, neighboring lessons, shared terminology, and this lesson's role. If the workspace does not reveal the lesson's position, ask the user for the missing curriculum context instead of inventing it.

## Mode contract

- `细纲` / `detailed`: match the accepted `影像基础参数` deck's content depth. Preserve source order, examples, metaphors, claims, and scope. Improve teachability, wording, and visuals only. Do not add adjacent professional workflows.
- `粗纲` / `sparse`: produce content more detailed than the accepted baseline by adding definitions, causes, relationships, examples, common misconceptions, and necessary boundaries. Expand vertically inside existing branches only. Never create a new branch or follow a low-relevance tangent. Every addition must map to one original node and authoritative evidence.

Read [references/content-policy.md](references/content-policy.md) before writing either mode.

## Required workflow

1. Read [references/workflow.md](references/workflow.md) and create an external scratch workspace.
2. Run `scripts/extract_source.py` to create `source-map.json`. For PDFs, also render and visually inspect every relevant page; extracted text alone is not hierarchy evidence.
3. Complete the mandatory source and mode checkpoint above.
4. Create `curriculum-context.json` and lock the lesson's module, prerequisites, downstream lessons, shared terms, and neighboring topics that must remain out of scope.
5. Build a source coverage matrix in source order. Include every valid node at least once. If one dense source node must split across consecutive slides, mark continuation slides with `source_coverage_kind` and `source_split_reason`; otherwise duplicate mappings fail QA.
6. Create `deck-spec.json` using the schema in [references/workflow.md](references/workflow.md).
7. Write two separate layers:
   - learner-facing screen copy that can be understood without narration;
   - lecture notes for oral transitions and emphasis, never rendered on slides.
8. Read [references/visual-system.md](references/visual-system.md), then create a slide-by-slide visual plan. Every normal knowledge slide must either reuse a source case image, rebuild a source visual, or include a generated/editable explanatory diagram that is fused into the page.
9. Read [references/design-system.md](references/design-system.md) and [references/page-design-quality.md](references/page-design-quality.md), then build the editable PPTX with `scripts/build_deck.mjs` and `@oai/artifact-tool`.
10. Run `scripts/audit_deck.py`, render every slide, create a contact sheet, and fix all errors before Canva import. `make_contact_sheet.py` writes a raster sheet when Pillow is available and an SVG sheet otherwise.
11. Read [references/canva-delivery.md](references/canva-delivery.md), run the Canva template access preflight for the chosen template route, import the verified PPTX as a new Canva design, and leave the source template unchanged.
12. Verify every Canva page, show the complete preview, and ask for one final approval. Save draft edits only after explicit approval.
13. Re-read the saved Canva design and confirm the forbidden-language count is zero before returning the final link. If template-native motifs were planned, run the final audit with `--canva-motif-report canva-native-motif-report.json`.

## Hard boundaries

- Keep the source's teaching order.
- Treat every deck as one component of the same self-media and editing curriculum. Preserve shared terminology, prerequisites, difficulty progression, and division of responsibility between lessons.
- Do not duplicate a neighboring lesson's main teaching task. Record the handoff to that lesson instead of expanding into it.
- Use one teaching node per slide by default; add slides instead of shrinking body text below 16 pt.
- Put definitions, explanations, examples, and visual interpretation on the slide. Do not create question-only or keyword-only pages.
- Keep source images inside knowledge pages. Never let a screenshot or example image replace the lesson text.
- Treat source reference images and case images as teaching units, not decoration. Account for every non-thumbnail source image in `course.source_image_coverage`; use one teachable case image per slide by default.
- A slide may use at most three independent source images, and only when all images remain readable and the visual plan records the image/text ratio and grouping reason. Four or more source images on one slide is a failed collage; split into more slides and explain cases in source order.
- Deck length follows teaching units, source nodes, and source case images, not the number of pages in the selected template bank. Never compress a course to match a 21-page template; reuse template page families and motifs as needed.
- Do not create a standalone "case images to make later" stage page in the learner deck. Case images and example diagrams must appear on the relevant knowledge pages with learner-facing interpretation.
- Treat page design as a first-class requirement, not a skin. The template's typography scale, alignment axes, proximity, contrast hierarchy, image slots, and module spacing must be reflected in the local PPT/contact sheet before Canva import.
- For abstract concepts, build the same kind of concrete visual bridge used in the accepted deck: familiar-object metaphors, before/after comparisons, process chains, simplified diagrams, or source screenshots with labels. Do not leave an abstract slide as text only unless `visual_plan.exception_reason` explains why.
- For decks longer than 12 pages, Canva-native template element use and per-page template-layout diversity are mandatory build inputs. Create `course.template_page_mapping`, `course.template_native_element_inventory`, and `visual_plan.template_motif` plans before local PPT generation; preview native motif proxies in the local PPT/contact sheet and replace them after Canva import instead of overlaying them.
- Canva-native elements must be existing native vector/shape/group/frame elements from the selected Canva template or its accessible duplicate. Do not satisfy this gate with arbitrary Canva library search results, random media asset IDs, or one repeated element on every motif page.
- Planned Canva-native elements must be real delivery requirements, not placeholders. `visual_plan.template_motif.native_element_ref` must name the chosen template design, source page, source element ID, element type, and confirm `copied_from_existing_template: true`; final delivery is blocked if proxy, pending, non-template, or repeated-motif IDs remain unverified.
- Every `visual_plan.template_motif.local_ppt_layout` must include a machine-checkable `motif_box` and `protected_zones` for title, body, captions, footer, and page number. Motifs that overlap readable content, sit in arbitrary corners, or rely only on a written "collision clear" note fail QA.
- Always run an image-generation review before local PPT generation. If the outline contains enough concrete case images, reuse source images where they fit, then generate extra text-free case illustrations only for text-heavy or abstract pages that still need a clearer visual bridge. If the outline is image-poor, treat generated teaching images as a primary build input, not a supplement: this includes no-image outlines, sparse outlines with too few case images, and detailed outlines whose text density is high but usable case-image coverage is low. Generate concrete text-free teaching images for metaphor-heavy and abstract knowledge pages by default, and use editable diagrams only when the visual is mainly arrows, labels, comparisons, or tables.
- Preserve intuitive metaphors even when approximate. Ask before changing one that appears directionally wrong.
- Never display production language such as `PDF`, `原稿`, `来源文档`, `制作说明`, `图旁注明`, `详细讲稿`, or `预计讲解时间`.
- Never display prompts, placeholders, source-tracking labels, or `Genji 是真想教会你`.
- Keep research citations in the evidence ledger, not on slides unless the user requests citations.
- Do not modify or overwrite the original Canva template. If the connector cannot access the chosen template on another device, ask for an accessible duplicate or explicit browser fallback instead of continuing with a broken Canva connection.

Read [references/qa-gates.md](references/qa-gates.md) before declaring any stage complete.

## Resources

- `scripts/extract_source.py`: extract a canonical source map from supported formats.
- `scripts/validate_source_map.py`: validate hierarchy, record the user-declared mode, and record PDF visual hierarchy checks.
- `scripts/audit_deck.py`: enforce coverage, mode, scope, screen-copy, PPTX text gates, and final Canva native motif report gates.
- `scripts/build_deck.mjs`: generate editable 16:9 slides using the selected template profile.
- `scripts/make_contact_sheet.py`: create a labeled full-deck review sheet as raster or SVG fallback.
- `references/visual-system.md`: mandatory rules for source case images, generated diagrams, and slide-level visual plans.
- `references/design-system.md`: mandatory rules for Canva template fidelity, fonts, colors, and layout rhythm.
- `references/page-design-quality.md`: mandatory rules for title scale, alignment, proximity, contrast, image evidence blocks, and contact-sheet design review.
- `references/canva-delivery.md`: Canva connector preflight, cross-device template access, and browser fallback rules.
- `assets/template-reference/`: immutable fallback visual reference for Canva template `DAHM5fsVEB0` when no other template is selected.
- `assets/golden-layouts/`: approved knowledge-page composition references.
