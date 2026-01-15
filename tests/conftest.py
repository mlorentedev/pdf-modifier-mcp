"""Shared pytest fixtures and constants for all tests."""

from pathlib import Path

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
