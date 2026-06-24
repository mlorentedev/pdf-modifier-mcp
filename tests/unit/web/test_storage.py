"""Tests for PDF storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdf_modifier_mcp.web.storage import PDFStorage, StorageError


def _make_pdf_bytes() -> bytes:
    """Create minimal valid PDF bytes."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\ntrailer\n<< /Size 1 >>\nstartxref\n0\n%%EOF\n"


class TestPDFStorage:
    """PDF storage tests."""

    def test_save_pdf_creates_file(self, tmp_path: Path) -> None:
        storage = PDFStorage(tmp_path / "storage")
        content = _make_pdf_bytes()
        result = storage.save_pdf("session1", content, "test.pdf")
        assert result.exists()
        assert result.read_bytes() == content

    def test_save_pdf_rejects_non_pdf(self, tmp_path: Path) -> None:
        storage = PDFStorage(tmp_path / "storage")
        with pytest.raises(StorageError, match="not a valid PDF"):
            storage.save_pdf("session1", b"not a pdf", "test.pdf")

    def test_sanitize_filename(self) -> None:
        name = PDFStorage._sanitize_filename("../../../etc/passwd")
        assert name == "passwd"
        assert "/" not in name

    def test_sanitize_filename_strips_null(self) -> None:
        name = PDFStorage._sanitize_filename("test\x00.pdf")
        assert "\x00" not in name

    def test_get_pdf_returns_path(self, tmp_path: Path) -> None:
        storage = PDFStorage(tmp_path / "storage")
        content = _make_pdf_bytes()
        storage.save_pdf("session1", content, "test.pdf")
        result = storage.get_pdf("session1")
        assert result.exists()

    def test_get_pdf_with_filename(self, tmp_path: Path) -> None:
        storage = PDFStorage(tmp_path / "storage")
        content = _make_pdf_bytes()
        storage.save_pdf("session1", content, "mydoc.pdf")
        result = storage.get_pdf("session1", "mydoc.pdf")
        assert result.name == "mydoc.pdf"

    def test_get_pdf_nonexistent_session(self, tmp_path: Path) -> None:
        storage = PDFStorage(tmp_path / "storage")
        with pytest.raises(StorageError, match="not found"):
            storage.get_pdf("nonexistent")

    def test_delete_session(self, tmp_path: Path) -> None:
        storage = PDFStorage(tmp_path / "storage")
        content = _make_pdf_bytes()
        storage.save_pdf("session1", content, "test.pdf")
        storage.delete_session("session1")
        assert not (tmp_path / "storage" / "session1").exists()

    def test_validate_pdf_header(self) -> None:
        assert PDFStorage._validate_pdf_header(b"%PDF-1.4...") is True
        assert PDFStorage._validate_pdf_header(b"%pdf-1.4...") is False
        assert PDFStorage._validate_pdf_header(b"not a pdf") is False
