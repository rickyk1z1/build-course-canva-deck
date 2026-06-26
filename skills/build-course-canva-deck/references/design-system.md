# Canva template design system

## References

- Default Canva template: `DAHM5fsVEB0` (21-page layout bank; never modify it).
- Accepted quality reference: `DAHNU2_rPtU` (content must never be copied into a new topic).
- Bundled assets: `assets/template-reference/` and `assets/golden-layouts/`.
- If the user supplies another template/design ID, inspect that template first and create a `template-profile.json` or `course.design_profile` before authoring slides. Do not reuse the default template colors, fonts, or layout rhythm for a different template.

## Visual tokens

Default profile for `DAHM5fsVEB0`:

- Canvas: 16:9, 1280x720 locally and 1920x1080 in Canva.
- Black: `#1C1C1C`.
- Orange: `#FC6736`.
- Cream: `#F2EBE3`.
- White: `#FFFFFF`.
- Primary title: Canva `站酷高端黑体`; local PPTX name `站酷高端黑`.
- Secondary title: Canva `思源黑体-细体`; local PPTX name `思源黑体 CN Light`.
- Body: `字由点字烈黑`.
- Decorative small text: Canva `思源黑体-粗体`; local PPTX name `思源黑体 CN Bold`.

For a different template, replace these tokens with the selected template's dominant dark, accent, light, neutral, title font, body font, rule style, margin scale, and page rhythm. Record the profile in the deck-spec so `build_deck.mjs` can use it.

## Composition rules

- Use large flat color fields, square divisions, strong typography, and disciplined image crops.
- Treat the chosen Canva template as a layout language, not just a color palette. Before building, inspect the selected template contact sheet and choose a template-like composition family for each slide.
- "Template-like" means aligned to the template's overall layout language, not copied from only one template page. You may combine and adapt layout ideas from multiple template pages when the structure, density, title axis, color mass, image treatment, and teaching relationship still feel native to the template.
- Plan each page from a reference template page or page family before generating the local PPTX. The slide spec must record `visual_plan.template_reference` with the inherited layout features and adaptation decision, plus `visual_plan.layout_variant` for the actual rendered composition family. Do not build a generic rectangular layout first and then add template-looking decoration later.
- Treat the template page count as a layout bank size, not the course page count. If coverage and readability require more pages than the template contains, cycle and adapt template page families; do not compress source nodes or source images to fit the template's 21-page default.
- Read `page-design-quality.md` before local PPT generation. Page design quality is not satisfied by alternating colors or layout names; the rendered slide must show template-like title scale, alignment, proximity, contrast, and image grouping.
- For decks longer than 12 pages, create `course.template_style_atlas` before `course.template_page_mapping`. The atlas is the execution plan for template alignment: identify reusable structure families from the full template bank, such as title statement, dark hero, image evidence, split field, side rail, comparison strip, dense index, flow/roadmap, gallery, close reading, and summary. Each atlas item must state source template pages, inherited geometry, best content fit, capacity limits, visual slot, and renderer layouts that can actually produce it.
- Then create `course.template_page_mapping` before generating the local PPTX. This mapping is a build input, not a retrospective note: every slide must name its template style family, reference page(s) or page family, layout family, native motif if any, content-fit reason, and local PPT decision.
- Preserve template diversity page by page through style families: title-only, dark hero, image triptych, split field, side rail, comparison strip, dense index, flow/roadmap, and summary pages should remain visually distinct when the selected template uses those patterns. If course content does not fit a reference family, change text width, wrapping, visual scale, or split the content across slides before abandoning the template composition.
- For long decks, distribute slides across multiple template structure families from the atlas. A deck that technically alternates colors but repeatedly uses the same underlying rectangular composition still fails template fidelity.
- Do not use a single dense index/table reference page as the default answer for "several points need to fit." `index-grid` or similar two-block/table structures are occasional pacing tools, not the normal knowledge-page pattern. If several adjacent source nodes all seem to need that layout, split, summarize, convert one to a flow/roadmap/statement/image-evidence page, or choose a different template reference page before build.
- `course.template_page_mapping` must read like a deliberate route through the template language. In long decks, no one style family, template reference page/page family, or rendered `layout_variant` should dominate the deck or recur three times in a row unless the source itself is a visibly repeated drill sequence and the director records why repetition is pedagogically intentional.
- The selected `layout` must be able to render the planned style family. Do not assign `layout_variant: gallery-strip`, `flow-path`, or `dark-spotlight` to a `table` or plain `light` slide if the current renderer will still output the same two-block/table geometry.
- For long decks, `build_deck.mjs` must render `visual_plan.layout_variant` into visibly different geometry. Alternating `image-left`, `image-right`, dark, light, and accent pages is not enough when the contact sheet still reads as one repeated two-column layout.
- Canva-native template elements are usable only when the current connector or approved browser route can address the selected element/group/frame itself. Scan the chosen template for existing native vector, shape, line, group, frame, side-panel, background-shape, and decorative geometry elements; record them in `course.template_native_element_inventory` only when they can be copied or reused atomically. Canva library search results, one-off media fills, generated raster art, unrelated design elements, and duplicated template pages do not count as template-native elements.
- For long decks, plan native motif usage where it strengthens the template language and page composition. Use more than one existing template element when motifs recur, and do not let one motif dominate the deck. If the connector cannot copy or reuse a native vector/shape/group element from the template, record `course.template_native_reuse_status` as blocked and continue with template-inspired editable geometry only if the deck still works without claiming native reuse; otherwise stop for an accessible duplicate or browser fallback.
- For the default `DAHM5fsVEB0` template, the large textured star/diamond, oversized circular geometry, heavy black/orange/cream field modules, side panels, and structural image frames are signature motifs. Treat them as template structure, not optional decoration. A long deck should plan several placements of these motifs as structural modules across different page families.
- `blocked-no-atomic-copy` is only a mid-work blocker, not a normal final state. If signature motifs are required and the connector cannot copy native elements/groups, the director must use an accessible duplicate or explicit browser fallback to move those elements, or ask the user to approve delivery without native motif transfer. Do not silently substitute local PPT shapes, SVG lookalikes, or generated textures and still call the result template-faithful.
- Never paste an entire template page into the final course deck to obtain a motif. Whole-page duplication is acceptable only as a temporary inspection aid outside the final design; no template text, placeholder, logo, unrelated image, or full-page composition may remain in the delivered course pages.
- Treat large textured template motifs as replacement composition modules, not decorations. This applies to every slide type, not only covers. If a motif replaces a cover strip, focus card, image frame, side panel, background mass, or other structural module, do not generate the replaced module. Place the motif by first following its reference template page position, crop, and scale; if course text forces a change, re-balance the whole page in the local PPT stage so the motif still has a clear anchor, breathing room, and no collision with title, explanation, footer, or page number.
- For template-native elements, preview the intended element in the generated local PPTX using a raster `local_preview_path` at the intended final position and scale. This raster is only a local preview proxy. The later Canva-native step must copy/reuse the recorded existing template element, delete or replace the proxy, and position the native element at the same approved box; it must not overlay the native element on top of the proxy or leave a pasted template page behind. Native insertion follows the approved local `motif_box` coordinates after scaling; it must not become a separate post-import layout exploration step.
- When a template motif competes with text, shrink or move the text area, add deliberate line breaks, or select a different template-like composition family. Do not push the motif into a corner just to avoid a wide text box, and do not keep the motif if the contact sheet shows it touching or covering title, body copy, captions, footer, page number, or the main teaching image.
- Each planned motif must include machine-checkable protected zones in local PPT coordinates: title, body, captions or teaching blocks, footer, page number, and any main image that must remain readable. A written statement that "collision is clear" is insufficient unless the `motif_box` avoids every protected zone in the local contact sheet.
- Avoid rounded card grids, pills, badges, button-like labels, excessive borders, and dashboard styling.
- Keep one dominant visual focus per slide.
- Convert generic bullets into designed information groups: meaningful labels, columns, or structured modules. Use numbers only for real source order, steps, ranking, or chronology; never add decorative numbering that can be mistaken for course logic.
- Use long horizontal rules and heavy caption bars only when the selected reference page uses that module. Default to short accent marks, grouped captions, and clear spacing instead.
- Keep a deliberate balance between text, visual evidence, breathing room, and template structure. Do not use a numeric ratio to justify cramped text or token visuals.
- Preserve breathing room through margins and module gaps.
- Keep learner-facing body text at 16 pt or larger. Captions and tertiary explanation should normally be at least 15 pt; never use 12-13 pt for content the learner must read.
- Keep ordinary slide titles at 36 pt or larger and prevent accidental wrapping. Short titles should usually be 46-58 pt; only long Chinese titles should step down toward 36-40 pt.
- Use images to explain, compare, or demonstrate; do not add decorative stock imagery without teaching value.
- Integrate source screenshots and generated case images into text-led knowledge pages. Avoid full-page screenshots unless the slide is explicitly a close-reading page with enough labels and interpretation.
- If a visual needs labels, keep labels editable in Canva/PPTX instead of baking Chinese text into the image.
- Prefer clear teaching diagrams over beautiful but generic imagery.
- Do not let the whole deck collapse into one repeated page pattern. For decks longer than 12 pages, intentionally vary image side, color field, comparison, table, roadmap, close-reading, and summary layouts while keeping the same template language.
- For decks longer than 12 pages, the middle knowledge section must not be mostly plain light `image-left` / `image-right` pages. Use dark-field and accent-field image variants often enough that the contact sheet reads like the selected template rhythm rather than a white-page slide generator.
- Avoid using the same exact content layout, layout family, template reference page/family, or rendered `layout_variant` for more than 2 consecutive knowledge pages unless the source is a repeated table or comparison sequence and the repetition is pedagogically intentional.
- Treat the contact sheet as the real rhythm test. If a run of pages still reads as the same title/text-block/image geometry after thumbnails are reduced, changing orange to cream, left to right, or `layout_variant` names is not enough.

## Layout bank

- `cover`: black field, orange vertical mass, cream geometric focus, minimal title copy.
- `roadmap`: orange or black field with grouped course branches.
- `light`: cream background, large title, explanation, black/orange information blocks.
- `dark`: black background, white copy, orange accent and cream secondary block.
- `orange`: orange background, black title, black/cream information blocks.
- `image-left` / `image-right`: source or generated image and learner-facing explanation share the page with clear hierarchy and enough room for captions.
- `image-left-dark` / `image-right-dark`: dark-field image page with light copy, accent rule, and a light or accent teaching block.
- `image-left-orange` / `image-right-orange`: accent-field image page with dark title and light/dark teaching blocks. The name is retained for backwards compatibility; for a non-orange template, treat it as the selected accent color.
- `comparison`: two clearly labeled sides with both text and visual evidence.
- `table`: compact factual comparison with sufficient row spacing.
- `summary`: return the lesson to its governing framework; do not introduce new knowledge.

Choose layouts by content relationship, not by alternating colors mechanically.

## Template fidelity review

Before final director review, compare the contact sheet against the selected template contact sheet. For the default template, use `assets/template-reference/template-21-pages-contact-sheet.jpg`:

- `course.template_page_mapping` exists for decks longer than 12 pages and was used before PPT generation;
- `course.template_style_atlas` exists and includes signature motif families when the selected template uses them;
- `page-design-quality.md` has been applied to title scale, text grouping, alignment axes, proximity, and image/caption treatment;
- large color fields should feel related to the template;
- title scale, rule lines, margins, and square divisions should match the template language;
- Canva-native motifs planned in `visual_plan.template_motif` appear as local preview proxies in the PPT/contact sheet, with space reserved for later replacement rather than overlay;
- planned native motifs come from the selected template's `course.template_native_element_inventory`, show at least two distinct motif sources across a long deck, do not repeat one element across most motif pages, and do not depend on pasting full template pages;
- motif boxes do not overlap protected title/body/caption/footer/page-number zones, and the contact sheet shows those motifs as integrated structural pieces rather than small corner stickers;
- images should be cropped with discipline and integrated into the page, not pasted as generic cards;
- page rhythm should show controlled variation rather than a single repeated two-column layout.
- for decks longer than 12 pages, the contact sheet should visibly alternate light, dark, and accent field pages in a template-like rhythm; a long white/light middle section fails even when every individual slide is readable.
- a deck that looks like a formatted document with images, long rules, black caption strips, or uniform bullet lists fails even if the automated audit passes.

If the deck looks like a generic generated slide deck with only the template colors applied, revise the layout before Canva import.
