---
id: "WEB-001-tasks"
type: spec-tasks
status: active
created: "2026-06-19"
---

# WEB-001: Tasks — Web UI

## TDD Workflow

For each task: RED (write failing test) → GREEN (implement) → REFACTOR (clean up).

---

## Phase 1: Backend Infrastructure

### T1.1: FastAPI App Setup
- [ ] **RED:** Write `test_health_endpoint_returns_200`
- [ ] **GREEN:** Create `src/pdf_modifier/web/app.py` with FastAPI app factory
- [ ] **GREEN:** Create `src/pdf_modifier/web/routes/health.py`
- [ ] **GREEN:** Add health endpoint returning `{"status": "ok"}`
- [ ] **REFACTOR:** Extract config to `src/pdf_modifier/web/config.py`

### T1.2: Configuration Management
- [ ] **RED:** Write `test_config_loads_from_env`
- [ ] **GREEN:** Create `src/pdf_modifier/web/config.py` with Pydantic Settings
- [ ] **GREEN:** Load `NAN_API_KEY`, `STORAGE_DIR`, `LOG_LEVEL`, `CORS_ORIGINS` from env
- [ ] **REFACTOR:** Add `.env.example` with all variables

### T1.3: Storage Service
- [ ] **RED:** Write `test_save_pdf_creates_file`
- [ ] **RED:** Write `test_save_pdf_rejects_oversized_file`
- [ ] **RED:** Write `test_sanitize_filename_strips_path_traversal`
- [ ] **GREEN:** Create `src/pdf_modifier/web/storage.py`
- [ ] **GREEN:** Implement `save_pdf(session_id, content, filename) → Path`
- [ ] **GREEN:** Implement `get_pdf(session_id) → Path`
- [ ] **GREEN:** Implement `delete_session(session_id)`
- [ ] **GREEN:** Implement `sanitize_filename(filename) → str`
- [ ] **GREEN:** Implement `validate_pdf_header(content) → bool`
- [ ] **REFACTOR:** Add `MAX_FILE_SIZE` validation from config

### T1.4: Session Manager
- [ ] **RED:** Write `test_create_session_returns_id`
- [ ] **RED:** Write `test_get_session_returns_data`
- [ ] **RED:** Write `test_get_expired_session_returns_none`
- [ ] **RED:** Write `test_cleanup_removes_expired_sessions`
- [ ] **GREEN:** Create `src/pdf_modifier/web/session.py`
- [ ] **GREEN:** Implement `SessionManager` class with `create()`, `get()`, `delete()`
- [ ] **GREEN:** Implement TTL-based expiration
- [ ] **GREEN:** Implement background cleanup task
- [ ] **REFACTOR:** Add `threading.Lock` for write operations

---

## Phase 2: PDF Endpoints

### T2.1: Upload Endpoint
- [ ] **RED:** Write `test_upload_pdf_returns_session_id`
- [ ] **RED:** Write `test_upload_non_pdf_returns_400`
- [ ] **RED:** Write `test_upload_oversized_returns_413`
- [ ] **GREEN:** Create `src/pdf_modifier/web/routes/pdf.py`
- [ ] **GREEN:** Implement `POST /api/pdf/upload` with file handling
- [ ] **GREEN:** Validate PDF magic bytes
- [ ] **GREEN:** Sanitize filename
- [ ] **GREEN:** Create session and store file
- [ ] **REFACTOR:** Add `python-multipart` dependency

### T2.2: Structure Endpoint
- [ ] **RED:** Write `test_get_structure_returns_pdf_data`
- [ ] **RED:** Write `test_get_structure_caches_result`
- [ ] **GREEN:** Implement `GET /api/pdf/{session_id}/structure`
- [ ] **GREEN:** Use `PDFAnalyzer.get_structure()` from core
- [ ] **GREEN:** Cache result in session
- [ ] **REFACTOR:** Wrap core call in `anyio.to_thread.run_sync`

### T2.3: Replace Endpoint
- [ ] **RED:** Write `test_replace_returns_modification_result`
- [ ] **RED:** Write `test_replace_updates_session`
- [ ] **GREEN:** Implement `POST /api/pdf/{session_id}/replace`
- [ ] **GREEN:** Accept `ReplacementSpec` from body
- [ ] **GREEN:** Use `PDFModifier.process()` from core
- [ ] **GREEN:** Store modified PDF path in session
- [ ] **REFACTOR:** Add `threading.Lock` for file write

### T2.4: Download Endpoint
- [ ] **RED:** Write `test_download_returns_pdf_file`
- [ ] **RED:** Write `test_download_no_modification_returns_original`
- [ ] **GREEN:** Implement `GET /api/pdf/{session_id}/download`
- [ ] **GREEN:** Return modified PDF if exists, original otherwise
- [ ] **GREEN:** Set correct Content-Type and Content-Disposition headers
- [ ] **REFACTOR:** Use `FileResponse` from FastAPI

### T2.5: Delete Endpoint
- [ ] **RED:** Write `test_delete_removes_session_and_files`
- [ ] **GREEN:** Implement `DELETE /api/pdf/{session_id}`
- [ ] **GREEN:** Remove session from manager
- [ ] **GREEN:** Delete files from storage
- [ ] **REFACTOR:** Add cleanup of orphaned files

---

## Phase 3: Frontend

### T3.1: SvelteKit Setup
- [ ] Initialize SvelteKit project in `apps/web/`
- [ ] Configure TypeScript strict mode
- [ ] Add Tailwind CSS
- [ ] Configure Vite proxy to backend API
- [ ] Add `pdfjs-dist` dependency

### T3.2: PDFDropzone Component
- [ ] Implement drag-and-drop zone with visual feedback
- [ ] Implement file picker fallback
- [ ] Validate file type (PDF only) client-side
- [ ] Show upload progress
- [ ] Call `POST /api/pdf/upload` on drop
- [ ] Redirect to editor page on success

### T3.3: API Client
- [ ] Create `src/lib/api/client.ts`
- [ ] Implement `upload()`, `structure()`, `replace()`, `download()`
- [ ] Implement `aiDetect()`, `aiClassify()`, `aiRedact()` (stubs for Phase 2)
- [ ] Add error handling and loading states

### T3.4: State Management
- [ ] Create `src/lib/stores/session.ts`
- [ ] Create `src/lib/stores/pdf.ts`
- [ ] Implement reactive state updates
- [ ] Add error and loading states

### T3.5: Editor Layout
- [ ] Create editor page at `/edit/[sessionId]`
- [ ] Implement 3-panel layout (structure | preview | form)
- [ ] Add responsive breakpoints (1024px, 1440px, 1920px)

### T3.6: StructureViewer Component
- [ ] Display text elements as cards with position, font, size
- [ ] Highlight selected element
- [ ] Sync selection with PDF preview

### T3.7: PDFPreview Component
- [ ] Render PDF using pdfjs-dist
- [ ] Implement zoom controls
- [ ] Implement page navigation
- [ ] Overlay replacement highlights (optional)

### T3.8: ReplacementForm Component
- [ ] Dynamic form for adding replacement pairs
- [ ] "Old text" → "New text" fields
- [ ] Add/remove replacement rows
- [ ] Debounced API call on change
- [ ] Show replacement count

### T3.9: DownloadButton Component
- [ ] Call `GET /api/pdf/{id}/download`
- [ ] Trigger browser download with correct filename
- [ ] Show loading state during download

### T3.10: Integration
- [ ] Connect all components
- [ ] Test full flow: upload → view → replace → download
- [ ] Handle edge cases (empty PDF, no text elements, large files)

---

## Phase 4: Infrastructure

### T4.1: Docker Backend
- [ ] Create multi-stage `Dockerfile` for FastAPI
- [ ] Create `docker-compose.base.yml`
- [ ] Create `docker-compose.dev.yml` (hot-reload)
- [ ] Create `docker-compose.prod.yml`
- [ ] Test build and run

### T4.2: Docker Frontend
- [ ] Create multi-stage `Dockerfile` for SvelteKit
- [ ] Create nginx config for SPA
- [ ] Test build and serve

### T4.3: CI/CD
- [ ] Add `test.yml` workflow (pytest + coverage)
- [ ] Add `mutation.yml` workflow (mutmut)
- [ ] Add `security.yml` workflow (gitleaks, pip-audit)
- [ ] Add `build.yml` workflow (Docker build)

### T4.4: Documentation
- [ ] Update `README.md` with web UI instructions
- [ ] Add API documentation (auto-generated from FastAPI)
- [ ] Add deployment guide in `docs/runbooks/`

---

## Dependencies

| Task | Depends on |
|---|---|
| T1.1-T1.4 | — (foundation) |
| T2.1-T2.5 | T1.1-T1.4 |
| T3.1-T3.10 | T2.1-T2.5 (API ready) |
| T4.1-T4.4 | T2.1-T2.5, T3.1-T3.10 |

## Estimated Effort

| Phase | Tasks | Estimated LOC | Days |
|---|---|---|---|
| Phase 1: Backend Infra | T1.1-T1.4 | ~350 | 3 |
| Phase 2: PDF Endpoints | T2.1-T2.5 | ~250 | 2 |
| Phase 3: Frontend | T3.1-T3.10 | ~800 | 5 |
| Phase 4: Infrastructure | T4.1-T4.4 | ~200 | 2 |
| **Total** | **24 tasks** | **~1600** | **~12** |
