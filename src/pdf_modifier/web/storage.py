"""PDF file storage on filesystem."""

from __future__ import annotations

from pathlib import Path

from ..core.exceptions import PDFModifierError
from ..logger import setup_logging


def _validate_session_id(session_id: str) -> str:
    """Validate session_id to prevent path traversal attacks."""
    # Reject absolute paths and path traversal
    if "/" in session_id or "\\" in session_id:
        raise StorageError(f"Invalid session_id: {session_id}")
    safe = Path(session_id).name
    if safe != session_id:
        raise StorageError(f"Invalid session_id: {session_id}")
    return safe


logger = setup_logging(__name__)

PDF_MAGIC = b"%PDF"


class StorageError(PDFModifierError):
    """Raised on storage operations failure."""

    code = "STORAGE_ERROR"


class PDFStorage:
    """Filesystem-based PDF storage with validation.

    Stores uploaded PDFs in a session-scoped directory.
    Validates PDF magic bytes on upload.

    Example:
        >>> storage = PDFStorage(Path("storage"))
        >>> path = storage.save_pdf("abc123", b"%PDF-1.4...", "document.pdf")
        >>> content = storage.get_pdf("abc123")
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_pdf(
        self,
        session_id: str,
        content: bytes,
        filename: str,
    ) -> Path:
        """Save a PDF file to storage.

        Args:
            session_id: Session identifier.
            content: Raw PDF bytes.
            filename: Original filename (sanitized).

        Returns:
            Path to the saved file.

        Raises:
            StorageError: If content is not a valid PDF.
        """
        if not self._validate_pdf_header(content):
            raise StorageError(
                "Uploaded file is not a valid PDF",
                {"filename": filename},
            )

        safe_name = self._sanitize_filename(filename)
        # Validate session_id to prevent path traversal
        session_id_safe = Path(session_id).name
        session_dir = self._base_dir / session_id_safe
        session_dir.mkdir(parents=True, exist_ok=True)
        output_path = session_dir / safe_name

        output_path.write_bytes(content)
        logger.info("Saved PDF: %s (%d bytes)", output_path, len(content))
        return output_path

    def get_pdf(self, session_id: str, filename: str | None = None) -> Path:
        """Get the path to a stored PDF.

        Args:
            session_id: Session identifier.
            filename: If provided, look for this specific file.
                     Otherwise returns the first PDF in the session dir.

        Returns:
            Path to the PDF file.

        Raises:
            StorageError: If file not found.
        """
        session_id_safe = Path(session_id).name
        session_dir = self._base_dir / session_id_safe
        if not session_dir.exists():
            raise StorageError(f"Session directory not found: {session_id}")

        if filename:
            path = session_dir / self._sanitize_filename(filename)
            if path.exists():
                return path
            raise StorageError(f"File not found in session: {filename}")

        # Return first PDF in session dir
        pdfs = list(session_dir.glob("*.pdf"))
        if pdfs:
            return pdfs[0]

        raise StorageError(f"No PDF found in session: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """Delete all files for a session."""
        session_id_safe = Path(session_id).name
        session_dir = self._base_dir / session_id_safe
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir, ignore_errors=True)
            logger.info("Deleted session directory: %s", session_id)

    @staticmethod
    def _validate_pdf_header(content: bytes) -> bool:
        """Check if content starts with PDF magic bytes."""
        return content[:4] == PDF_MAGIC

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a filename to prevent path traversal.

        Strips directory components and null bytes.
        """
        # Take only the basename
        name = Path(filename).name
        # Strip null bytes
        name = name.replace("\x00", "")
        # Limit length
        if len(name) > 255:
            name = name[:255]
        return name
