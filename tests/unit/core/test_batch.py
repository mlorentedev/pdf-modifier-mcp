"""Tests for batch_process function."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdf_modifier_mcp.core.models import ReplacementSpec
from pdf_modifier_mcp.core.modifier import batch_process

from ...conftest import create_pdf

if TYPE_CHECKING:
    from pathlib import Path


class TestBatchProcessMultipleFiles:
    """Tests for processing multiple files in a batch."""

    def test_batch_processes_multiple_files(self, tmp_path: Path) -> None:
        """All valid files are processed and results aggregated."""
        pdf1 = create_pdf(tmp_path / "file1.pdf", text="Hello World")
        pdf2 = create_pdf(tmp_path / "file2.pdf", text="Hello World")
        output_dir = tmp_path / "output"

        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = batch_process([str(pdf1), str(pdf2)], str(output_dir), spec)

        assert result.total_files == 2
        assert result.successful == 2
        assert result.failed == 0
        assert len(result.results) == 2
        assert len(result.errors) == 0
        assert (output_dir / "file1.pdf").exists()
        assert (output_dir / "file2.pdf").exists()

    def test_batch_skips_failed_files(self, tmp_path: Path) -> None:
        """Corrupt or missing files are skipped without failing the batch."""
        pdf_good = create_pdf(tmp_path / "good.pdf", text="Hello World")
        pdf_missing = tmp_path / "missing.pdf"
        output_dir = tmp_path / "output"

        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = batch_process([str(pdf_good), str(pdf_missing)], str(output_dir), spec)

        assert result.total_files == 2
        assert result.successful == 1
        assert result.failed == 1
        assert len(result.results) == 1
        assert len(result.errors) == 1
        assert result.errors[0]["file"] == str(pdf_missing)

    def test_batch_output_dir_structure(self, tmp_path: Path) -> None:
        """Output files are placed in output_dir with original filenames."""
        subdir = tmp_path / "inputs"
        subdir.mkdir()
        pdf1 = create_pdf(subdir / "report.pdf", text="Draft Version")
        output_dir = tmp_path / "results"

        spec = ReplacementSpec(replacements={"Draft": "Final"})
        result = batch_process([str(pdf1)], str(output_dir), spec)

        assert result.successful == 1
        output_file = output_dir / "report.pdf"
        assert output_file.exists()
        assert result.results[0].output_path == str(output_file)

    def test_batch_empty_list(self, tmp_path: Path) -> None:
        """Empty input list returns zero counts and no errors."""
        output_dir = tmp_path / "output"
        spec = ReplacementSpec(replacements={"a": "b"})
        result = batch_process([], str(output_dir), spec)

        assert result.total_files == 0
        assert result.successful == 0
        assert result.failed == 0
        assert len(result.results) == 0
        assert len(result.errors) == 0

    def test_batch_with_regex(self, tmp_path: Path) -> None:
        """Regex replacements work across batch files."""
        pdf1 = create_pdf(tmp_path / "file1.pdf", text="Date: 2024-01-15")
        pdf2 = create_pdf(tmp_path / "file2.pdf", text="Date: 2024-06-30")
        output_dir = tmp_path / "output"

        spec = ReplacementSpec(
            replacements={r"\d{4}-\d{2}-\d{2}": "REDACTED"},
            use_regex=True,
        )
        result = batch_process([str(pdf1), str(pdf2)], str(output_dir), spec)

        assert result.total_files == 2
        assert result.successful == 2
        assert result.failed == 0
        for res in result.results:
            assert res.replacements_made >= 1

    def test_batch_creates_output_dir(self, tmp_path: Path) -> None:
        """Output directory is created automatically if it does not exist."""
        pdf = create_pdf(tmp_path / "test.pdf", text="Hello")
        output_dir = tmp_path / "nested" / "deep" / "output"

        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = batch_process([str(pdf)], str(output_dir), spec)

        assert result.successful == 1
        assert output_dir.exists()

    def test_batch_skips_same_input_output(self, tmp_path: Path) -> None:
        """Files where input == output are reported as errors."""
        output_dir = tmp_path  # Same directory as the input files
        pdf = create_pdf(tmp_path / "conflict.pdf", text="Hello")

        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = batch_process([str(pdf)], str(output_dir), spec)

        assert result.total_files == 1
        assert result.successful == 0
        assert result.failed == 1
        assert "same" in result.errors[0]["error"].lower()
