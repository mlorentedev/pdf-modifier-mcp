"""Tests for PDFModifier internal methods."""

from pdf_modifier_mcp.core import PDFModifier


class TestPDFModifier:
    """Tests for PDFModifier internal methods."""

    def test_get_font_properties_helvetica(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("ArialMT")
        assert code == "helv"
        assert name == "Helvetica"

    def test_get_font_properties_bold(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("Arial-BoldMT")
        assert code == "HeBo"
        assert name == "Helvetica-Bold"

    def test_get_font_properties_courier(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("CourierNew")
        assert code == "Cour"
        assert name == "Courier"

    def test_convert_color_int(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color(16711680)  # Red: 0xFF0000
        assert (r, g, b) == (1.0, 0.0, 0.0)

    def test_convert_color_tuple(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color((0.5, 0.5, 0.5))
        assert (r, g, b) == (0.5, 0.5, 0.5)

    def test_convert_color_invalid(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color("invalid")  # type: ignore[arg-type]
        assert (r, g, b) == (0.0, 0.0, 0.0)
