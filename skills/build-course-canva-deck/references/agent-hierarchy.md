# Agent hierarchy

Use this hierarchy for course-deck builds and substantial revisions when subagents are available. These are proposal-only role workers under one director, not independent durable writers.

The director must act as the router and reviewer. It reads the broad source and reference context first, then sends each worker a bounded task packet. A worker should not independently read the same full source, curriculum, template, or Canva context unless its packet explicitly allows it.

```
总导演 / build-course-canva-deck
├── 课程统筹师
├── 原稿场记
├── 课堂编剧
├── 视觉分镜师
└── 成片审片员
```

## Role names

- `总导演`: owns the final film of the lesson. It routes context, approves proposals, executes asset generation, builds PPTX, imports into Canva, and delivers the editable deck.
- `课程统筹师`: thinks like a course producer. It decides where this lesson sits, what it should teach, what it should hand off, and what neighboring lessons must own instead.
- `原稿场记`: thinks like a script supervisor. It preserves source order, continuity, sibling lists, examples, and source images so nothing quietly disappears.
- `课堂编剧`: thinks like a teacher-writer. It turns approved source points into self-contained learner-facing screen copy.
- `视觉分镜师`: thinks like a storyboard designer. It decides how each slide should be seen, which cases need images, which source images to reuse, and which generated images the director should create.
- `成片审片员`: thinks like a final reviewer. It checks whether the work can become a reliable learner-facing deck without authoring new content.

## Working language

Use Chinese for worker-facing reasoning summaries, findings, proposal prose, slide copy, QA comments, and handoff notes. Keep JSON keys, file paths, command names, script flags, schema enum values, source IDs, and API/tool identifiers in English. Quote or preserve English source text only when it is actual evidence that must remain traceable.

## Director routing contract

Before dispatching a worker, the director creates one scoped brief under `scratch/agent-briefs/`:

- `scratch/agent-briefs/source-context.brief.md`
- `scratch/agent-briefs/slide-plan.brief.md`
- `scratch/agent-briefs/screen-copy.brief.md`
- `scratch/agent-briefs/visual-plan.brief.md`
- `scratch/agent-briefs/quality-gate.brief.md`

Each brief must include:

- `role_name`: the Chinese worker name.
- `objective`: the exact proposal to produce.
- `allowed_read_paths`: exact files, extracted slices, rendered pages, or reference documents the worker may read.
- `forbidden_reads`: broad files or systems the worker must not open, such as the raw source, neighboring courses, template bank, Canva design, or unrelated references when not needed.
- `write_path`: one scratch output path only, or the limited QA paths for 成片审片员.
- `source_node_scope`: all nodes, a contiguous node range, or explicit node IDs.
- `mode`: `detailed` or `sparse`, copied from the user-declared `细纲` or `粗纲`.
- `boundary_summary`: curriculum scope, excluded neighboring topics, and handoffs relevant to this worker.
- `acceptance_checks`: concrete checks the director will run before using the proposal.
- `open_questions`: context gaps the worker should report instead of guessing.

Worker rule: read the brief first, then read only `allowed_read_paths`. If additional context is required, write a `context_request` entry in the proposal or QA findings and stop that part of the task. Do not broaden your own read scope.

## Dispatch sequence

The director does not need to run every worker at the same time. Use staged dispatch so downstream workers receive curated upstream proposals rather than re-reading broad context.

1. 总导演 performs source intake, source extraction, mode recording, curriculum/reference discovery, and initial source-image inventory.
2. 成片审片员 reviews all first-stage briefs before any content worker starts.
3. 课程统筹师 and 原稿场记 may run in parallel because their write paths and read scopes do not overlap materially.
4. 总导演 reviews those proposals, resolves conflicts, and creates a narrower brief for 课堂编剧.
5. 课堂编剧 writes learner-facing screen copy from the approved source-node plan and allowed excerpts.
6. 总导演 reviews the copy proposal and creates a narrower brief for 视觉分镜师.
7. 视觉分镜师 plans visuals, layout capacity, template motif use, and `image_generation_tasks` from the slide plan, screen copy, source-image inventory, and selected template references.
8. 总导演 executes approved `image_generation_tasks`, writes image assets, records asset paths, and updates the durable deck spec.
9. 成片审片员 checks after every proposal, before director merge, and before build/import.
10. 总导演 alone merges proposals into durable files, runs scripts, builds PPTX, imports into Canva, edits Canva, requests final approval, and returns the final link.

## 总导演 / build-course-canva-deck

Own all durable writes and external actions:

- `source-map.json`
- `curriculum-context.json`
- `deck-spec.json`
- screen-copy and recording-script files, if produced
- `scratch/agent-briefs/*.brief.md` or `*.brief.json`
- generated image assets and image asset manifests
- PPTX generation
- QA reports
- Canva import, Canva edits, and final approval

The director dispatches the five proposal workers, merges proposals, resolves conflicts, executes approved image-generation tasks, reruns deterministic scripts, and fixes failures. It must never let a worker write final files, edit the source, modify a Canva template, touch a Canva design, call image-generation tools, or save final image assets.

The director should be the only role that reads all broad context by default. It may pass extracted slices, summaries, node ranges, image inventories, and relevant reference documents to workers, but it should not pass full source or full template context unless that worker has a direct verification need.

## 课程统筹师

Purpose: identify where the lesson belongs in the curriculum and define scope boundaries.

Default allowed reads:

- its director brief
- authoritative source path, hash, title, top-level source summary, and source-node index prepared by the director
- discovered curriculum map files and neighboring lesson files explicitly listed in the brief
- selected `细纲` or `粗纲` mode

Default forbidden reads:

- full raw source file, unless the director brief says the lesson identity cannot be determined from extracted summaries
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
- any `context_request` needed to resolve unclear curriculum position

Must not write final files or author slides.

## 原稿场记

Purpose: preserve source hierarchy, order, examples, enumerations, continuity, and source images.

Default allowed reads:

- its director brief
- `source-map.json`
- authoritative source file only when the brief explicitly says raw hierarchy, PDF layout, or embedded image verification is required
- rendered PDF pages or source image inventory explicitly listed in the brief
- boundary summary from 课程统筹师, if already approved by the director

Default forbidden reads:

- neighboring course files beyond the approved boundary summary
- content-policy, design-system, page-design, template bank, Canva designs, and unrelated references
- screen copy or visual proposals that would bias source-order planning

Output:

- `scratch/slide-plan.proposal.json`

Must include:

- ordered source-node groups
- exact sibling enumerations that must remain visible
- source images that must be used or accounted for
- warnings for repeated wording, early use of later-node phrases, or groups too dense for one slide
- proposed slide boundaries that keep coverage within the QA density limit
- any `context_request` for unreadable source hierarchy or images

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

- conclusion-style titles that follow source order
- self-contained explanations
- complete sibling lists and examples
- distinct `screen_evidence` phrases for each distinct source node
- sparse-mode additions only when directly mapped and evidenced
- any `context_request` for missing evidence, unclear wording, or suspected out-of-scope expansion

Must not move later source-node wording into earlier pages unless the source already repeats it there. Must not put required knowledge only in speaker notes.

## 视觉分镜师

Purpose: plan the teachable visual and layout system before the director builds the PPTX.

Default allowed reads:

- its director brief
- director-approved slide plan and screen-copy proposal
- source image inventory, selected rendered source images, and generated-image review notes listed in the brief
- selected template profile, selected template reference pages, and only the visual, design, and page-quality references listed in the brief

Default forbidden reads:

- full raw source file
- neighboring course files
- curriculum map files beyond the approved boundary summary
- Canva designs or templates directly, unless the director brief authorizes a read-only template inventory check
- image-generation tools, final image asset directories, PPTX build outputs, and Canva import/edit actions

Output:

- `scratch/visual-plan.proposal.json`

Must include:

- visual asset type per slide
- source image usage or omission reasons
- generated-image candidates when needed
- complete `image_generation_tasks` for every generated case image or illustration the director should execute
- template page mapping and native motif plan
- layout capacity checks showing every required bullet, block, and enumeration can render
- split recommendations when a layout cannot fit the source content
- any `context_request` for missing template inventory, image dimensions, or motif collision risks

Each `image_generation_tasks` item must include:

- `task_id`
- `slide_number`
- `source_node_ids`
- `teaching_goal`
- `asset_role`
- `preferred_route`: `gpt-image-2`, `imagegen`, or `editable-diagram-fallback`
- `prompt`
- `negative_prompt`
- `text_policy`: usually `no_baked_in_text`
- `reference_inputs`: source image IDs or brief excerpts, if any
- `composition_notes`: aspect ratio, framing, subject, background, and where labels will be added as editable text
- `candidate_count`
- `selection_criteria`
- `fallback_plan`

Must not call image-generation tools, save final assets, build the PPTX, import into Canva, or replace source content with decorative visuals.

## 成片审片员

Purpose: audit briefs, proposals, generated-image tasks, and rendered outputs without authoring content.

Default allowed reads:

- its director brief
- all worker briefs being audited
- proposal files being audited
- `source-map.json`, source coverage matrix, audit reports, contact sheets, and rendered slide artifacts explicitly listed for the current gate
- raw source excerpts only when required to verify a specific source-order or evidence finding

Default forbidden reads:

- direct Canva edits, template modifications, final file writes, image-generation tool calls, or any content-authoring output path
- broad source or curriculum exploration unrelated to a concrete finding

Outputs:

- `scratch/supervisor-log.md`
- `scratch/supervisor-findings.json`
- `scratch/qa-findings.md`

Run checks at four gates:

1. Before worker dispatch: authoritative source, mode, bounded worker briefs, allowed reads, forbidden reads, and scratch-only write paths.
2. After every proposal: role boundaries, source order, complete enumerations, no repeated/early wording, no narration-only knowledge, valid `image_generation_tasks`, and no unauthorized file reads or writes.
3. Before director merge: one-to-one coverage feasibility, monotonic order, distinct evidence, layout capacity, executable image-generation tasks, and unresolved conflicts.
4. Before build/import: deterministic `audit_deck.py` result, rendered PPTX same-slide evidence, generated-image assets or documented fallbacks, Canva preflight, and zero unresolved findings.

The 成片审片员 must not author slide text, slide plans, visual plans, image-generation tasks, or final files. It can require the director to rerun a worker, narrow a brief, provide missing excerpts, revise a prompt, execute or bypass an image-generation task, or split a slide.
