---
id: "AI-001-tasks"
type: spec-tasks
status: active
created: "2026-06-19"
---

# AI-001: Tasks — AI Detection

## TDD Workflow

For each task: RED (write failing test) → GREEN (implement) → REFACTOR (clean up).

---

## Phase 1: AI Client Infrastructure

### T1.1: NaN Cloud Client
- [ ] **RED:** Write `test_client_sends_enable_thinking_false`
- [ ] **RED:** Write `test_client_adds_auth_header`
- [ ] **RED:** Write `test_client_handles_429_with_retry`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/client.py`
- [ ] **GREEN:** Implement `NaNClient` class with httpx async
- [ ] **GREEN:** Add `enable_thinking: false` to every request
- [ ] **GREEN:** Add retry with backoff on 429/5xx
- [ ] **REFACTOR:** Extract config to constructor

### T1.2: Model Router
- [ ] **RED:** Write `test_router_returns_mimo_for_vision`
- [ ] **RED:** Write `test_router_returns_qwen_for_translation`
- [ ] **RED:** Write `test_router_override_takes_precedence`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/router.py`
- [ ] **GREEN:** Implement `TaskType` enum
- [ ] **GREEN:** Implement `ModelRouter.get_model(task_type) → str`
- [ ] **GREEN:** Add config override via env var
- [ ] **REFACTOR:** Document model mapping in docstring

### T1.3: Throttle
- [ ] **RED:** Write `test_throttle_limits_concurrency`
- [ ] **RED:** Write `test_throttle_raises_on_limit`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/throttle.py`
- [ ] **GREEN:** Implement `Throttle` class with asyncio.Semaphore
- [ ] **GREEN:** Default concurrency: 3 (env-overridable)
- [ ] **REFACTOR:** Add metrics/logging for throttle events

### T1.4: Prompt Templates
- [ ] **RED:** Write `test_render_detect_prompt_with_pdf_text`
- [ ] **RED:** Write `test_render_classify_prompt_with_pdf_text`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/prompts/`
- [ ] **GREEN:** Create `detect_fields.j2` template
- [ ] **GREEN:** Create `classify_doc.j2` template
- [ ] **GREEN:** Create `redact_pii.j2` template
- [ ] **GREEN:** Implement `render_prompt(template_name, **kwargs) → str`
- [ ] **REFACTOR:** Add schema for expected JSON output

### T1.5: AI Models
- [ ] **RED:** Write `test_detect_result_schema_validates`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/models.py`
- [ ] **GREEN:** Implement `DetectResult`, `ClassifyResult`, `RedactResult` Pydantic models
- [ ] **REFACTOR:** Add field descriptions and validators

---

## Phase 2: AI Endpoints

### T2.1: Detect Fields Endpoint
- [ ] **RED:** Write `test_detect_returns_field_list`
- [ ] **RED:** Write `test_detect_uses_mimo_model`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/detect`
- [ ] **GREEN:** Extract PDF text via `PDFAnalyzer`
- [ ] **GREEN:** Call AI with detect prompt
- [ ] **GREEN:** Parse response into `DetectResult`
- [ ] **REFACTOR:** Add caching in session

### T2.2: Classify Document Endpoint
- [ ] **RED:** Write `test_classify_returns_document_type`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/classify`
- [ ] **GREEN:** Call AI with classify prompt
- [ ] **GREEN:** Return document type (invoice, contract, CV, etc.)
- [ ] **REFACTOR:** Use qwen3.6 (fast, cheap)

### T2.3: Redact PII Endpoint
- [ ] **RED:** Write `test_redact_finds_nif`
- [ ] **RED:** Write `test_redact_finds_email`
- [ ] **RED:** Write `test_redact_finds_phone`
- [ ] **RED:** Write `test_redact_finds_credit_card`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/redact`
- [ ] **GREEN:** Call AI with redact prompt
- [ ] **GREEN:** Return list of PII items with positions
- [ ] **GREEN:** Auto-generate replacements
- [ ] **REFACTOR:** Add confidence scores

---

## Phase 3: Frontend AI Panel

### T3.1: AIPanel Component
- [ ] Create `src/lib/components/AIPanel.svelte`
- [ ] Add "Detect Fields" button
- [ ] Add "Classify Document" button
- [ ] Add "Redact PII" button
- [ ] Show loading states during AI calls
- [ ] Display results in structured format

### T3.2: Integration
- [ ] Connect AI results to ReplacementForm
- [ ] Auto-populate replacements from detection
- [ ] Show AI suggestions with accept/reject

---

## Dependencies

| Task | Depends on |
|---|---|
| T1.1-T1.5 | — (foundation) |
| T2.1-T2.3 | T1.1-T1.5, WEB-001 (API ready) |
| T3.1-T3.2 | T2.1-T2.3, WEB-001 (frontend ready) |

## Estimated Effort

| Phase | Tasks | Estimated LOC | Days |
|---|---|---|---|
| Phase 1: AI Infrastructure | T1.1-T1.5 | ~400 | 3 |
| Phase 2: AI Endpoints | T2.1-T2.3 | ~250 | 2 |
| Phase 3: Frontend AI | T3.1-T3.2 | ~150 | 1.5 |
| **Total** | **10 tasks** | **~800** | **~6.5** |
