# Agent Hierarchy

Use this hierarchy for every course-deck build and substantial revision. Workers are proposal-only role specialists under one director. There is no standalone final reviewer role and no single-orchestrator authoring fallback.

If the current runtime cannot dispatch subagents, or requires explicit user authorization that has not been given, the director must stop after safe source/mode intake and report the blocker. Do not simulate these roles sequentially in the director for deck builds.

```
总导演 / build-course-canva-deck
├── 课程统筹师
├── 原稿场记
├── 课堂编剧
└── 视觉分镜师
```

The director routes bounded context, merges proposals, makes final durable files, builds/imports the deck, and performs process review plus final learner-facing review. Each worker carries its own quality standard and returns evidence in `self_check`; this distributes quality responsibility without adding a second approval system.

## Working Language

Use Chinese for worker-facing summaries, proposal prose, slide copy, self-check notes, and handoff notes. Keep JSON keys, file paths, command names, script flags, schema enum values, source IDs, and API/tool identifiers in English.

## Director Brief Contract

Before dispatching a worker, the director creates one scoped brief under `scratch/agent-briefs/`:

- `scratch/agent-briefs/source-context.brief.md`
- `scratch/agent-briefs/slide-plan.brief.md`
- `scratch/agent-briefs/screen-copy.brief.md`
- `scratch/agent-briefs/visual-triage.brief.md`
- `scratch/agent-briefs/visual-plan.brief.md`

Each brief should be short enough that the worker can act like a course specialist, not a form-filling process. Include:

- worker name and exact proposal objective;
- allowed reads and clearly forbidden broad reads;
- one write path for the scratch proposal;
- source node scope, source path context, mode, and curriculum boundary;
- relevant role standards from `role-standards.md`;
- concrete evidence the worker must provide in `self_check`;
- open questions the worker should report instead of guessing;
- prior proposal or state summary only when this is a revision or range continuation.

Worker rule: read the brief first, then read only `allowed_read_paths`. If additional context is required, write a `context_request` entry and stop that part of the task. Do not broaden your own read scope.

## Role Continuity

The four worker names are logical roles, not separate identities per dispatch. For long or multi-pass work, the director keeps a compact state summary so a later invocation of the same role can continue without repeating or contradicting itself:

- `scratch/agent-state/role-registry.json`
- `scratch/agent-state/course-producer.state.json`
- `scratch/agent-state/script-supervisor.state.json`
- `scratch/agent-state/teacher-writer.state.json`
- `scratch/agent-state/storyboard-designer.state.json`

Use these stable `role_id` values:

- `course-producer` for 课程统筹师
- `script-supervisor` for 原稿场记
- `teacher-writer` for 课堂编剧
- `storyboard-designer` for 视觉分镜师

A role may have many invocations, but each invocation continues from the same approved state. If the runtime starts a fresh subagent process, the director passes the prior state summary and previous approved output; the fresh process is only an execution detail, not a new logical worker.

Workers do not directly mutate role-state files. They may propose a short `state_update`; the director keeps or rewrites it after reviewing the proposal. Do not make role state more detailed than the work requires.

## Dispatch Sequence

1. 总导演 performs source intake, extraction, mode recording, curriculum/reference discovery, and initial source-image inventory.
2. 总导演 creates `scratch/agent-state/role-registry.json` and initial per-role state files.
3. 课程统筹师 and 原稿场记 may run in parallel because their write paths and read scopes do not overlap materially.
4. 总导演 reviews both proposals against their `self_check`, resolves conflicts, and creates narrower briefs for 课堂编剧 and visual triage.
5. 课堂编剧 and the first 视觉分镜师 `visual-triage` pass may run in parallel after the slide plan is approved.
6. 总导演 reviews copy and triage, resolves slide splits or source-image decisions, then creates final visual briefs.
7. 视觉分镜师 finalizes visuals, layout capacity, template reference use, layout variety, and approved `image_generation_tasks`. Long decks may split this into contiguous slide ranges under the same `role_id`.
8. 总导演 executes approved image-generation tasks, writes assets, merges proposals into durable files, runs mechanical scripts, builds PPTX, renders the deck, performs final learner-facing review, imports into Canva, and asks for final approval.

## 总导演 / build-course-canva-deck

Owns all durable writes and external actions:

- `source-map.json`
- `curriculum-context.json`
- `deck-spec.json`
- screen-copy and recording-script files, if produced
- `scratch/agent-briefs/*.brief.md` or `*.brief.json`
- `scratch/agent-state/*.state.json`
- generated image assets and image asset manifests
- PPTX generation
- mechanical audit reports
- Canva import, Canva edits, and final approval

The director should be the only role that reads all broad context by default. It may pass extracted slices, summaries, node ranges, image inventories, and relevant reference documents to workers, but should not pass full source or full template context unless that worker has a direct verification need.

Director review responsibilities:

- Before dispatch: verify source, mode, role brief boundaries, source path context, and required self-check evidence.
- After each proposal: inspect the proposal's `self_check`; merge only when the role has answered its own standards with concrete evidence.
- After director edits: re-check any changed source grouping, copy, visual fallback, or layout against the affected role standard.
- Before PPTX build: confirm coverage matrix, source path order, screen evidence, meaningful labels, visual plan, and layout rhythm.
- After rendering: review the contact sheet and full-size flagged slides as a learner, not as a script validator.
- Before delivery: verify Canva page count, forbidden terms, visible evidence, and final page previews.

The director must not create a standalone reviewer role. Mechanical scripts are guards, not approval.

## 课程统筹师

Purpose: identify where the lesson belongs in the curriculum and define scope boundaries.

Default allowed reads:

- its director brief
- authoritative source path, hash, title, top-level source summary, and source-node index prepared by the director
- discovered curriculum map files and neighboring lesson files explicitly listed in the brief
- selected `细纲` or `粗纲` mode

Default forbidden reads:

- full raw source file, unless the brief says the lesson identity cannot be determined from extracted summaries
- template references, visual-system references, PPTX outputs, and Canva designs
- slide copy proposals or visual proposals

Output:

- `scratch/source-context.proposal.json`

Must include:

- course system, module, and lesson role
- prerequisites and downstream handoff
- shared terminology
- excluded neighboring topics
- risks where the lesson could duplicate another lesson
- `self_check`
- any `context_request` needed to resolve unclear curriculum position

Required `self_check` evidence:

- `scope_fit`: quote the course role in one clear sentence.
- `neighbor_boundary`: name overlaps excluded or handed off.
- `term_consistency`: name shared terms whose meaning was preserved.
- `no_content_authoring`: confirm no slide copy, slide plans, or visuals were authored.

## 原稿场记

Purpose: preserve source hierarchy, source path, order, examples, enumerations, continuity, and source images.

Default allowed reads:

- its director brief
- `source-map.json`
- authoritative source file only when the brief explicitly says raw hierarchy, PDF layout, or embedded image verification is required
- rendered source pages or source image inventory explicitly listed in the brief
- boundary summary from 课程统筹师, if already approved by the director

Default forbidden reads:

- neighboring course files beyond the approved boundary summary
- design-system, page-design, template bank, Canva designs, and unrelated references
- screen copy or visual proposals that would bias source-order planning

Output:

- `scratch/slide-plan.proposal.json`

Must include:

- ordered source-node groups
- for every slide group, the ancestor path from root to current branch
- exact sibling enumerations that must remain visible
- source images that must be used or accounted for
- warnings for repeated wording, early use of later-node phrases, dense groups, or hierarchy ambiguity
- proposed slide boundaries that keep coverage within density limits
- `self_check`
- any `context_request` for unreadable source hierarchy or images

Required `self_check` evidence:

- `hierarchy_preserved`: cite representative source paths and slide groups.
- `source_path_visible`: every proposed group has a clear source path and current branch label.
- `sibling_order`: sibling lists remain complete and in source order, or are split into consecutive slides.
- `no_material_pool_rewrite`: name any regrouping avoided because it would invent a new narrative.
- `image_accounting`: every non-thumbnail source image in scope is used, redrawn, or has an omission reason.

Must not improve copy style, generate visuals, or hide source nodes behind metadata.

## 课堂编剧

Purpose: write learner-facing screen copy while preserving or expanding the source according to mode.

Default allowed reads:

- its director brief
- `scratch/source-context.proposal.json` after director review
- `scratch/slide-plan.proposal.json` after director review
- director-provided source-node excerpts and evidence ledger for the assigned node scope
- `content-policy.md`

Default forbidden reads:

- full raw source file unless a specific excerpt is listed in `allowed_read_paths`
- neighboring course files beyond the approved boundary summary
- visual-system, design-system, page-design, template bank, PPTX outputs, and Canva designs

Output:

- `scratch/screen-copy.proposal.json`

Must include:

- conclusion-style titles that follow the source path
- self-contained explanations
- complete sibling lists and examples
- distinct `screen_evidence` phrases for each distinct source node
- no learner-facing source-path/order/coverage prose such as `本页顺序`
- sparse-mode additions only when directly mapped and evidenced
- `self_check`
- any `context_request` for missing evidence, unclear wording, or suspected out-of-scope expansion

Required `self_check` evidence:

- `title_source_fit`: quote representative titles and their source paths.
- `block_label_meaning`: quote structured-layout labels and the real relationship they name. No filler labels.
- `page_logic`: identify risk pages and how explanation, blocks, and caption support the title.
- `self_contained`: state where definitions, examples, and visual interpretation are visible on the page.
- `evidence_distinct`: each mapped source node has distinct visible evidence on the same slide.
- `no_backstage_copy`: source path/order/coverage evidence stays in metadata, not rendered screen text.
- `no_level_shuffle`: name any later-branch wording that was kept out of earlier pages.

Must not put required knowledge only in speaker notes.

## 视觉分镜师

Purpose: plan teachable visuals and layout before the director builds the PPTX.

Default allowed reads:

- its director brief
- director-approved slide plan and, for final visual passes, approved screen copy
- source image inventory, selected rendered source images, and generated-image review notes listed in the brief
- selected template profile, prebuilt template-native element inventory, selected template reference pages, and only the visual/design/page-quality references listed in the brief

Default forbidden reads:

- full raw source file
- neighboring course files
- curriculum map files beyond the approved boundary summary
- Canva designs or templates directly, unless the director brief authorizes a read-only template inventory check
- image-generation tools, final image asset directories, PPTX build outputs, and Canva import/edit actions

Outputs:

- `scratch/visual-triage.proposal.json`
- `scratch/visual-plan.part-NN.proposal.json` for long-deck range proposals when used
- `scratch/visual-plan.proposal.json` for the director-reviewed merged visual proposal

Must include:

- visual asset type per slide or slide range
- source image usage or omission reasons
- generated-image candidates and concrete bypass reasons
- approved `image_generation_tasks` only for pages that need generated teaching images
- for long decks, a `template_style_atlas` distilled from the whole selected template's layout language before slide-level mapping
- template page/style mapping and native motif plan from the director-provided template inventory, or a blocker when atomic native-element copy is unavailable
- layout capacity checks showing every required bullet, block, and enumeration can render
- split recommendations when a layout cannot fit the source content
- layout rhythm plan for long decks
- `self_check`
- any `context_request` for missing template inventory, image dimensions, or motif collision risks

Required `self_check` evidence:

- `visual_teaches_node`: state what each planned visual helps the learner understand.
- `layout_capacity`: name any slide that needs splitting, alternate layout, or wording reduction before build.
- `meaningful_structure`: comparison/table/two-panel pages have named relationships that match the copy; no filler labels or arbitrary A/B framing.
- `rhythm_variety`: long decks use several atlas style families and avoid repeated layout runs; background modes, template references, rendered layouts, and composition families vary for a teaching reason.
- `source_image_priority`: source case images are reused before generated substitutes when they directly teach the node.
- `native_template_source`: planned native motifs reference the director-provided template inventory; if the tool cannot copy elements atomically, record the blocker instead of inventing inventory.
- `native_not_proxy`: local raster previews, PPT shapes, SVG lookalikes, Canva search assets, generated textures, and pasted full template pages are not counted as template-native elements.
- `no_whole_page_paste`: no final course page is made by pasting a full template page.
- `signature_motif_transfer`: for templates with signature native motifs, planned pages use those motifs as structural modules and define the post-import transfer route.
- `labels_editable`: generated images contain no baked-in Chinese/UI labels; labels remain editable slide text.

Must not call image-generation tools, save final assets, build the PPTX, import into Canva, or replace source content with decorative visuals.
