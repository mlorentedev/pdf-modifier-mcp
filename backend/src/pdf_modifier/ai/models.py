"""AI-specific Pydantic models for NaN Cloud responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DetectField(BaseModel):
    """A detected field from document analysis."""

    name: str = Field(description="Field name (e.g., 'invoice_number', 'date')")
    value: str = Field(description="Extracted value")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence (0-1)")
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None


class DetectResult(BaseModel):
    """Result of AI-powered field detection."""

    success: bool = True
    fields: list[DetectField] = Field(default_factory=list)
    document_type: str | None = None
    model: str = Field(description="Model used for detection")


class ClassificationAlternative(BaseModel):
    """Alternative classification with confidence."""

    type: str = Field(description="Alternative document type")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")


class ClassifyResult(BaseModel):
    """Result of document classification."""

    success: bool = True
    document_type: str = Field(description="Classified type (invoice, contract, CV, etc.)")
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: list[ClassificationAlternative] = Field(
        default_factory=list,
        description="Alternative classifications with confidence scores",
    )
    model: str = Field(description="Model used for classification")


class RedactItem(BaseModel):
    """A PII item found for redaction."""

    pii_type: str = Field(description="Type of PII (email, phone, nif, credit_card, etc.)")
    value: str = Field(description="The PII value found")
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_replacement: str = Field(
        default="[REDACTED]", description="Suggested replacement text"
    )


class RedactResult(BaseModel):
    """Result of PII redaction detection."""

    success: bool = True
    items: list[RedactItem] = Field(default_factory=list)
    model: str = Field(description="Model used for redaction")


class EmbeddingResult(BaseModel):
    """Result of text embedding."""

    success: bool = True
    model: str
    dimensions: int
    embeddings: list[list[float]] = Field(description="List of embedding vectors")


class EmbeddingQuery(BaseModel):
    """Query for generating embeddings."""

    model: str = Field(default="qwen3-embedding")
    input: str | list[str] = Field(..., description="Text or list of texts to embed")


# --- Vision Models (VIS-001) ---


class OCRPageResult(BaseModel):
    """OCR result for a single page."""

    page: int = Field(description="Page number (0-indexed)")
    text: str = Field(description="Extracted text")
    confidence: float = Field(ge=0.0, le=1.0, description="OCR confidence")
    has_text_layer: bool = Field(description="Whether page had existing text layer")


class OCRResult(BaseModel):
    """Result of OCR extraction."""

    success: bool = True
    pages: list[OCRPageResult] = Field(default_factory=list)
    total_pages: int = Field(description="Total pages processed")
    model: str = Field(description="Model used for OCR")


class SignaturePosition(BaseModel):
    """Position of a detected signature."""

    page: int = Field(description="Page number (0-indexed)")
    bbox: tuple[float, float, float, float] = Field(description="Bounding box (x0, y0, x1, y1)")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    signature_type: str = Field(
        default="unknown",
        description="Type: handwritten, digital, stamp",
    )


class SignatureDetectionResult(BaseModel):
    """Result of signature detection."""

    success: bool = True
    signatures: list[SignaturePosition] = Field(default_factory=list)
    total_found: int = Field(description="Total signatures found")
    model: str = Field(description="Model used for detection")


class PDFDifference(BaseModel):
    """A single difference between two PDFs."""

    page: int = Field(description="Page number (0-indexed)")
    difference_type: str = Field(description="Type: text_change, added, removed, formatting")
    description: str = Field(description="Human-readable description")
    old_value: str | None = Field(default=None, description="Original value")
    new_value: str | None = Field(default=None, description="New value")
    bbox: tuple[float, float, float, float] | None = None


class PDFComparisonResult(BaseModel):
    """Result of PDF comparison."""

    success: bool = True
    differences: list[PDFDifference] = Field(default_factory=list)
    total_differences: int = Field(description="Total differences found")
    identical: bool = Field(description="Whether PDFs are identical")
    model: str = Field(description="Model used for comparison")
