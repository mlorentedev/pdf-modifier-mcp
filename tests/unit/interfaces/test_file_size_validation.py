"""Tests for file size validation in CLI and MCP interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from pdf_modifier_mcp.interfaces.cli import app
from pdf_modifier_mcp.interfaces.mcp import modify_pdf_content
from tests.conftest import create_pdf

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


class TestCLIMaxFileSize:
    """File size validation exposed through CLI."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_cli_modify_rejects_large_file(self, tmp_path: Path, runner: CliRunner) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output = tmp_path / "output.pdf"
        # Set max_size to 1 byte so any PDF exceeds it
        result = runner.invoke(
            app,
            [
                "modify",
                str(pdf),
                str(output),
                "--replace",
                "Hello=World",
                "--max-size",
                "1",
            ],
        )
        assert result.exit_code == 1
        assert "exceeds limit" in result.stdout or "Error" in result.stdout

    def test_cli_modify_accepts_within_limit(self, tmp_path: Path, runner: CliRunner) -> None:
        pdf = create_pdf(tmp_path / "input.pdf", text="Hello World")
        output = tmp_path / "output.pdf"
        result = runner.invoke(
            app,
            [
                "modify",
                str(pdf),
                str(output),
                "--replace",
                "Hello=Hola",
                "--max-size",
                "10485760",
            ],
        )
        assert result.exit_code == 0
        assert "Success" in result.stdout

    def test_cli_batch_rejects_large_file(self, tmp_path: Path, runner: CliRunner) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output_dir = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "batch",
                str(pdf),
                "--output-dir",
                str(output_dir),
                "--replace",
                "Hello=World",
                "--max-size",
                "1",
            ],
        )
        # batch_process handles errors internally; output shows 0 succeeded, 1 failed
        assert "0 succeeded" in result.stdout or "1 failed" in result.stdout

    def test_cli_analyze_rejects_large_file(self, tmp_path: Path, runner: CliRunner) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        result = runner.invoke(
            app,
            ["analyze", str(pdf), "--max-size", "1"],
        )
        assert result.exit_code == 1
        assert "exceeds limit" in result.stdout or "Error" in result.stdout

    def test_cli_inspect_rejects_large_file(self, tmp_path: Path, runner: CliRunner) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        result = runner.invoke(
            app,
            ["inspect", str(pdf), "Hello", "--max-size", "1"],
        )
        assert result.exit_code == 1
        assert "exceeds limit" in result.stdout or "Error" in result.stdout

    def test_cli_links_rejects_large_file(self, tmp_path: Path, runner: CliRunner) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        result = runner.invoke(
            app,
            ["links", str(pdf), "--max-size", "1"],
        )
        assert result.exit_code == 1
        assert "exceeds limit" in result.stdout or "Error" in result.stdout


class TestEnvVarMaxFileSize:
    """MAX_FILE_SIZE via environment variable."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_env_var_sets_max_size(
        self, tmp_path: Path, runner: CliRunner, monkeypatch: MonkeyPatch
    ) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output = tmp_path / "output.pdf"
        monkeypatch.setenv("PDF_MOD_MAX_FILE_SIZE", "1")
        result = runner.invoke(
            app,
            ["modify", str(pdf), str(output), "--replace", "Hello=World"],
        )
        assert result.exit_code == 1
        assert "exceeds limit" in result.stdout or "Error" in result.stdout

    def test_env_var_accepts_valid_size(
        self, tmp_path: Path, runner: CliRunner, monkeypatch: MonkeyPatch
    ) -> None:
        pdf = create_pdf(tmp_path / "input.pdf", text="Hello World")
        output = tmp_path / "output.pdf"
        monkeypatch.setenv("PDF_MOD_MAX_FILE_SIZE", "10485760")
        result = runner.invoke(
            app,
            ["modify", str(pdf), str(output), "--replace", "Hello=Hola"],
        )
        assert result.exit_code == 0
        assert "Success" in result.stdout

    def test_cli_flag_overrides_env(
        self, tmp_path: Path, runner: CliRunner, monkeypatch: MonkeyPatch
    ) -> None:
        """CLI --max-size flag takes precedence over env var."""
        pdf = create_pdf(tmp_path / "input.pdf", text="Hello World")
        output = tmp_path / "output.pdf"
        # Env says 1 byte (reject), but CLI flag says 10 MB (accept)
        monkeypatch.setenv("PDF_MOD_MAX_FILE_SIZE", "1")
        result = runner.invoke(
            app,
            [
                "modify",
                str(pdf),
                str(output),
                "--replace",
                "Hello=Hola",
                "--max-size",
                "10485760",
            ],
        )
        assert result.exit_code == 0
        assert "Success" in result.stdout


class TestMCPMaxFileSize:
    """File size validation exposed through MCP tools."""

    def test_modify_pdf_rejects_large_file(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output = tmp_path / "output.pdf"
        result = modify_pdf_content(
            input_path=str(pdf),
            output_path=str(output),
            replacements={"Hello": "World"},
            max_file_size=1,
        )
        import json

        data = json.loads(result)
        assert data["success"] is False
        assert data["error"] == "FILE_TOO_LARGE"

    def test_modify_pdf_accepts_within_limit(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf", text="Hello World")
        output = tmp_path / "output.pdf"
        result = modify_pdf_content(
            input_path=str(pdf),
            output_path=str(output),
            replacements={"Hello": "Hola"},
            max_file_size=10 * 1024 * 1024,
        )
        import json

        data = json.loads(result)
        assert data["success"] is True
        assert data["replacements_made"] > 0

    def test_batch_modify_rejects_large_file(self, tmp_path: Path) -> None:
        from pdf_modifier_mcp.interfaces.mcp import batch_modify_pdf_content

        pdf = create_pdf(tmp_path / "input.pdf")
        output_dir = tmp_path / "out"
        result = batch_modify_pdf_content(
            input_paths=[str(pdf)],
            output_dir=str(output_dir),
            replacements={"Hello": "World"},
            max_file_size=1,
        )
        import json

        data = json.loads(result)
        assert data["failed"] == 1
        assert "FILE_TOO_LARGE" in data["errors"][0]["error"]

    def test_read_pdf_structure_rejects_large_file(self, tmp_path: Path) -> None:
        from pdf_modifier_mcp.interfaces.mcp import read_pdf_structure

        pdf = create_pdf(tmp_path / "input.pdf")
        result = read_pdf_structure(
            input_path=str(pdf),
            max_file_size=1,
        )
        import json

        data = json.loads(result)
        assert data["success"] is False
        assert data["error"] == "FILE_TOO_LARGE"

    def test_inspect_pdf_fonts_rejects_large_file(self, tmp_path: Path) -> None:
        from pdf_modifier_mcp.interfaces.mcp import inspect_pdf_fonts

        pdf = create_pdf(tmp_path / "input.pdf")
        result = inspect_pdf_fonts(
            input_path=str(pdf),
            terms=["Hello"],
            max_file_size=1,
        )
        import json

        data = json.loads(result)
        assert data["success"] is False
        assert data["error"] == "FILE_TOO_LARGE"

    def test_list_pdf_hyperlinks_rejects_large_file(self, tmp_path: Path) -> None:
        from pdf_modifier_mcp.interfaces.mcp import list_pdf_hyperlinks

        pdf = create_pdf(tmp_path / "input.pdf")
        result = list_pdf_hyperlinks(
            input_path=str(pdf),
            max_file_size=1,
        )
        import json

        data = json.loads(result)
        assert data["success"] is False
        assert data["error"] == "FILE_TOO_LARGE"

    def test_extract_embedded_fonts_rejects_large_file(self, tmp_path: Path) -> None:
        from pdf_modifier_mcp.interfaces.mcp import extract_embedded_fonts

        pdf = create_pdf(tmp_path / "input.pdf")
        result = extract_embedded_fonts(
            input_path=str(pdf),
            max_file_size=1,
        )
        import json

        data = json.loads(result)
        assert data["success"] is False
        assert data["error"] == "FILE_TOO_LARGE"
