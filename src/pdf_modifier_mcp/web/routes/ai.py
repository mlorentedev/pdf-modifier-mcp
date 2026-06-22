"""AI endpoints — stubs for future integration."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/{session_id}/detect")
async def detect_fields(session_id: str) -> dict[str, str]:
    """Detect document fields using AI.

    TODO: Implement with AI-001 client.
    """
    return {"status": "not_implemented", "message": "AI detection requires AI-001"}


@router.post("/{session_id}/classify")
async def classify_document(session_id: str) -> dict[str, str]:
    """Classify document type using AI.

    TODO: Implement with AI-001 client.
    """
    return {"status": "not_implemented", "message": "AI classification requires AI-001"}


@router.post("/{session_id}/redact")
async def redact_pii(session_id: str) -> dict[str, str]:
    """Detect PII for redaction using AI.

    TODO: Implement with AI-001 client.
    """
    return {"status": "not_implemented", "message": "AI redaction requires AI-001"}
