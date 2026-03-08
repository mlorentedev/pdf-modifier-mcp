"""Pydantic models for PDF Modifier I/O."""

from __future__ import annotations

import re

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


class ModificationResult(BaseModel):
    """Result of PDF modification operation."""

    success: bool
    input_path: str
    output_path: str
    replacements_made: int
    pages_modified: int
    warnings: list[str] = Field(default_factory=list)
