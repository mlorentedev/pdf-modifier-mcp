---
tags: [spec, verification]
created: "2026-09-08"
---

# Verification - CORE-146-whole-span-exact-match

## Evidence

- [x] AC1 (whole_span rejects partial substring, matches exact span, cross-span) -> commits `5c283d8` / tests `tests/unit/core/test_modifier_whole_span.py::TestWholeSpanLiteral` (4 tests) + `TestWholeSpanCrossSpan` (2 tests)
- [x] AC2 (default behaviour unchanged) -> baseline `177 passed, 11 skipped` on `origin/master` before the change; after: `339 passed, 17 skipped` full unit suite (including the 11 new tests), zero modifications to existing tests
- [x] AC3 (whole_span + use_regex -> fullmatch) -> commit `5c283d8` / tests `TestWholeSpanRegex::test_regex_fullmatch_rejects_partial` + `test_regex_fullmatch_matches_exact`
- [x] AC4 (CLI/MCP/API/UI propagation) -> commit `79b45aa` (`tests/unit/web/test_routes.py::TestReplaceWholeSpan`, `tests/unit/interfaces/test_mcp.py::TestMCPWholeSpan`) + commit `eb394c4` (Web UI checkbox, `svelte-check` 0 errors, vitest 50 passed)

## Test status

- Test suite: `cd backend && uv run pytest tests/unit -q` -> **339 passed, 17 skipped**
- Frontend: `npx svelte-check` -> 0 errors (2 pre-existing warnings, unrelated files); `npx vitest run` -> **50 passed**
- Lint/type: `ruff check` clean; `mypy src/pdf_modifier` -> 0 issues
- Manual smoke test: `pdf-mod modify in.pdf out.pdf -r '24=X' --whole-span` on a PDF containing `24 hours` -> `Replacements: 0`, output text byte-identical (`24 hours`), exit 0
- Mutation: delegated to CI (`mutation.yml` on the PR); the 11 new tests assert both match and no-match paths, so the matching mutations are non-vacuous

## Decisions made during implementation

- `whole_span` + `use_regex` combination resolves to regex `fullmatch` (documented in the model field description) rather than a validation error — decided with the human in session (2026-09-08), recorded in proposal Risks as RESOLVED.
- Cross-span under `whole_span` compares the **stripped merged line text** against the target (not per-span equality): a target equal to a single span inside a longer line legitimately matches via the single-span pass (covered by `test_cross_span_partial_target_rejected` using a target that equals no span).
- The initial cross-span test used target `World`, which matched the single-span exact path — the test was corrected to `o Wo` to isolate the cross-span route; recorded here because the first failing run was a wrong test, not a wrong implementation.

## Promotion candidates

- [x] Lesson for the repo's `docs/lessons/`? no — the substring-vs-exact-match trade-off is documented in the field description and checkbox hint
- [ ] ADR-worthy decision? no — the flag mirrors the existing `use_regex` design; no architectural deviation
- [ ] Pattern candidate? no — single-project UX decision

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/CORE-146-whole-span-exact-match/` -> `specs/archive/CORE-146-whole-span-exact-match/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
