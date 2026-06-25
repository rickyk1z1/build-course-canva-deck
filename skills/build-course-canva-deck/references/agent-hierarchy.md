# Agent hierarchy

Use this hierarchy for course-deck builds and substantial revisions when subagents are available. These are proposal-only role skills under one controller, not independent durable writers.

```
Controller Agent / build-course-canva-deck
├── Source & Curriculum Agent
├── Source Fidelity Agent
├── Learning Copy Agent
├── Visual Layout Agent
└── Quality Gate Agent
```

## Controller Agent / build-course-canva-deck

Own all durable writes and external actions:

- `source-map.json`
- `curriculum-context.json`
- `deck-spec.json`
- screen-copy and recording-script files, if produced
- PPTX generation
- QA reports
- Canva import, Canva edits, and final approval

The controller dispatches the five role skills, merges proposals, resolves conflicts, reruns deterministic scripts, and fixes failures. It must never let a worker write final files, edit the source, modify a Canva template, or touch a Canva design.

## Source & Curriculum Agent

Purpose: identify where the lesson belongs in the curriculum.

Inputs:

- authoritative source path and hash
- discovered neighboring course files
- selected `细纲` or `粗纲` mode

Output:

- `scratch/source-context.proposal.json`

Must include:

- course system, module, and lesson role
- prerequisites and downstream handoff
- shared terminology
- excluded neighboring topics
- risks where the lesson could duplicate another lesson

Must not write final files or author slides.

## Source Fidelity Agent

Purpose: preserve source hierarchy, order, examples, enumerations, and source images.

Inputs:

- `source-map.json`
- authoritative source file
- embedded source image inventory

Output:

- `scratch/slide-plan.proposal.json`

Must include:

- ordered source-node groups
- exact sibling enumerations that must remain visible
- source images that must be used or accounted for
- warnings for repeated wording, early use of later-node phrases, or groups too dense for one slide
- proposed slide boundaries that keep coverage within the QA density limit

Must not improve copy style, generate visuals, or hide source nodes behind metadata.

## Learning Copy Agent

Purpose: write learner-facing screen copy while preserving or expanding the source according to mode.

Inputs:

- `source-map.json`
- `scratch/source-context.proposal.json`
- `scratch/slide-plan.proposal.json`
- `content-policy.md`

Output:

- `scratch/screen-copy.proposal.json`

Must include:

- conclusion-style titles that follow source order
- self-contained explanations
- complete sibling lists and examples
- distinct `screen_evidence` phrases for each distinct source node
- sparse-mode additions only when directly mapped and evidenced

Must not move later source-node wording into earlier pages unless the source already repeats it there. Must not put required knowledge only in speaker notes.

## Visual Layout Agent

Purpose: plan the teachable visual and layout system before the controller builds the PPTX.

Inputs:

- source image inventory
- screen-copy proposal
- template profile and reference pages
- visual, design, and page-quality references

Output:

- `scratch/visual-plan.proposal.json`

Must include:

- visual asset type per slide
- source image usage or omission reasons
- generated-image candidates when needed
- template page mapping and native motif plan
- layout capacity checks showing every required bullet, block, and enumeration can render
- split recommendations when a layout cannot fit the source content

Must not build the PPTX, import into Canva, or replace source content with decorative visuals.

## Quality Gate Agent

Purpose: audit proposals and rendered outputs without authoring content.

Outputs:

- `scratch/supervisor-log.md`
- `scratch/supervisor-findings.json`
- `scratch/qa-findings.md`

Run checks at four gates:

1. Before worker dispatch: source, mode, role prompts, scratch-only write paths.
2. After every proposal: role boundaries, source order, complete enumerations, no repeated/early wording, no narration-only knowledge.
3. Before controller merge: one-to-one coverage feasibility, monotonic order, distinct evidence, layout capacity, unresolved conflicts.
4. Before build/import: deterministic `audit_deck.py` result, rendered PPTX same-slide evidence, Canva preflight, and zero unresolved findings.

The Quality Gate role must not author slide text, slide plans, visual plans, or final files. It can require the controller to rerun a worker or split a slide.
