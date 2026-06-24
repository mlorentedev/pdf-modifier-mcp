"""PDF management endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...core.analyzer import PDFAnalyzer
from ...core.exceptions import PDFModifierError
from ...core.models import ReplacementSpec
from ...core.modifier import PDFModifier
from ...logger import setup_logging
from ..deps import get_session_manager, get_storage
from ..session import SessionManager
from ..storage import PDFStorage

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    storage: PDFStorage = Depends(get_storage),
    session_mgr: SessionManager = Depends(get_session_manager),
) -> dict[str, str]:
    """Upload a PDF file and create a session."""
    from ..config import WebSettings

    max_size = WebSettings().max_file_size

    # Stream with size limit to avoid loading entire file into memory
    content_chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size:
            break
        content_chunks.append(chunk)

    if total_size > max_size:
        size_mb = total_size / (1024 * 1024)
        limit_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size {size_mb:.1f} MB exceeds limit of {limit_mb:.0f} MB",
        )

    content = b"".join(content_chunks)

    # Validate PDF magic bytes
    if not content[:4] == b"%PDF":
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF")

    session_id = session_mgr.create(Path("temp"))

    # Save directly to session directory
    session_dir = storage._base_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    safe_name = storage._sanitize_filename(file.filename or "upload.pdf")
    output_path = session_dir / safe_name
    output_path.write_bytes(content)

    return {"session_id": session_id}


@router.get("/{session_id}/structure")
async def get_structure(
    session_id: str,
    storage: PDFStorage = Depends(get_storage),
    session_mgr: SessionManager = Depends(get_session_manager),
) -> dict[str, Any]:
    """Get the structural analysis of a PDF.

    Args:
        session_id: Session identifier.
        storage: PDF storage dependency.
        session_mgr: Session manager dependency.

    Returns:
        PDF structure as JSON.

    Raises:
        HTTPException 404: If session not found.
    """
    session = session_mgr.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    pdf_path = storage.get_pdf(session_id)

    try:
        analyzer = PDFAnalyzer(str(pdf_path))
        result = await anyio.to_thread.run_sync(analyzer.get_structure)
        session_mgr.update_structure(session_id, result.model_dump())
        return result.model_dump()
    except PDFModifierError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/{session_id}/replace")
async def replace_text(
    session_id: str,
    body: dict[str, Any],
    storage: PDFStorage = Depends(get_storage),
    session_mgr: SessionManager = Depends(get_session_manager),
) -> dict[str, Any]:
    """Apply text replacements to a PDF.

    Args:
        session_id: Session identifier.
        body: Request body with 'replacements' dict and optional fields.
        storage: PDF storage dependency.
        session_mgr: Session manager dependency.

    Returns:
        Modification result.

    Raises:
        HTTPException 404: If session not found.
    """
    session = session_mgr.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    pdf_path = storage.get_pdf(session_id)
    output_path = pdf_path.parent / f"modified_{pdf_path.name}"

    try:
        replacements = body.get("replacements", {})
        use_regex = body.get("use_regex", False)
        pages = body.get("pages")
        spec = ReplacementSpec(replacements=replacements, use_regex=use_regex)
        modifier = PDFModifier(str(pdf_path), str(output_path))

        page_range: tuple[int, int] | None = None
        if pages:
            parts = pages.split("-")
            if len(parts) == 1:
                try:
                    page_range = (int(parts[0]), int(parts[0]))
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid page format: {parts[0]}")
            elif len(parts) == 2:
                try:
                    page_range = (int(parts[0]), int(parts[1]))
                except ValueError:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid page format in range: {parts}"
                    )

        result = await anyio.to_thread.run_sync(modifier.process, spec, page_range)
        session_mgr.set_modified_path(session_id, output_path)
        return result.model_dump()
    except PDFModifierError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error during PDF modification")
        raise HTTPException(status_code=500, detail="Modification failed")


@router.get("/{session_id}/download")
async def download_pdf(
    session_id: str,
    storage: PDFStorage = Depends(get_storage),
    session_mgr: SessionManager = Depends(get_session_manager),
) -> FileResponse:
    """Download the (modified or original) PDF.

    Returns the modified PDF if it exists, otherwise the original.

    Raises:
        HTTPException 404: If session not found.
    """
    session = session_mgr.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Return modified if exists
    if session.modified_path and session.modified_path.exists():
        return FileResponse(
            str(session.modified_path),
            media_type="application/pdf",
            filename=session.modified_path.name,
        )

    # Return original
    pdf_path = storage.get_pdf(session_id)
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    storage: PDFStorage = Depends(get_storage),
    session_mgr: SessionManager = Depends(get_session_manager),
) -> dict[str, str]:
    """Delete a session and all its files.

    Raises:
        HTTPException 404: If session not found.
    """
    exists = session_mgr.delete(session_id)
    if not exists:
        raise HTTPException(status_code=404, detail="Session not found")

    storage.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}
