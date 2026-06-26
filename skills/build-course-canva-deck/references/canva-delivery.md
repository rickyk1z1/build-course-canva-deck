# Canva delivery

## Preconditions

- Confirm the Canva connector is connected to an account that can access the chosen template route.
- Default visual template: `DAHM5fsVEB0`. If the user supplies another template/design ID, that ID becomes the chosen visual template for this run.
- Accepted reference design when available: `DAHNU2_rPtU`; it is a quality reference, not a content source.
- Keep the chosen source template unchanged.

## Access preflight

Run this before importing or creating any Canva design:

1. Run Canva connector tool discovery before judging capability:
   - Search for the exact import/read operations, not only generic Canva words. Include `import_design_from_url`, `design_file`, `PPTX`, `presentation`, `get_design`, `get_design_pages`, and `get_design_content` in the discovery query.
   - If the first search does not expose an import tool, run one targeted second search for `Canva import_design_from_url design_file PPTX presentation`. Do not declare Canva import unavailable after a single generic or vague search.
   - When `_import_design_from_url` is available, use it with `design_file` for the verified local PPTX. Do not stop for browser fallback just because template-native element copy is unavailable.
   - Record the exact discovery queries and whether `_import_design_from_url`, `_get_design`, `_get_design_pages`, and `_get_design_content` were exposed.
2. Search/read the chosen template ID from `course.template_design_id` or the user's explicit template link. Use `DAHM5fsVEB0` only when no other template is selected.
3. Search/read the accepted reference design `DAHNU2_rPtU` when available.
4. Record the result in `canva-access.json`:
   - active Canva account or workspace if the tool exposes it;
   - accessible template/reference IDs;
   - import/read tool availability from step 1;
   - chosen template route;
   - connector errors and timestamps.
5. If the chosen template returns `design not found` but other designs are readable, treat it as a template permission/workspace problem, not as proof the design does not exist.
6. If the connector returns internal errors such as MCP `-32603`, treat it as a connector/service failure. Retry once after reconnecting; do not repeatedly call the same failing operation.
7. Do not import or create the final Canva design until one route below is available.

Allowed template routes:

- **Connector route:** connector can access the chosen template; proceed normally.
- **Accessible duplicate route:** user provides a duplicate template/design ID that the current connector can access; use it for this device while preserving the same visual system.
- **Bundled-reference route:** connector cannot access the template, but the local PPTX has already been built from bundled template references; ask the user to connect the correct Canva account or provide an accessible duplicate before Canva import.
- **Browser fallback route:** only after explicit user approval, use the user's logged-in browser/Chrome session to upload/import the verified PPTX and inspect pages. Operate only on a new design; never modify the canonical template.

If none of these routes is available, stop and report the blocker. Do not continue by guessing permissions.

## Import route

Use the verified local PPTX as the Canva construction bridge. Import it as a new presentation with a course-specific name. This route preserves editable text and avoids relying on unsupported arbitrary page duplication in a non-autofill Canva design.

After import:

1. Read the new design metadata and confirm page count.
2. Read all rich text and scan forbidden language.
3. If the selected template has signature native motifs or any slide uses `visual_plan.template_motif`, execute the native motif replacement plan before visual approval:
   - use the local PPT `local_preview_path` image only as a local preview proxy;
   - verify each motif's `native_element_ref` points to an existing native vector/shape/group/frame element in the chosen template or accessible duplicate; do not replace this with a Canva library search result or unrelated asset ID;
   - match the imported proxy by page index and `local_ppt_layout.motif_box` position/size;
   - for vector/shape/group/frame motifs, copy or reuse the recorded existing template element itself and paste/place it at the already-approved scaled box, then delete or replace the local proxy;
   - never paste an entire template page into the final course deck as a shortcut for retrieving a motif; if the only available operation is whole-page duplication, mark native reuse blocked for this run;
   - use media `update_fill` only for motifs whose recorded template source is actually an image/frame fill; it does not satisfy vector motif reuse;
   - if the connector cannot copy/reuse the native template element, stop for an accessible duplicate or explicit browser fallback rather than substituting a random Canva asset;
   - never leave the proxy image underneath an overlaid native Canva element, and never leave template-placeholder text, logo marks, or unrelated source-page objects in the final course page.
4. Write `canva-native-motif-report.json` with one row per planned motif: slide number, motif kind, source template design/page/element ID, element type, local proxy match result, final Canva element result, collision status, final status, and blocker if any. Final delivery is blocked when any motif remains `pending`, `proxy_only`, `unmatched`, `non_template_asset`, `overlaps_text`, `repeated_single_element`, `whole_page_paste`, or `blocked` without explicit user approval. A report that only says `blocked-no-atomic-copy` is not a completed template-faithful delivery for templates whose style depends on signature motifs.
5. Retrieve page previews and inspect the complete deck.
6. Confirm font appearance, missing glyphs, image crops, page numbering, native motif replacement, motif diversity, no motif/text overlap, no source-tracking/meta copy, no pasted template page residue, and layout consistency.
7. Apply corrections in one editing transaction when possible.
8. Show every returned thumbnail and a complete contact sheet to the user.

## Approval rule

Default to one final review checkpoint. Internal content, visual, and layout reviews happen before the user-facing checkpoint.

If a Canva editing transaction exists, explicitly ask whether to save the shown changes. Do not commit until the user clearly approves. Cancel if the user rejects the draft.

After commit, re-read design metadata and rich text. Return the edit URL only after page count and forbidden-language checks pass.

## Failure handling

- Template inaccessible: use bundled reference images to finish the local PPTX, then ask the user to connect the correct Canva account, provide an accessible duplicate template ID, or approve browser fallback before import.
- Same login but different access: explain that Canva connector access can differ from browser-visible access because of team/workspace context, token scope, link permissions, or connector cache. Verify by directly opening/copying the template in the target device's browser and by reconnecting the Canva integration.
- Connector internal error: retry once after reconnecting. If it still fails, ask for browser fallback rather than repeatedly calling the broken connector.
- Import page mismatch: stop, repair the local PPTX, and re-import as a new design.
- Missing font or broken glyph: do not silently substitute. Correct the PPTX font names or fix in Canva, then re-preview.
- Thumbnail server error: retry the affected page; do not treat a missing preview as approval.
