# Page Design Quality

This guide adapts professional slide-design lessons for editable Canva/PPTX course decks. It is informed by the public `op7418/guizang-ppt-skill` design discipline, but it does not copy that project's templates, code, or registered layouts. Use these rules as judgment and QA standards for `build-course-canva-deck`.

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

## Locked Reference Layout

Before building each slide, choose a reference template page or page family and a real `visual_plan.layout_variant`.

Do not invent a freeform page because the content is hard to fit. First try:

- shorten the on-slide wording;
- split the content into another slide;
- change image crop or slot;
- pick a closer reference page family;
- move secondary explanation into speaker notes.

`visual_plan.layout_variant` must be rendered into visible geometry. It is not a tag for reporting after the fact.

## Typography Discipline

Use a clear size and weight ladder:

- page title: the dominant element, generally 36-58 pt locally depending on Chinese length;
- cover/title-only hero text: usually 60 pt or larger when the title fits;
- kicker/section label: small, bold, above the title or on the same left axis;
- body explanation: readable supporting copy, usually 16-18 pt, not tiny annotation text;
- point labels: short orange/black labels or numbers, usually 16 pt for text labels and 26 pt for numeric labels;
- point bodies / tertiary explanations: usually 16-17 pt; do not use 12-13 pt to make dense content fit;
- captions: short interpretation near the image, usually 15-16 pt, not a heavy full-width production bar.

Recording decks are viewed during teaching, not only inspected as static design thumbnails. If a page starts to need 12-13 pt for learner-facing explanation, split the slide, reduce copy, or move detail to speaker notes.

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

A page with many same-sized text blocks fails even if the alignment is neat. Convert bullets into labeled point groups, columns, cards, or numbered mini-modules. Keep each module internally close and leave more space between unrelated modules.

## Image Treatment

Images are evidence blocks:

- use fixed slots and consistent crop logic;
- keep source screenshots readable;
- use `contain` for text-heavy source images;
- use `cover` only for photos or generated scenes where cropping will not remove teaching content;
- avoid decorative frames, shadows, rounded corners, or arbitrary borders unless they exist in the template reference;
- use a short editable caption near the image to state what the learner should observe.

If source images are too small or visually noisy, make a collage or rebuild them as a cleaner teaching visual, but preserve the original teaching relationship.

## Pre-Build Design Table

For decks longer than 12 pages, create or verify a design table before PPT generation:

`slide -> reference page -> layout_variant -> title scale -> primary axis -> image slot -> text group -> caption style -> likely risk`

This table must be used to build the deck, not added after rendering.

## Contact Sheet Review

A passing contact sheet must show:

- title scale and placement close to the reference template language;
- real layout variety without collapsing into repeated two-column pages;
- body copy visibly secondary to title and image evidence;
- aligned modules and stable margins;
- captions close to images;
- no page that reads like a dense document excerpt;
- no accidental single-character title wrap;
- no overuse of horizontal rules, black bars, or uniform bullets.

If the contact sheet looks technically varied but not designed, revise the layout before Canva import.
