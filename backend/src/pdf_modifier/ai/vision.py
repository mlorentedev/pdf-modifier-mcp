"""AI vision capabilities for PDF image conversion and analysis.

Provides PDF-to-image conversion, Base64 encoding, and image manipulation
for use with AI vision models (mimo-v2.5).

Example:
    >>> from pdf_modifier.ai.vision import pdf_page_to_image, encode_image_base64
    >>> image_bytes = pdf_page_to_image("document.pdf", page_num=0)
    >>> data_uri = encode_image_base64(image_bytes)
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import fitz  # PyMuPDF

from ..logger import setup_logging

logger = setup_logging(__name__)

DEFAULT_DPI = 150
DEFAULT_QUALITY = 85


class ImageFormat(StrEnum):
    """Supported image output formats."""

    PNG = "png"
    JPEG = "jpeg"


@dataclass
class ImageOptions:
    """Options for image conversion.

    Attributes:
        dpi: Resolution in dots per inch (72-300). Default: 150.
        format: Output image format. Default: PNG.
        quality: JPEG quality (1-100). Default: 85. Ignored for PNG.
    """

    dpi: int = DEFAULT_DPI
    format: ImageFormat = ImageFormat.PNG
    quality: int = DEFAULT_QUALITY

    def __post_init__(self) -> None:
        """Validate options after initialization."""
        if not 72 <= self.dpi <= 300:
            raise ValueError(f"dpi must be between 72 and 300, got {self.dpi}")
        if not 1 <= self.quality <= 100:
            raise ValueError(f"quality must be between 1 and 100, got {self.quality}")


def pdf_page_to_image(
    pdf_path: str | Path,
    page_num: int = 0,
    dpi: int = DEFAULT_DPI,
    options: ImageOptions | None = None,
) -> bytes:
    """Convert a PDF page to image bytes.

    Args:
        pdf_path: Path to the PDF file.
        page_num: Page number (0-indexed).
        dpi: Resolution in dots per inch. Ignored if options provided.
        options: Optional ImageOptions for fine-grained control.

    Returns:
        Image bytes in the specified format (default: PNG).

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        IndexError: If page_num is out of range.

    Example:
        >>> image_bytes = pdf_page_to_image("doc.pdf", page_num=0, dpi=150)
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Use options if provided, otherwise create from dpi
    if options is None:
        options = ImageOptions(dpi=dpi)

    doc = fitz.open(str(pdf_path))
    try:
        if page_num < 0 or page_num >= len(doc):
            raise IndexError(f"Page {page_num} out of range (0-{len(doc) - 1})")

        page = doc[page_num]

        # Create pixmap with specified DPI
        zoom = options.dpi / 72  # 72 is the default PDF DPI
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)

        # Convert to bytes
        if options.format == ImageFormat.PNG:
            image_bytes: bytes = pix.tobytes("png")
        elif options.format == ImageFormat.JPEG:
            image_bytes = pix.tobytes("jpeg", jpg_quality=options.quality)
        else:
            image_bytes = pix.tobytes("png")

        logger.debug(
            "Converted page %d to %s image (%d bytes, %d DPI)",
            page_num,
            options.format,
            len(image_bytes),
            options.dpi,
        )
        return image_bytes

    finally:
        doc.close()


def encode_image_base64(
    image_bytes: bytes,
    format_hint: str = "png",
) -> str:
    """Encode image bytes to Base64 data URI.

    Args:
        image_bytes: Raw image bytes.
        format_hint: MIME type hint (e.g., 'png', 'jpeg'). Default: 'png'.

    Returns:
        Data URI string: "data:image/{format};base64,{data}"

    Example:
        >>> data_uri = encode_image_base64(image_bytes, format_hint="png")
        >>> # Returns: "data:image/png;base64,iVBORw0KGgo..."
    """
    b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/{format_hint};base64,{b64_encoded}"

    logger.debug(
        "Encoded %d bytes to Base64 data URI (%d chars)",
        len(image_bytes),
        len(data_uri),
    )
    return data_uri


def pdf_page_to_data_uri(
    pdf_path: str | Path,
    page_num: int = 0,
    dpi: int = DEFAULT_DPI,
    options: ImageOptions | None = None,
) -> str:
    """Convert a PDF page directly to Base64 data URI.

    Convenience function combining pdf_page_to_image and encode_image_base64.

    Args:
        pdf_path: Path to the PDF file.
        page_num: Page number (0-indexed).
        dpi: Resolution in dots per inch.
        options: Optional ImageOptions for fine-grained control.

    Returns:
        Data URI string ready for AI API input.

    Example:
        >>> data_uri = pdf_page_to_data_uri("doc.pdf", page_num=0)
        >>> # Use in API: {"image": data_uri}
    """
    if options is None:
        options = ImageOptions(dpi=dpi)

    image_bytes = pdf_page_to_image(pdf_path, page_num, options=options)
    return encode_image_base64(image_bytes, format_hint=options.format)


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """Get the number of pages in a PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Number of pages.

    Example:
        >>> count = get_pdf_page_count("doc.pdf")
        >>> print(f"PDF has {count} pages")
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    try:
        return len(doc)
    finally:
        doc.close()
