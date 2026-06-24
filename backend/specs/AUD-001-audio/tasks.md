---
id: "AUD-001-tasks"
type: spec-tasks
status: active
created: "2026-06-19"
---

# AUD-001: Tasks — Audio Capabilities

## TDD Workflow

For each task: RED (write failing test) → GREEN (implement) → REFACTOR (clean up).

---

## Phase 1: Audio Client

### T1.1: TTS Client
- [ ] **RED:** Write `test_tts_returns_audio_bytes`
- [ ] **RED:** Write `test_tts_uses_kokoro_model`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/audio.py`
- [ ] **GREEN:** Implement `text_to_speech(text, voice) → bytes`
- [ ] **GREEN:** Use kokoro model
- [ ] **GREEN:** Support Spanish voices (ef_dora, em_alex)
- [ ] **REFACTOR:** Add voice selection options

### T1.2: STT Client
- [ ] **RED:** Write `test_stt_returns_transcription`
- [ ] **RED:** Write `test_stt_handles_large_audio`
- [ ] **GREEN:** Implement `speech_to_text(audio_bytes) → str`
- [ ] **GREEN:** Use whisper model
- [ ] **GREEN:** Split audio >2 min into chunks
- [ ] **REFACTOR:** Add language detection

### T1.3: Audio Utilities
- [ ] **RED:** Write `test_convert_audio_format`
- [ ] **RED:** Write `test_split_audio_chunks`
- [ ] **GREEN:** Implement `convert_to_ogg(audio_bytes) → bytes`
- [ ] **GREEN:** Implement `split_audio(audio_bytes, max_duration=120) → list[bytes]`
- [ ] **REFACTOR:** Use ffmpeg subprocess

---

## Phase 2: Audio Endpoints

### T2.1: TTS Endpoint
- [ ] **RED:** Write `test_tts_endpoint_returns_audio`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/tts`
- [ ] **GREEN:** Accept page range and voice parameters
- [ ] **GREEN:** Extract text from PDF
- [ ] **GREEN:** Generate audio
- [ ] **GREEN:** Return audio file
- [ ] **REFACTOR:** Cache generated audio

### T2.2: STT Endpoint
- [ ] **RED:** Write `test_stt_endpoint_returns_text`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/stt`
- [ ] **GREEN:** Accept audio file upload
- [ ] **GREEN:** Transcribe audio
- [ ] **GREEN:** Return transcribed text
- [ ] **REFACTOR:** Handle multiple audio formats

### T2.3: Voice Dictation Endpoint
- [ ] **RED:** Write `test_dictation_returns_replacements`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/dictate`
- [ ] **GREEN:** Accept voice input
- [ ] **GREEN:** Transcribe with whisper
- [ ] **GREEN:** Parse with qwen3.6 for replacements
- [ ] **GREEN:** Return replacement map
- [ ] **REFACTOR:** Add confirmation step

---

## Phase 3: Frontend Integration

### T3.1: Audio Controls
- [ ] Add "Read Aloud" button with voice selector
- [ ] Add "Transcribe" button for embedded audio
- [ ] Add "Voice Dictate" button
- [ ] Audio player component for playback
- [ ] Download button for generated audio

---

## Dependencies

| Task | Depends on |
|---|---|
| T1.1-T1.3 | AI-001 (client infrastructure) |
| T2.1-T2.3 | T1.1-T1.3 |
| T3.1 | T2.1-T2.3 |

## Estimated Effort

| Phase | Tasks | Estimated LOC | Days |
|---|---|---|---|
| Phase 1: Audio Client | T1.1-T1.3 | ~200 | 2 |
| Phase 2: Audio Endpoints | T2.1-T2.3 | ~250 | 2 |
| Phase 3: Frontend | T3.1 | ~100 | 1 |
| **Total** | **7 tasks** | **~550** | **~5** |
