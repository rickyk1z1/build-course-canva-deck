---
name: build-course-canva-deck
description: Use when creating or substantially revising a Canva recording deck from a course outline, mind map, PDF, document, or knowledge tree for this course system.
---

# Build Course Canva Deck

Create a complete recording presentation from a course knowledge outline. The Canva deck is the only deliverable. The target is a chaptered course deck that reads like a careful human instructor built it: the source hierarchy becomes the deck spine, second-level outline headings appear as fixed section-cover pages, page logic is coherent, each visual teaches the current point, and a zero-basis learner understands the page without guessing. Treat the accepted `影像基础参数` deck as the content-depth and visual-quality baseline, not as reusable subject matter. Use the bundled `DAHM5fsVEB0` template profile only when the user has not supplied a different template.

The skill leans on three references plus a checklist. Read them when their stage is reached:
- [references/content-and-source.md](references/content-and-source.md) — source intake, mode contract, deck-level chapter spine, teaching standard, curriculum boundary, coverage ledger.
- [references/visual-and-design.md](references/visual-and-design.md) — structural page layouts, per-slide visuals, source-image priority, generated-image teaching specificity, template fidelity (layout language first).
- [references/roles-and-delivery.md](references/roles-and-delivery.md) — the four roles, brief contract, director acceptance lock, Canva delivery.
- [references/non-regression-checklist.md](references/non-regression-checklist.md) — the director's mandatory pre-delivery learner review.

## Non-Negotiable Checkpoint

1. Inspect every supplied source before authoring.
2. If sources conflict or overlap, ask the user to choose one authoritative source. Do not merge them by assumption.
3. After inspecting the authoritative source, ask the user to reply exactly with either `细纲` or `粗纲`. Do not infer the mode from length, hierarchy, file type, or apparent detail. Do not proceed until the user chooses.
4. Record the choice in `source-map.json` with `validate_source_map.py --mode detailed|sparse --write`.
5. Discover the lesson's curriculum position. If the workspace does not reveal it, ask the user instead of inventing it.

## Mandatory Four-Role Workflow

For any request to build or substantially revise a course deck, use the four proposal-only roles under one director. There is no single-orchestrator authoring fallback for deck builds.

```text
总导演 / build-course-canva-deck
├── 课程统筹师
├── 原稿场记
├── 课堂编剧
└── 视觉分镜师
```

The director owns all durable writes and external actions (`source-map.json`, `curriculum-context.json`, `deck-spec.json`, generated assets, PPTX build, audit, Canva import/edit, final approval), plus process review after each proposal and final learner-facing review. Each worker is proposal-only, carries its own standard, and returns a compact handoff plus a `self_check` backed by concrete evidence. Do not create a separate reviewer role.

If subagents cannot be dispatched, runtime policy requires user authorization that has not been given, or the user disables workers, stop after safe source/mode intake and report the blocker. Read [references/roles-and-delivery.md](references/roles-and-delivery.md) before dispatching.

## Required Workflow

1. Create an external scratch workspace. Run `scripts/extract_source.py` to create `source-map.json`. For PDFs, render and visually inspect every relevant page.
2. Complete the source and mode checkpoint above.
3. Create `curriculum-context.json` and lock the lesson's module, prerequisites, downstream lessons, shared terms, and neighboring topics that must stay out of scope.
4. Create four scoped worker briefs and dispatch in the staged order from the roles reference.
5. Build a deck spine from the source hierarchy: optional course cover, one `lesson-overview` total-introduction page, then for each root child/second-level heading in source order one fixed `section-cover` page followed by that section's content pages, and one final `summary` page. Section-cover small text previews the section's immediate child/third-level headings as upcoming knowledge points; it must not reveal the section's conclusions.
6. Build a source coverage matrix in source order: every valid node exactly once, with root/section heading nodes covered by overview or section-cover pages and descendant nodes covered inside their section.
7. Create `deck-spec.json`. Write one learner-facing screen-copy layer that follows the approved deck spine and source order. Source order, path, coverage, and review evidence live in `source_node_treatments` or notes for the producer, never in rendered slide text. Optional `speaker_notes` are short internal transition hints only.
8. Create the visual plan: structural pages use their fixed layout families; every normal knowledge slide reuses a source case image, rebuilds a source visual, includes a generated teaching image, or uses an editable diagram/table fused into the page.
9. Build the editable PPTX with `scripts/build_deck.mjs` and `@oai/artifact-tool`.
10. Run `scripts/audit_deck.py`, render every slide, create a contact sheet, and fix all mechanical errors. A passing audit is never approval by itself.
11. Perform the director's final learner review against [references/non-regression-checklist.md](references/non-regression-checklist.md) and record it in `交付前自检.md` before Canva import.
12. Run the Canva access preflight, import the verified PPTX as a new Canva design, and leave the source template unchanged.
13. Verify every Canva page, show the complete preview, ask for one final approval, then return the link after page-count and forbidden-language checks pass.

## Hard Boundaries

- Keep the source's teaching order and hierarchy. In detailed mode the mind-map path is the course structure; do not flatten levels into a reorganized script.
- Preserve the deck spine: the first non-cover page is a total lesson overview; each second-level outline heading/root child gets its own fixed section-cover page before its content; no section content may appear before its section cover; the final page is a summary.
- On section-cover pages, bullets/small text are a source-ordered overview of that section's direct child headings or adjacent child-heading groups. They are not conclusions, takeaways, promises, or value judgments. Record their source anchors in `section_preview_items`; do not count these child nodes as covered until their real content pages.
- Replace the old left-footer text `线上录课课件` with `framework_progress_label` on normal content pages. The value is the current second-level outline heading/root child for the knowledge being taught. Structural pages (`cover`, `lesson-overview`, `section-cover`, `summary`) may omit this left-footer progress text.
- Preserve detailed-outline sibling lists as complete visible lists; split slides if they do not fit.
- Do not invent a teaching label unanchored to the current node, an ancestor path, or a stated relationship. Generic labels such as `对比 A`, `结构顺序 A`, `左侧`, `方案 A/B` are failed screen copy.
- Do not render producer-facing source evidence as courseware. `本页顺序`, `对应节点`, `来源路径`, `source_node`, `screen_evidence`, coverage notes, and production language are metadata, not learner copy.
- Treat every deck as one component of the same self-media and editing curriculum. Preserve shared terminology, prerequisites, difficulty progression, and lesson boundaries; do not duplicate a neighboring lesson's main task.
- Put definitions, explanations, examples, and visual interpretation on the slide. Do not create question-only, keyword-only, or separate lecture-notes deliverables.
- If a layout cannot display every required sibling item, block, or evidence phrase, split the slide or choose another layout. Never let the renderer drop, shrink, or hide content.
- Keep source images inside knowledge pages as teaching units. A slide may use at most three readable source images.
- Deck length follows teaching units, source nodes, source images, and readability, not the template's page count.
- Template fidelity means the template's colors, fonts, type scale, alignment axes, spacing, density, color mass, and overall layout language reproduced as editable composition. Do not reduce template analysis to square modules or force every element into box grids; element geometry is flexible when the overall composition remains coordinated and template-like. Do not copy Canva's native vector/shape elements; there is no native-element reuse in this skill.
- A case image must visibly teach the current source point and its enumerated ideas. For image pages, record `case_visual_map` linking visible slide points to concrete image details. Pure text pages must first consider a generated case image or editable diagram and use `text-only-exception` only with a concrete bypass reason. Generated images carry no baked-in Chinese, UI labels, watermarks, or promotional text; labels stay editable slide text.
- When any quality issue appears, run the director acceptance lock: mark the deck not approved, trace to the earliest responsible stage, fix it, rebuild, and re-run the non-regression checklist.
- Do not modify or overwrite the original Canva template.

## Resources

- `scripts/extract_source.py`: extract a canonical source map from supported formats.
- `scripts/validate_source_map.py`: validate hierarchy and record the user-declared mode.
- `scripts/audit_deck.py`: deterministic guard for coverage, source order, per-node screen evidence, mode, scope, hierarchy flattening, forbidden terms, meaningful structured labels, and PPTX/layout checks. Structural hard errors only — it does not judge teaching quality.
- `scripts/build_deck.mjs`: generate editable 16:9 slides using the selected template profile.
- `scripts/make_contact_sheet.py`: create a labeled full-deck review sheet.
- `references/`: the three references and the non-regression checklist listed above.
- `assets/template-reference/`: immutable visual reference for Canva template `DAHM5fsVEB0` when no other template is selected.
- `assets/golden-layouts/`: approved knowledge-page composition references.
