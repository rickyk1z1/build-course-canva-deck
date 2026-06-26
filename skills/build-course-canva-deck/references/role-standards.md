# Role Standards

These are work standards, not a separate review phase. Each worker applies the standards for its own proposal and returns a `self_check`. The director uses those self-checks during merge and performs the final learner-facing review.

`self_check` is evidence, not a checklist. Each answer must name the concrete source path, slide group, visible phrase, visual decision, or unresolved risk that proves the worker actually checked the issue. Do not answer with only `yes`, `pass`, `已检查`, or repeated template wording.

## Shared Standards

- Preserve the authoritative source hierarchy. In detailed mode, the source path and sibling order are the lesson structure.
- Do not treat XMind, PDF, or outline nodes as a material pool to reorganize into a new script.
- Every slide title and block label must be anchored to the current source node, an ancestor path, or an explicit teaching relationship.
- Do not use filler labels. Examples include `对比 A`, `对比 B`, `结构顺序 A`, `结构顺序 B`, `左侧`, `右侧`, `方案 A`, `方案 B`, `要点 A`, and `要点 B`; the real rule is that a label must tell the learner what relationship they are seeing.
- The learner-facing page must be understandable without speaker notes.
- Do not place source tracking, hierarchy proof, coverage notes, production labels, or template-construction notes on learner-facing slides.
- A script or audit pass is not approval. It only catches mechanical failures.

## 课程统筹师 Standards

Owns curriculum fit and boundary discipline.

The proposal must answer:

- What is this lesson's exact job in the curriculum?
- What knowledge is prerequisite, and what is downstream handoff?
- Which neighboring lesson topics must stay out of scope?
- Which shared terms must keep a stable meaning?

Self-check evidence:

- `scope_fit`: quote the one-sentence course role.
- `neighbor_boundary`: list concrete overlaps excluded or handed off.
- `term_consistency`: name the shared terms whose meaning was preserved.
- `no_content_authoring`: state that no slide copy, slide plans, or visuals were authored, and note any boundary advice only.

Common failure to prevent: expanding into title-cover workflow, data-review metrics, software-button operations, full shooting workflow, color grading, commercial growth analysis, or any neighboring course's main task.

## 原稿场记 Standards

Owns source fidelity, hierarchy, and grouping.

The proposal must answer:

- What source path does each proposed slide group belong to?
- Which ancestor and sibling nodes must remain visible?
- Which sibling enumerations cannot be collapsed?
- Which source images are teaching units?
- Where is the source too dense and needs a slide split?

Self-check evidence:

- `hierarchy_preserved`: show at least one representative root -> branch -> current-node path and confirm grouping follows that path.
- `source_path_visible`: every slide group records its ancestor path and current branch in human-readable form.
- `sibling_order`: list any sibling enumerations that must stay complete and how they are split when needed.
- `no_material_pool_rewrite`: name any tempting regrouping that was rejected because it would flatten the source.
- `image_accounting`: list non-thumbnail source images in scope and whether each is used, redrawn, or omitted with a reason.

Common failure to prevent: a slide that technically maps node IDs but loses the mind-map path, mixes sibling levels, or turns a detailed branch into a generic teaching topic.

## 课堂编剧 Standards

Owns learner-facing meaning and source-anchored wording.

The proposal must answer:

- Does the title match the current source branch?
- Does the explanation explain that title?
- Do block headings describe real relationships?
- Can the learner understand the page without narration?
- Does every mapped node have visible evidence on the same page?

Self-check evidence:

- `title_source_fit`: quote representative titles and the source path they belong to.
- `block_label_meaning`: quote any comparison/table/two-panel labels and state the real relationship they name.
- `page_logic`: for risk pages, state how title, explanation, points, caption, and visual serve one teaching point.
- `self_contained`: identify any page that would need narration; if none, say how definitions/examples are visible on the page.
- `evidence_distinct`: show how each mapped source node gets a distinct visible phrase.
- `no_backstage_copy`: confirm that source order/path evidence stays in metadata and quote any risky page rewritten to remove `本页顺序`-style copy.
- `no_level_shuffle`: name any later-branch term that was not pulled forward, or explain why a reused term is source-approved.

Common failure to prevent: labels that look organized but name no real relationship, duplicate or reset numbering, vague titles unrelated to the blocks, and screen copy that exposes the production process while failing to teach the source node.

## 视觉分镜师 Standards

Owns teachable visuals, template fit, native motif planning, and layout rhythm.

The proposal must answer:

- What does the visual help the learner understand?
- Does the chosen layout fit the actual amount of text and evidence?
- Are comparison/table/two-panel structures meaningful?
- Are long-deck layouts varied in structure, not only color?
- Are source images reused before substitutes?
- Are Canva-native motifs selected from a real template inventory and copied as specific elements rather than whole pages?

Self-check evidence:

- `visual_teaches_node`: state what each visual makes easier to understand, not only its asset type.
- `layout_capacity`: name slides that need splitting, alternate layout, or text reduction before build; never assume the renderer will handle overflow.
- `meaningful_structure`: quote structured-layout labels and the relationship they express.
- `template_style_atlas`: for long decks, list the template structure families being used, their source template pages, best-fit content types, capacity limits, and renderer layouts.
- `rhythm_variety`: identify any repeated template style family, reference page/family, `layout_variant`, or thumbnail geometry; three adjacent pages or a dominant catch-all family must be redesigned before build, not explained away.
- `source_image_priority`: list source case images reused before generated substitutes.
- `native_template_source`: every planned native motif references an item from `course.template_native_element_inventory`; if atomic copying is unavailable, record the blocker instead of inventing inventory.
- `native_not_proxy`: PPT shapes, SVG lookalikes, raster proxies, random Canva assets, generated textures, unrelated design elements, and duplicated template pages are not counted as template-native elements.
- `no_whole_page_paste`: state that no final course page is created by pasting a full template page; if the tool only offers whole-page duplication, native motif reuse is blocked for that run.
- `signature_motif_transfer`: for templates with signature native motifs, name which motifs are planned as structural modules and how they will be transferred after import; blocked transfer must stop final delivery unless the user explicitly accepts a non-native fallback.
- `labels_editable`: generated images have no baked-in Chinese/UI labels.

Common failure to prevent: a long middle section that only changes colors while keeping the same composition, repeated dense index/table pages used as the default way to fit multiple points, abstract comparison boxes that do not compare anything, template-looking elements that are not actually copied from the selected Canva template, and final pages that still contain pasted template-page content.

## 总导演 Standards

Owns merge decisions, generated asset execution, mechanical checks, local rendering, Canva import, and final learner-facing review.

Before merging a worker proposal:

- Read its `self_check`.
- Reject or return any proposal whose self-check is generic, missing, contradicted by the proposal itself, or written as a status report without concrete evidence.
- Do not silently repair a worker's source grouping, copy, or visual plan in a way that bypasses that role's standard.

After director changes:

- If changing slide grouping, re-check 原稿场记 standards.
- If changing title, block labels, or explanation, re-check 课堂编剧 standards.
- If changing layout, fallback visual, generated-image decision, or template motif, re-check 视觉分镜师 standards.
- If changing scope or neighboring lesson boundary, re-check 课程统筹师 standards.

Before local PPTX build:

- Coverage matrix proves every included source node is covered exactly once.
- Slide groups follow source path and sibling order.
- Every comparison/table/two-panel page has meaningful labels.
- Every long-deck layout run is intentional and visibly varied in geometry, evidence treatment, template reference page/family, and teaching structure, not only color.
- Every planned native motif references a verified template element inventory item, signature motif transfer is planned when the template depends on it, and no planned operation depends on pasting a whole template page into the final deck.

After local rendering:

- Inspect contact sheet and full-size flagged pages.
- Fix overlap, clipping, duplicate text, wrong numbering, broken title wrapping, missing images, and repeated layout runs.
- Read pages as a zero-basis learner: title, explanation, blocks, caption, and visual must form one coherent teaching unit. Remove any `本页顺序`-style source evidence, page construction notes, or other backstage copy from the visible slide.
- Read the deck as an instructor preparing to record: the lesson should follow the source hierarchy, build momentum, use examples at the moment they help, and feel authored rather than assembled from repeated components.

After Canva import:

- Verify page count and rich text.
- Execute native motif replacement from the selected template or accessible duplicate.
- Write `canva-native-motif-report.json` or an equivalent record.
- Do not deliver if any planned native motif is `proxy_only`, `non_template_asset`, `unmatched`, `pending`, `whole_page_paste`, or `blocked` without explicit user approval.

Mechanical scripts support this review, but do not replace it.
