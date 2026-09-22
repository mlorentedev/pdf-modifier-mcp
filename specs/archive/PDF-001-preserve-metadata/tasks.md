---
tags: [spec, tasks, templates]
created: "2026-09-07"
---

# Tasks - PDF-001-preserve-metadata

> TDD order. One task = one focused commit. Tick as you go. Reorder freely while spec is in `draft` state; freeze once you start `implementing`.
>
> **Inline markers** (optional, additive — borrowed from `github/spec-kit`, adapt-not-adopt per #141):
> - `[P]` — this task has **no dependency on another unchecked task**, so it is safe to run in parallel (fan out to a `Workflow`, or just batch). TDD chains (test → implement → refactor of the *same* behavior) are sequential and must NOT carry `[P]`; independent behaviors can.
> - `[AC<n>]` — this task helps satisfy **acceptance criterion #`<n>`** from `proposal.md`. Lets `/spec check` map coverage deterministically; omit it and the check falls back to semantic judgment.

## Setup

- [ ] Branch created from main: `feat/PDF-001-preserve-metadata`
- [ ] `proposal.md` is complete and acceptance criteria are testable
- [ ] No open questions left in `proposal.md` "Risks / open questions"

## Implementation

> TDD order, one commit per task. Already implemented (retro-filled spec); ticks reflect the shipped state.

- [x] [AC1] Write failing test asserting metadata is preserved by default (`test_modifier_metadata.py::test_metadata_preserved_by_default`)
- [x] [AC1] Capture `doc.metadata` on open (`PDFModifier._extract_metadata`) and restore it before save (`_restore_metadata`)
- [x] [AC2] Write failing test asserting `preserve_metadata=False` updates `modDate` (`test_disable_allows_mod_date_change`)
- [x] [AC2] Stamp a fresh `modDate` via `fitz.get_pdf_now()` when `preserve_metadata=False`
- [x] [AC3] Surface the option in CLI (`--preserve-metadata/--no-preserve-metadata`)
- [x] [AC3] Surface the option in MCP (`modify_pdf_content`, `batch_modify_pdf_content`)
- [x] [AC3] Surface the option in the web replace API body
- [x] [AC3] Add the "Preserve original PDF metadata" checkbox (default on) to the Web UI
- [x] [AC4] Verify no standard metadata field is dropped/emptied after save (covered by the preserve tests)
- [x] Run `mypy`, `ruff`, and the backend + frontend suites

## Closing

- [ ] Every acceptance criterion from `proposal.md` is covered by at least one test
- [ ] Every acceptance criterion has a matching entry in `features.json` (see below) with a non-vacuous verification command
- [ ] Type checks pass
- [ ] Lint passes
- [ ] No unrelated changes in the diff (no scope creep)
- [ ] `verification.md` filled in
- [ ] PR opened referencing this spec folder

## Machine-readable features

This spec emits a sibling `features.json` (alongside this file) following [[pattern-feature-list-as-primitive]]. The JSON is the harness-facing contract: each acceptance criterion maps to ≥1 feature with `id`, `behavior`, `verification` (executable command), `state` (lifecycle), and `evidence` (harness-captured output).

**Pass-state gating:** the agent CANNOT write `"state": "passing"` — only the harness, after running `verification` and capturing exit code 0, may set that terminal state. Reviewers must reject PRs where features.json contains `passing` entries with empty `evidence`.

Minimal `features.json` skeleton (drop into `<repo>/specs/PDF-001-preserve-metadata/features.json`):

```json
[
  {
    "id": "PDF-001-preserve-metadata-f1",
    "behavior": "<one-line copy of an acceptance criterion>",
    "verification": "<single shell command; exit 0 means pass>",
    "state": "pending",
    "evidence": ""
  }
]
```
