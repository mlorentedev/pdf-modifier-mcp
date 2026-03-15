"""Core business logic for PDF modification."""

from __future__ import annotations

from .analyzer import PDFAnalyzer
from .exceptions import (
    FileSizeExceededError,
    InvalidPatternError,
    PDFModifierError,
    PDFNotFoundError,
    PDFPasswordError,
    PDFReadError,
    PDFWriteError,
)
from .models import (
    BatchResult,
    FontInspectionResult,
    FontMatch,
    ModificationResult,
    PageStructure,
    PDFStructure,
    ReplacementSpec,
    TextElement,
)
from .modifier import PDFModifier, batch_process

__all__ = [
    # Classes
    "PDFAnalyzer",
    "PDFModifier",
    # Functions
    "batch_process",
    # Models
    "BatchResult",
    "FontInspectionResult",
    "FontMatch",
    "ModificationResult",
    "PageStructure",
    "PDFStructure",
    "ReplacementSpec",
    "TextElement",
    # Exceptions
    "FileSizeExceededError",
    "InvalidPatternError",
    "PDFModifierError",
    "PDFNotFoundError",
    "PDFPasswordError",
    "PDFReadError",
    "PDFWriteError",
]
