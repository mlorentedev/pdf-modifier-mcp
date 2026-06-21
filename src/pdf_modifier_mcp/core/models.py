"""Pydantic models for PDF Modifier I/O."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

# --- Input Models ---


class ReplacementSpec(BaseModel):
    """Specification for text replacements."""

    replacements: dict[str, str] = Field(
        min_length=1,
        max_length=100,
        description="Map of 'old text' -> 'new text'. Use 'text|URL' for hyperlinks.",
    )
    use_regex: bool = Field(default=False, description="Treat keys as regex patterns")
    compiled_patterns: dict[str, re.Pattern[str]] | None = Field(
        default=None, description="Pre-compiled regex patterns (internal use)", exclude=True
    )

    @model_validator(mode="after")
    def validate_regex_patterns(self) -> ReplacementSpec:
        """Validate regex patterns if use_regex is enabled and pre-compile them."""
        if self.use_regex:
            compiled = {}
            for pattern in self.replacements:
                try:
                    compiled[pattern] = re.compile(pattern)
                except re.error as e:
                    raise ValueError(f"Invalid regex '{pattern}': {e}") from e
            self.compiled_patterns = compiled
        return self


# --- Output Models ---


class TextElement(BaseModel):
    """Single text span extracted from PDF."""

    text: str
    bbox: tuple[float, float, float, float] = Field(description="Bounding box (x0, y0, x1, y1)")
    origin: tuple[float, float] = Field(description="Text origin point (x, y)")
    font: str
    size: float
    color: int


class PageStructure(BaseModel):
    """Structural analysis of a single PDF page."""

    page: int = Field(ge=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    elements: list[TextElement]


class PDFStructure(BaseModel):
    """Complete PDF structure analysis."""

    success: bool = True
    file_path: str
    total_pages: int
    pages: list[PageStructure]


class FontMatch(BaseModel):
    """Font inspection result for a matched term."""

    page: int
    term: str
    context: str = Field(description="Surrounding text (truncated)")
    font: str
    size: float
    origin: tuple[float, float]


class FontInspectionResult(BaseModel):
    """Results from font inspection."""

    success: bool = True
    file_path: str
    terms_searched: list[str]
    matches: list[FontMatch]
    total_matches: int


class Hyperlink(BaseModel):
    """Details of a hyperlink found in a PDF."""

    page: int
    uri: str
    bbox: tuple[float, float, float, float]
    text: str | None = Field(None, description="Text covered by the link area (if available)")


class HyperlinkInventory(BaseModel):
    """Complete inventory of hyperlinks in a PDF."""

    success: bool = True
    file_path: str
    total_links: int
    links: list[Hyperlink]


class ModificationResult(BaseModel):
    """Result of PDF modification operation."""

    success: bool
    input_path: str
    output_path: str
    replacements_made: int
    pages_modified: int
    warnings: list[str] = Field(default_factory=list)


class BatchResult(BaseModel):
    """Result of batch PDF modification."""

    total_files: int
    successful: int
    failed: int
    results: list[ModificationResult]
    errors: list[dict[str, str]] = Field(default_factory=list)


# --- Font Models ---


class FontProperties(BaseModel):
    """Resolved font properties for text insertion.

    Combines the font identifier (Base 14 code or custom alias) with
    style flags and an optional custom font file path.

    Example:
        >>> props = FontProperties(fontname="helv", is_bold=False)
        >>> props = FontProperties(fontname="arial", fontfile="/path/to/arial.ttf", is_bold=True)
    """

    fontname: str = Field(description="Font identifier (Base 14 code or custom alias)")
    fontfile: str | None = Field(
        default=None,
        description="Path to a custom TTF/OTF font file (None for Base 14 fonts)",
    )
    is_bold: bool = Field(default=False, description="Whether the font is bold")
    is_italic: bool = Field(default=False, description="Whether the font is italic")
    is_serif: bool = Field(default=False, description="Whether the font is serif")
    is_monospaced: bool = Field(default=False, description="Whether the font is monospaced")
    embed: bool = Field(
        default=True,
        description="Whether the font should be embedded in the output PDF",
    )

    @model_validator(mode="after")
    def validate_fontfile(self) -> FontProperties:
        """Validate that fontfile exists when provided."""
        if self.fontfile is not None and not Path(self.fontfile).exists():
            raise ValueError(f"font file does not exist: {self.fontfile}")
        return self


class EmbeddedFontInfo(BaseModel):
    """Metadata and buffer for an embedded font in a PDF.

    Example:
        >>> info = EmbeddedFontInfo(
        ...     name="Arial Regular",
        ...     type="TrueType",
        ...     subtype="ttf",
        ...     buffer=b"...",
        ...     page_numbers=[1, 2],
        ... )
    """

    name: str = Field(description="Human-readable font name")
    type: str = Field(description="Font type (TrueType, Type1, Type0, CID, etc.)")
    subtype: str = Field(description="Font subtype (ttf, helv, etc.)")
    buffer: bytes = Field(description="Raw font file bytes")
    page_numbers: list[int] = Field(
        default_factory=list,
        description="Page numbers where this font appears",
    )
