# Content and source

This reference covers source intake, the detailed/sparse mode contract, optional lecture-script reference, the deck-level chapter spine, the zero-basis teaching standard, the curriculum-system boundary, the source coverage ledger, and screen copy as the teaching layer. The goal is a deck a careful human instructor would build: the authoritative source hierarchy is visible as presentation structure, the real teaching chapter nodes are identified before authoring, page logic is coherent, and a zero-basis learner understands each page without guessing.

## Teaching standard

Write for zero-basis self-media editing learners who need a fast, directionally correct mental model. Prefer familiar objects, visible relationships, and plain language over terminology debates. Keep technical statements accurate enough to guide action without turning an introductory lesson into an advanced workflow.

Screen copy carries the knowledge. Each normal knowledge slide must be understandable without narration and contains a conclusion-style title, a self-contained explanation, enough structured points/comparisons/steps to preserve the current source branch without filler, and a visual interpretation when an image is present. Do not create a separate lecture-notes deliverable. Optional `speaker_notes` may exist only as short transition reminders; they may be empty. Never use notes to carry knowledge required for comprehension, and never render notes, source-order proof, coverage metadata, curriculum exclusions, or production metadata on a slide.

Before layout, create `screen.teaching_expansion` for every normal knowledge slide:

```json
{
  "mode_handling": "sparse-vertical-expansion | detailed-clarification",
  "learner_takeaway": "学员看完这一页能判断或说出的结论",
  "source_based_explanation": "可直接上屏的解释，不是制作思路",
  "example_or_judgment_cue": "熟悉例子、判断标准、常见误区或图像观察提示",
  "display_priority": ["本页必须上屏的短句，按重要性排序"],
  "internal_only": ["不能上屏的邻课边界、生产约束或证据"]
}
```

The visible `title`, `screen.explanation`, `screen.bullets`, `screen.blocks`, and `screen.caption` are selected from this learner-facing expansion and the source text. They must not be selected from worker briefs, source ledger fields, scope notes, audit errors, or curriculum exclusions. If a layout has empty text space, fill it with a useful definition, cause, relationship, example, misconception, judgment cue, or image interpretation from `teaching_expansion`; otherwise leave the space open or choose a more image-led layout. Empty space is never a reason to display construction/process wording such as "先知道整节课怎么展开" or boundary wording such as "不进入软件按钮".

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

Keep boundary decisions internal. `excluded_neighbor_topics`, scope exclusions, and "do not cover X" reminders belong in `curriculum-context.json`, `scope_check`, `课程体系关联说明.md`, or delivery notes, never in learner-facing title, explanation, bullets, caption, or blocks. A cover/overview bullet such as `不进入软件按钮`, `不讲快捷键`, `不涉及调色`, or similar negative scope wording is failed screen copy. If the learner needs orientation, write the positive teaching value instead, for example "先建立包装判断" rather than "不进入软件按钮."

Keep an internal `课程体系关联说明.md` in the output folder recording this lesson's position, prerequisites used, downstream hooks left, excluded neighbor topics, and shared/new terminology. This file never goes onto a Canva page.

## Mode contract

The user explicitly replies `细纲` or `粗纲`. Never infer the mode from length, hierarchy, file type, or apparent detail.

**`细纲` / detailed** — preserve the source path, level hierarchy, sibling order, examples, metaphors, claims, and scope. Improve sentence clarity, grouping, wording, and visuals only. Screen copy may add connective phrasing, definitions already implied by the source, observation cues for source images, and cleaner peer labels, but may not introduce concepts, workflows, software operations, or adjacent branches the source did not develop. Do not treat the outline as a loose material pool. Verify unstable facts when necessary, but flag a substantive conflict for the user instead of silently expanding. Use the accepted `影像基础参数` deck as the depth baseline.

**`粗纲` / sparse** — produce more detailed content than the baseline while staying faithful to the supplied tree. Expand vertically inside each existing node with: a direct definition; why it matters or what causes it; its relationship to sibling/parent nodes; a familiar example or analogy; a common misconception when useful; a practical boundary. Do not expand horizontally. These expansions are meant to become learner-facing page content, not hidden notes: use them to replace empty layout areas with concrete teaching value. For every addition: map it to one original source node, classify it with an allowed kind (`definition`, `cause`, `relationship`, `example`, `misconception`, `boundary`), mark relevance `direct`, record authoritative HTTPS evidence, and remove it if explaining it requires a new branch, if it belongs to `excluded_neighbor_topics`, or if it conflicts with `course_role`.

## Optional lecture-script reference

If the user supplies both an authoritative outline/XMind and a lecture script, the outline remains the only authoritative source. The script is optional reference material for the screen-copy pass: it can help the classroom writer choose more natural phrasing, understand the intended emphasis, and avoid screen copy that sounds disconnected from the eventual recording.

Record this in `deck-spec.json` only as:

```json
{
  "course": {
    "reference_script": {
      "path": "path/to/script.md",
      "authoritative": false,
      "usage": "screen-copy-reference-only"
    }
  }
}
```

The reference script must not become `source-map.json`, `outline_mode`, `chapter_spine`, `source_node_ids`, `source_node_treatments`, source-image anchoring, generated-image obligation, or coverage evidence. Do not ask the user to provide a script by default; this is only used when the user already supplies one. Never render reference-process phrases such as `根据讲稿整理`, `这一段讲的是`, `本段讲的是`, or `讲稿整理`.

## Source-structure reading pass

Before building the deck spine, read the whole source as a teaching structure. Read the whole source tree as a teaching outline. Do not assume that root children, second-level headings, or any fixed depth are chapters. Many course mind maps use one or more wrapper levels such as a course title, framing question, ability statement, or administrative container before the real chapter nodes begin.

Create and approve an ordered `chapter_spine`:

```json
[
  {
    "source_node_id": "n0012",
    "title": "源节点标题",
    "source_path": "root > wrapper > chapter",
    "depth": 3,
    "reason": "why this node behaves as a teaching chapter",
    "preview_child_node_ids": ["n0013", "n0020"]
  }
]
```

Chapter-selection rules:

- Choose chapter nodes from the source, not invented labels. A chapter node is a source node whose descendants form a coherent teachable unit and whose siblings at the same chosen chapter level form the lesson's main sequence.
- Chapter nodes must be in source order and must not overlap: a selected chapter cannot be an ancestor or descendant of another selected chapter.
- If the root child is only a wrapper, do not create a section-cover for it. Cover wrapper/title/framing nodes on the lesson overview while keeping every source node covered exactly once.
- Prefer the shallowest depth that represents real teaching units, but allow third, fourth, or deeper chapter starts when upper levels are containers.
- If two plausible chapter spines produce materially different deck structures, stop and ask the user to choose instead of guessing.
- Mirror the approved list in `deck-spec.json` as `course.chapter_spine`. The audit uses this field; if it is absent, the audit falls back to root children only for older/simple specs.

## Deck-level chapter spine

The deck sequence is part of the teaching, not a styling layer added after writing copy. Build the deck from the source hierarchy before choosing page layouts:

1. Optional `cover` page for the course title.
2. Exactly one `lesson-overview` page as the first non-cover page. It introduces what this lesson solves, covers the root and any non-chapter wrapper/framing nodes, and previews the approved chapter nodes in order.
3. For each approved `chapter_spine` node, create exactly one `section-cover` page before any content from that chapter. This page behaves like a chapter or subsection divider embedded in the presentation, not a decorative title slide. Its small text previews that chapter's direct child headings or adjacent child-heading groups as compact agenda cues; it does not state the chapter's conclusions and does not reuse the exact learner-facing wording that will appear as a normal page title, evidence phrase, shortcut list, bullet, block heading, or explanation.
4. After each section cover, place that chapter's descendant content pages in source path and sibling order. Page layouts may vary inside a section according to teaching relationship and visual need.
5. End with exactly one `summary` page that consolidates the lesson's key takeaways across sections.

Do not flatten source headings into ordinary knowledge pages to save page count. Do not begin teaching a chapter before its section-cover page. Do not mix two approved chapters on one normal knowledge slide. Do not use section-cover bullets for conclusions, takeaways, promises, value judgments, dense shortcut lists, or full child-page teaching copy. If a child heading is itself a complete operation string or teaching statement, rewrite the section-cover preview as a shorter agenda label while preserving the child node in `section_preview_items`; teach the full phrase on the normal knowledge page only. The layout system may repeat fixed structural pages (`lesson-overview`, `section-cover`, `summary`) because they signal course structure; layout variety is expected inside the content pages of each section.

## Source intake

1. Enumerate supplied files and compute hashes.
2. Resolve the authoritative source with the user if more than one file could control content. Do not merge by assumption.
3. Extract text, hierarchy, order, notes, and embedded images from the authoritative outline via `scripts/extract_source.py` into `source-map.json`. For `.xmind`, every topic-attached image must carry the textual topic anchor as `source_node_id`, `source_node_text`, `source_path_ids`, `source_path_text`, and `source_path`; image-only child topics inherit the nearest textual parent topic. A non-thumbnail image without a topic anchor is an extraction blocker, not a visual-storyboard decision.
4. For PDFs or exported mind maps, render and visually inspect hierarchy; text order alone is not hierarchy evidence.
5. Ask the user to choose `细纲` or `粗纲`; record the explicit reply with `scripts/validate_source_map.py --mode detailed|sparse --write`.
6. Read the full source structure and approve `chapter_spine`; create `curriculum-context.json`.

Deterministic extraction routes: `.xmind` (parse `content.json` or legacy `content.xml`, keep topic order and resources); `.opml`/`.mm` (XML outline order); `.docx` (paragraph styles + `word/media`); `.md`/`.txt` (heading/list/paragraph order); `.pdf` (page text and images, then visually reconstruct hierarchy). If scan quality or connectors are unreadable, stop and request a clearer export.

## Source coverage ledger

Build a coverage ledger with one row per included source node:

`source node -> source path -> slide number -> visible evidence -> visual treatment -> status`

Rules:

- `source_node_ids` must match `source_node_treatments` exactly and in order.
- `screen_evidence` must be an exact visible learner-facing phrase from the slide title, explanation, bullets, caption, or blocks. Metadata-only coverage is a failure. Producer-facing evidence on the slide is also a failure: never write `本页顺序`, `本页内容`, source paths, node IDs, coverage notes, "this page covers…" prose, or construction/process wording such as "先知道整节课怎么展开" just to satisfy the ledger or fill a layout slot.
- Distinct source nodes on the same slide need distinct evidence phrases unless the source text is identical.
- Evidence should appear on the page in source order.
- Every included node is covered exactly once.

For hierarchical outlines, record the current source path for each slide group before writing copy. In detailed mode the path and sibling order are the teaching sequence; do not regroup nodes into a new narrative because it sounds smoother. Preserve sibling enumerations as complete visible peer items: if a node has four peer children, the slide shows four peer items in source order or splits them into consecutive slides. Do not rely on speaker notes, generated images, or metadata to carry omitted siblings. Keep distinctive wording in its source position; do not pull a later node's phrase into an earlier title unless the source already repeats it there.

Coverage mapping for structural pages: the `lesson-overview` page covers the root lesson node and any non-chapter wrapper/framing nodes that are not section-cover chapters; each `section-cover` page covers exactly one approved `chapter_spine` node with `coverage_status: section-heading`; the final `summary` page may have no source-node mapping when it synthesizes previously covered nodes. A section-cover also records `section_preview_items` for the immediate child headings shown as small text, but those child nodes are not considered covered by the section-cover. Normal knowledge pages cover descendants inside the current approved chapter only.

`section_preview_items` shape:

```json
[
  {
    "source_node_id": "n0012",
    "screen_evidence": " visible phrase from the section-cover bullet "
  }
]
```

Use `source_node_ids` instead of `source_node_id` only when one preview bullet deliberately groups adjacent child headings; keep grouped IDs in source order.

Section preview evidence is allowed to be a compact agenda label, not necessarily the full source-node text, but it must be visible on the section-cover page and must stay shorter than the later knowledge-page copy. Never use ellipses (`…` or `...`) to squeeze a child list into a section cover. If the cue needs multiple verbs, shortcuts, or slash-separated operations, split it into normal content pages and leave only the group label on the cover.

## Framework progress footer

Normal content pages use the left footer as a knowledge-framework progress label, not as a generic courseware stamp. Set `framework_progress_label` to the current approved chapter heading for the page's mapped knowledge nodes. Example: if `chapter_spine` selects `选题方向规划`, pages under that chapter use `选题方向规划` even if it is depth 3 or 4 in the extracted source.

Do not render `线上录课课件` as the left footer. Structural pages (`cover`, `lesson-overview`, `section-cover`, `summary`) may omit the left-footer progress label because they already signal deck structure. If a structural page does include it, it must not use the static courseware stamp.

## Authoring standard

- Preserve source order before optimizing transitions; preserve every source node before adding vertical explanation.
- Preserve the deck spine before optimizing page count or visual rhythm: total overview, section cover, section content, next section cover, final summary.
- Put the current approved chapter heading in `framework_progress_label` for normal content pages; omit it on structural pages when it would add visual noise.
- Cover and lesson-overview bullets state positive learner outcomes, the lesson's major chapter sequence, or what the learner will be able to judge/do after the lesson. They must not state excluded neighboring tasks as "不进入/不讲/不涉及 X"; those are production boundaries, not student-facing teaching points.
- Every normal knowledge page must have `screen.teaching_expansion` before visual layout. In sparse mode, this is where vertical expansion lives and later becomes visible explanation, examples, judgment cues, and image prompts. In detailed mode, this records source-faithful clarification and observation cues. If an optional lecture script is present, it can refine the wording inside the current source node's scope, but it cannot add new coverage or reorder the page. If the expansion cannot yield useful visible copy, split/merge/reframe the page instead of filling layout space with producer-facing text.
- Give each knowledge page one clear teaching point with enough visible points to preserve the branch; do not add filler to hit a count.
- Use comparison/table/two-panel layouts only when the content relationship is real and named in learner-facing labels.
- Keep pages readable without narration.
- Keep every visible phrase complete. Do not manually or automatically shorten learner copy with `…` or `...`; split the slide or rewrite the sentence instead.
- Keep production evidence and scope exclusions off the screen: source paths, hierarchy proof, coverage notes, planning labels, and negative boundary phrases such as "不进入/不讲/不涉及 X" belong in spec fields or review files, never in learner-facing title/explanation/bullets/caption/blocks.
- Do not invent a teaching label unanchored to the current node, an ancestor path, or a stated relationship. Generic labels such as `对比 A`, `结构顺序 A`, `左侧`, `方案 A/B` are failed copy.

## Research policy

Use official documentation, standards bodies, product manuals, or primary research first; secondary sources only when primary ones do not explain a beginner-facing concept. Keep URLs and claim notes in the evidence ledger. Do not display citations on slides unless requested.
