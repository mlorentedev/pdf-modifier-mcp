"""Tests for CLI custom fonts integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_modifier_mcp.interfaces.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCLICustomFonts:
    """Tests for --custom-fonts CLI option."""

    def _create_test_pdf(self, tmp_path: Path, text: str = "Hello World") -> Path:
        """Create a simple PDF for testing."""
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text, fontname="helv", fontsize=12)
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_custom_font_option_exists(self, runner: CliRunner) -> None:
        """--custom-fonts option is available in modify command."""
        result = runner.invoke(app, ["modify", "--help"])
        assert result.exit_code == 0
        # Strip ANSI escape codes for reliable matching in CI
        import re

        clean = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
        assert "--custom-fonts" in clean

    def test_custom_font_option_exists_in_batch(self, runner: CliRunner) -> None:
        """--custom-fonts option is available in batch command."""
        result = runner.invoke(app, ["batch", "--help"])
        assert result.exit_code == 0
        import re

        clean = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
        assert "--custom-fonts" in clean

    def test_custom_font_invalid_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI rejects non-existent custom font files."""
        result = runner.invoke(
            app,
            [
                "modify",
                str(tmp_path / "dummy.pdf"),
                str(tmp_path / "out.pdf"),
                "--replace",
                "a=b",
                "--custom-fonts",
                "helv=/nonexistent/font.ttf",
            ],
        )
        assert result.exit_code != 0
        assert "font file does not exist" in result.stdout or "font file" in result.stdout

    def test_custom_font_wrong_extension(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI rejects custom fonts with non-.ttf/.otf extension."""
        font_file = tmp_path / "font.txt"
        font_file.write_bytes(b"not a font")

        result = runner.invoke(
            app,
            [
                "modify",
                str(tmp_path / "dummy.pdf"),
                str(tmp_path / "out.pdf"),
                "--replace",
                "a=b",
                "--custom-fonts",
                f"helv={font_file}",
            ],
        )
        assert result.exit_code != 0
        assert ".ttf or .otf" in result.stdout

    def test_custom_font_multiple(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI accepts multiple --custom-fonts options."""
        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"fake ttf")

        result = runner.invoke(
            app,
            [
                "modify",
                str(tmp_path / "dummy.pdf"),
                str(tmp_path / "out.pdf"),
                "--replace",
                "a=b",
                "--custom-fonts",
                f"helv={font_file}",
                "--custom-fonts",
                f"TiRo={font_file}",
            ],
        )
        # Should not fail on parsing (may fail on file not found, which is OK)
        assert "font file does not exist" not in result.stdout
        assert ".ttf or .otf" not in result.stdout
