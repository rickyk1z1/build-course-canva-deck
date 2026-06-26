---
name: build-course-canva-deck
description: Use when creating or substantially revising a Canva recording deck from a course outline, mind map, PDF, document, or knowledge tree for this course system.
---

# Build Course Canva Deck

Create a complete recording presentation from a course knowledge outline. The target is a deck that reads like a careful human instructor built it: the source hierarchy is visible, page logic is coherent, each visual teaches the current point, and a zero-basis learner can understand the page without guessing. Treat the accepted `影像基础参数` deck as the content-depth and visual-quality baseline, not as reusable subject matter. Treat the Canva template as configurable: use the bundled `DAHM5fsVEB0` profile only when the user has not supplied a different template.

## Non-Negotiable Checkpoint

1. Inspect every supplied source before authoring.
2. If sources conflict or overlap, ask the user to choose one authoritative source. Do not merge them by assumption.
3. After inspecting the authoritative source, ask the user to reply exactly with either `细纲` or `粗纲`.
4. Do not infer the mode from length, hierarchy, file type, or apparent detail. Do not proceed until the user chooses.
5. Record the choice in `source-map.json` with `validate_source_map.py --mode detailed|sparse --write`.

Before authoring, read [references/curriculum-system.md](references/curriculum-system.md). Discover the existing curriculum map, neighboring lessons, shared terminology, and this lesson's role. If the workspace does not reveal the lesson's position, ask the user for the missing curriculum context instead of inventing it.

## Mode Contract

- `细纲` / `detailed`: preserve the source path, level hierarchy, sibling order, examples, metaphors, claims, and scope. Improve teachability, wording, and visuals only. Do not treat the outline as a loose material pool.
- `粗纲` / `sparse`: add definitions, causes, relationships, examples, misconceptions, and boundaries only inside existing branches. Every addition must map to one original node and authoritative evidence. Never create a new branch or low-relevance tangent.

Read [references/content-policy.md](references/content-policy.md) before writing either mode.

## Mandatory Four-Role Workflow

For any request to build or substantially revise a course deck, use the four proposal-only roles under one director. This skill has no single-orchestrator authoring fallback for deck builds.

If subagent tooling is unavailable, runtime policy requires explicit user authorization that has not been given, or the user disables workers, stop after any safe source/mode intake and report the blocker. Do not continue into slide planning, screen copy, visual planning, PPTX generation, or Canva delivery as a single orchestrator. Simple read-only questions may still be answered directly without entering the deck-build workflow.

Read [references/agent-hierarchy.md](references/agent-hierarchy.md) and [references/role-standards.md](references/role-standards.md) before dispatching workers.

```text
总导演 / build-course-canva-deck
├── 课程统筹师
├── 原稿场记
├── 课堂编剧
└── 视觉分镜师
```

- **总导演 / build-course-canva-deck** owns all durable writes and external actions: `source-map.json`, `curriculum-context.json`, `deck-spec.json`, generated image assets, PPTX generation, mechanical audit reports, Canva import, Canva edits, and final approval. It also owns process review after each proposal and final learner-facing review before delivery.
- **课程统筹师** defines curriculum position, prerequisites, neighboring boundaries, shared terms, and handoff topics. Its self-check prevents adjacent-course drift.
- **原稿场记** preserves the source hierarchy, source path, sibling order, examples, metaphors, source images, and slide grouping. Its self-check prevents the mind map from being flattened or rearranged.
- **课堂编剧** writes learner-facing screen copy from approved source-node excerpts. Its self-check prevents invented labels, missing explanations, narration-only knowledge, source-level mismatch, and visible production/meta copy.
- **视觉分镜师** plans source images, generated-image candidates, editable diagrams, template references, layout variety, and fit. Its self-check prevents meaningless comparison/table blocks, generated cases that do not visibly teach the current knowledge point, repeated page structures, text-image collisions, decorative visuals, and whole-template-page pasting.

Before dispatching any worker, the director creates a scoped brief in `scratch/agent-briefs/<role>.brief.md` or `scratch/agent-briefs/<role>.brief.json`. Keep the brief short and readable. It must tell the worker:

- the director's concise recap of the user's current non-negotiable requirement for this run;
- the exact proposal to produce and where to write it;
- which source excerpts, context files, rendered pages, or template references it may read;
- the current source path, node scope, mode, and curriculum boundary;
- the role standards that matter for this pass;
- any plug-in expert skill the worker may invoke, and which part of that skill is relevant;
- what concrete evidence the worker must show before the director can trust the proposal;
- what to report as an open question instead of guessing.

Workers read only their brief plus files listed in `allowed_read_paths`. If a worker needs more context, it writes a `context_request` in its proposal instead of independently reading broad source, curriculum, template, or Canva files.

Worker proposals must include a `self_check` section, but it is not a checkbox ritual. Each answer must point to concrete source paths, slide groups, visible phrases, layout decisions, or unresolved risks. Generic answers such as "已检查" or "符合要求" are not mergeable. Do not create a separate final-review worker, lecture-notes worker, or fifth review role.

Use workers to reduce context piling, not to make the process more mechanical. Each worker returns a compact expert handoff that downstream roles can trust without rereading broad context: 课程统筹师 gives a boundary card, 原稿场记 gives the source-order spine, 课堂编剧 gives the zero-basis teaching script spine, and 视觉分镜师 gives the visual-understanding map. The director passes these handoffs, not every upstream file, unless a worker explicitly requests more context.

Supporting presentation/design/Canva skills are plug-in expert capabilities for the four roles. The director controls the macro route: goal recap, source/order boundary, role scope, allowed expert slots, conflict resolution, durable writes, and final acceptance. Within that boundary, a worker may invoke its authorized expert skill directly and return the expert guidance as part of its proposal. Plug-in experts cannot replace this skill's source intake, four-role workflow, learner-facing courseware standard, or director acceptance lock.

The director's review is simple and human-facing:

1. After each proposal, check the role's `self_check` before merging.
2. When the director changes grouping, wording, fallback visuals, or layouts, re-check the affected role standard directly because no worker has reviewed that new change.
3. Run scripts only as mechanical guards for extraction, coverage, density, forbidden terms, PPTX text, and obvious structural errors. A passing report is never approval by itself.
4. After rendering, inspect the full deck as a learner: source hierarchy, page logic, readable layout, meaningful labels, no repeated layout run, no overlap, no clipped text, no backstage/source-tracking text, and no page whose structure only makes sense to the producer.

The director also owns the global acceptance contract. A deck is approved only when all of these are true at the same time: source nodes are complete and in order, screen copy is readable without narration, pages are not crowded, layout rhythm visibly changes for teaching reasons, visuals make the current point easier to understand, and Canva delivery is editable and reviewable. No role proposal, script, audit report, or field value can trade one of these standards away.

When any quality issue appears, do not patch only the visible symptom. Mark the current deck as not approved and run a director loop review across the chain: source grouping -> screen copy -> visual plan -> deck spec -> PPTX render/contact sheet -> Canva delivery. Identify which earlier stage allowed the issue, revise the earliest responsible stage, then rebuild and re-review. If an audit passes but the contact sheet or learner review fails, the deck still fails and the workflow/check must be tightened; do not treat field compliance as success.

## Required Workflow

1. Read [references/workflow.md](references/workflow.md) and create an external scratch workspace.
2. Run `scripts/extract_source.py` to create `source-map.json`. For PDFs, also render and visually inspect every relevant page; extracted text alone is not hierarchy evidence.
3. Complete the mandatory source and mode checkpoint above.
4. Create four scoped worker briefs and dispatch in the staged order from `agent-hierarchy.md`. If workers cannot be dispatched, stop and report the blocker instead of performing those phases sequentially in the orchestrator.
5. Create `curriculum-context.json` and lock the lesson's module, prerequisites, downstream lessons, shared terms, and neighboring topics that must remain out of scope.
6. Build a source coverage matrix in source order. Include every valid node exactly once. Each slide group must preserve the XMind/source path and sibling order, not just monotonic node IDs.
7. Create `deck-spec.json` using the schema in [references/workflow.md](references/workflow.md).
8. Write one learner-facing screen-copy layer and one zero-basis recording script spine that follow the approved source order. Source order, source path, coverage, and review evidence belong in `source_node_treatments`, the coverage ledger, or notes for the producer, never in rendered slide text. Optional `speaker_notes` may exist only as short internal transition hints and must never contain knowledge required for comprehension or page logic.
9. Read [references/visual-system.md](references/visual-system.md), then create the visual plan in staged passes. For long decks, first create a template style atlas from the selected template's overall layout language, then map each slide to a content-appropriate structure family before PPTX generation. Every normal knowledge slide must reuse a source case image, rebuild a source visual, include a generated teaching image, or use an editable explanatory diagram/table that is fused into the page.
10. Read [references/design-system.md](references/design-system.md), [references/page-design-quality.md](references/page-design-quality.md), and [references/role-standards.md](references/role-standards.md), then build the editable PPTX with `scripts/build_deck.mjs` and `@oai/artifact-tool`.
11. Run `scripts/audit_deck.py`, render every slide, create a contact sheet, and fix all mechanical errors.
12. Perform the director's final learner review before Canva import. This review has priority over script success: title-to-source-path fit, meaningful block labels, page-to-page hierarchy order, layout variety, no overlap, no duplicate text, no pasted template pages, no nonsense comparison/table framing, no production/source-tracking text, no machine-like field compliance that a human learner cannot read, and no contact-sheet repetition hidden behind unique field names.
13. Read [references/canva-delivery.md](references/canva-delivery.md), run the Canva connector tool-discovery and template access preflights, import the verified PPTX as a new Canva design when the connector import tool is available, and leave the source template unchanged.
14. Verify every Canva page, show the complete preview, and ask for one final approval. Save draft edits only after explicit approval.
15. Re-read the saved Canva design and confirm the forbidden-language count is zero before returning the final link.

## Hard Boundaries

- Keep the source's teaching order and hierarchy. In detailed mode, the mind-map path is the course structure; do not flatten first/second/third-level topics into a reorganized script.
- Preserve detailed-outline sibling lists as complete visible lists. If they do not fit, split slides.
- Do not invent a teaching label that is not anchored to the current source node, an ancestor source path, or a clearly stated relationship. Generic labels such as `对比 A`, `对比 B`, `结构顺序 A`, `结构顺序 B`, `左侧`, `右侧`, or `方案 A/B` are examples of failed screen copy, not the complete list.
- Do not pull distinctive wording from later source nodes into earlier titles or labels unless the source already repeats it there.
- Do not render producer-facing source evidence as courseware. Phrases such as `本页顺序`, `本页内容`, `对应节点`, `来源路径`, `source path`, `screen_evidence`, or coverage notes are metadata, not learner copy. If the only way to prove hierarchy is to describe the page construction, the screen copy is not finished.
- Treat every deck as one component of the same self-media and editing curriculum. Preserve shared terminology, prerequisites, difficulty progression, and lesson boundaries.
- Do not duplicate a neighboring lesson's main teaching task. Record the handoff to that lesson instead of expanding into it.
- Use one teaching node or one tight source branch per slide by default. Do not treat `source_node_ids` as coverage by itself: every mapped source node must have visible `source_node_treatments.screen_evidence`.
- Put definitions, explanations, examples, and visual interpretation on the slide. Do not create question-only or keyword-only pages.
- Do not create a separate lecture-notes deliverable. Screen copy must carry the teaching; optional `speaker_notes` are internal transition hints only.
- If a layout cannot display every required sibling item, block, or evidence phrase, split the slide or choose a different layout before building. Never let a renderer silently drop, shrink, or hide content.
- Keep source images inside knowledge pages. Treat source reference images and case images as teaching units, not decoration.
- A slide may use at most three independent source images, and only when all images remain readable and the visual plan records the grouping reason.
- Deck length follows teaching units, source nodes, source images, and learner readability, not the number of pages in the selected template bank.
- Treat page design as a first-class requirement, not a skin. The template's typography scale, alignment axes, proximity, contrast hierarchy, image slots, and module spacing must be reflected in the local PPT/contact sheet before Canva import.
- Template reuse is atomic. Copy or reuse only the specific verified native element/group/frame needed for the course page. Never paste an entire template page into the final deck as a shortcut for "using template elements"; if the available tool only supports whole-page duplication, record the blocker and use a template-inspired editable composition or ask for an approved fallback.
- For abstract concepts, build concrete visual bridges: familiar-object metaphors, before/after comparisons, process chains, simplified diagrams, or source screenshots with labels.
- Always run an image-generation review before local PPT generation. Source-rich decks preserve source images first; image-poor decks treat generated teaching images as a primary build input.
- A generated case image must visibly teach the current source point. Record the knowledge anchor, concrete visible detail, and quick learner takeaway before generation, then reject images that only match the mood or palette.
- Generated images must not contain baked-in Chinese, UI labels, watermarks, or promotional text. Labels, arrows, and explanations must be editable slide text.
- For long decks, record `visual_plan.rendered_pattern` or `visual_plan.thumbnail_pattern` as a plain description of the actual contact-sheet geometry. This is not a compliance label; if the rendered thumbnail contradicts it, the director treats the page as failed and revises the plan/build rather than renaming the field.
- Never display production language such as `PDF`, `原稿`, `来源文档`, `制作说明`, `图旁注明`, `详细讲稿`, `预计讲解时间`, `视觉说明`, `对应节点`, prompts, placeholders, source-tracking labels, or `Genji 是真想教会你`.
- Do not modify or overwrite the original Canva template.

## Resources

- `scripts/extract_source.py`: extract a canonical source map from supported formats.
- `scripts/validate_source_map.py`: validate hierarchy and record the user-declared mode.
- `scripts/audit_deck.py`: mechanical guard for coverage, hierarchy risk, source-node density, per-node screen evidence, mode, scope, screen-copy, layout repetition, and PPTX text checks.
- `scripts/build_deck.mjs`: generate editable 16:9 slides using the selected template profile.
- `scripts/make_contact_sheet.py`: create a labeled full-deck review sheet.
- `references/agent-hierarchy.md`: four proposal roles, role boundaries, continuity, and self-check outputs.
- `references/role-standards.md`: distributed role standards and the director's lightweight review checklist.
- `references/visual-system.md`: rules for source case images, generated diagrams, and slide-level visual plans.
- `references/design-system.md`: rules for Canva template fidelity, fonts, colors, and layout rhythm.
- `references/page-design-quality.md`: rules for title scale, alignment, proximity, contrast, image evidence blocks, and contact-sheet review.
- `references/canva-delivery.md`: Canva connector preflight, cross-device template access, and browser fallback rules.
- `assets/template-reference/`: immutable fallback visual reference for Canva template `DAHM5fsVEB0` when no other template is selected.
- `assets/golden-layouts/`: approved knowledge-page composition references.
