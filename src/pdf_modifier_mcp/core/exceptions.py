"""Custom exceptions for PDF Modifier operations."""

from __future__ import annotations

from typing import Any


class PDFModifierError(Exception):
    """Base exception with structured error info."""

    code: str = "PDF_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "success": False,
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class PDFNotFoundError(PDFModifierError):
    """PDF file does not exist or is not accessible."""

    code = "FILE_NOT_FOUND"


class PDFReadError(PDFModifierError):
    """Failed to read or parse PDF - may be corrupted or encrypted."""

    code = "READ_ERROR"


class PDFWriteError(PDFModifierError):
    """Failed to write output PDF."""

    code = "WRITE_ERROR"


class PDFPasswordError(PDFModifierError):
    """Raised when a PDF requires a password but none (or an incorrect one) was provided."""

    code = "PASSWORD_ERROR"


class InvalidPatternError(PDFModifierError):
    """Regex pattern is invalid."""

    code = "INVALID_PATTERN"
