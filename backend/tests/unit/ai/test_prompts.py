"""Tests for prompt template rendering."""

from __future__ import annotations

from pdf_modifier.ai.prompts import render_prompt


class TestPromptRendering:
    """Prompt template tests."""

    def test_detect_fields_template(self) -> None:
        result = render_prompt(
            "detect_fields.j2",
            pdf_text="Invoice #12345 dated 2024-01-15 for $100",
        )
        assert "Invoice #12345" in result or "Invoice" in result
        assert "pdf_text" not in result  # Should be substituted
        assert "detect_fields" in result.lower() or "document" in result.lower()

    def test_classify_template(self) -> None:
        result = render_prompt(
            "classify_doc.j2",
            pdf_text="This is an invoice for services rendered",
        )
        assert "invoice" in result
        assert "pdf_text" not in result

    def test_redact_pii_template(self) -> None:
        result = render_prompt(
            "redact_pii.j2",
            pdf_text="Contact: test@example.com, Phone: 555-1234",
        )
        assert "email" in result.lower()
        assert "pdf_text" not in result

    def test_template_variables_substituted(self) -> None:
        """Ensure {{ pdf_text }} is replaced, not left as Jinja syntax."""
        result = render_prompt("detect_fields.j2", pdf_text="Hello World")
        # The template content should contain "Hello World"
        assert "Hello World" in result
