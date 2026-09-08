---
tags: [spec, tasks]
created: "2026-09-08"
---

# Tasks - CORE-146-whole-span-exact-match

> TDD order. One task = one focused commit. Tick as you go. Reorder freely while spec is in `draft` state; freeze once you start `implementing`.
>
> **Inline markers** (optional, additive — borrowed from `github/spec-kit`, adapt-not-adopt per #141):
> - `[P]` — this task has **no dependency on another unchecked task**, so it is safe to run in parallel (fan out to a `Workflow`, or just batch). TDD chains (test → implement → refactor of the *same* behavior) are sequential and must NOT carry `[P]`; independent behaviors can.
> - `[AC<n>]` — this task helps satisfy **acceptance criterion #`<n>`** from `proposal.md`. Lets `/spec check` map coverage deterministically; omit it and the check falls back to semantic judgment.

## Setup

- [x] Branch created from master: `feat/CORE-146-whole-span-exact-match`
- [x] `proposal.md` is complete and acceptance criteria are testable
- [x] No open questions left in `proposal.md` "Risks / open questions" (`whole_span`+`use_regex` → `fullmatch`, resolved 2026-09-08)

## Implementation

> TDD order, one commit per task.

- [x] [AC2] Regression guard: confirm the existing core suite passes unmodified with the new field defaulted off
- [x] [AC1] Write failing tests: `whole_span=True` — target `24` does not match `24 hours`, matches exact span `24` (single-span pass)
- [x] [AC1] Implement `whole_span` in `ReplacementSpec` and the literal matching path of `_match_single_span`
- [x] [AC3] Write failing test: `whole_span=True` + `use_regex=True` uses `fullmatch` (pattern `24` does not match `24 hours`)
- [x] [AC3] Implement `fullmatch` switch in the regex matching path
- [x] [AC1] Write failing test: cross-span matching respects `whole_span` (concatenated text must equal the target exactly)
- [x] [AC1] Implement `whole_span` in the cross-span comparison
- [x] [AC4] Surface the option in CLI (`--whole-span`)
- [x] [AC4] Surface the option in MCP (`modify_pdf_content`, `batch_modify_pdf_content`)
- [x] [AC4] Surface the option in the web replace API body
- [x] [AC4] Add the "Whole-span exact match" checkbox (default off) to the Web UI next to the regex control
- [x] Run `mypy`, `ruff`, backend suite, frontend `svelte-check` + vitest

## Closing

- [x] Every acceptance criterion from `proposal.md` is covered by at least one test
- [x] Every acceptance criterion has a matching entry in `features.json` (see below) with a non-vacuous verification command
- [x] Type checks pass
- [x] Lint passes
- [x] No unrelated changes in the diff (no scope creep)
- [x] `verification.md` filled in
- [x] PR opened referencing this spec folder

## Machine-readable features

This spec emits a sibling `features.json` (alongside this file) following [[pattern-feature-list-as-primitive]]. The JSON is the harness-facing contract: each acceptance criterion maps to ≥1 feature with `id`, `behavior`, `verification` (executable command), `state` (lifecycle), and `evidence` (harness-captured output).

**Pass-state gating:** the agent CANNOT write `"state": "passing"` — only the harness, after running `verification` and capturing exit code 0, may set that terminal state. Reviewers must reject PRs where features.json contains `passing` entries with empty `evidence`.
