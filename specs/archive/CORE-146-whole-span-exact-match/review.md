---
spec: "CORE-146-whole-span-exact-match"
verdict: "PASS"
reviewed_sha: "c1abea4212aea1ded8dd27dfd54238297a3faea1"
reviewer: "nan/mimo-v2.5"
date: "2026-09-08"
---

## Adversarial review

**Scope**: CORE-146-whole-span-exact-match (4 commits: `5c283d8`, `79b45aa`, `eb394c4`, `c1abea4`)
**Sources**: `specs/CORE-146-whole-span-exact-match/{proposal,tasks,verification,features}.json`, `git diff 592e397..c1abea4` (full feature diff; launcher-resolved base `79b45aa` excluded the core commit — corrected to parent `592e397` for completeness)

### Spec and task alignment

All four acceptance criteria have corresponding implementation and tests:

| AC | Implementation | Tests | Verdict |
|----|---------------|-------|---------|
| AC1 (literal whole_span) | `modifier.py:360-362` (single-span), `modifier.py:446-461` (cross-span) | `TestWholeSpanLiteral` (4), `TestWholeSpanCrossSpan` (2) | Covered |
| AC2 (default unchanged) | Default `whole_span=False` | Full suite `339 passed, 17 skipped` — no regressions | Covered |
| AC3 (regex fullmatch) | `modifier.py:360` (`fullmatch` when `whole_span`) | `TestWholeSpanRegex` (2) | Covered |
| AC4 (surfaces) | CLI `--whole-span`, MCP `whole_span` param, API `whole_span` body field, Web UI checkbox | `TestMCPWholeSpan` (2), `TestReplaceWholeSpan` (2) | Covered |

All 14 tasks in `tasks.md` are ticked. The diff matches the proposal scope exactly — no creep detected.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|-------------|
| Minor | REAL | spec | `proposal.md` AC checkboxes (`- [ ]`) remain unchecked despite verification.md confirming all ACs pass | proposal.md lines 57-66 | N/A (spec hygiene) | spec (`proposal.md` — edit allowed; outside contract set for staleness) |
| Minor | REAL | spec | `features.json` entries all have `"state": "pending"` with empty `"evidence"` — diverges from verification.md which documents passing results; harness has not run to set terminal state | features.json (all 4 entries) | N/A (harness state) | spec (`features.json` — edit allowed; outside contract set for staleness) |
| Minor | THEORETICAL | tests | MCP and API interface tests only assert negative path (`whole_span=True` rejects substring) — they do not assert positive path (`whole_span=True` accepts exact match). A regression where `whole_span` is silently ignored on these surfaces would still pass the interface tests | `test_mcp.py::TestMCPWholeSpan`, `test_routes.py::TestReplaceWholeSpan` — both only test rejection | `test_modify_whole_span_rejects_substring`, `test_batch_whole_span_rejects_substring`, `test_replace_whole_span_rejects_substring` | tests (add positive-path assertions to MCP and API tests) |
| Minor | THEORETICAL | code | `_find_matches_in_merged` cross-span path calls `merged.find(target)` after confirming `stripped == target` — the `find()` always succeeds because the equality check guarantees the target exists in `merged`, but the code has no guard for the (impossible) `-1` case | `modifier.py:458` | `test_cross_span_exact_concatenation_matches` (covers the happy path) | code (defensive; low priority — `find` returning -1 is unreachable given the preceding equality) |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | A | All 4 ACs verified; single-span, cross-span, regex, and default paths all tested and passing |
| Verification       | B | Core + interface tests exist and pass; features.json not yet harness-populated (pending state); MCP/API tests lack positive-path assertions |
| Scope              | A | Diff matches proposal exactly; CI changes from a separate PR (PR #150) appear in the git range but are not part of this feature |
| Reliability        | A | Error paths unchanged (whole_span is a new orthogonal flag); default-off backward compatibility confirmed by full suite |
| Maintainability    | A | Clean naming, short functions, inline docstrings explain `whole_span` semantics; field description on `ReplacementSpec.whole_span` is self-documenting |
| Handoff-readiness  | B | Verification.md filled, tasks ticked, PR opened; features.json not yet harness-populated; proposal.md AC checkboxes unchecked |

### Verdict
PASS

### Recommended next steps

- **Before archive** (spec hygiene, not blocking):
  1. Check the AC boxes in `proposal.md` (AC1–AC4) — they remain `- [ ]` despite all being verified.
  2. Run the harness (`dotf spec review` output or equivalent) to populate `features.json` states from `"pending"` to `"passing"` with evidence, or manually update if the harness is not available.
- **Follow-up ticket** (minor, non-blocking):
  3. Add positive-path assertions to `TestMCPWholeSpan` and `TestReplaceWholeSpan` (e.g., test that `whole_span=True` with an exact-match target produces `replacements_made=1`). This closes the interface-test gap where a silently-ignored `whole_span` would still pass.
- **Archive is advisable** in the current state: the verdict is PASS, all findings are Minor, and no Blockers or REAL Majors exist. The spec hygiene items (1–2) can be applied in the same session as the archive without invalidating this review, since `proposal.md` and `features.json` are outside the staleness-checked contract set for this review's own `reviewed_sha`.
