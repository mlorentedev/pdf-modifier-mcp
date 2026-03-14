"""Core business logic for PDF modification."""

from __future__ import annotations

from .analyzer import PDFAnalyzer
from .exceptions import (
    InvalidPatternError,
    PDFModifierError,
    PDFNotFoundError,
    PDFPasswordError,
    PDFReadError,
    PDFWriteError,
)
from .models import (
    FontInspectionResult,
    FontMatch,
    ModificationResult,
    PageStructure,
    PDFStructure,
    ReplacementSpec,
    TextElement,
)
from .modifier import PDFModifier

__all__ = [
    # Classes
    "PDFAnalyzer",
    "PDFModifier",
    # Models
    "FontInspectionResult",
    "FontMatch",
    "ModificationResult",
    "PageStructure",
    "PDFStructure",
    "ReplacementSpec",
    "TextElement",
    # Exceptions
    "InvalidPatternError",
    "PDFModifierError",
    "PDFNotFoundError",
    "PDFPasswordError",
    "PDFReadError",
    "PDFWriteError",
]
