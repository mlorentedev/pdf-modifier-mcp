"""PDF text replacement engine with style preservation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import fitz

from .exceptions import PDFReadError, PDFWriteError
from .models import ModificationResult, ReplacementSpec

logger = logging.getLogger(__name__)


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

    def __init__(self, input_path: str | Path, output_path: str | Path) -> None:
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self._doc: fitz.Document | None = None
        self._warnings: list[str] = []

    def __enter__(self) -> PDFModifier:
        try:
            self._doc = fitz.open(self.input_path)
        except Exception as e:
            raise PDFReadError(f"Cannot open PDF: {e}", {"path": str(self.input_path)}) from e
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
        if not self._doc:
            try:
                self._doc = fitz.open(self.input_path)
            except Exception as e:
                raise PDFReadError(f"Cannot open PDF: {e}") from e

        total_replacements = 0
        pages_modified: set[int] = set()

        try:
            for page_num, page in enumerate(self._doc):
                items = self._collect_replacements(page, spec.replacements, spec.use_regex)

                if not items:
                    continue

                pages_modified.add(page_num)

                # Batch: add all redaction annotations first
                for item in items:
                    page.add_redact_annot(item["bbox"], fill=(1, 1, 1))

                # Single apply_redactions() call per page (efficient)
                page.apply_redactions()

                # Insert all replacement text
                for item in items:
                    self._insert_replacement(page, item)
                    total_replacements += 1

            self._doc.save(str(self.output_path))
            logger.info(
                "Saved %s with %d replacements across %d pages",
                self.output_path,
                total_replacements,
                len(pages_modified),
            )

        except Exception as e:
            raise PDFWriteError(f"Failed to process/save PDF: {e}") from e
        finally:
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
        replacements: dict[str, str],
        use_regex: bool,
    ) -> list[dict[str, Any]]:
        """Scan page and collect items to replace."""
        items: list[dict[str, Any]] = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    original = span["text"]

                    for target, replacement_raw in replacements.items():
                        match_found = False
                        if use_regex:
                            if re.search(target, text):
                                match_found = True
                        elif target in text:
                            match_found = True

                        if match_found:
                            # Parse replacement for URL
                            replacement_text = replacement_raw
                            url = None

                            if "|" in replacement_raw:
                                candidate_text, candidate_url = replacement_raw.rsplit("|", 1)
                                candidate_url = candidate_url.strip()

                                if candidate_url == "void(0)" or candidate_url.startswith(
                                    ("http://", "https://", "mailto:", "javascript:")
                                ):
                                    replacement_text = candidate_text
                                    url = (
                                        "javascript:void(0)"
                                        if candidate_url == "void(0)"
                                        else candidate_url
                                    )

                            font_code, font_std = self._get_font_properties(span["font"])

                            if use_regex:
                                new_text = re.sub(target, replacement_text, original)
                            else:
                                new_text = original.replace(target, replacement_text)

                            items.append(
                                {
                                    "bbox": span["bbox"],
                                    "origin": span["origin"],
                                    "text": new_text,
                                    "url": url,
                                    "font_code": font_code,
                                    "font_std": font_std,
                                    "size": span["size"],
                                    "color": span["color"],
                                }
                            )
                            break  # One replacement per span

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
                self._warnings.append(f"Could not add link for '{item['text']}': {e}")
