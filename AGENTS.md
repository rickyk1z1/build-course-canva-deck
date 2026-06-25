# build-course-canva-deck AGENTS.md

This file guides agents who maintain this skill repository. It is not the runtime instruction source for users of `$build-course-canva-deck`.

## Scope

- Runtime behavior belongs in `skills/build-course-canva-deck/SKILL.md` and directly linked files under `skills/build-course-canva-deck/references/`.
- User-facing install and overview belong in `README.md`.
- Deterministic enforcement belongs in `skills/build-course-canva-deck/scripts/` and tests.
- Long-term maintenance decisions and substantive changes belong in `.agent/CONTINUITY.md`.
- Do not put a runtime rule only in this file; agents using the installed skill may never read it.
- Do not store course-project facts here. Project-specific context belongs in that project's `AGENTS.md`.

## Change Routing

- Agent architecture, role names, staged dispatch, or worker brief fields:
  update `SKILL.md`, `references/agent-hierarchy.md`, `references/workflow.md`, and `README.md`.
- Source intake, `细纲`/`粗纲`, source-map schema, extraction, or validation:
  update `references/workflow.md`, `references/qa-gates.md`, `scripts/extract_source.py`, `scripts/validate_source_map.py`, fixtures, and tests as needed.
- Source coverage, `screen_evidence`, forbidden learner-facing terms, density limits, or PPTX XML audit:
  update `references/qa-gates.md`, `references/workflow.md`, `references/content-policy.md`, `scripts/audit_deck.py`, and tests.
- Visual planning, source images, generated images, `image_generation_tasks`, image-poor rules, or Canva-native motifs:
  update `references/visual-system.md`, `references/workflow.md`, `references/agent-hierarchy.md`, `references/qa-gates.md`, `scripts/audit_deck.py`, `scripts/build_deck.mjs`, and `README.md` when user-visible.
- Template fidelity, page design, layout rhythm, typography, or contact-sheet review:
  update `references/design-system.md`, `references/page-design-quality.md`, `references/workflow.md`, `scripts/build_deck.mjs`, and relevant tests.
- Canva import, template access, browser fallback, draft approval, or saved-design verification:
  update `references/canva-delivery.md`, `references/workflow.md`, `SKILL.md`, and `README.md`.
- Skill trigger metadata or UI chip text:
  update `SKILL.md` frontmatter and `skills/build-course-canva-deck/agents/openai.yaml` together.

## Maintenance Rules

- Keep `SKILL.md` lean. Move detailed rules, examples, schemas, and long explanations into `references/`.
- Avoid duplicate rule copies. If a rule must be mentioned in more than one file, keep one canonical detailed version and summarize elsewhere.
- Preserve the proposal-only worker boundary: workers write scratch proposals; the controller/director owns durable files, image generation execution, PPTX build, Canva actions, and final approval.
- Preserve logical worker continuity: repeated calls to the same role must use stable `role_id` state under `scratch/agent-state/`, even if the runtime starts a fresh subagent process.
- Keep tests and docs aligned with the current role names: `总导演`, `课程统筹师`, `原稿场记`, `课堂编剧`, `视觉分镜师`, `成片审片员`.
- Do not weaken source-order, visible evidence, sibling enumeration, source-image coverage, or Canva-template safety gates for convenience.
- Do not overwrite original template assets or generated reference assets unless the user explicitly asks.
- If user feedback reveals a repeatable failure mode, update the relevant runtime reference and add or adjust a test when the failure is script-enforceable.
- After any user-requested skill repository change, run the appropriate validation, commit, and push to `origin/main` immediately. Skip only when the user explicitly asks for local-only work, validation fails and cannot be fixed in the same turn, or GitHub authentication/network access is blocked.

## Validation

Install development validation dependencies when `yaml`/`PyYAML` is unavailable:

```bash
python3 -m pip install --user -r requirements-dev.txt
```

For documentation-only changes, run:

```bash
git diff --check
rg -n "Controller Agent|Source & Curriculum Agent|Source Fidelity Agent|Learning Copy Agent|Visual Layout Agent|Quality Gate Agent|Supervisor|质检门代理|视觉版式代理|屏显文案代理|源序保真代理|源材与课程边界代理|总控代理" README.md skills/build-course-canva-deck || true
```

For skill metadata or structure changes, also run when available:

```bash
python3 /Users/ricky/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/build-course-canva-deck
```

For Python script changes, run at minimum:

```bash
python3 -m py_compile skills/build-course-canva-deck/scripts/extract_source.py skills/build-course-canva-deck/scripts/validate_source_map.py skills/build-course-canva-deck/scripts/audit_deck.py skills/build-course-canva-deck/scripts/make_contact_sheet.py
```

For audit, schema, density, visual gate, or fixture changes, run:

```bash
python3 tests/run_tests.py
python3 skills/build-course-canva-deck/tests/test_audit_deck_density.py
```

For builder or layout-rendering changes, also build or inspect a representative deck/contact sheet when practical, and document any skipped visual verification.

## Continuity

- Update `.agent/CONTINUITY.md` for cross-turn plans, long-term decisions, role architecture changes, QA policy changes, script behavior changes, and rollback decisions.
- Keep continuity entries factual. Use `[USER]`, `[CODE]`, `[TOOL]`, or `[ASSUMPTION]`.
- Do not record every tiny edit. Record changes that affect future maintenance or skill behavior.
- If a previous continuity entry becomes stale, append a correction with evidence instead of rewriting history.
