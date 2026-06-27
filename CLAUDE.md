# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is **not an application** — it is the source repository for a single Codex Skill, `build-course-canva-deck`, plus its maintainer tooling and tests. The skill turns a course outline (PDF, XMind, DOCX, Markdown, TXT, OPML, FreeMind) into a Canva recording deck for one shared self-media / video-editing curriculum. The Canva deck is the only end deliverable.

The installable skill lives under `skills/build-course-canva-deck/`. Everything at repo root (`README.md`, `AGENTS.md`, `requirements-dev.txt`, `.agent/`) is maintainer infrastructure that ships *around* the skill, not inside it. A user installs the skill by symlinking `skills/build-course-canva-deck/` into `~/.codex/skills/`.

## Two audiences, two instruction layers — do not confuse them

- **Runtime rules** (how the skill behaves for an end user) live ONLY in `skills/build-course-canva-deck/SKILL.md` and `skills/build-course-canva-deck/references/`. A user running the installed skill sees nothing else.
- **Maintainer rules** (how to edit this repo) live in `AGENTS.md` and `.agent/CONTINUITY.md`. These are git-ignored / local-only and are never read at skill runtime.

Never put a runtime rule only in `AGENTS.md` or `CONTINUITY.md` — the installed skill will never see it. Conversely, `AGENTS.md` is explicitly excluded from git (`.gitignore`) and must not be committed or pushed.

## Maintenance validation commands

Install dev deps first in a fresh environment (needed because skill validation imports PyYAML):

```bash
python3 -m pip install --user -r requirements-dev.txt
```

Compile-check the Python scripts after editing any of them:

```bash
python3 -m py_compile skills/build-course-canva-deck/scripts/extract_source.py skills/build-course-canva-deck/scripts/validate_source_map.py skills/build-course-canva-deck/scripts/audit_deck.py skills/build-course-canva-deck/scripts/make_contact_sheet.py
```

Syntax-check the builder after editing it:

```bash
node --check skills/build-course-canva-deck/scripts/build_deck.mjs
```

Documentation-only changes — check whitespace and scan for stale legacy role names that should no longer appear:

```bash
git diff --check
rg -n "Controller Agent|Source & Curriculum Agent|Source Fidelity Agent|Learning Copy Agent|Visual Layout Agent|Quality Gate Agent|Supervisor|qa-gates" README.md skills/build-course-canva-deck || true
```

For skill metadata / structure changes, when available:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/build-course-canva-deck
```

## Skill runtime architecture (the "big picture")

The skill is a **single director (`总导演`) over four proposal-only worker roles**. This shape is the core design and is enforced across SKILL.md and references — do not collapse it to a single orchestrator and do not add a fifth standalone reviewer role (a sixth `成片审片员` role existed historically and was deliberately removed; the director owns review).

```
总导演 / build-course-canva-deck
├── 课程统筹师   (curriculum position, prerequisites, neighbor boundaries, shared terms)
├── 原稿场记     (source hierarchy/order/sibling preservation, source images)
├── 课堂编剧     (learner-facing screen copy from approved source excerpts)
└── 视觉分镜师   (visual plan, source-image reuse, generated-image candidates, layout variety)
```

Key invariants that span multiple files and are easy to break:

- **Workers are proposal-only.** Only `总导演` performs durable writes (`source-map.json`, `curriculum-context.json`, `deck-spec.json`, screen-copy files), image generation, PPTX build, audit runs, and all Canva actions. Workers write scratch proposals under `scratch/agent-briefs/` and `scratch/` and return a compact handoff plus an evidence-backed `self_check`.
- **Roles are logical, not per-call identities.** Repeated calls to the same role name are continuing invocations; the director carries prior approved state forward in the next brief. (Earlier designs used `role_id` state files and `invocation_id` merge machinery — the current design dropped that in favor of the director simply restating prior output. If you see references to `scratch/agent-state/` or `state_update`, treat them as stale.)
- **Working language is Chinese** for worker prose, slide copy, self-checks, and handoffs; JSON keys, file paths, script flags, schema enum values, and tool identifiers stay English.
- **Mode is user-declared, never inferred.** After inspecting the authoritative source the skill must wait for the user to reply exactly `细纲` (detailed: preserve order/hierarchy/siblings, optimize expression only) or `粗纲` (sparse: expand vertically inside existing nodes only, each addition mapped to a source node with evidence). Never auto-select by length, depth, or file type.
- **Specialist skills are role-scoped plug-ins, not alternate generators.** The director grants a worker a narrow expert slot (e.g. `课堂编剧` → `presentations:Presentations`; `视觉分镜师` → `awesome-design-md`, `baoyu-slide-deck`). Plug-ins cannot replace source intake, the four-role workflow, the learner-facing standard, or director acceptance.

### Reference files and when each applies

`SKILL.md` is intentionally lean and links out. Detailed rules live in three references plus a checklist, loaded at the relevant stage:

- `references/content-and-source.md` — source intake, `细纲`/`粗纲` contract, zero-basis teaching standard, curriculum boundary, source coverage ledger.
- `references/visual-and-design.md` — per-slide teaching visuals, source-image priority, generated-image teaching specificity (`knowledge_anchor` / `observable_teaching_detail` / `instant_takeaway`), template fidelity (color + font + layout language only; **no** Canva native-element reuse).
- `references/roles-and-delivery.md` — the four roles, brief contract, director acceptance lock, Canva delivery preflight/import/approval.
- `references/non-regression-checklist.md` — the director's mandatory pre-delivery learner review, recorded in `交付前自检.md`.

The `.git status` may show deleted older references (`agent-hierarchy.md`, `workflow.md`, `qa-gates.md`, `design-system.md`, etc.) and new consolidated ones. The four files above are the current set; do not reintroduce the old split.

## Scripts: deterministic guards only

The scripts under `skills/build-course-canva-deck/scripts/` are **guardrails, not the authoring brain**. They catch deterministic hard errors; whether the deck reads like a real human instructor's courseware is the director's judgment, verified against the contact sheet and the non-regression checklist. A passing audit is never approval by itself.

- `extract_source.py --input <file> --output <source-map.json> [--assets-dir <dir>]` — format-neutral ordered source map; routes per extension (xmind/opml/mm/docx/md/txt/pdf), preserving topic order and embedded images.
- `validate_source_map.py <source-map.json> [--mode detailed|sparse] [--write] [--require-mode]` — validates hierarchy and records the user-declared mode.
- `audit_deck.py --deck-spec <spec> --source-map <map> --report <out> [--pptx <pptx>] [--layout-dir <dir>]` — deterministic checks: coverage exactly-once, source order, per-node visible `screen_evidence` (must appear in the actual PPTX page XML, not just spec/notes/images), forbidden learner-facing terms, generic-label rejection, hierarchy-flattening, structural repetition. Subjective ratio/count concerns are warnings, not hard errors.
- `build_deck.mjs --spec <deck-spec.json> --output <pptx> --workspace <dir> [--asset-dir <dir>]` — renders editable 16:9 slides via `@oai/artifact-tool`. It does **not** silently truncate points or shrink-fit text; layouts (flow nodes, statement fields, side rails, comparison vs. table) are driven by `visual_plan.rendered_pattern` / `thumbnail_pattern`.
- `make_contact_sheet.py --input-dir <previews> --output <sheet> [--cols 4] [--thumb-width 560] [--gap 20]` — labeled full-deck review sheet for the director's learner review.

`@oai/artifact-tool` is resolved from a scratch workspace's `node_modules` or the bundled Codex primary runtime; `build_deck.mjs` will fail with guidance if neither is available, so builds normally run inside Codex or a prepared scratch workspace, not from this repo root directly.

## Hard runtime constraints (do not weaken for convenience)

These have each regressed before and are now protected by docs + tests. Per `AGENTS.md`, never weaken source-order, visible same-page evidence, sibling-enumeration completeness, source-image coverage, or Canva-template safety gates:

- Every valid source node maps exactly once; each mapped node needs a distinct, same-page, source-ordered visible `screen_evidence` phrase (identical source text is the only reuse exception).
- Detailed-mode sibling enumerations render complete and visible (split slides rather than dropping, hiding in notes, or burying in generated images).
- No producer/backstage text on learner slides (`本页顺序`, `对应节点`, `来源路径`, `source_node`, `screen_evidence`, coverage notes, `PDF`, `原稿`, `制作说明`, etc.).
- No generic structural labels (`对比 A`, `方案 A/B`, `左侧`); comparison/table columns must name a real relationship.
- Template fidelity = palette + typography + type scale + alignment axes + spacing + layout language reproduced as editable composition. Do **not** copy Canva native vector/shape elements; there is no native-element reuse path.
- Typography floors: body ≥16 pt, captions ≥15 pt, ordinary titles ≥36 pt.
- Deck length follows teaching units / source nodes / source images / readability — never padded to match the 21-page `DAHM5fsVEB0` template, and the original Canva template is never modified.

## Change routing and continuity

`AGENTS.md` holds a "Change Routing" table mapping each rule category (agent architecture, source intake, coverage/evidence, visual planning, template/layout, Canva delivery, skill metadata) to the exact set of files to update together — consult it before editing so docs, scripts, and references stay aligned. Keep `SKILL.md` lean and push detail into `references/`; avoid duplicate canonical copies of a rule.

Record substantive, long-term decisions (architecture, review policy, script-behavior, rollbacks) in `.agent/CONTINUITY.md` with `[USER]` / `[CODE]` / `[DECISION]` / `[TOOL]` / `[ASSUMPTION]` tags; append corrections rather than rewriting history, and don't log trivial edits.

Two standing user policies recorded in continuity:

- **Do not edit this skill with an engineering-first mindset.** Human courseware quality — teaching logic, learner comprehension, visual sense, page-level meaning, director judgment — comes before schema neatness, quotas, or code-like compliance. Scripts/tests/quotas are guardrails only and must not make the skill stiff or mechanical.
- **Push to `origin/main` requires explicit user confirmation immediately before each push.** Validate and commit locally after a requested change, but ask before pushing. Skip local commit only when the user asks for local-only work, when validation fails and can't be fixed in-turn, or when auth/network blocks it.
