---
id: "PDF-001-preserve-metadata"
type: spec
status: archived # draft | implementing | verifying | archived
created: "2026-09-07"
issue: "#137"   # repo#NNN — GitHub issue / Project item that tracks this spec
tags: [spec, proposal, retroactive]
template_version: "1.0"
---

# PDF-001-preserve-metadata

> **Naming**: file lives at `<repo>/specs/archive/PDF-001-preserve-metadata/proposal.md`. `PDF-001-preserve-metadata` is `AREA-NNN-slug`.
>
> **Retroactive archive (2026-09-22)**: the feature was implemented and merged via #138 before these spec artifacts landed on master — they lived only on the discarded `feat/preserve-pdf-metadata` branch and are rescued here for the audit trail. Verification evidence in `verification.md` was produced on-branch pre-merge (2026-09-07). No independent adversarial review was run for this spec; the issue #137 closed with the merge.

## Why

A faithful PDF reproduction must not silently rewrite the document's identity metadata. When the replacement engine redacts and re-inserts text and then saves, PyMuPDF may rewrite the Info dictionary (`creationDate`, `modDate`, `producer`), which breaks fidelity for PDFs that must appear untouched after a text edit (e.g. a confirmation re-shipped as-is). This spec makes metadata preservation an explicit, deterministic default so a "faithful replica" keeps its identity, while still letting callers opt into stamping a fresh `modDate` to reflect the edit.

## What

Add a `preserve_metadata` option (default **true**) to the replacement engine, surfaced through every interface:

- **CLI** — `--preserve-metadata/--no-preserve-metadata` flag on `modify` and `batch`.
- **MCP** — `preserve_metadata` parameter on `modify_pdf_content` and `batch_modify_pdf_content`.
- **Web API** — `preserve_metadata` field on the `POST /api/pdf/{id}/replace` body.
- **Web UI** — a "Preserve original PDF metadata" checkbox, **checked by default**.

When `preserve_metadata` is false, only `modDate` is stamped with the current time to reflect the edit; the rest (including `creationDate`) is left unchanged.

## Out of scope

- Embedding/re-using the original fonts (tracked separately).
- Any change to encryption/password handling.
- Per-file override within a single batch (exposed as one global flag).
- Renaming the project/package.

## Risks / open questions

- PyMuPDF already preserves metadata on a plain `save()` (verified empirically), so this is a deterministic safeguard rather than a fix for an observed loss. The opt-out path is what makes the flag meaningful.
- `set_metadata` must not be given PyMuPDF-internal keys (`format`, `encryption`) — they are excluded when capturing/restoring.

## Acceptance criteria

- [x] **AC1** By default, replacing text preserves the original `creationDate`, `modDate`, and `producer` exactly.
- [x] **AC2** With `preserve_metadata=False`, `modDate` is updated to the current time while `creationDate` is preserved.
- [x] **AC3** The flag is surfaced in the CLI, MCP tools, web replace API, and Web UI (checkbox default on).
- [x] **AC4** None of the standard metadata fields are dropped or emptied after a save.

> All four verified — see `verification.md` Evidence (AC3's web API / Web UI wiring is inspection-verified; no executable test existed at merge time).

## References

- Bitácora board: GitHub issue #137 (`issue:` frontmatter field).
- Related ADR: none (small additive option).
- Related patterns: `00_meta/patterns/pattern-spec-driven-development.md`.
