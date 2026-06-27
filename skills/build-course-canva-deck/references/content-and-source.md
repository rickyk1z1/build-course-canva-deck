# Content and source

This reference covers source intake, the detailed/sparse mode contract, the deck-level chapter spine, the zero-basis teaching standard, the curriculum-system boundary, the source coverage ledger, and screen copy as the teaching layer. The goal is a deck a careful human instructor would build: the source hierarchy is visible as presentation structure, page logic is coherent, and a zero-basis learner understands each page without guessing.

## Teaching standard

Write for zero-basis self-media editing learners who need a fast, directionally correct mental model. Prefer familiar objects, visible relationships, and plain language over terminology debates. Keep technical statements accurate enough to guide action without turning an introductory lesson into an advanced workflow.

Screen copy carries the knowledge. Each normal knowledge slide must be understandable without narration and contains a conclusion-style title, a self-contained explanation, enough structured points/comparisons/steps to preserve the current source branch without filler, and a visual interpretation when an image is present. Do not create a separate lecture-notes deliverable. Optional `speaker_notes` may exist only as short transition reminders; they may be empty. Never use notes to carry knowledge required for comprehension, and never render notes, source-order proof, coverage metadata, or production metadata on a slide.

Preserve user-supplied examples and metaphors instead of replacing them with more technical ones. Keep the direction of the explanation correct; ask before altering a metaphor that may reverse the intended logic.

## Curriculum system boundary

Treat every deck as one chapter of the same self-media and editing curriculum, not an independent article. A single lesson serves overall knowledge progression, shared terminology, and module division.

Before authoring, discover the lesson's position: search the workspace for the course map, knowledge tree, existing courseware titles, curriculum notes, and neighboring lessons. Create `curriculum-context.json`:

```json
{
  "system_name": "自媒体与视频剪辑课程体系",
  "module": "当前所属模块",
  "course_role": "本课在整体体系中负责解决的问题",
  "prerequisite_lessons": [],
  "next_lessons": [],
  "shared_terms": {},
  "neighbor_topics": [],
  "excluded_neighbor_topics": []
}
```

If the workspace cannot confirm the module position, prerequisites, or neighbors, ask the user. Do not invent course structure.

Boundary rules: reuse established terminology, metaphor, difficulty, and phrasing; this lesson only carries its own teaching task; review prerequisites briefly without re-teaching them in full; for downstream lessons leave a one-line cognitive hook, do not teach ahead; record cross-references instead of duplicating a neighbor's full coverage; do not reorder the authoritative outline's levels or sibling order under the excuse of "optimizing flow."

Keep an internal `课程体系关联说明.md` in the output folder recording this lesson's position, prerequisites used, downstream hooks left, excluded neighbor topics, and shared/new terminology. This file never goes onto a Canva page.

## Mode contract

The user explicitly replies `细纲` or `粗纲`. Never infer the mode from length, hierarchy, file type, or apparent detail.

**`细纲` / detailed** — preserve the source path, level hierarchy, sibling order, examples, metaphors, claims, and scope. Improve sentence clarity, grouping, wording, and visuals only. Do not introduce concepts, workflows, software operations, or adjacent branches the source did not develop. Do not treat the outline as a loose material pool. Verify unstable facts when necessary, but flag a substantive conflict for the user instead of silently expanding. Use the accepted `影像基础参数` deck as the depth baseline.

**`粗纲` / sparse** — produce more detailed content than the baseline while staying faithful to the supplied tree. Expand vertically inside each existing node with: a direct definition; why it matters or what causes it; its relationship to sibling/parent nodes; a familiar example or analogy; a common misconception when useful; a practical boundary. Do not expand horizontally. For every addition: map it to one original source node, classify it with an allowed kind (`definition`, `cause`, `relationship`, `example`, `misconception`, `boundary`), mark relevance `direct`, record authoritative HTTPS evidence, and remove it if explaining it requires a new branch, if it belongs to `excluded_neighbor_topics`, or if it conflicts with `course_role`.

## Deck-level chapter spine

The deck sequence is part of the teaching, not a styling layer added after writing copy. Build the deck from the source hierarchy before choosing page layouts:

1. Optional `cover` page for the course title.
2. Exactly one `lesson-overview` page as the first non-cover page. It introduces what this lesson solves and previews the source's second-level sections in order.
3. For each root child / second-level outline heading, create exactly one `section-cover` page before any content from that section. This page behaves like a chapter or subsection divider embedded in the presentation, not a decorative title slide.
4. After each section cover, place that section's descendant content pages in source path and sibling order. Page layouts may vary inside a section according to teaching relationship and visual need.
5. End with exactly one `summary` page that consolidates the lesson's key takeaways across sections.

Do not flatten source headings into ordinary knowledge pages to save page count. Do not begin teaching a section before its section-cover page. Do not mix two top-level sections on one normal knowledge slide. The layout system may repeat fixed structural pages (`lesson-overview`, `section-cover`, `summary`) because they signal course structure; layout variety is expected inside the content pages of each section.

## Source intake

1. Enumerate supplied files and compute hashes.
2. Resolve the authoritative source with the user if more than one file could control content. Do not merge by assumption.
3. Extract text, hierarchy, order, notes, and embedded images via `scripts/extract_source.py` into `source-map.json`.
4. For PDFs or exported mind maps, render and visually inspect hierarchy; text order alone is not hierarchy evidence.
5. Ask the user to choose `细纲` or `粗纲`; record the explicit reply with `scripts/validate_source_map.py --mode detailed|sparse --write`.
6. Discover the curriculum map and neighbors; create `curriculum-context.json`.

Deterministic extraction routes: `.xmind` (parse `content.json` or legacy `content.xml`, keep topic order and resources); `.opml`/`.mm` (XML outline order); `.docx` (paragraph styles + `word/media`); `.md`/`.txt` (heading and list order); `.pdf` (page text and images, then visually reconstruct hierarchy). If scan quality or connectors are unreadable, stop and request a clearer export.

## Source coverage ledger

Build a coverage ledger with one row per included source node:

`source node -> source path -> slide number -> visible evidence -> visual treatment -> status`

Rules:

- `source_node_ids` must match `source_node_treatments` exactly and in order.
- `screen_evidence` must be an exact visible learner-facing phrase from the slide title, explanation, bullets, caption, or blocks. Metadata-only coverage is a failure. Producer-facing evidence on the slide is also a failure: never write `本页顺序`, `本页内容`, source paths, node IDs, coverage notes, or "this page covers…" prose just to satisfy the ledger.
- Distinct source nodes on the same slide need distinct evidence phrases unless the source text is identical.
- Evidence should appear on the page in source order.
- Every included node is covered exactly once.

For hierarchical outlines, record the current source path for each slide group before writing copy. In detailed mode the path and sibling order are the teaching sequence; do not regroup nodes into a new narrative because it sounds smoother. Preserve sibling enumerations as complete visible peer items: if a node has four peer children, the slide shows four peer items in source order or splits them into consecutive slides. Do not rely on speaker notes, generated images, or metadata to carry omitted siblings. Keep distinctive wording in its source position; do not pull a later node's phrase into an earlier title unless the source already repeats it there.

Coverage mapping for structural pages: the `lesson-overview` page covers the root lesson node; each `section-cover` page covers exactly one root child / second-level heading with `coverage_status: section-heading`; the final `summary` page may have no source-node mapping when it synthesizes previously covered nodes. Normal knowledge pages cover descendants inside the current section only.

## Authoring standard

- Preserve source order before optimizing transitions; preserve every source node before adding vertical explanation.
- Preserve the deck spine before optimizing page count or visual rhythm: total overview, section cover, section content, next section cover, final summary.
- Give each knowledge page one clear teaching point with enough visible points to preserve the branch; do not add filler to hit a count.
- Use comparison/table/two-panel layouts only when the content relationship is real and named in learner-facing labels.
- Keep pages readable without narration.
- Keep production evidence off the screen: source paths, hierarchy proof, coverage notes, and planning labels belong in spec fields or review files, never in learner-facing title/explanation/bullets/caption/blocks.
- Do not invent a teaching label unanchored to the current node, an ancestor path, or a stated relationship. Generic labels such as `对比 A`, `结构顺序 A`, `左侧`, `方案 A/B` are failed copy.

## Research policy

Use official documentation, standards bodies, product manuals, or primary research first; secondary sources only when primary ones do not explain a beginner-facing concept. Keep URLs and claim notes in the evidence ledger. Do not display citations on slides unless requested.
