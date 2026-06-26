# End-to-end workflow

## Output Workspace

Keep scratch files outside the user's project. Put durable deliverables in `<source-parent>/<course-stem>-课件产物/` unless the user chooses another location:

- `<course-stem>-屏显稿.md`
- `<course-stem>-Canva导入稿.pptx`
- `curriculum-context.json`
- `课程体系关联说明.md`
- `canva-access.json`
- `assets/`
- `mechanical-audit-report.json`
- `canva-native-motif-report.json` when template-native motifs are planned
- `canva-design.txt`

Never overwrite source files.

## Mandatory Proposal-Only Multi-Agent Workspace

Use the four-role proposal worker set from `agent-hierarchy.md` for every course-deck build and substantial revision. Workers are advisory only; the director owns durable files, generated assets, PPTX build, Canva import/editing, and final approval.

There is no single-orchestrator authoring fallback. If subagents cannot be dispatched because the runtime lacks the tool, current tool policy requires explicit user authorization, the user disables workers, or the worker environment is otherwise unsafe, stop and report the blocker. The director may complete safe source/mode intake, but must not proceed to slide planning, screen copy, visual planning, PPTX generation, or Canva delivery by simulating the worker roles alone.

Create short worker briefs under `scratch/agent-briefs/`. A brief should fit on one readable page when possible:

- exact proposal objective and write path;
- allowed source excerpts, context files, rendered pages, or template references;
- forbidden broad reads such as unrelated lessons, full template banks, or Canva designs unless explicitly needed;
- source node scope, human-readable source path, mode, and curriculum boundary;
- relevant role standards and concrete `self_check` evidence required;
- open questions the worker should report instead of guessing;
- prior approved state only when this is a revision or range continuation.

Do not create a separate reviewer worker. Every worker owns its own standard, and the director reviews proposals during merge plus performs final learner-facing review.

Visual planning is staged:

1. `visual-triage`: source image reuse, visual asset type, generated-image candidates, and obvious layout/split risks.
2. `visual-finalize`: template references, native motif planning, layout capacity, rhythm, and approved `image_generation_tasks`.

For long decks, split visual work by contiguous slide ranges if that keeps proposals easier to reason about. Preserve the same logical `storyboard-designer` role state across ranges.

If subagents are unavailable or unsafe for the current run, the director records the limitation and stops instead of performing the same phases sequentially.

## Source Intake

1. Enumerate supplied files and compute hashes.
2. Resolve the authoritative source with the user if more than one file could control content.
3. Extract text, hierarchy, order, notes, and embedded images.
4. For PDFs or exported mind maps, render and visually inspect hierarchy; text order alone is not hierarchy evidence.
5. Ask the user to choose `细纲` or `粗纲`; never infer the mode.
6. Search the workspace for the curriculum map and neighboring lessons. Create `curriculum-context.json`; ask only when the course position cannot be discovered.
7. Record the explicit mode reply in `source-map.json`.

Supported deterministic extraction routes:

- `.xmind`: parse `content.json` or legacy `content.xml`, retaining topic order and resources.
- `.opml` / `.mm`: parse XML outline order.
- `.docx`: read paragraph styles and extract `word/media`.
- `.md` / `.txt`: preserve heading and list order.
- `.pdf`: extract page text and images, then visually reconstruct hierarchy.

If scan quality or connectors are unreadable, stop and request a clearer export. Do not guess.

## Content Modeling

Create a coverage ledger with one row per included source node:

`source node -> source path -> slide number -> visible evidence -> visual treatment -> status`

The ledger must prove content preservation before wording optimization, vertical expansion, or visuals:

- `source_node_ids` must match `source_node_treatments` exactly and in order.
- `screen_evidence` must be an exact visible learner-facing phrase from the slide title, explanation, bullets, caption, or blocks.
- Metadata-only coverage is a failure.
- Producer-facing evidence is also a failure when it appears on the slide. Do not write `本页顺序`, `本页内容`, source paths, node IDs, coverage notes, or "this page covers..." prose just to satisfy the ledger.
- Distinct source nodes on the same slide need distinct evidence phrases unless the source text itself is identical.
- Evidence should appear on the page in source order.

For hierarchical outlines, record the current source path for every slide group before writing screen copy. In detailed mode, the path and sibling order are the teaching sequence. Do not regroup nodes into a new narrative just because it sounds smoother.

For detailed outlines, preserve sibling enumerations as visible peer items. If a source node has four peer children, the slide must show four peer items in source order or split them into consecutive slides. Do not rely on speaker notes, generated images, or metadata to carry omitted siblings.

Keep distinctive wording in its source position. If a later node introduces a phrase, do not use that phrase as an earlier slide title or label unless the source already repeats it there.

Screen copy is the teaching layer. It must contain the definitions, explanations, examples, conclusions, and visual interpretation needed for a learner to understand the page without narration. It should read like courseware, not like a production report. `speaker_notes` may be empty or contain only short transition reminders.

## Deck Spec

`deck-spec.json` is an implementation bridge, not the course design itself. Keep it complete enough for scripts and Canva import, but do not let field completion replace human teaching judgment.

Minimum course fields:

- `course.title`
- `course.audience`
- `course.outline_mode`
- `course.authoritative_source`
- `course.template_design_id`
- `course.curriculum_context`
- `course.template_page_mapping` for long decks
- `course.template_native_element_inventory` when atomically reusable native template elements are planned
- `course.template_native_reuse_status` when native reuse is blocked or intentionally not needed
- `course.image_generation_review`
- `course.source_image_coverage` when source images exist
- `course.page_design_review` for long decks

Minimum slide fields:

- `number`, `section`, `title`, `layout`
- `screen.explanation`, `screen.bullets`, `screen.caption`, `screen.blocks`
- `speaker_notes` only for transition hints
- `visuals`
- `visual_plan`
- `source_node_ids`
- `source_node_treatments`
- `added_content`
- `scope_check`

Allowed layouts: `cover`, `roadmap`, `light`, `dark`, `orange`/`accent`, `image-left`, `image-right`, `image-left-dark`, `image-right-dark`, `image-left-orange`/`image-left-accent`, `image-right-orange`/`image-right-accent`, `comparison`, `table`, `summary`.

## Visuals And Template Use

Every normal knowledge slide needs a teaching visual or a justified text-only exception. A teaching visual may be a source case image, redrawn source visual, generated text-free case image, editable diagram, or editable table. It must make the current source node easier to understand.

Source images are authoritative teaching units:

- Account for every non-thumbnail source image as used, redrawn, or omitted with a concrete reason.
- Use one teachable source case per slide by default.
- Use two or three source images only for explicit comparisons or source-ordered sequences.
- Four or more independent source images should be split across pages or rebuilt into a cleaner teaching visual.

Image generation is decided by teaching need, not by quota:

- Reuse source cases first when they directly teach the node.
- Generate text-free case images for abstract, metaphor-heavy, or image-poor branches that become clearer with a concrete scene.
- Prefer editable diagrams/tables for arrows, process chains, labels, comparisons, and factual grids.
- Record selected generated pages, bypass reasons, and fallbacks, but do not generate images only to satisfy a count.
- Workers plan `image_generation_tasks`; the director executes approved tasks and records selected assets.

Template fidelity is a design requirement, not decoration:

- For long decks, first create `course.template_style_atlas` from the selected template's overall layout language. The atlas should list structure families, source template pages, geometry, best-fit content, capacity limits, visual slots, and renderer layouts. This is how agents know what to build before any audit runs.
- Choose a reference template page or page family before building each slide.
- Use the template's typography scale, alignment axes, color fields, image treatment, and module spacing.
- Long decks must show real composition variety, not only alternating colors or left/right image positions.
- Long decks must route through the template's structure families dynamically. Do not let one reference page/family, style family, or rendered `layout_variant` dominate because it is convenient for dense text; dense index/table structures should be occasional, source-justified pages.
- Canva-native motifs must come from the selected template or an accessible duplicate and must be copied at the element/group/frame level. Raster proxies, PPT shapes, random Canva library assets, unrelated design elements, and duplicated template pages do not count as native template elements.
- If native motif copying is blocked, record `course.template_native_reuse_status` with the blocker. Do not force fake inventory or paste a whole template page to satisfy the field. Continue with a template-inspired editable composition only when the deck still reads correctly without claiming native motif reuse; otherwise stop for an accessible duplicate or browser fallback.

## Authoring Standard

- Preserve source order before optimizing transitions.
- Preserve every source node before adding vertical explanation or examples.
- Give each knowledge page one clear teaching point. Use enough visible points to preserve the source branch; do not add filler to hit a count.
- Use comparison/table/two-panel layouts only when the content relationship is real and named in learner-facing labels.
- Keep pages readable without narration. Notes cannot compensate for missing definitions, examples, evidence, or visual interpretation.
- Keep production evidence off the screen. Source paths, hierarchy proof, coverage notes, and visual-planning labels belong in spec fields or review files, not in the learner-facing title, explanation, bullets, captions, or blocks.
- Before choosing a layout, check whether the renderer can show every required bullet, block, and enumerated child. Layout caps are not permission to truncate.
- Generated illustrations must be concrete teaching scenes or examples. Each generated image must carry a source-linked `knowledge_anchor` and an `observable_teaching_detail` that names what in the picture teaches the point. Reject decorative abstract graphics, generic icons, atmosphere-only scenes, or workflow-looking placeholders that do not clarify the node.

## Human Instructor Finish

The final deck should feel like a careful instructor prepared it for recording, not like a schema was filled. Before delivery, read the whole deck in order and ask:

- Does the learner feel the mind-map path unfolding, rather than a rearranged material pool?
- Does each page have one teacher-like conclusion, a plain explanation, and visible examples or evidence?
- Do template structure, native motifs, and images make the current idea easier to understand, rather than decorating a generic page?
- For generated images, can the learner see the knowledge point in a concrete object, action, state, or before/after contrast?
- Does the rhythm change because the teaching relationship changes, not because a color or layout name rotated?
- Would a zero-basis learner understand the page if the instructor paused speaking for a few seconds?

If the answer is no, revise the content or design. Do not deliver a deck merely because audit fields are present.

## Build And Delivery

1. Run the content audit before building.
2. Build the PPTX and export per-slide PNG plus layout JSON.
   - Pass the external scratch directory as `--workspace`.
   - If `@oai/artifact-tool` cannot resolve from scratch or bundled runtime, stop and initialize an isolated scratch Node workspace instead of changing the user's project dependencies.
3. Inspect the montage and every flagged slide at full size.
4. Run the final audit against `deck-spec.json`, PPTX XML, and layout JSON.
5. Fix mechanical errors, then perform the director's learner review.
   - Reject any page that reads like a source coverage report, production note, or template-construction note.
   - Reject any long run where the contact sheet shows the same geometry with only color or left/right changes.
   - Reject any final Canva page that contains unedited template copy, logos, placeholder text, or a pasted full template page.
6. Run the Canva access preflight from `canva-delivery.md`.
7. Import the verified PPTX into Canva as a new presentation.
8. Verify page count, rich text, font mapping, images, page previews, and native motif replacement.
9. Show one final complete review to the user.
10. Commit Canva draft edits only after explicit approval.
11. Re-read the saved design and return its edit link.
