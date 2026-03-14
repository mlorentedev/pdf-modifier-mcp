"""Tests for CLI interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz
from typer.testing import CliRunner

from pdf_modifier_mcp.interfaces.cli import app

from ...conftest import SAMPLE_PDF

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


class TestCLIModify:
    """Tests for CLI modify command."""

    def test_simple_replacement(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = runner.invoke(
            app, ["modify", str(SAMPLE_PDF), str(output_pdf), "-r", "$27.99=$99.99"]
        )
        assert result.exit_code == 0
        assert "Success" in result.stdout
        assert output_pdf.exists()

    def test_regex_replacement(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = runner.invoke(
            app,
            [
                "modify",
                str(SAMPLE_PDF),
                str(output_pdf),
                "-r",
                r"January \d{2}, \d{4}=February 01, 2030",
                "--regex",
            ],
        )
        assert result.exit_code == 0

    def test_multiple_replacements(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = runner.invoke(
            app,
            [
                "modify",
                str(SAMPLE_PDF),
                str(output_pdf),
                "-r",
                "$27.99=$99.99",
                "-r",
                "BrosTrend=TestBrand",
            ],
        )
        assert result.exit_code == 0
        assert "Success" in result.stdout

    def test_invalid_format_error(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = runner.invoke(app, ["modify", str(SAMPLE_PDF), str(output_pdf), "-r", "no_equals"])
        assert result.exit_code == 1

    def test_nonexistent_file_error(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["modify", str(tmp_path / "missing.pdf"), str(tmp_path / "out.pdf"), "-r", "a=b"],
        )
        assert result.exit_code == 1

    def test_shows_warnings(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = runner.invoke(
            app, ["modify", str(SAMPLE_PDF), str(output_pdf), "-r", "$27.99=$99.99"]
        )
        assert result.exit_code == 0
        assert "Replacements:" in result.stdout


class TestCLIAnalyze:
    """Tests for CLI analyze command."""

    def test_plain_text(self) -> None:
        result = runner.invoke(app, ["analyze", str(SAMPLE_PDF)])
        assert result.exit_code == 0
        assert "Page 1" in result.stdout

    def test_json_output(self) -> None:
        result = runner.invoke(app, ["analyze", str(SAMPLE_PDF), "--json"])
        assert result.exit_code == 0
        assert "total_pages" in result.stdout


class TestCLIInspect:
    """Tests for CLI inspect command."""

    def test_finds_terms(self) -> None:
        result = runner.invoke(app, ["inspect", str(SAMPLE_PDF), "Order"])
        assert result.exit_code == 0

    def test_no_matches(self) -> None:
        result = runner.invoke(app, ["inspect", str(SAMPLE_PDF), "XYZNONEXISTENT"])
        assert result.exit_code == 0
        assert "No matches" in result.stdout


class TestCLILinks:
    """Tests for CLI links command."""

    def test_no_links_message(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "no_links.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        result = runner.invoke(app, ["links", str(pdf_path)])
        assert result.exit_code == 0
        assert "No hyperlinks" in result.stdout

    def test_with_links(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "with_links.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Click")
        link_rect = fitz.Rect(95, 90, 200, 110)
        page.insert_link({"from": link_rect, "uri": "https://example.com", "kind": fitz.LINK_URI})
        doc.save(str(pdf_path))
        doc.close()

        result = runner.invoke(app, ["links", str(pdf_path)])
        assert result.exit_code == 0
        assert "https://example.com" in result.stdout


class TestCLIHelp:
    """Tests for CLI help."""

    def test_help_shows_commands(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "modify" in result.stdout
        assert "analyze" in result.stdout
        assert "inspect" in result.stdout
        assert "links" in result.stdout
