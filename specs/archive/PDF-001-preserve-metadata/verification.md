---
tags: [spec, verification, templates]
created: "2026-09-07"
---

# Verification - PDF-001-preserve-metadata

## Evidence

Every acceptance criterion mapped to concrete proof.

- [x] **AC1** -> `test_modifier_metadata.py::test_metadata_preserved_by_default` (+ `test_creation_and_mod_date_preserved`), commit `77e172f`. Also confirmed end-to-end via CLI on a real PDF: `creationDate`/`modDate`/`producer`/`title` byte-identical after replacement.
- [x] **AC2** -> `test_modifier_metadata.py::test_disable_allows_mod_date_change`. CLI `--no-preserve-metadata` on a real PDF updated `modDate` to `D:20260907192259-06'00'` while keeping `creationDate`.
- [x] **AC3** -> `tests/unit/interfaces/test_cli.py::TestModifyCommand` (flag parsed); MCP `modify_pdf_content`/`batch_modify_pdf_content` signatures updated; web `routes/pdf.py` reads `preserve_metadata`; UI checkbox in `+page.svelte` (bound `preserveMetadata`, default `true`) with `client.ts` sending `preserve_metadata`.
- [x] **AC4** -> preserve tests assert `creationDate`/`modDate`/`producer`/`title`/`creator` are non-empty and unchanged.

## Test status

- Backend: `pytest tests/unit/core tests/unit/interfaces` -> **236 passed, 17 skipped**.
- Frontend: `npm run check` -> 0 errors; `npm test` -> **50 passed**.
- Lint/type: `ruff check` clean, `mypy src tests` -> Success (66 files).
- Manual smoke test: regenerated a booking confirmation via the CLI (`--regex`). Default run kept metadata identical; `--no-preserve-metadata` stamped a fresh `modDate` and left `creationDate` intact. `price+tax=total` remained consistent.
- No regressions: yes — all pre-existing tests pass.

## Decisions made during implementation

- Metadata is captured on open excluding PyMuPDF-internal keys (`format`, `encryption`); only writable string fields are preserved.
- The opt-out (`preserve_metadata=False`) stamps only `modDate` via `fitz.get_pdf_now()` — `creationDate` is never touched.
- PyMuPDF already preserves metadata on a plain `save()`; this feature makes preservation explicit/deterministic and adds the opt-out, rather than fixing an observed loss.

## Promotion candidates

- [x] Lesson for the repo's `docs/lessons/`? **yes** — "PyMuPDF preserves PDF metadata on save; make it an explicit option with an opt-out that stamps `modDate`." (register as the next lesson NNN).
- [ ] ADR-worthy decision for the repo's `docs/adr/adr-XXX.md`? no — small additive option; the spec documents it.
- [ ] New pattern candidate for `00_meta/patterns/`? no — repo-specific.

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/PDF-001-preserve-metadata/` -> `specs/archive/PDF-001-preserve-metadata/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any) — register the lesson if kept
