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
