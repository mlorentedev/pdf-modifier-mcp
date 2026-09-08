---
id: "CORE-146-whole-span-exact-match"
type: spec
status: draft # draft | implementing | verifying | archived
created: "2026-09-07"
issue: "mlorentedev/pdf-modifier-mcp#146"   # repo#NNN — GitHub issue / Project item that tracks this spec
tags: [spec, proposal]
template_version: "1.0"
---

# CORE-146-whole-span-exact-match

> **Naming**: file lives at `<repo>/specs/CORE-146-whole-span-exact-match/proposal.md`. `CORE-146-whole-span-exact-match` is `AREA-NNN-slug` (e.g. `TOOL-001-secret-drift`).

## Why

<!-- from issue #146: feat(core): whole-span exact match option to avoid substring collisions -->

A short replacement target such as `24` corrupts unrelated spans (e.g. `24 hours`) because
the literal matching in `_match_single_span` is substring-based (`target in text`). The only
workaround today is regex with anchors (`^24$`), which requires the user to know regex —
unacceptable for the Web UI audience. Without this option, a careless short target silently
destroys neighbouring text and the user only notices in the output PDF.

## What

1. New field `whole_span: bool = False` on `ReplacementSpec`. When `True`, literal targets
   must match the **entire** span text (equality after `strip()`) instead of a substring,
   and regex patterns switch from `search` to `fullmatch`. Default behaviour is unchanged.
2. The option is exposed on every surface: `--whole-span` CLI flag, a parameter on the MCP
   `modify`/`batch` tools, a field in the replace API body, and a checkbox in the Web UI
   next to the existing `use_regex` control.
3. Backward compatible: with `whole_span=False` (the default) every existing behaviour and
   test result is unchanged.

## Out of scope

- `core/analyzer.py` is NOT touched (sacred core).
- No per-target option maps (e.g. per-replacement flags) — a single global flag, mirroring
  `use_regex`.
- No change to cross-span matching semantics beyond respecting `whole_span` in its
  comparison (concatenated span text must equal the target exactly when enabled).

## Risks / open questions

- [RESOLVED] `whole_span` + `use_regex` interaction: combined use switches the regex match
  to `fullmatch` (documented, no validation error). Decided 2026-09-08 in session.
- Cross-span matching under `whole_span` must compare the concatenated span text exactly —
  covered by a dedicated test.
- Regression risk: all existing tests must pass unchanged with the default off; mutation
  score must not drop.

## Acceptance criteria

- [ ] AC1: With `whole_span=True`, target `24` does NOT replace a span containing
      `24 hours`, but DOES replace a span whose text is exactly `24`.
- [ ] AC2: With `whole_span=False` (default), behaviour is byte-identical to the current
      one — the full existing test suite passes without modification.
- [ ] AC3: With `whole_span=True` + `use_regex=True`, patterns use `fullmatch`: pattern
      `24` does not match `24 hours`.
- [ ] AC4: All four surfaces (CLI flag, MCP tool parameter, API body field, Web UI
      checkbox) accept and propagate the option end-to-end.

## References

- Bitácora board: `mlorentedev/pdf-modifier-mcp#146`
- Related patterns: `00_meta/patterns/pattern-testing-standards.md` (TDD), `00_meta/patterns/pattern-spec-driven-development.md`
- Sister spec: `specs/PDF-001-preserve-metadata/` (same core + surfaces propagation shape)
