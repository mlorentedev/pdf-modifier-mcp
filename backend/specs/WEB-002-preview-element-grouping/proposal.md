---
id: "WEB-002-preview-element-grouping"
type: spec
status: draft # draft | implementing | verifying | archived
created: "2026-08-06"
issue: "mlorentedev/pdf-modifier-mcp#118"   # repo#NNN — GitHub issue / Project item that tracks this spec
tags: [spec, proposal]
template_version: "1.0"
---

# WEB-002-preview-element-grouping

> **Naming**: file lives at `<repo>/specs/WEB-002-preview-element-grouping/proposal.md`. `WEB-002-preview-element-grouping` is `AREA-NNN-slug` (e.g. `TOOL-001-secret-drift`).

## Why

<!-- from issue #118: feat(web): improve PDF preview — intelligent element grouping + sync -->

The "Elements" sidebar (added in #93) lists every raw text span PyMuPDF extracts — "Hello" and "World" appear as two separate entries when the PDF shows "Hello World". With real documents this produces dozens of fragmented, near-duplicate entries that are useless for selecting replacement targets. Clicking an entry neither scrolls the preview to the text nor navigates to the right page, so the sidebar and the canvas feel disconnected; and the highlight rect covers the full pdf.js text item width instead of the exact text bounds, making selection look sloppy.

If we ship without this, the sidebar stays noise and the preview feature from #93 remains half-finished (issue #118 explicitly tracks it as remaining work).

## What

Concrete behavior change. What does the system do after this PR that it did not do before? Observable, not implementation-focused.

1. **Sidebar grouping** — the Elements sidebar merges consecutive text spans on the same baseline (same font, same size, small horizontal gap) into a single semantic entry ("Hello World" instead of "Hello" + "World").
2. **Click-to-locate** — clicking an element in the sidebar scrolls the preview canvas so the highlighted text is visible, navigating to the element's page if it is not the current one.
3. **Precise highlight bounds** — the highlight rect(s) cover only the matched text within a pdf.js item, not the item's full width.

**Architecture decision (review):** the fix is a **frontend post-processing step** (`frontend/src/lib/utils/`), NOT a backend analyzer change — the repo rule "core is sacred" forbids modifying `core/analyzer.py` (AGENTS.md Standing Order #1), and the grouping is presentation logic that belongs to the web layer. The `get_structure` API contract stays unchanged. [AGENT-SUGGESTION — accept or move to backend]

## Out of scope

- Backend / analyzer changes (core is sacred; the API contract `GET /api/pdf/{id}/structure` is unchanged)
- Keyboard shortcuts (#99), batch processing UI (#98), undo/redo for replacements (#94), session persistence (#96) — separate issues
- Changing what text the replacement engine matches (grouping is display-only)
- [AGENT-SUGGESTION — add anything else that should NOT sneak in]

## Risks / open questions

- **Gap heuristic is layout-sensitive** — merging by baseline + gap can join words from adjacent columns if the gap threshold is too generous. Mitigation: only merge when same `origin.y` (baseline), same font+size, and gap ≤ ~1.2× font size; tests must cover a two-column layout. [MUST resolve before code: threshold value]
- **Precise highlight width is approximate** — pdf.js text items don't expose per-character widths, so matching a substring inside an item requires estimating width proportionally to the full item width (breaks with ligatures/kerning). Mitigation: proportional estimate is accepted (cosmetic layer); verify visually against sample PDFs. [MUST resolve before code: accept proportional estimate?]
- **Scroll math depends on zoom** — canvas coordinates must be mapped to the scroll container's client coordinates at the current zoom factor; zoom changes must not break the scroll target.
- **Type mismatch found** — `frontend/src/lib/api/client.ts` declares `text_elements` but the backend serializes `elements`; `+page.svelte` already reads `p.elements`. Fix the TS interface in this PR (small, in-scope debt fix).

## Acceptance criteria

Observable outcomes. Each must be testable.

- [ ] AC1: Sidebar shows grouped entries — spans on the same line/font/size with small gaps render as one entry with concatenated text; a two-column page does not merge across columns.
- [ ] AC2: Clicking a sidebar entry scrolls the preview container so the highlighted text is in view; if the entry is on another page, the preview navigates to that page first.
- [ ] AC3: Highlight rects cover only the matched text bounds (not the full pdf.js item width) at any zoom level.
- [ ] AC4: Vitest unit tests cover grouping (single-line merge, cross-column split) and highlight precision; `npm run check` passes; existing backend tests unchanged (no backend diff).

## References

- Bitácora board: [mlorentedev/pdf-modifier-mcp#118](https://github.com/mlorentedev/pdf-modifier-mcp/issues/118) (the GitHub issue / Project item tracking this spec)
- Related ADR: `backend/docs/adr/adr-009-frontend.md`
- Related patterns: `pattern-mcp-tool-design` (display-only grouping, no contract change)
