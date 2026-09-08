---
id: lesson-015-pymupdf-preserves-metadata-on-save
type: lesson
status: active
created: "2026-09-07"
owner: manu
tags: [pdf-modifier-mcp, lesson, pymupdf, metadata, fidelity]
---

# PyMuPDF preserves PDF metadata on save; make it an explicit option

**Context:** Replacing text in a PDF via redaction + reinsert (the `core/modifier.py` path). A "faithful replica" should keep the document's identity metadata (`creationDate`, `modDate`, `producer`).
**Problem:** Assumed `doc.save()` would rewrite metadata. Verified empirically it does **not** — PyMuPDF preserves the Info dict on a plain `save()`. So the real gap was control, not loss.
**Solution:** Added a `preserve_metadata` option (default **true**) that explicitly captures and restores the original metadata before save — a deterministic safeguard rather than a fix. The opt-out (`preserve_metadata=False`) stamps a fresh `modDate` via `fitz.get_pdf_now()` to reflect the edit, leaving `creationDate` untouched. Exclude PyMuPDF-internal keys (`format`, `encryption`) when capturing.
**Tags:** `#pymupdf` `#metadata` `#pdf` `#fidelity` `#modifier`
