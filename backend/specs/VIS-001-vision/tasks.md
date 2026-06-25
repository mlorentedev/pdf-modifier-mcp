---
id: "VIS-001-tasks"
type: spec-tasks
status: active
created: "2026-06-19"
---

# VIS-001: Tasks — Vision and OCR

## TDD Workflow

For each task: RED (write failing test) → GREEN (implement) → REFACTOR (clean up).

---

## Phase 1: Image Conversion

### T1.1: PDF to Image Converter
- [x] **RED:** Write `test_convert_page_to_png_returns_bytes`
- [x] **RED:** Write `test_convert_page_respects_dpi`
- [x] **GREEN:** Create `src/pdf_modifier/ai/vision.py`
- [x] **GREEN:** Implement `pdf_page_to_image(page_num, dpi=150) → bytes`
- [x] **GREEN:** Use fitz `page.get_pixmap()` for rendering
- [x] **REFACTOR:** Add quality options (DPI, format)

### T1.2: Base64 Encoding
- [x] **RED:** Write `test_encode_image_base64_returns_data_uri`
- [x] **GREEN:** Implement `encode_image_base64(image_bytes) → str`
- [x] **GREEN:** Return data URI format for API input
- [x] **REFACTOR:** Handle different image formats

---

## Phase 2: Vision Endpoints

### T2.1: OCR Endpoint
- [x] **RED:** Write `test_ocr_scanned_pdf_returns_text`
- [x] **RED:** Write `test_ocr_with_text_layer_returns_error`
- [x] **GREEN:** Implement `POST /api/ai/{session_id}/ocr`
- [x] **GREEN:** Convert PDF pages to images
- [x] **GREEN:** Send images to mimo-v2.5 for OCR
- [x] **GREEN:** Return extracted text per page
- [x] **REFACTOR:** Handle multi-page PDFs in batches

### T2.2: Signature Detection Endpoint
- [x] **RED:** Write `test_detect_signatures_returns_positions`
- [x] **GREEN:** Implement `POST /api/ai/{session_id}/detect-signatures`
- [x] **GREEN:** Send PDF images to mimo-v2.5
- [x] **GREEN:** Return signature positions and confidence
- [x] **REFACTOR:** Add bounding box coordinates

### T2.3: PDF Comparison Endpoint
- [x] **RED:** Write `test_compare_pdfs_returns_differences`
- [x] **GREEN:** Implement `POST /api/ai/compare`
- [x] **GREEN:** Accept two session IDs
- [x] **GREEN:** Send both PDFs to mimo-v2.5
- [x] **GREEN:** Return list of differences
- [x] **REFACTOR:** Support side-by-side view

---

## Phase 3: Frontend Integration

### T3.1: Vision Panel
- [ ] Add "OCR" button for scanned PDFs
- [ ] Add "Detect Signatures" button
- [ ] Show OCR results in text viewer
- [ ] Highlight signature positions on PDF preview

---

## Dependencies

| Task | Depends on |
|---|---|
| T1.1-T1.2 | AI-001 (client infrastructure) |
| T2.1-T2.3 | T1.1-T1.2 |
| T3.1 | T2.1-T2.2 |

## Estimated Effort

| Phase | Tasks | Estimated LOC | Days |
|---|---|---|---|
| Phase 1: Image Conversion | T1.1-T1.2 | ~100 | 1 |
| Phase 2: Vision Endpoints | T2.1-T2.3 | ~300 | 2.5 |
| Phase 3: Frontend | T3.1 | ~100 | 1 |
| **Total** | **6 tasks** | **~500** | **~4.5** |
