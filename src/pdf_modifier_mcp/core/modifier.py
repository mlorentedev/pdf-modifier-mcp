"""PDF text replacement engine with style preservation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

import fitz

from ..logger import setup_logging
from .exceptions import (
    FileSizeExceededError,
    PDFModifierError,
    PDFNotFoundError,
    PDFPasswordError,
    PDFReadError,
    PDFWriteError,
)
from .models import BatchResult, ModificationResult, ReplacementSpec

logger = setup_logging(__name__)

DEFAULT_MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB


class PDFModifier:
    """
    PDF text replacement engine with style preservation.

    Supports:
    - Exact text matching
    - Regex pattern matching
    - Hyperlink creation (text|URL syntax)
    - Font style preservation (Base 14 fonts)

    Example:
        >>> spec = ReplacementSpec(replacements={"old": "new"})
        >>> modifier = PDFModifier("input.pdf", "output.pdf")
        >>> result = modifier.process(spec)
        >>> print(result.replacements_made)

        # Or with context manager:
        >>> with PDFModifier("input.pdf", "output.pdf") as modifier:
        ...     result = modifier.process(spec)
    """

    def __init__(
        self,
        input_path: str | Path,
        output_path: str | Path,
        password: str | None = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        self.input_path = Path(input_path).absolute()
        self.output_path = Path(output_path).absolute()
        self.password = password
        self.max_file_size = max_file_size

        if self.input_path == self.output_path:
            raise ValueError("Input and output paths cannot be the same. Risk of file corruption.")

        self._doc: fitz.Document | None = None
        self._warnings: list[str] = []

    def _open_doc(self) -> fitz.Document:
        """Safely open the document with password authentication if required."""
        if not self.input_path.exists():
            raise PDFNotFoundError(
                f"PDF file not found: {self.input_path}",
                {"path": str(self.input_path)},
            )

        file_size = self.input_path.stat().st_size
        if file_size > self.max_file_size:
            size_mb = file_size / (1024 * 1024)
            limit_mb = self.max_file_size / (1024 * 1024)
            raise FileSizeExceededError(
                f"PDF file is {size_mb:.1f} MB, exceeds limit of {limit_mb:.0f} MB",
                {
                    "path": str(self.input_path),
                    "size_bytes": file_size,
                    "limit_bytes": self.max_file_size,
                },
            )

        try:
            doc = fitz.open(self.input_path)
            if doc.needs_pass:
                if not self.password:
                    raise PDFPasswordError("PDF is password protected. Please provide a password.")
                if not doc.authenticate(self.password):
                    raise PDFPasswordError("Incorrect password provided for the PDF.")
            return doc
        except PDFPasswordError:
            raise
        except Exception as e:
            raise PDFReadError(f"Cannot open PDF: {e}", {"path": str(self.input_path)}) from e

    def __enter__(self) -> PDFModifier:
        self._doc = self._open_doc()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Explicitly close the document."""
        if self._doc:
            self._doc.close()
            self._doc = None

    def process(self, spec: ReplacementSpec) -> ModificationResult:
        """
        Execute all replacements and return structured result.

        Batches redactions per page for efficiency.

        Args:
            spec: ReplacementSpec containing replacements and options.

        Returns:
            ModificationResult with success status and statistics.

        Raises:
            PDFReadError: If the PDF cannot be opened.
            PDFWriteError: If the output cannot be saved.
        """
        doc_opened_here = False
        if not self._doc:
            self._doc = self._open_doc()
            doc_opened_here = True

        total_replacements = 0
        pages_modified: set[int] = set()

        try:
            for page_num, page in enumerate(self._doc):
                items = self._collect_replacements(page, spec)

                if not items:
                    continue

                pages_modified.add(page_num)

                # Batch: add all redaction annotations first
                for item in items:
                    if "bboxes" in item:
                        for bbox in item["bboxes"]:
                            page.add_redact_annot(bbox, fill=(1, 1, 1))
                    else:
                        page.add_redact_annot(item["bbox"], fill=(1, 1, 1))

                # Single apply_redactions() call per page (efficient)
                page.apply_redactions()

                # Insert all replacement text
                for item in items:
                    self._insert_replacement(page, item)
                    total_replacements += 1
        except PDFModifierError:
            raise
        except Exception as e:
            raise PDFReadError(f"Failed to process PDF pages: {e}") from e

        try:
            self._doc.save(str(self.output_path))
            logger.info(
                "Saved %s with %d replacements across %d pages",
                self.output_path,
                total_replacements,
                len(pages_modified),
            )
        except Exception as e:
            raise PDFWriteError(f"Failed to save PDF: {e}") from e
        finally:
            if doc_opened_here:
                self.close()

        return ModificationResult(
            success=True,
            input_path=str(self.input_path),
            output_path=str(self.output_path),
            replacements_made=total_replacements,
            pages_modified=len(pages_modified),
            warnings=self._warnings,
        )

    def _get_font_properties(self, font_name: str) -> tuple[str, str]:
        """
        Map PDF font names to PyMuPDF Base 14 font codes.

        Returns:
            Tuple of (font_code for insert_text, font_name for width calculation)
        """
        name_lower = font_name.lower()

        if "courier" in name_lower:
            if "bold" in name_lower:
                return ("CoBo", "Courier-Bold")
            return ("Cour", "Courier")
        elif "times" in name_lower or "serif" in name_lower:
            if "bold" in name_lower:
                return ("TiBo", "Times-Bold")
            return ("TiRo", "Times-Roman")
        elif "bold" in name_lower:
            return ("HeBo", "Helvetica-Bold")
        return ("helv", "Helvetica")

    def _convert_color(
        self, color_input: int | list[float] | tuple[float, ...]
    ) -> tuple[float, float, float]:
        """Convert PyMuPDF color to RGB float tuple (0.0-1.0)."""
        if isinstance(color_input, int):
            r = ((color_input >> 16) & 0xFF) / 255.0
            g = ((color_input >> 8) & 0xFF) / 255.0
            b = (color_input & 0xFF) / 255.0
            return (r, g, b)
        elif isinstance(color_input, list | tuple) and len(color_input) >= 3:
            return tuple(c if c <= 1.0 else c / 255.0 for c in color_input[:3])  # type: ignore[return-value]
        return (0.0, 0.0, 0.0)

    def _collect_replacements(
        self,
        page: fitz.Page,
        spec: ReplacementSpec,
    ) -> list[dict[str, Any]]:
        """Scan page and collect items to replace.

        Two-pass approach:
        1. Single-span matching (fast path for most cases).
        2. Cross-span matching per line: concatenate span texts and match
           across boundaries, mapping results back to individual spans.
        """
        items: list[dict[str, Any]] = []
        matched_span_ids: set[int] = set()
        blocks = page.get_text("dict")["blocks"]

        # --- Pass 1: single-span matching ---
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    original = span["text"]

                    for target, replacement_raw in spec.replacements.items():
                        match_found = False
                        if spec.use_regex and spec.compiled_patterns:
                            pattern = spec.compiled_patterns[target]
                            if pattern.search(text):
                                match_found = True
                        elif target in text:
                            match_found = True

                        if match_found:
                            item = self._build_replacement_item(
                                span,
                                original,
                                target,
                                replacement_raw,
                                spec,
                            )
                            items.append(item)
                            matched_span_ids.add(id(span))
                            break  # One replacement per span

        # --- Pass 2: cross-span matching ---
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if len(spans) < 2:
                    continue

                cross_items = self._match_across_spans(
                    spans,
                    spec,
                    matched_span_ids,
                )
                items.extend(cross_items)

        return items

    def _build_replacement_item(
        self,
        span: dict[str, Any],
        original: str,
        target: str,
        replacement_raw: str,
        spec: ReplacementSpec,
    ) -> dict[str, Any]:
        """Build a single replacement item dict from a span match."""
        replacement_text = replacement_raw
        url = None

        if "|" in replacement_raw:
            candidate_text, candidate_url = replacement_raw.rsplit("|", 1)
            candidate_url = candidate_url.strip()

            if candidate_url == "void(0)" or candidate_url.startswith(
                ("http://", "https://", "mailto:", "javascript:")
            ):
                replacement_text = candidate_text
                url = "javascript:void(0)" if candidate_url == "void(0)" else candidate_url

        font_code, font_std = self._get_font_properties(span["font"])

        if spec.use_regex and spec.compiled_patterns:
            pattern = spec.compiled_patterns[target]
            new_text = pattern.sub(replacement_text, original)
        else:
            new_text = original.replace(target, replacement_text)

        return {
            "bbox": span["bbox"],
            "origin": span["origin"],
            "text": new_text,
            "url": url,
            "font_code": font_code,
            "font_std": font_std,
            "size": span["size"],
            "color": span["color"],
        }

    def _match_across_spans(
        self,
        spans: list[dict[str, Any]],
        spec: ReplacementSpec,
        matched_span_ids: set[int],
    ) -> list[dict[str, Any]]:
        """Match replacement targets across concatenated span texts.

        For each line, concatenate all span texts, find matches in
        the merged string, then map each match back to the spans it
        overlaps. Only produces items for matches that span at least
        two spans (single-span matches are handled in pass 1).
        """
        items: list[dict[str, Any]] = []

        # Build concatenated text and offset map
        merged = ""
        span_ranges: list[tuple[int, int]] = []  # (start, end) in merged
        for span in spans:
            start = len(merged)
            merged += span["text"]
            span_ranges.append((start, len(merged)))

        merged_stripped = merged.strip()
        if not merged_stripped:
            return items

        for target, replacement_raw in spec.replacements.items():
            matches: list[tuple[int, int]] = []
            if spec.use_regex and spec.compiled_patterns:
                pattern = spec.compiled_patterns[target]
                for m in pattern.finditer(merged):
                    matches.append((m.start(), m.end()))
            else:
                start = 0
                while True:
                    idx = merged.find(target, start)
                    if idx == -1:
                        break
                    matches.append((idx, idx + len(target)))
                    start = idx + 1

            for m_start, m_end in matches:
                involved: list[int] = []
                for i, (s_start, s_end) in enumerate(span_ranges):
                    if s_start < m_end and s_end > m_start:
                        involved.append(i)

                # Skip single-span matches (handled in pass 1)
                if len(involved) < 2:
                    continue

                # Skip if any involved span was already matched
                if any(id(spans[i]) in matched_span_ids for i in involved):
                    continue

                first_span = spans[involved[0]]
                bboxes = [tuple(spans[i]["bbox"]) for i in involved]
                # Merged bbox: min x0/y0, max x1/y1
                x0 = min(b[0] for b in bboxes)
                y0 = min(b[1] for b in bboxes)
                x1 = max(b[2] for b in bboxes)
                y1 = max(b[3] for b in bboxes)

                matched_text = merged[m_start:m_end]

                # Parse replacement
                replacement_text = replacement_raw
                url = None
                if "|" in replacement_raw:
                    candidate_text, candidate_url = replacement_raw.rsplit("|", 1)
                    candidate_url = candidate_url.strip()
                    if candidate_url == "void(0)" or candidate_url.startswith(
                        ("http://", "https://", "mailto:", "javascript:")
                    ):
                        replacement_text = candidate_text
                        url = "javascript:void(0)" if candidate_url == "void(0)" else candidate_url

                # Compute new text
                if spec.use_regex and spec.compiled_patterns:
                    pattern = spec.compiled_patterns[target]
                    new_text = pattern.sub(
                        replacement_text,
                        matched_text,
                    )
                else:
                    new_text = matched_text.replace(
                        target,
                        replacement_text,
                    )

                font_code, font_std = self._get_font_properties(
                    first_span["font"],
                )

                items.append(
                    {
                        "bbox": (x0, y0, x1, y1),
                        "bboxes": bboxes,
                        "origin": first_span["origin"],
                        "text": new_text,
                        "url": url,
                        "font_code": font_code,
                        "font_std": font_std,
                        "size": first_span["size"],
                        "color": first_span["color"],
                    }
                )

                # Mark all involved spans as matched
                for i in involved:
                    matched_span_ids.add(id(spans[i]))

        return items

    def _insert_replacement(self, page: fitz.Page, item: dict[str, Any]) -> None:
        """Insert replacement text with original styling."""
        color = self._convert_color(item["color"])

        page.insert_text(
            item["origin"],
            item["text"],
            fontname=item["font_code"],
            fontsize=item["size"],
            color=color,
        )

        # Handle hyperlinks
        link_url = item["url"]
        if not link_url and item["text"].strip().startswith(("http://", "https://")):
            link_url = item["text"].strip()

        if link_url:
            try:
                font = fitz.Font(item["font_std"])
                text_width = font.text_length(item["text"], fontsize=item["size"])

                x0 = item["origin"][0]
                y_baseline = item["origin"][1]
                link_rect = fitz.Rect(
                    x0,
                    y_baseline - item["size"],
                    x0 + text_width,
                    y_baseline + (item["size"] * 0.25),
                )

                page.insert_link(
                    {
                        "kind": fitz.LINK_URI,
                        "from": link_rect,
                        "uri": link_url,
                    }
                )
            except Exception as e:
                msg = f"Could not add link for '{item['text']}': {e}"
                logger.warning(msg)
                self._warnings.append(msg)


def batch_process(
    file_paths: Sequence[str | Path],
    output_dir: str | Path,
    spec: ReplacementSpec,
    password: str | None = None,
) -> BatchResult:
    """
    Apply the same replacements to multiple PDF files.

    Each file is processed independently; failures in one file do not
    affect the rest of the batch. Output files are written to
    ``output_dir`` using the same filename as the input.

    Args:
        file_paths: List of input PDF file paths.
        output_dir: Directory where modified PDFs will be saved.
        spec: ReplacementSpec containing replacements and options.
        password: Optional password for encrypted PDFs.

    Returns:
        BatchResult with per-file results and aggregate statistics.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[ModificationResult] = []
    errors: list[dict[str, str]] = []

    for file_path in file_paths:
        file_path = Path(file_path)
        output_path = output_dir / file_path.name

        if file_path.absolute() == output_path.absolute():
            errors.append(
                {
                    "file": str(file_path),
                    "error": "Input and output paths are the same",
                }
            )
            continue

        try:
            modifier = PDFModifier(str(file_path), str(output_path), password=password)
            result = modifier.process(spec)
            results.append(result)
        except Exception as e:
            logger.warning("Batch: failed to process %s: %s", file_path, e)
            errors.append({"file": str(file_path), "error": str(e)})

    return BatchResult(
        total_files=len(file_paths),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )
