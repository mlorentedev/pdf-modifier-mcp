# ADR-012: Audio Pipeline — TTS/STT with Chunking Strategy

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** ADR-002 (AI Layer), AUD-001

## Context

Audio capabilities require:
- TTS: Convert PDF text to speech (kokoro)
- STT: Transcribe audio embedded in PDFs or uploaded by user (whisper)
- Voice dictation: Speech → text → replacements

Key constraints from NaN Cloud:
- whisper: 25MB file limit, timeout >2 min, 10 RPM
- kokoro: 15 RPM, <1s latency
- No native audio processing in Python stdlib

## Decision

### Audio Format

- **Storage:** OGG/Opus (compressed, small files)
- **Whisper input:** OGG/Opus preferred (smaller than WAV)
- **Kokoro output:** WAV (raw), convert to OGG for storage

### Format Conversion

- **Tool:** ffmpeg via subprocess (not Python libraries)
- **Why:** ffmpeg is the standard, handles all formats, already available on VPS
- **Fallback:** If ffmpeg not installed, log warning and skip conversion

```python
import subprocess

def convert_to_ogg(input_bytes: bytes) -> bytes:
    """Convert audio to OGG/Opus via ffmpeg."""
    result = subprocess.run(
        ["ffmpeg", "-i", "pipe:0", "-c:a", "libopus", "-b:a", "48k", "pipe:1"],
        input=input_bytes,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AudioConversionError(f"ffmpeg failed: {result.stderr}")
    return result.stdout
```

### Whisper Chunking

- **Problem:** whisper timeout >2 min for long audio
- **Solution:** Split audio into chunks of ≤2 minutes

```python
MAX_CHUNK_DURATION = 120  # seconds

def split_audio(audio_bytes: bytes) -> list[bytes]:
    """Split audio into ≤2 min chunks using ffmpeg."""
    # Get duration via ffprobe
    duration = get_audio_duration(audio_bytes)
    if duration <= MAX_CHUNK_DURATION:
        return [audio_bytes]

    chunks = []
    for start in range(0, duration, MAX_CHUNK_DURATION):
        chunk = ffmpeg_extract(audio_bytes, start, MAX_CHUNK_DURATION)
        chunks.append(chunk)
    return chunks
```

### TTS Pipeline

```
PDF Text → Split by page/paragraph → kokoro TTS → WAV → OGG → Cache
```

- **Voice selection:** Configurable per request (default: `ef_dora` for Spanish)
- **Batch:** Process page by page, concatenate audio
- **Cache:** Store generated audio in session directory

### STT Pipeline

```
Audio upload → Validate size (<25MB) → Convert to OGG → Split if >2min → whisper → Text
```

- **Language:** Auto-detect (whisper feature)
- **Format:** Accept any format, convert to OGG before processing
- **Timeout:** 30s per chunk (whisper ~1x realtime)

### Voice Dictation Pipeline

```
Voice input → whisper STT → qwen3.6 parse → Replacement map
```

- **Step 1:** Transcribe with whisper
- **Step 2:** Send transcript to qwen3.6 with prompt: "Extract replacement pairs from this dictation"
- **Step 3:** Return structured `{"old": "new"}` map
- **Step 4:** User confirms before applying

### Token/Cost Estimation

```
TTS:
  - 1 page of text ≈ 300 words ≈ 400 tokens
  - kokoro: ~1s per page
  - 10 pages ≈ 10s, 10 RPM limit → 1 min for 10 pages

STT:
  - 1 min audio ≈ 1 chunk
  - whisper: ~1x realtime → 1 min processing per 1 min audio
  - 10 RPM limit → 10 concurrent transcriptions
```

## Consequences

- ffmpeg is a system dependency (must be installed on VPS)
- OGG/Opus format minimizes storage and transfer
- Chunking prevents whisper timeouts
- Caching avoids re-generating audio

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Python pydub/librosa | No ffmpeg dependency | Slower, more dependencies, less format support | **Rejected** |
| WAV only (no conversion) | Simpler | 10x larger files, slower upload/download | **Rejected** |
| Streaming TTS | Real-time playback | Complex, NaN Cloud may not support SSE for TTS | **Rejected** |
| No chunking | Simpler | Fails on audio >2 min | **Rejected** |
