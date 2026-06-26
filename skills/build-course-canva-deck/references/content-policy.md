# Content policy

## Shared teaching standard

Write for zero-basis learners who need a fast, directionally correct mental model. Prefer familiar objects, visible relationships, and plain language over terminology debates. Keep technical statements accurate enough to guide action without turning an introductory lesson into an advanced workflow.

Treat all decks as chapters of one self-media and editing curriculum. Reuse established terminology and metaphor systems, respect prerequisite order, and keep each lesson responsible for a distinct teaching task. Read `curriculum-system.md` before optimizing or expanding content.

## Detailed outline (`细纲`)

Use the accepted `影像基础参数` deck as the depth baseline.

- Preserve every useful definition, relationship, number, example, and conclusion from the authoritative source.
- Preserve the exact branch order and the user's metaphor system.
- Improve sentence clarity, grouping, and teachability.
- Add only connective wording needed to make existing knowledge understandable.
- Do not introduce concepts, workflows, software operations, or adjacent branches that the source did not develop.
- Verify unstable facts when necessary, but do not silently expand the lesson. Flag a substantive conflict for the user.

## Sparse outline (`粗纲`)

Produce more detailed teaching content than the accepted baseline while remaining highly faithful to the supplied tree.

Expand vertically inside each existing node with:

- a direct definition;
- why it matters or what causes it;
- its relationship to sibling or parent nodes;
- a familiar example or analogy;
- a common misconception when useful;
- a practical boundary that prevents misunderstanding.

Do not expand horizontally. A topic is out of scope when it cannot be mapped directly to an original node or when its relevance drops into a neighboring workflow. For example, a branch about encoding and containers may explain their definitions, relationship, trade-offs, and examples, but must not branch into editing-software button operations.

An addition is also out of scope when it belongs to a neighboring course, duplicates material already taught elsewhere, or skips prerequisites expected by the overall curriculum.

For every addition:

1. Map it to one original source node.
2. Classify it with an allowed addition kind.
3. Mark relevance as `direct`.
4. Record authoritative evidence.
5. Remove it if explaining it requires a new branch not present in the source.
6. Remove it if it belongs to `excluded_neighbor_topics` or conflicts with the current lesson's `course_role`.

## Screen copy as the teaching layer

Screen copy carries the knowledge. Each normal knowledge slide must be understandable without narration and includes:

- a conclusion-style title;
- one self-contained explanation paragraph;
- enough structured points, comparisons, or steps to preserve the current source branch without filler;
- a visual interpretation when an image is present.

Do not create a separate lecture-notes deliverable. Optional `speaker_notes` may exist only as short internal transition reminders, delivery rhythm hints, or emphasis cues. They may be empty. Never use notes to compensate for missing screen knowledge, and never render notes or production metadata on a slide.

## Metaphors and examples

- Preserve user-supplied examples and metaphors instead of replacing them with more technical ones.
- Treat them as teaching shortcuts; do not overemphasize literal correctness.
- Keep the direction of the explanation correct.
- Ask before altering a metaphor that may reverse the intended logic.

## Research policy

Use official documentation, standards bodies, product manuals, or primary research first. Use secondary sources only when primary sources do not explain a beginner-facing concept. Keep URLs and claim notes in the evidence ledger. Do not display citations on slides unless requested.
