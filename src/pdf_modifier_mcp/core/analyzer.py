"""PDF structure analysis and text extraction."""

from __future__ import annotations

from pathlib import Path

import fitz

from ..logger import setup_logging
from .exceptions import PDFPasswordError, PDFReadError
from .models import (
    FontInspectionResult,
    FontMatch,
    Hyperlink,
    HyperlinkInventory,
    PageStructure,
    PDFStructure,
    TextElement,
)

logger = setup_logging(__name__)


class PDFAnalyzer:
    """
    PDF structure analysis and text extraction.

    Provides methods for:
    - Extracting complete document structure as Pydantic models
    - Plain text extraction
    - Font property inspection

    Example:
        >>> analyzer = PDFAnalyzer("document.pdf")
        >>> structure = analyzer.get_structure()
        >>> print(structure.total_pages)

        >>> result = analyzer.inspect_fonts(["Invoice", "Total"])
        >>> print(result.total_matches)
    """

    def __init__(self, file_path: str | Path, password: str | None = None) -> None:
        self.file_path = Path(file_path)
        self.password = password

    def _open_doc(self) -> fitz.Document:
        """Safely open the document with password authentication if required."""
        try:
            doc = fitz.open(self.file_path)
            if doc.needs_pass:
                if not self.password:
                    raise PDFPasswordError("PDF is password protected. Please provide a password.")
                if not doc.authenticate(self.password):
                    raise PDFPasswordError("Incorrect password provided for the PDF.")
            return doc
        except PDFPasswordError:
            raise
        except Exception as e:
            raise PDFReadError(f"Failed to open PDF: {e}") from e

    def get_structure(self) -> PDFStructure:
        """
        Extract complete PDF structure as typed model.

        Returns page dimensions, text elements with positions,
        fonts, sizes, and colors.

        Returns:
            PDFStructure containing all pages and elements.

        Raises:
            PDFReadError: If the PDF cannot be read.
            PDFPasswordError: If password is required but not provided or incorrect.
        """
        try:
            with self._open_doc() as doc:
                pages = []
                for page_num, page in enumerate(doc, start=1):
                    elements = []
                    blocks = page.get_text("dict")["blocks"]

                    for block in blocks:
                        if "lines" not in block:
                            continue
                        for line in block["lines"]:
                            for span in line["spans"]:
                                elements.append(
                                    TextElement(
                                        text=span["text"],
                                        bbox=tuple(span["bbox"]),  # type: ignore[arg-type]
                                        origin=tuple(span["origin"]),  # type: ignore[arg-type]
                                        font=span["font"],
                                        size=span["size"],
                                        color=span["color"],
                                    )
                                )

                    pages.append(
                        PageStructure(
                            page=page_num,
                            width=page.rect.width,
                            height=page.rect.height,
                            elements=elements,
                        )
                    )

                return PDFStructure(
                    file_path=str(self.file_path),
                    total_pages=len(pages),
                    pages=pages,
                )

        except Exception as e:
            raise PDFReadError(f"Failed to analyze PDF: {e}", {"path": str(self.file_path)}) from e

    def extract_text(self) -> str:
        """
        Extract plain text from all pages.

        Returns:
            Formatted string with page separators.

        Raises:
            PDFReadError: If the PDF cannot be read.
            PDFPasswordError: If password is required but not provided or incorrect.
        """
        try:
            with self._open_doc() as doc:
                output = [f"Analyzed {self.file_path} with {len(doc)} pages.\n"]
                for page_num, page in enumerate(doc, start=1):
                    output.append(f"--- Page {page_num} ---")
                    output.append(page.get_text("text"))
                    output.append("-" * 20)
                return "\n".join(output)
        except PDFPasswordError:
            raise
        except Exception as e:
            raise PDFReadError(f"Failed to extract text: {e}") from e

    def inspect_fonts(self, terms: list[str]) -> FontInspectionResult:
        """
        Search for terms and report their font properties.

        Useful for ensuring style matching before replacements.

        Args:
            terms: List of text strings to search for.

        Returns:
            FontInspectionResult with all matches.

        Raises:
            PDFReadError: If the PDF cannot be read.
            PDFPasswordError: If password is required but not provided or incorrect.
        """
        matches: list[FontMatch] = []

        try:
            with self._open_doc() as doc:
                for page_num, page in enumerate(doc, start=1):
                    blocks = page.get_text("dict")["blocks"]

                    for block in blocks:
                        if "lines" not in block:
                            continue
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"]
                                for term in terms:
                                    if term in text:
                                        matches.append(
                                            FontMatch(
                                                page=page_num,
                                                term=term,
                                                context=text[:100],
                                                font=span["font"],
                                                size=span["size"],
                                                origin=tuple(span["origin"]),  # type: ignore[arg-type]
                                            )
                                        )

            return FontInspectionResult(
                file_path=str(self.file_path),
                terms_searched=terms,
                matches=matches,
                total_matches=len(matches),
            )

        except Exception as e:
            raise PDFReadError(f"Failed to inspect fonts: {e}") from e

    def get_hyperlinks(self) -> HyperlinkInventory:
        """
        Extract all hyperlinks from the document.

        Returns:
            HyperlinkInventory containing all found URIs and their locations.

        Raises:
            PDFReadError: If the PDF cannot be read.
            PDFPasswordError: If password is required but not provided or incorrect.
        """
        links: list[Hyperlink] = []

        try:
            with self._open_doc() as doc:
                for page_num, page in enumerate(doc, start=1):
                    for link in page.get_links():
                        if "uri" in link:
                            # Try to find text under the link's bbox
                            text = page.get_textbox(link["from"])
                            links.append(
                                Hyperlink(
                                    page=page_num,
                                    uri=link["uri"],
                                    bbox=tuple(link["from"]),  # type: ignore[arg-type]
                                    text=text.strip() if text else None,
                                )
                            )

            return HyperlinkInventory(
                file_path=str(self.file_path),
                total_links=len(links),
                links=links,
            )

        except Exception as e:
            raise PDFReadError(f"Failed to extract hyperlinks: {e}") from e
