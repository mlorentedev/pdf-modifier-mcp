"""Tests for MCP interface."""

import json
from pathlib import Path

from pdf_modifier_mcp.interfaces.mcp import (
    inspect_pdf_fonts,
    mcp,
    modify_pdf_content,
    read_pdf_structure,
)

from ...conftest import SAMPLE_PDF


class TestMCPServer:
    """Tests for MCP server."""

    def test_server_name(self) -> None:
        assert mcp.name == "pdf-modifier-mcp"


class TestMCPReadStructure:
    """Tests for read_pdf_structure tool."""

    def test_returns_valid_json(self) -> None:
        result = read_pdf_structure(str(SAMPLE_PDF))
        parsed = json.loads(result)
        assert "total_pages" in parsed
        assert parsed["total_pages"] >= 1

    def test_error_on_invalid_file(self, tmp_path: Path) -> None:
        result = read_pdf_structure(str(tmp_path / "missing.pdf"))
        parsed = json.loads(result)
        assert parsed["success"] is False


class TestMCPInspectFonts:
    """Tests for inspect_pdf_fonts tool."""

    def test_returns_matches(self) -> None:
        result = inspect_pdf_fonts(str(SAMPLE_PDF), ["Order", "$"])
        parsed = json.loads(result)
        assert parsed["total_matches"] >= 1

    def test_no_matches(self) -> None:
        result = inspect_pdf_fonts(str(SAMPLE_PDF), ["XYZNONEXISTENT"])
        parsed = json.loads(result)
        assert parsed["total_matches"] == 0


class TestMCPModifyContent:
    """Tests for modify_pdf_content tool."""

    def test_simple_replacement(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(str(SAMPLE_PDF), str(output_pdf), {"$27.99": "$99.99"})
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert output_pdf.exists()

    def test_regex_replacement(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(
            str(SAMPLE_PDF),
            str(output_pdf),
            {r"January \d{2}, \d{4}": "February 01, 2030"},
            use_regex=True,
        )
        parsed = json.loads(result)
        assert parsed["success"] is True

    def test_hyperlink_syntax(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(
            str(SAMPLE_PDF), str(output_pdf), {"Order Summary": "Click|https://example.com"}
        )
        parsed = json.loads(result)
        assert parsed["success"] is True

    def test_error_on_invalid_file(self, tmp_path: Path) -> None:
        result = modify_pdf_content(
            str(tmp_path / "missing.pdf"), str(tmp_path / "out.pdf"), {"a": "b"}
        )
        parsed = json.loads(result)
        assert parsed["success"] is False
