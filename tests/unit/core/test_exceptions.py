"""Tests for custom exceptions."""

import pytest

from pdf_modifier_mcp.core.exceptions import (
    FileSizeError,
    InvalidPatternError,
    PDFModifierError,
    PDFNotFoundError,
    PDFReadError,
    PDFWriteError,
    TextNotFoundError,
)


class TestExceptions:
    """Tests for custom exceptions."""

    def test_base_error_initialization(self) -> None:
        error = PDFModifierError("Test message", {"key": "value"})
        assert error.message == "Test message"
        assert error.details == {"key": "value"}

    def test_base_error_to_dict(self) -> None:
        error = PDFModifierError("Test error")
        result = error.to_dict()
        assert result["success"] is False
        assert result["error"] == "PDF_ERROR"
        assert result["message"] == "Test error"

    def test_error_codes(self) -> None:
        assert PDFNotFoundError("x").code == "FILE_NOT_FOUND"
        assert PDFReadError("x").code == "READ_ERROR"
        assert PDFWriteError("x").code == "WRITE_ERROR"
        assert InvalidPatternError("x").code == "INVALID_PATTERN"
        assert TextNotFoundError("x").code == "TEXT_NOT_FOUND"
        assert FileSizeError("x").code == "FILE_TOO_LARGE"

    def test_all_inherit_from_base(self) -> None:
        exceptions = [
            PDFNotFoundError,
            PDFReadError,
            PDFWriteError,
            InvalidPatternError,
            TextNotFoundError,
            FileSizeError,
        ]
        for exc_class in exceptions:
            assert isinstance(exc_class("Test"), PDFModifierError)

    def test_can_catch_with_base_class(self) -> None:
        with pytest.raises(PDFModifierError):
            raise PDFReadError("Test")
