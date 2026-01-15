"""Integration tests for PDF Modifier.

Tests cover:
- Core library API (PDFAnalyzer, PDFModifier)
- CLI interface via subprocess
- Error handling and edge cases
"""

import json
import subprocess
import sys
from pathlib import Path

from pdf_modifier_mcp.core import PDFAnalyzer, PDFModifier, ReplacementSpec

from ..conftest import EXAMPLES_OUTPUT_DIR, SAMPLE_PDF


def run_cli(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run CLI command via subprocess."""
    cmd = [sys.executable, "-m", "pdf_modifier_mcp.interfaces.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


# =============================================================================
# Core Library Tests
# =============================================================================


class TestCoreTextReplacement:
    """Tests for core PDFModifier text replacement."""

    def test_simple_replacement(self, output_pdf: Path) -> None:
        """Replace exact text strings."""
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_pdf))
        spec = ReplacementSpec(replacements={"$27.99": "$99.99", "BrosTrend": "TechGiant"})
        result = modifier.process(spec)

        assert result.success
        assert result.replacements_made >= 2
        assert output_pdf.exists()

        analyzer = PDFAnalyzer(str(output_pdf))
        text = analyzer.extract_text()
        assert "$99.99" in text
        assert "TechGiant" in text

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

    def test_hyperlink_creation(self, output_pdf: Path) -> None:
        """Create a neutralized (void) link."""
        modifier = PDFModifier(str(SAMPLE_PDF), str(output_pdf))
        spec = ReplacementSpec(replacements={"Order Summary": "My Summary|void(0)"})
        result = modifier.process(spec)

        assert result.success
        assert output_pdf.exists()


class TestCoreUseCases:
    """Real-world use case examples that save to examples_output/."""

    def test_price_adjustment(self) -> None:
        """Update prices in an invoice."""
        output = EXAMPLES_OUTPUT_DIR / "price_adjustment.pdf"
        modifier = PDFModifier(str(SAMPLE_PDF), str(output))
        spec = ReplacementSpec(replacements={"$27.99": "$45.00", "$111.70": "$128.71"})
        result = modifier.process(spec)

        assert result.success

        analyzer = PDFAnalyzer(str(output))
        text = analyzer.extract_text()
        assert "$45.00" in text

    def test_anonymization(self) -> None:
        """Redact PII from a document."""
        output = EXAMPLES_OUTPUT_DIR / "anonymized.pdf"
        modifier = PDFModifier(str(SAMPLE_PDF), str(output))
        spec = ReplacementSpec(
            replacements={
                r"Order # \d{3}-\d{7}-\d{7}": "Order # REDACTED-ID",
                r"Manuel Lorente": "REDACTED PERSON",
            },
            use_regex=True,
        )
        result = modifier.process(spec)

        assert result.success

        analyzer = PDFAnalyzer(str(output))
        text = analyzer.extract_text()
        assert "REDACTED-ID" in text


# =============================================================================
# CLI Tests
# =============================================================================


class TestCLIAnalyze:
    """CLI analyze command tests."""

    def test_json_output(self) -> None:
        """JSON output contains expected structure."""
        result = run_cli("analyze", str(SAMPLE_PDF), "--json")

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "total_pages" in data
        assert "pages" in data
        assert data["total_pages"] >= 1

    def test_plain_text(self) -> None:
        """Plain text analysis works."""
        result = run_cli("analyze", str(SAMPLE_PDF))

        assert result.returncode == 0
        assert "Page 1" in result.stdout


class TestCLIModify:
    """CLI modify command tests."""

    def test_simple_replacement(self, tmp_path: Path) -> None:
        """Simple text replacement via CLI."""
        output = tmp_path / "output.pdf"
        result = run_cli(
            "modify",
            str(SAMPLE_PDF),
            str(output),
            "-r",
            "BrosTrend=TestBrand",
            "-r",
            "$27.99=$99.99",
        )

        assert result.returncode == 0
        assert "Success" in result.stdout
        assert output.exists()

    def test_regex_replacement(self, tmp_path: Path) -> None:
        """Regex replacement via CLI."""
        output = tmp_path / "output.pdf"
        result = run_cli(
            "modify",
            str(SAMPLE_PDF),
            str(output),
            "-r",
            r"\d{4}=2099",
            "--regex",
        )

        assert result.returncode == 0


class TestCLIInspect:
    """CLI inspect command tests."""

    def test_finds_term(self) -> None:
        """Finds and displays font info."""
        result = run_cli("inspect", str(SAMPLE_PDF), "Order")
        assert result.returncode == 0

    def test_no_matches(self) -> None:
        """Handles non-existent terms gracefully."""
        result = run_cli("inspect", str(SAMPLE_PDF), "NONEXISTENT_XYZ")
        assert result.returncode == 0
        assert "No matches" in result.stdout


class TestCLIErrors:
    """CLI error handling tests."""

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Error for non-existent input file."""
        result = run_cli(
            "modify",
            str(tmp_path / "missing.pdf"),
            str(tmp_path / "out.pdf"),
            "-r",
            "a=b",
            check=False,
        )
        assert result.returncode == 1

    def test_invalid_format(self, tmp_path: Path) -> None:
        """Error for invalid replacement format."""
        result = run_cli(
            "modify",
            str(SAMPLE_PDF),
            str(tmp_path / "out.pdf"),
            "-r",
            "no_equals_sign",
            check=False,
        )
        assert result.returncode == 1


class TestCLIHelp:
    """CLI help tests."""

    def test_main_help(self) -> None:
        """Main help shows commands."""
        result = run_cli("--help")
        assert result.returncode == 0
        assert "modify" in result.stdout
        assert "analyze" in result.stdout
        assert "inspect" in result.stdout
