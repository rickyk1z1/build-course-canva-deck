# Canva delivery

## Preconditions

- Confirm the Canva connector is connected to an account that can access template `DAHM5fsVEB0`.
- Read the template and accepted reference design when available.
- Keep the original template unchanged.

## Import route

Use the verified local PPTX as the Canva construction bridge. Import it as a new presentation with a course-specific name. This route preserves editable text and avoids relying on unsupported arbitrary page duplication in a non-autofill Canva design.

After import:

1. Read the new design metadata and confirm page count.
2. Read all rich text and scan forbidden language.
3. Retrieve page previews and inspect the complete deck.
4. Confirm font appearance, missing glyphs, image crops, page numbering, and layout consistency.
5. Apply corrections in one editing transaction when possible.
6. Show every returned thumbnail and a complete contact sheet to the user.

## Approval rule

Default to one final review checkpoint. Internal content, visual, and layout reviews happen before the user-facing checkpoint.

If a Canva editing transaction exists, explicitly ask whether to save the shown changes. Do not commit until the user clearly approves. Cancel if the user rejects the draft.

After commit, re-read design metadata and rich text. Return the edit URL only after page count and forbidden-language checks pass.

## Failure handling

- Template inaccessible: use bundled reference images to finish the local PPTX, then ask the user to connect the correct Canva account before import.
- Import page mismatch: stop, repair the local PPTX, and re-import as a new design.
- Missing font or broken glyph: do not silently substitute. Correct the PPTX font names or fix in Canva, then re-preview.
- Thumbnail server error: retry the affected page; do not treat a missing preview as approval.
