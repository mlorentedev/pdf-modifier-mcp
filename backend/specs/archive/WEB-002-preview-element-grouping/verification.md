---
tags: [spec, verification]
created: "2026-08-06"
---

# Verification - WEB-002-preview-element-grouping

## Evidence

Map every acceptance criterion from `proposal.md` to concrete proof (commit hash, test name, or observed behavior).

- [x] AC1 -> `frontend/src/lib/utils/grouping.test.ts` (10 tests: merge, gap split, baseline split, font split, size split, 3-span merge, per-line split, float jitter, span retention) — commit `d2c5423`
- [x] AC2 -> `frontend/src/lib/utils/scroll.test.ts` (6 tests: center, clamp top, clamp bottom, horizontal clamp, above-viewport clamp, zero-size container) + wiring in `PdfPreview.svelte` (`locateElement`: page nav + `computeScrollTarget` at current scale) and `+page.svelte` (`prefillFromGroup`) — commits `3e935cd`, `06545e7`
- [x] AC3 -> `frontend/src/lib/utils/highlight.test.ts` (13 tests incl. 4 new: substring crop x=90/w=75, multi-item match, boundary crop, different-baseline no-join) — commit `3e935cd`
- [x] AC4 -> `PageStructure.elements` fixed in `client.ts`; `npm run check` 0 errors (master had 10 pre-existing; fixed pdf.js v6 `render({canvas})`, `TextItem` narrowing, `globalThis`); backend/ diff limited to the spec folder — commit `06545e7`

## Test status

- Test suite: `npx vitest run` -> **4 files passed, 35 tests passed** (grouping 10, scroll 6, highlight 13, client 6)
- Type check: `npm run check` -> **0 errors, 2 warnings** (both warnings pre-existing in master: `canvas` not `$state`, dropzone keyboard handler)
- Manual smoke test: user validated the app on the running Docker stack (grouping + click-to-locate + highlight OK); Playwright e2e (5 tests) covers upload, grouping, locate, highlight, undo/redo — PR #121
- No regressions in existing test suite: yes (all 35 pass; backend untouched)

## Decisions made during implementation

- **Grouping lives in the frontend** (`frontend/src/lib/utils/grouping.ts`), not `core/analyzer.py` — the repo rule "core is sacred" forbids analyzer changes (validated with the user before tasks.md froze).
- **Join separator heuristic in highlight.ts**: a space is inserted between pdf.js items on the same baseline only when there is a horizontal gap (real word boundary); visually contiguous items (one word split by a style change) join without a separator. Decided after the first RED test failed on "Hello"+"World" vs "Hello Wor"+"ld".
- **Scroll always centers** (not just when off-screen) — the test initially asserted both "no scroll when visible" and a clamped negative target; clarified to "center + clamp to [0, max]" semantics, which is the predictable UX for click-to-locate.
- **Fixed 10 pre-existing svelte-check errors** in the same PR (Standing Order #4 "clean as you go", trivial <5 min each): pdf.js v6 requires `render({ canvas })` (was `canvasContext`), `TextItem` narrowing via `Extract` + explicit map, vitest `globalThis` instead of `global`.

## Promotion candidates

Before archiving, flag what (if anything) should be promoted to the vault. If all three are "no", archive in repo is the only persistence.

- [ ] Lesson for the repo's `docs/lessons.md`? **yes** — "pdf.js v6: `render({ canvas })` not `canvasContext`; items on the same baseline need a gap-aware space when joining text for multi-item term matching" (2 lines, after user validation)
- [ ] ADR-worthy decision for the repo's `docs/adr/adr-XXX.md`? **no** (display-only grouping; no contract change — implementation detail)
- [ ] New pattern candidate for `00_meta/patterns/`? Only if this recurs in >1 project. **no**

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/<feature-id>/` -> `specs/archive/<feature-id>/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
