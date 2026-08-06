---
tags: [spec, tasks]
created: "2026-08-06"
---

# Tasks - WEB-002-preview-element-grouping

> TDD order. One task = one focused commit. Tick as you go. Reorder freely while spec is in `draft` state; freeze once you start `implementing`.

## Setup

- [x] Branch created from main: `feat/web-118-element-grouping` (worktree `pdf-modifier-mcp-wt-118-element-grouping`, outside the repo)
- [x] `proposal.md` is complete and acceptance criteria are testable (user validated: frontend post-process, gap ≤ 1.2× font-size, proportional highlight estimate)
- [x] No open questions left in `proposal.md` "Risks / open questions" (both MUST-resolve items accepted by user)

## Implementation

> TDD order. Grouping (AC1) and click-to-locate (AC2) are independent behaviors — their first test carries `[P]`. Highlight precision (AC3) shares the `highlight.ts` module with AC1's sibling helpers but is a distinct behavior; sequential TDD within each chain.

- [ ] [P] [AC1] RED — Write failing `frontend/src/lib/utils/grouping.test.ts`: groupElements() merges consecutive same-line/same-font/same-size spans into one entry with concatenated text; two-column layout does NOT merge across columns (gap > threshold)
- [ ] [AC1] GREEN — Implement `frontend/src/lib/utils/grouping.ts` (`groupElements`, gap threshold ≤ 1.2× font-size, same baseline `origin.y` + font + size)
- [ ] [AC1] Refactor — extract threshold constant, document heuristic limits in docstring
- [ ] [P] [AC2] RED — Write failing test for click-to-locate: `+page.svelte` click on grouped element triggers navigation to the element's page + scroll request
- [ ] [AC2] GREEN — Wire click-to-locate: `PdfPreview.svelte` accepts `focusTarget` prop (page + bbox), navigates page if needed, scrolls `.pdf-scroll` container to center the rect (zoom-aware mapping)
- [ ] [AC3] RED — Extend `highlight.test.ts`: getHighlightRects() returns rect covering only the matched substring width within an item (proportional estimate), empty when no match
- [ ] [AC3] GREEN — Update `highlight.ts` to crop the item rect to the matched substring (proportional to full item width, clamp to item bounds)
- [ ] [AC4] Fix type mismatch: `frontend/src/lib/api/client.ts` `PageStructure.text_elements` → `elements` (backend serializes `elements`; `+page.svelte` already reads `p.elements`) — svelte-check validates
- [ ] [AC4] Refactor `+page.svelte` sidebar: render grouped entries (`filteredGroups` derived), keep search working over grouped text, retain `prefillFromElement`

## Closing

- [ ] Every acceptance criterion from `proposal.md` is covered by at least one test (AC1 grouping, AC2 scroll/nav, AC3 highlight, AC4 type+checks)
- [ ] Every acceptance criterion has a matching entry in `features.json` with a non-vacuous verification command
- [ ] `npm run check` passes (svelte-check + tsconfig)
- [ ] `npm run test` passes (vitest, incl. existing highlight tests)
- [ ] No unrelated changes in the diff (no scope creep; backend/ untouched)
- [ ] `verification.md` filled in
- [ ] PR opened referencing this spec folder
- [ ] User validates the running app (Docker stack up, manual user-testing of sidebar grouping, click-to-locate, highlight precision) before PR merge

## Machine-readable features

This spec emits a sibling `features.json` (alongside this file) following [[pattern-feature-list-as-primitive]]. The JSON is the harness-facing contract: each acceptance criterion maps to ≥1 feature with `id`, `behavior`, `verification` (executable command), `state` (lifecycle), and `evidence` (harness-captured output).

**Pass-state gating:** the agent CANNOT write `"state": "passing"` — only the harness, after running `verification` and capturing exit code 0, may set that terminal state. Reviewers must reject PRs where features.json contains `passing` entries with empty `evidence`.
