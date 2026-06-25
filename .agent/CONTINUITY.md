[PROGRESS]
- 2026-06-24T05:43:57+0800 [USER] User found generated course deck typography too small and asked to fix the default scale in the build-course-canva-deck skill and sync GitHub.
- 2026-06-24T05:43:57+0800 [CODE] Raised default builder typography for titles, cover titles, explanations, point labels/bodies, and captions; documented font-size floors in design QA references; added regression checks in tests/run_tests.py.
- 2026-06-24T06:16:02+0800 [USER] User reported that source/case images were underused, multiple cases were compressed into one unreadable slide, decks kept matching the 21-page template count, and Canva native elements were not actually taking effect.
- 2026-06-24T06:16:02+0800 [CODE] Updated build-course-canva-deck skill docs and audit gates: source-image coverage is mandatory, each slide may use at most 3 readable source images, 2-3 source-image slides require ratio and grouping metadata, deck length must follow teaching coverage instead of template page count, and Canva-native motif plans must use non-placeholder asset IDs with post-import reporting.
- 2026-06-24T19:03:11+0800 [USER] User found the Canva-native motif rules still allowed one non-template element to repeat across pages and sometimes block slide text.
- 2026-06-24T19:03:11+0800 [CODE] Tightened motif rules and audit gates: native motifs must reference existing selected-template vector/shape/group/frame elements, long decks require `course.template_native_element_inventory`, motif sources must vary across pages, and motif boxes must avoid machine-readable protected text/footer/page-number zones.
- 2026-06-25T14:00:00+0800 [USER] Requested fixes for build-course-canva-deck and synchronization between local installed skill and GitHub repository.
- 2026-06-25T14:00:00+0800 [TOOL] Added regression coverage for multi-image PPTX rendering, source-node split mappings, PDF visual hierarchy validation, Canva-native motif final report auditing, and SVG contact sheet fallback.
[DECISIONS]
- 2026-06-25T14:00:00+0800 [CODE] Allow duplicate source-node mappings only for declared continuation slides with source_coverage_kind and source_split_reason.
- 2026-06-25T14:00:00+0800 [CODE] Prefer gpt-image-2 in README to match visual-system and audit behavior.
