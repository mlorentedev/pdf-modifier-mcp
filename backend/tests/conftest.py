"""Shared pytest fixtures and constants for all tests."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

# Paths
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
SAMPLE_PDF = TEST_DATA_DIR / "sample.pdf"
EXAMPLES_OUTPUT_DIR = TEST_DIR / "examples_output"


@pytest.fixture(scope="session", autouse=True)
def setup_examples_dir() -> None:
    """Ensure examples output directory exists."""
    EXAMPLES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def output_pdf(tmp_path: Path) -> Path:
    """Default output path using pytest tmp_path."""
    return tmp_path / "output.pdf"


def create_pdf(path: Path, text: str = "Hello World", fontsize: float = 12) -> Path:
    """Create a simple single-page PDF with text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), text, fontsize=fontsize)
    doc.save(str(path))
    doc.close()
    return path


def create_encrypted_pdf(
    path: Path,
    text: str = "Encrypted content",
    user_pw: str = "secret",
    owner_pw: str | None = None,
    permissions: int = fitz.PDF_PERM_PRINT,
) -> Path:
    """Create a password-protected PDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), text)
    encrypt = fitz.PDF_ENCRYPT_AES_256
    save_kwargs: dict[str, object] = {
        "encryption": encrypt,
        "user_pw": user_pw,
        "permissions": permissions,
    }
    if owner_pw:
        save_kwargs["owner_pw"] = owner_pw
    doc.save(str(path), **save_kwargs)
    doc.close()
    return path
