"""Tests for AI models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdf_modifier_mcp.ai.models import (
    ClassificationAlternative,
    ClassifyResult,
    DetectField,
    DetectResult,
    RedactItem,
    RedactResult,
)


class TestDetectField:
    """DetectField model tests."""

    def test_valid_field(self) -> None:
        field = DetectField(name="invoice_number", value="INV-001", confidence=0.95)
        assert field.name == "invoice_number"
        assert field.value == "INV-001"
        assert field.confidence == 0.95

    def test_field_with_optional_fields(self) -> None:
        field = DetectField(
            name="date",
            value="2024-01-15",
            confidence=0.9,
            page=1,
            bbox=(10.0, 20.0, 50.0, 30.0),
        )
        assert field.page == 1
        assert field.bbox == (10.0, 20.0, 50.0, 30.0)

    def test_confidence_validation_below(self) -> None:
        with pytest.raises(ValidationError):
            DetectField(name="test", value="v", confidence=-0.1, page=None, bbox=None)

    def test_confidence_validation_above(self) -> None:
        with pytest.raises(ValidationError):
            DetectField(name="test", value="v", confidence=1.5, page=None, bbox=None)


class TestDetectResult:
    """DetectResult model tests."""

    def test_empty_result(self) -> None:
        result = DetectResult(model="mimo-v2.5")
        assert result.success is True
        assert result.fields == []

    def test_result_with_fields(self) -> None:
        fields = [
            DetectField(
                name="invoice",
                value="INV-001",
                confidence=0.95,
                page=None,
                bbox=None,
            ),
        ]
        result = DetectResult(fields=fields, document_type="invoice", model="mimo-v2.5")
        assert len(result.fields) == 1
        assert result.document_type == "invoice"


class TestClassifyResult:
    """ClassifyResult model tests."""

    def test_valid_classification(self) -> None:
        result = ClassifyResult(
            document_type="invoice",
            confidence=0.92,
            alternatives=[ClassificationAlternative(type="receipt", confidence=0.05)],
            model="qwen3.6",
        )
        assert result.document_type == "invoice"
        assert len(result.alternatives) == 1

    def test_confidence_validation(self) -> None:
        with pytest.raises(ValidationError):
            ClassifyResult(document_type="test", confidence=1.5, model="test")


class TestRedactResult:
    """RedactResult model tests."""

    def test_valid_redaction(self) -> None:
        items = [
            RedactItem(
                pii_type="email",
                value="test@example.com",
                confidence=0.98,
                suggested_replacement="[REDACTED]",
            )
        ]
        result = RedactResult(items=items, model="mimo-v2.5")
        assert len(result.items) == 1
        assert result.items[0].pii_type == "email"

    def test_empty_result(self) -> None:
        result = RedactResult(model="mimo-v2.5")
        assert result.items == []
