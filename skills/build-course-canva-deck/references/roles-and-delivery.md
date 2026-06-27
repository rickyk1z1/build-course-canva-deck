# Roles and delivery

This reference covers the four proposal-only roles under one director, the lightweight brief contract, the director acceptance lock, and Canva delivery. Workers are advisory; the director owns all durable files, generated assets, PPTX build, Canva import/editing, and final approval. There is no standalone reviewer role and no single-orchestrator authoring fallback for deck builds.

If the runtime cannot dispatch subagents, requires user authorization that has not been given, or the user disables workers, the director stops after safe source/mode intake and reports the blocker. Simple read-only questions may still be answered directly.

## Roles

```
总导演 / build-course-canva-deck
├── 课程统筹师
├── 原稿场记
├── 课堂编剧
└── 视觉分镜师
```

- **总导演** owns curriculum/source intake and extraction, all durable writes (`source-map.json`, `curriculum-context.json`, `deck-spec.json`, screen-copy files, briefs), generated-image execution, PPTX build, mechanical audit, Canva import/edit, process review after each proposal, and final learner-facing review.
- **课程统筹师** defines curriculum position, prerequisites, neighboring boundaries, and shared terms. Prevents adjacent-course drift.
- **原稿场记** preserves source hierarchy, source path, sibling order, second-level section spine, third-level section-cover previews, examples, metaphors, source images, and slide grouping. Prevents the mind map from being flattened or rearranged.
- **课堂编剧** writes learner-facing screen copy from approved source-node excerpts, including lesson overview, section-cover copy, section content, and final summary. Section-cover bullets summarize upcoming third-level headings rather than conclusions. Prevents invented labels, missing explanations, narration-only knowledge, source-level mismatch, and visible production/meta copy.
- **视觉分镜师** plans fixed structural layouts, source images, generated-image candidates, editable diagrams, template references, section-internal layout variety, balance, and fit. Prevents meaningless comparison/table blocks, off-point generated images, repeated content-page structures, text-image collisions, top-heavy/underfilled pages, and decorative visuals.

Each worker returns one compact handoff the director can pass downstream instead of broad context: 课程统筹师 → boundary card; 原稿场记 → source-order spine with section-cover spine and preview child IDs; 课堂编剧 → zero-basis teaching-script spine with overview/section/summary copy; 视觉分镜师 → structural-layout and visual-understanding map.

## Working language

Use Chinese for worker-facing summaries, proposal prose, slide copy, self-check notes, and handoffs. Keep JSON keys, file paths, command names, script flags, schema enum values, source IDs, and tool identifiers in English.

## Brief contract

Before dispatching a worker, the director writes one short scoped brief under `scratch/agent-briefs/` (one readable page). It states: the director's concise recap of the user's current non-negotiable requirement; the exact proposal and write path; allowed reads and forbidden broad reads; source path, node scope, mode, and curriculum boundary; the role standards that matter; concrete evidence the worker must show; and what to report as an open question instead of guessing. Workers read only their brief plus `allowed_read_paths`; if they need more, they write a `context_request` instead of widening scope.

Worker proposals include a `self_check` that is evidence, not a checkbox: each answer names a concrete source path, slide group, visible phrase, layout decision, or unresolved risk. Generic answers (`已检查`, `符合要求`) are not mergeable.

Role continuity is lightweight: the four worker names are logical roles. For multi-pass work the director carries a short prior-state summary in the next brief so a later invocation continues without contradicting itself. There are no per-role state files, `invocation_id`, or `state_update` merge machinery; the director simply restates approved prior output when continuing a role.

## Dispatch sequence

1. 总导演 does source intake, extraction, mode recording, curriculum discovery, and source-image inventory.
2. 课程统筹师 and 原稿场记 may run in parallel.
3. 总导演 reviews both against their self-check and briefs 课堂编剧 and visual triage.
4. 课堂编剧 and 视觉分镜师 (triage pass) may run in parallel after the slide plan is approved.
5. 总导演 reviews copy and triage, then briefs the final visual pass.
6. 视觉分镜师 finalizes structural layout families, visuals, layout capacity, template references, section-internal layout variety, composition balance, and `image_generation_tasks`. Long decks may split by contiguous slide ranges.
7. 总导演 executes approved image generation, merges proposals into durable files, runs the audit, builds the PPTX, renders and reviews as a learner, imports into Canva, and asks for final approval.

## Specialist skill routing

This skill is the main route. Other design/presentation/Canva skills are role-level plug-in experts, not alternate deck generators. The director controls the macro layer (requirement recap, source/order contract, curriculum boundary, role scope, allowed expert slots, durable writes, conflict resolution, acceptance) and grants a worker a narrow expert slot in its brief: skill name, allowed sections, task question, output shape, hard boundaries. The worker may invoke that skill directly and must report what it kept or rejected. Typical slots: 课堂编剧 may use `presentations:Presentations` for storytelling/density/readability only; 视觉分镜师 may use `awesome-design-md`, `presentations:Presentations`, and `baoyu-slide-deck` for design/layout/prompt references. Plug-ins cannot replace source intake, the four-role workflow, the learner-facing standard, or director acceptance.

## Director acceptance lock

The director owns non-regression across the whole deck. These must hold at the same time: source nodes complete and in order; the deck spine follows overview → section cover → section content → next section → summary; screen copy readable without narration; pages not crowded or top-heavy; section content layout rhythm visibly changes for teaching reasons; visuals make the current point easier to understand; Canva delivery editable and reviewable. No proposal, script, or field value trades one of these away.

When any issue appears, do not patch only the symptom. Mark the deck not approved and trace the chain back: source grouping → screen copy → visual plan → deck-spec → PPTX render/contact sheet → Canva delivery. Fix the earliest responsible stage, rebuild, and re-run the full director review plus the non-regression checklist. A passing audit script is never approval by itself; if the audit passes but the contact sheet or learner review fails, the deck still fails.

Run the full non-regression checklist (`references/non-regression-checklist.md`) before delivery and record the result in `交付前自检.md`.

## Canva delivery

Preconditions: confirm the Canva connector can access the chosen template route; default template `DAHM5fsVEB0` unless the user supplies another; keep the chosen template unchanged.

Access preflight (before importing/creating any design):

1. Run connector tool discovery for the exact import/read operations (`import_design_from_url`, `design_file`, `PPTX`, `presentation`, `get_design`, `get_design_pages`, `get_design_content`). Run one targeted second search before declaring import unavailable. When `_import_design_from_url` is available, use it with `design_file` for the verified local PPTX.
2. Search/read the chosen template ID; record account, accessible IDs, tool availability, chosen route, and connector errors in `canva-access.json`.
3. If the chosen template returns `design not found` but other designs read, treat it as a permission/workspace problem, not proof it doesn't exist.
4. On connector internal errors (e.g. MCP `-32603`), retry once after reconnecting; do not hammer the failing operation.

Template routes: connector route (proceed); accessible-duplicate route (user provides a reachable duplicate, preserve the same visual system); bundled-reference route (build local PPTX from bundled references, ask the user to connect the correct account or provide a duplicate before import); browser-fallback route (only after explicit user approval, operate on a new design, never modify the canonical template). If none is available, stop and report.

Import the verified local PPTX as a new presentation with a course-specific name (preserves editable text). After import: confirm page count; read rich text and scan forbidden language; retrieve page previews and inspect the full deck; confirm font appearance, missing glyphs, image crops, page numbering, and layout consistency; show the complete preview/contact sheet to the user.

Approval: default to one final user checkpoint after internal reviews. If a Canva editing transaction exists, ask explicitly before saving; cancel if rejected. After commit, re-read design metadata and rich text; return the edit URL only after page-count and forbidden-language checks pass.

Failure handling: template inaccessible → finish local PPTX from bundled references, then ask for the correct account/duplicate/browser fallback; same login different access → explain workspace/token/link differences and verify by opening the template in the device browser; import page mismatch → repair the PPTX and re-import as a new design; missing font/broken glyph → fix PPTX font names or fix in Canva, then re-preview; thumbnail server error → retry the page, never treat a missing preview as approval.
