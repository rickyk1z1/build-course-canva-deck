# Page Design Quality

This guide adapts professional slide-design lessons for editable Canva/PPTX course decks. It is informed by the public `op7418/guizang-ppt-skill` design discipline, but it does not copy that project's templates, code, or registered layouts. Use these rules as judgment and review standards for `build-course-canva-deck`.

## Design Baseline

The selected Canva template is the golden visual source. A deck fails when it only borrows the palette while ignoring the template's typography scale, alignment axes, spacing, module grouping, and image treatment.

For the default `DAHM5fsVEB0` template, the target feel is:

- strong title-led pages, not document pages;
- large black/orange/cream fields with clear rectangular modules;
- small but readable explanatory copy grouped under a stronger visual anchor;
- image blocks used as evidence or examples, not decoration;
- generous air between title, body groups, and visual evidence;
- no generic horizontal rule across every page;
- no long black caption bars unless the reference template page actually uses that module.

## Template Style Atlas

Before building each slide in a long deck, make a small atlas of the selected template's structure families. The atlas should capture the template's ideas, not just page numbers:

- title axis and title scale;
- major color-field structure;
- image or evidence slot;
- information-module shape;
- content density;
- best-fit content types;
- capacity limits and split triggers;
- local renderer layouts that can actually reproduce the geometry.

Then choose a style family for each slide. A page may adapt ideas from several template pages, but it must still look like it belongs to the same template language.

## Locked Reference Layout

Before building each slide, choose a template style family plus a reference template page or page family and a real `visual_plan.layout_variant`.

Do not invent a freeform page because the content is hard to fit. First try:

- shorten the on-slide wording;
- split the content into another slide;
- change image crop or slot;
- pick a closer reference page family;
- move non-essential production reminders out of the learner page.

`visual_plan.layout_variant` must be rendered into visible geometry. It is not a tag for reporting after the fact. If the current `layout` renderer cannot produce the planned geometry, choose another `layout` or change the visual plan before build.

## Typography Discipline

Use a clear size and weight ladder:

- page title: the dominant element, generally 36-58 pt locally depending on Chinese length;
- cover/title-only hero text: usually 60 pt or larger when the title fits;
- kicker/section label: small, bold, above the title or on the same left axis;
- body explanation: readable supporting copy, usually 16-18 pt, not tiny annotation text;
- point labels: short orange/black labels or numbers, usually 16 pt for text labels and 26 pt for numeric labels;
- point bodies / tertiary explanations: usually 16-17 pt; do not use 12-13 pt to make dense content fit;
- captions: short interpretation near the image, usually 15-16 pt, not a heavy full-width production bar.

Recording decks are viewed during teaching, not only inspected as static design thumbnails. If a page starts to need 12-13 pt for learner-facing explanation, split the slide, reduce copy, or remove non-essential detail. Do not move knowledge required for comprehension into speaker notes.

For Chinese titles:

- shorten first, then reduce size;
- avoid single-character line breaks;
- keep the title on the upper-left template axis unless the selected reference page is a centered/statement page;
- do not let a long title force every other module downward into a cramped lower half.

## Alignment And Proximity

Every page must have a small set of obvious axes:

- title/kicker share one left axis;
- image and caption belong to the same group;
- explanation and point groups share one text axis;
- repeated cards or example images share height and baseline;
- footer and page number sit outside the main content group.

Avoid:

- double padding that makes the body more inset than the title;
- centering a title by accident while body modules are left-aligned;
- scattered bullets whose spacing makes unrelated ideas look grouped;
- captions floating far from the image they explain.

## Contrast And Grouping

Use contrast to create reading order:

1. title;
2. primary case image or diagram;
3. explanation paragraph;
4. labeled points;
5. caption or footnote.

A page with many same-sized text blocks fails even if the alignment is neat. Convert bullets into labeled point groups, columns, or structured modules. Use numbered modules only for real order, steps, ranking, or source enumeration. Keep each module internally close and leave more space between unrelated modules.

## Image Treatment

Images are evidence blocks:

- use fixed slots and consistent crop logic;
- keep source screenshots readable;
- use `contain` for text-heavy source images;
- use `cover` only for photos or generated scenes where cropping will not remove teaching content;
- avoid decorative frames, shadows, rounded corners, or arbitrary borders unless they exist in the template reference;
- use a short editable caption near the image to state what the learner should observe.

If source images are too small or visually noisy, split them across pages, crop to one teachable case, or rebuild them as a cleaner teaching visual. Do not make a new collage of independent images merely to fit more cases on one page.

## Pre-Build Design Table

For decks longer than 12 pages, create or verify a design table before PPT generation:

`slide -> reference page -> layout_variant -> title scale -> primary axis -> image slot -> text group -> caption style -> likely risk`

This table must be used to build the deck, not added after rendering.

## Contact Sheet Review

A passing contact sheet must show:

- title scale and placement close to the reference template language;
- real layout variety without collapsing into repeated two-column pages;
- no run of three or more knowledge pages that keeps the same thumbnail geometry while only changing color, left/right position, or layout names;
- no repeated fallback to one dense index/table page family for unrelated teaching nodes;
- visible use of several template structure families, not only one "safe" information-block structure;
- body copy visibly secondary to title and image evidence;
- generated case images show a concrete detail that teaches the current slide's knowledge point, not just an attractive scene in the right color range;
- aligned modules and stable margins;
- captions close to images;
- Canva-native motif proxies act as structural template pieces rather than small stickers in arbitrary corners;
- every motif clears the title, body copy, captions, footer, page number, and main teaching image;
- motif sources vary across the deck instead of repeating one template element on every motif page;
- no pasted full template page or leftover template placeholder content in the course deck;
- no page that reads like a dense document excerpt;
- no page that reads like a production/source coverage note;
- no accidental single-character title wrap;
- no overuse of horizontal rules, black bars, or uniform bullets.

If the contact sheet looks technically varied but not designed, revise the layout before Canva import.
