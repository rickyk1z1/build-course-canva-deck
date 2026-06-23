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
- Plan each page from a reference template page or page family before generating the local PPTX. The slide spec must record `visual_plan.template_reference` with the inherited layout features and adaptation decision, plus `visual_plan.layout_variant` for the actual rendered composition family. Do not build a generic rectangular layout first and then add template-looking decoration later.
- For decks longer than 12 pages, create `course.template_page_mapping` before generating the local PPTX. This mapping is a build input, not a retrospective note: every slide must name its template reference page/page family, layout family, native motif if any, and local PPT decision.
- Preserve template diversity page by page: title-only, dark hero, image triptych, split field, side rail, comparison strip, dense index, and summary pages should remain visually distinct when the selected template uses those patterns. If course content does not fit a reference layout, change text width, wrapping, visual scale, or split the content across slides before abandoning the template composition.
- For long decks, distribute slides across multiple template reference pages/page families. A deck that technically alternates colors but repeatedly uses the same underlying rectangular composition still fails template fidelity.
- For long decks, `build_deck.mjs` must render `visual_plan.layout_variant` into visibly different geometry. Alternating `image-left`, `image-right`, dark, light, and accent pages is not enough when the contact sheet still reads as one repeated two-column layout.
- Canva-native template elements are mandatory for long decks when the selected template provides reusable motifs or structural assets. Scan the template for reusable native assets such as grainy stars, texture blocks, decorative geometry, image-frame motifs, side panels, and background masses, then assign them to matching new-course pages before local PPT generation. A long deck must not rely only on generic PPT rectangles and imported images.
- Treat large textured template motifs as replacement composition modules, not decorations. This applies to every slide type, not only covers. If a motif replaces a cover strip, focus card, image frame, side panel, background mass, or other structural module, do not generate the replaced module. Place the motif by first following its reference template page position, crop, and scale; if course text forces a change, re-balance the whole page in the local PPT stage so the motif still has a clear anchor, breathing room, and no collision with title, explanation, footer, or page number.
- For Canva-native library assets, still preview the asset in the generated local PPTX using a raster `local_preview_path` at the intended final position and scale. This raster is only a local preview proxy. The later Canva-native step must replace that proxy with the native asset, or delete the proxy before inserting the native asset at the same box; it must not overlay the native asset on top of the proxy. The native insertion should follow the already-approved local PPT `motif_box` coordinates after scaling; it must not become a separate post-import layout exploration step.
- When a template motif competes with text, shrink or move the text area, add deliberate line breaks, or select a different template-like composition family. Do not push the motif into a corner just to avoid a wide text box.
- Avoid rounded card grids, pills, badges, button-like labels, excessive borders, and dashboard styling.
- Keep one dominant visual focus per slide.
- Use approximately 40% text and 50% visual area on illustrated knowledge slides, with the remaining space as breathing room and template structure.
- Preserve about 10% breathing room through margins and module gaps.
- Keep body text at 16 pt or larger. Split content before reducing type.
- Keep ordinary slide titles at 35 pt or larger and prevent accidental wrapping.
- Use images to explain, compare, or demonstrate; do not add decorative stock imagery without teaching value.
- Integrate source screenshots and generated case images into text-led knowledge pages. Avoid full-page screenshots unless the slide is explicitly a close-reading page with enough labels and interpretation.
- If a visual needs labels, keep labels editable in Canva/PPTX instead of baking Chinese text into the image.
- Prefer clear teaching diagrams over beautiful but generic imagery.
- Do not let the whole deck collapse into one repeated page pattern. For decks longer than 12 pages, intentionally vary image side, color field, comparison, table, roadmap, close-reading, and summary layouts while keeping the same template language.
- For decks longer than 12 pages, the middle knowledge section must not be mostly plain light `image-left` / `image-right` pages. Use dark-field and accent-field image variants often enough that the contact sheet reads like the selected template rhythm rather than a white-page slide generator.
- Avoid using the same exact content layout, layout family, or background color mode for more than 4 consecutive knowledge pages unless the source is a repeated table or comparison sequence and the repetition is pedagogically intentional.

## Layout bank

- `cover`: black field, orange vertical mass, cream geometric focus, minimal title copy.
- `roadmap`: orange or black field with grouped course branches.
- `light`: cream background, large title, explanation, black/orange information blocks.
- `dark`: black background, white copy, orange accent and cream secondary block.
- `orange`: orange background, black title, black/cream information blocks.
- `image-left` / `image-right`: source or generated image occupies about half the page; explanation, bullets, and caption occupy about 40%.
- `image-left-dark` / `image-right-dark`: dark-field image page with light copy, accent rule, and a light or accent teaching block.
- `image-left-orange` / `image-right-orange`: accent-field image page with dark title and light/dark teaching blocks. The name is retained for backwards compatibility; for a non-orange template, treat it as the selected accent color.
- `comparison`: two clearly labeled sides with both text and visual evidence.
- `table`: compact factual comparison with sufficient row spacing.
- `summary`: return the lesson to its governing framework; do not introduce new knowledge.

Choose layouts by content relationship, not by alternating colors mechanically.

## Template fidelity gate

Before final QA, compare the contact sheet against the selected template contact sheet. For the default template, use `assets/template-reference/template-21-pages-contact-sheet.jpg`:

- `course.template_page_mapping` exists for decks longer than 12 pages and was used before PPT generation;
- large color fields should feel related to the template;
- title scale, rule lines, margins, and square divisions should match the template language;
- Canva-native motifs planned in `visual_plan.template_motif` appear as local preview proxies in the PPT/contact sheet, with space reserved for later replacement rather than overlay;
- images should be cropped with discipline and integrated into the page, not pasted as generic cards;
- page rhythm should show controlled variation rather than a single repeated two-column layout.
- for decks longer than 12 pages, the contact sheet should visibly alternate light, dark, and accent field pages in a template-like rhythm; a long white/light middle section fails even when every individual slide is readable.

If the deck looks like a generic generated slide deck with only the template colors applied, revise the layout before Canva import.
