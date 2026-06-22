# Quality gates

## Source gate

- One authoritative source is explicitly selected.
- A user-declared mode is recorded; mode is never inferred.
- Node IDs are unique and ordered.
- Parent nodes precede children.
- Embedded images and unreadable regions are accounted for.

## Content gate

- Every included source node maps to at least one slide.
- Slide source-node order is monotonic.
- Detailed mode contains no added-content records.
- Sparse additions map to original nodes, use allowed addition kinds, have `direct` relevance, and include evidence URLs.
- Sparse additions do not create new branches or enter neighboring workflows.
- User examples and metaphors are preserved.

## Learner-facing gate

Scan titles, explanations, bullets, captions, and visible block text. Reject:

- `PDF`, `原稿`, `来源文档`, `制作说明`, `图旁注明`;
- `详细讲稿`, `预计讲解时间`, `视觉说明`, `对应节点`;
- prompts, TODOs, lorem ipsum, placeholders, and tool tokens;
- `Genji 是真想教会你`.

Production metadata may exist in internal notes, but never in visible screen fields or PPTX slide XML.

## Slide gate

- No question-only or keyword-only knowledge pages.
- Every normal knowledge slide has a complete explanation and 3-5 useful points.
- Images are accompanied by interpretation and do not replace the page's knowledge text.
- Body text is at least 16 pt; ordinary titles are at least 35 pt.
- No unintended overlap, clipping, title wrapping, broken connectors, or missing images.
- Page numbers, headers, fonts, and visual tokens are consistent.
- The full rendered contact sheet and any flagged page are inspected.

## Canva gate

- Canva page count equals the PPTX page count.
- Every page has been previewed.
- Rich-text scan contains zero forbidden terms.
- The original template remains unchanged.
- Draft changes are committed only after explicit user approval.
- Saved design is re-read and verified before delivery.
