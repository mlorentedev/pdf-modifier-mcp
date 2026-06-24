---
id: "WEB-001"
type: spec
status: active
created: "2026-06-19"
feature: Web UI for PDF editing
---

# WEB-001: Web UI for PDF Editing

## What

Add a web interface to PDF Modifier MCP that allows non-technical users to upload PDFs via drag-and-drop, view the detected structure, edit text replacements via a form, preview changes live, and download the modified PDF.

## Why

- The CLI and MCP interfaces require technical knowledge
- A web UI makes the tool accessible to anyone
- Visual structure editing is more intuitive than CLI replacement strings
- This is the foundation for all AI-powered features (Phases 2-5)

## Scope

### In Scope
- FastAPI backend with REST endpoints
- SvelteKit frontend with drag-and-drop upload
- PDF structure visualization
- Form-based text replacement
- Live PDF preview with PDF.js
- Download modified PDF
- Session management with TTL
- Docker deployment

### Out of Scope (deferred)
- AI-powered features (see AI-001)
- Mobile responsive design (desktop-first)
- User authentication (single-user for now)
- Multi-language UI (English first)

## Acceptance Criteria

1. [ ] User can drag-and-drop a PDF onto the upload area
2. [ ] PDF is uploaded and session is created
3. [ ] Structure is displayed (text elements with positions)
4. [ ] User can create replacement pairs via form
5. [ ] PDF preview shows the document
6. [ ] Download button provides the modified PDF
7. [ ] Session expires after configurable TTL
8. [ ] All existing CLI and MCP tests still pass
9. [ ] Backend has >80% test coverage
10. [ ] Frontend builds without errors

## Technical Notes

- ADR-001: FastAPI + SvelteKit
- ADR-003: Filesystem storage with TTL
- ADR-004: In-memory session management
- ADR-005: Async strategy with anyio.to_thread
- ADR-006: Docker deployment on VPS
- ADR-007: Security (upload validation, CORS, headers)
