"""AI endpoints — vision/OCR, signature detection, PDF comparison.

All vision endpoints are gated behind feature flags:
- FEATURE_VISION_ENABLED=true
- FEATURE_OCR_ENABLED=true
- FEATURE_SIGNATURE_DETECTION_ENABLED=true
- FEATURE_PDF_COMPARISON_ENABLED=true

Example:
    curl -X POST http://localhost:8000/api/ai/{session_id}/ocr
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...ai.exceptions import AIVisionError
from ...ai.models import OCRResult, PDFComparisonResult, SignatureDetectionResult
from ..config import FeatureFlags
from ..deps import get_feature_flags, get_session_pdf_path, get_vision_service

router = APIRouter(prefix="/api/ai", tags=["ai", "vision"])


# --- Request/Response Models ---


class OCRRequest(BaseModel):
    """Request body for OCR endpoint."""

    pages: list[int] | None = Field(
        default=None,
        description="Specific pages to OCR (0-indexed). None = all pages.",
    )
    dpi: int = Field(default=150, ge=72, le=300, description="Image resolution")


class SignatureDetectionRequest(BaseModel):
    """Request body for signature detection endpoint."""

    pages: list[int] | None = Field(default=None, description="Pages to analyze")
    dpi: int = Field(default=150, ge=72, le=300, description="Image resolution")


class PDFComparisonRequest(BaseModel):
    """Request body for PDF comparison endpoint."""

    session_id_b: str = Field(description="Session ID of the second PDF")
    pages: list[int] | None = Field(default=None, description="Pages to compare")
    dpi: int = Field(default=150, ge=72, le=300, description="Image resolution")


# --- Vision Endpoints ---


@router.post("/{session_id}/ocr")
async def ocr_endpoint(
    session_id: str,
    request: OCRRequest | None = None,
    flags: FeatureFlags = Depends(get_feature_flags),
    pdf_path: str | None = Depends(get_session_pdf_path),
) -> dict[str, Any]:
    """Extract text from scanned PDF using AI vision.

    Requires:
        - FEATURE_VISION_ENABLED=true
        - FEATURE_OCR_ENABLED=true
        - Valid session with uploaded PDF
    """
    # Feature flag check FIRST
    if not flags.ocr_available:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "OCR not available",
                "message": "Set FEATURE_VISION_ENABLED=true and FEATURE_OCR_ENABLED=true",
            },
        )

    # Then validate PDF path
    if pdf_path is None:
        raise HTTPException(status_code=404, detail={"error": "PDF not found for session"})

    try:
        vision_service = get_vision_service()
        pages = request.pages if request else None
        dpi = request.dpi if request else 150

        result: OCRResult = await vision_service.ocr(pdf_path, pages=pages, dpi=dpi)
        return result.model_dump()

    except AIVisionError as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"OCR failed: {e}"})


@router.post("/{session_id}/detect-signatures")
async def detect_signatures_endpoint(
    session_id: str,
    request: SignatureDetectionRequest | None = None,
    flags: FeatureFlags = Depends(get_feature_flags),
    pdf_path: str | None = Depends(get_session_pdf_path),
) -> dict[str, Any]:
    """Detect signatures in PDF using AI vision.

    Requires:
        - FEATURE_VISION_ENABLED=true
        - FEATURE_SIGNATURE_DETECTION_ENABLED=true
        - Valid session with uploaded PDF
    """
    # Feature flag check FIRST
    if not flags.signature_detection_available:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Signature detection not available",
                "message": (
                    "Set FEATURE_VISION_ENABLED=true and "
                    "FEATURE_SIGNATURE_DETECTION_ENABLED=true"
                ),
            },
        )

    # Then validate PDF path
    if pdf_path is None:
        raise HTTPException(status_code=404, detail={"error": "PDF not found for session"})

    try:
        vision_service = get_vision_service()
        pages = request.pages if request else None
        dpi = request.dpi if request else 150

        result: SignatureDetectionResult = await vision_service.detect_signatures(
            pdf_path, pages=pages, dpi=dpi
        )
        return result.model_dump()

    except AIVisionError as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"Signature detection failed: {e}"})


@router.post("/compare")
async def compare_pdfs_endpoint(
    request: PDFComparisonRequest,
    session_id_a: str = Query(..., description="Session ID of the first PDF"),
    flags: FeatureFlags = Depends(get_feature_flags),
) -> dict[str, Any]:
    """Compare two PDFs and find differences.

    Requires:
        - FEATURE_VISION_ENABLED=true
        - FEATURE_PDF_COMPARISON_ENABLED=true
        - Two valid sessions with uploaded PDFs
    """
    # Feature flag check FIRST
    if not flags.pdf_comparison_available:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "PDF comparison not available",
                "message": (
                    "Set FEATURE_VISION_ENABLED=true and " "FEATURE_PDF_COMPARISON_ENABLED=true"
                ),
            },
        )

    # Then validate both PDF paths
    pdf_path_a = get_session_pdf_path(session_id_a)
    pdf_path_b = get_session_pdf_path(request.session_id_b)

    if pdf_path_a is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PDF not found for session_a"},
        )
    if pdf_path_b is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PDF not found for session_b"},
        )

    try:
        vision_service = get_vision_service()
        pages = request.pages if request else None
        dpi = request.dpi if request else 150

        result: PDFComparisonResult = await vision_service.compare(
            pdf_path_a, pdf_path_b, pages=pages, dpi=dpi
        )
        return result.model_dump()

    except AIVisionError as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"PDF comparison failed: {e}"})
