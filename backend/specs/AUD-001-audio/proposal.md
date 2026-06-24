---
id: "AUD-001"
type: spec
status: active
created: "2026-06-19"
feature: Audio Capabilities (TTS/STT)
---

# AUD-001: Audio Capabilities (TTS/STT)

## What

Add text-to-speech (TTS) to read PDFs aloud, speech-to-text (STT) to transcribe audio embedded in PDFs, and voice dictation to edit PDFs by voice using NaN Cloud audio models.

## Why

- Accessibility: visually impaired users can listen to PDFs
- Some PDFs contain embedded audio notes
- Voice dictation enables hands-free editing
- Differentiates from all other PDF tools

## Scope

### In Scope
- TTS endpoint (kokoro, 67 voices)
- STT endpoint (whisper, 99+ languages)
- Voice dictation endpoint (whisper → qwen3.6)
- Frontend audio controls

### Out of Scope
- Real-time streaming TTS (batch only)
- Voice cloning
- Multi-speaker detection

## Acceptance Criteria

1. [ ] TTS produces audio from PDF text
2. [ ] STT transcribes embedded audio
3. [ ] Voice dictation converts speech to replacements
4. [ ] Spanish voices work (ef_dora, em_alex)
5. [ ] Audio files are downloadable

## Technical Notes

- kokoro: 82M, <1s latency, 15 RPM
- whisper: large-v3, ~1x realtime, 10 RPM, 25MB limit
- whisper timeout >2 min → split audio into chunks
- Use OGG/Opus format for efficiency
