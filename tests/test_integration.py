"""Integration tests for PDF modification operations.

Tests use temporary directories by default. To generate persistent example
outputs for documentation, run: pytest -m examples --examples-output
"""

from pathlib import Path

import pytest

from pdf_modifier_mcp.core import PDFAnalyzer, PDFModifier, ReplacementSpec

# Paths
TEST_DATA_DIR = Path(__file__).parent / "data"
SAMPLE_PDF = TEST_DATA_DIR / "sample.pdf"
EXAMPLES_OUTPUT_DIR = Path(__file__).parent / "examples_output"


@pytest.fixture
def output_pdf(tmp_path: Path) -> Path:
    """Default output path using pytest tmp_path."""
    return tmp_path / "output.pdf"


@pytest.fixture(scope="session", autouse=True)
def setup_examples_dir() -> None:
    """Ensure examples output directory exists."""
    EXAMPLES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class TestTextReplacement:
    """Tests for basic text replacement functionality."""

    def test_simple_replacement(self, output_pdf: Path) -> None:
        """Replace exact text strings."""
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_pdf))
        spec = ReplacementSpec(
            replacements={
                "$27.99": "$99.99",
                "BrosTrend": "TechGiant",
            }
        )
        result = modifier.process(spec)

        assert result.success
        assert result.replacements_made >= 2
        assert output_pdf.exists()

        analyzer = PDFAnalyzer(str(output_pdf))
        text = analyzer.extract_text()
        assert "$99.99" in text
        assert "TechGiant" in text
        assert "$27.99" not in text

    def test_regex_replacement(self, output_pdf: Path) -> None:
        """Replace text using regex patterns."""
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_pdf))
        spec = ReplacementSpec(
            replacements={r"January \d{2}, \d{4}": "February 01, 2030"},
            use_regex=True,
        )
        result = modifier.process(spec)

        assert result.success

        analyzer = PDFAnalyzer(str(output_pdf))
        text = analyzer.extract_text()
        assert "February 01, 2030" in text
        assert "January 12, 2026" not in text


class TestHyperlinks:
    """Tests for hyperlink creation and neutralization."""

    def test_create_void_link(self, output_pdf: Path) -> None:
        """Create a neutralized (void) link."""
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_pdf))
        spec = ReplacementSpec(replacements={"Order Summary": "My Summary|void(0)"})
        result = modifier.process(spec)

        assert result.success
        assert output_pdf.exists()

        analyzer = PDFAnalyzer(str(output_pdf))
        text = analyzer.extract_text()
        assert "My Summary" in text


class TestUseCaseExamples:
    """
    Documentation examples demonstrating real-world use cases.

    These tests save outputs to examples_output/ for manual verification.
    """

    def test_example_price_adjustment(self) -> None:
        """Use case: Update prices in an invoice."""
        output_path = EXAMPLES_OUTPUT_DIR / "1_price_adjustment.pdf"
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_path))

        spec = ReplacementSpec(
            replacements={
                "$27.99": "$45.00",
                "$111.70": "$128.71",
            }
        )
        result = modifier.process(spec)

        assert result.success

        analyzer = PDFAnalyzer(str(output_path))
        text = analyzer.extract_text()
        assert "$45.00" in text
        assert "$128.71" in text

    def test_example_anonymization(self) -> None:
        """Use case: Redact PII from a document."""
        output_path = EXAMPLES_OUTPUT_DIR / "2_anonymized.pdf"
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_path))

        spec = ReplacementSpec(
            replacements={
                r"Order # \d{3}-\d{7}-\d{7}": "Order # REDACTED-ID",
                r"Manuel Lorente": "REDACTED PERSON",
            },
            use_regex=True,
        )
        result = modifier.process(spec)

        assert result.success

        analyzer = PDFAnalyzer(str(output_path))
        text = analyzer.extract_text()
        assert "REDACTED-ID" in text
        assert "REDACTED PERSON" in text

    def test_example_date_rolling(self) -> None:
        """Use case: Update dates in a recurring document."""
        output_path = EXAMPLES_OUTPUT_DIR / "3_date_rolling.pdf"
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_path))

        spec = ReplacementSpec(
            replacements={r"January \d{2}, 2026": "February 01, 2026"},
            use_regex=True,
        )
        result = modifier.process(spec)

        assert result.success

        analyzer = PDFAnalyzer(str(output_path))
        text = analyzer.extract_text()
        assert "February 01, 2026" in text
