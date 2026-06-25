"""Vision service — orchestrates vision.py + AI client for OCR, signatures, comparison.

This is the business logic layer that sits between the web routes and the
low-level vision.py / AI client. It handles:
- PDF → images → AI API calls
- Feature flag gating
- Result parsing and validation

Example:
    >>> async with VisionService(client, router, throttle) as svc:
    ...     result = await svc.ocr(session_pdf_path, pages=[0, 1])
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..logger import setup_logging
from .exceptions import AIVisionError
from .models import (
    OCRPageResult,
    OCRResult,
    PDFComparisonResult,
    PDFDifference,
    SignatureDetectionResult,
    SignaturePosition,
)
from .router import TaskType
from .vision import encode_image_base64, get_pdf_page_count, pdf_page_to_image

if TYPE_CHECKING:
    from .client import NaNClient
    from .router import ModelRouter
    from .throttle import Throttle

logger = setup_logging(__name__)

# Prompt templates for vision tasks
OCR_SYSTEM_PROMPT = (
    "You are an OCR assistant. Extract ALL text from the provided image. "
    "Return ONLY the extracted text, nothing else. "
    "Preserve line breaks and spacing."
)

SIGNATURE_SYSTEM_PROMPT = (
    "You are a signature detection assistant. Analyze the image and identify "
    "any signatures, stamps, or handwritten marks. Return a JSON array of "
    'objects with keys: "page" (int), "bbox" (array of 4 floats: x0,y0,x1,y1), '
    '"confidence" (float 0-1), '
    '"signature_type" (string: handwritten/digital/stamp). '
    "If no signatures found, return an empty array."
)

COMPARISON_SYSTEM_PROMPT = (
    "You are a PDF comparison assistant. Compare the two provided images and "
    "identify ALL differences. Return a JSON array of objects with keys: "
    '"page" (int), '
    '"difference_type" (string: text_change/added/removed/formatting), '
    '"description" (string), "old_value" (string or null), '
    '"new_value" (string or null). '
    "If identical, return an empty array."
)


class VisionService:
    """Orchestrates vision capabilities with AI client.

    Args:
        client: NaN Cloud API client.
        router: Model router for selecting vision models.
        throttle: Rate limiter for AI requests.

    Example:
        >>> async with VisionService(client, router, throttle) as svc:
        ...     ocr_result = await ocr(some_pdf)
    """

    def __init__(
        self,
        client: NaNClient,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        self._client = client
        self._router = router
        self._throttle = throttle

    async def __aenter__(self) -> VisionService:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    def _get_vision_model(self) -> str:
        """Get the vision model from the router."""
        return self._router.get_model(TaskType.VISION)

    async def ocr(
        self,
        pdf_path: str | Path,
        pages: list[int] | None = None,
        dpi: int = 150,
    ) -> OCRResult:
        """Extract text from scanned PDF via AI vision.

        Args:
            pdf_path: Path to the PDF file.
            pages: Specific pages to OCR (0-indexed). None = all pages.
            dpi: Image resolution for conversion.

        Returns:
            OCRResult with extracted text per page.

        Raises:
            AIVisionError: If OCR fails.
        """
        pdf_path = Path(pdf_path)
        model = self._get_vision_model()
        total_pages = get_pdf_page_count(pdf_path)

        if pages is None:
            pages = list(range(total_pages))

        results: list[OCRPageResult] = []

        for page_num in pages:
            image_bytes = pdf_page_to_image(pdf_path, page_num, dpi=dpi)
            data_uri = encode_image_base64(image_bytes)

            async with self._throttle.acquire():
                try:
                    messages: list[dict[str, Any]] = [
                        {"role": "system", "content": OCR_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_uri},
                                },
                                {
                                    "type": "text",
                                    "text": ("Extract all text from " "this document image."),
                                },
                            ],
                        },
                    ]
                    response = await self._client.chat(
                        model=model,
                        messages=messages,
                    )

                    content = response["choices"][0]["message"]["content"]
                    results.append(
                        OCRPageResult(
                            page=page_num,
                            text=content.strip(),
                            confidence=0.9,
                            has_text_layer=False,
                        )
                    )
                    logger.debug("OCR completed for page %d", page_num)

                except Exception as e:
                    logger.error("OCR failed for page %d: %s", page_num, e)
                    raise AIVisionError(f"OCR failed for page {page_num}: {e}") from e

        return OCRResult(
            pages=results,
            total_pages=total_pages,
            model=model,
        )

    async def detect_signatures(
        self,
        pdf_path: str | Path,
        pages: list[int] | None = None,
        dpi: int = 150,
    ) -> SignatureDetectionResult:
        """Detect signatures in PDF via AI vision.

        Args:
            pdf_path: Path to the PDF file.
            pages: Specific pages to analyze (0-indexed). None = all.
            dpi: Image resolution for conversion.

        Returns:
            SignatureDetectionResult with detected signatures.

        Raises:
            AIVisionError: If detection fails.
        """
        pdf_path = Path(pdf_path)
        model = self._get_vision_model()
        total_pages = get_pdf_page_count(pdf_path)

        if pages is None:
            pages = list(range(total_pages))

        all_signatures: list[SignaturePosition] = []

        for page_num in pages:
            image_bytes = pdf_page_to_image(pdf_path, page_num, dpi=dpi)
            data_uri = encode_image_base64(image_bytes)

            async with self._throttle.acquire():
                try:
                    sig_messages: list[dict[str, Any]] = [
                        {
                            "role": "system",
                            "content": SIGNATURE_SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_uri},
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Detect any signatures, " "stamps, or handwritten marks."
                                    ),
                                },
                            ],
                        },
                    ]
                    response = await self._client.chat(
                        model=model,
                        messages=sig_messages,
                    )

                    content = response["choices"][0]["message"]["content"]
                    signatures_data = self._parse_json_array(content)

                    for sig in signatures_data:
                        all_signatures.append(
                            SignaturePosition(
                                page=sig.get("page", page_num),
                                bbox=tuple(sig.get("bbox", [0, 0, 0, 0])),
                                confidence=sig.get("confidence", 0.5),
                                signature_type=sig.get("signature_type", "unknown"),
                            )
                        )

                    logger.debug(
                        "Signature detection for page %d: %d found",
                        page_num,
                        len(signatures_data),
                    )

                except Exception as e:
                    logger.error(
                        "Signature detection failed for page %d: %s",
                        page_num,
                        e,
                    )
                    raise AIVisionError(f"Signature detection failed: {e}") from e

        return SignatureDetectionResult(
            signatures=all_signatures,
            total_found=len(all_signatures),
            model=model,
        )

    async def compare(
        self,
        pdf_path_a: str | Path,
        pdf_path_b: str | Path,
        pages: list[int] | None = None,
        dpi: int = 150,
    ) -> PDFComparisonResult:
        """Compare two PDFs and find differences.

        Args:
            pdf_path_a: Path to the first PDF.
            pdf_path_b: Path to the second PDF.
            pages: Pages to compare (0-indexed). None = all common.
            dpi: Image resolution for conversion.

        Returns:
            PDFComparisonResult with found differences.

        Raises:
            AIVisionError: If comparison fails.
        """
        pdf_path_a = Path(pdf_path_a)
        pdf_path_b = Path(pdf_path_b)
        model = self._get_vision_model()

        count_a = get_pdf_page_count(pdf_path_a)
        count_b = get_pdf_page_count(pdf_path_b)

        if pages is None:
            pages = list(range(min(count_a, count_b)))

        all_differences: list[PDFDifference] = []

        for page_num in pages:
            image_a = pdf_page_to_image(pdf_path_a, page_num, dpi=dpi)
            image_b = pdf_page_to_image(pdf_path_b, page_num, dpi=dpi)

            data_uri_a = encode_image_base64(image_a)
            data_uri_b = encode_image_base64(image_b)

            async with self._throttle.acquire():
                try:
                    cmp_messages: list[dict[str, Any]] = [
                        {
                            "role": "system",
                            "content": COMPARISON_SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_uri_a},
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_uri_b},
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Compare these two document "
                                        "images. The first is the "
                                        "original, the second is the "
                                        "modified version. "
                                        "List ALL differences."
                                    ),
                                },
                            ],
                        },
                    ]
                    response = await self._client.chat(
                        model=model,
                        messages=cmp_messages,
                    )

                    content = response["choices"][0]["message"]["content"]
                    diffs_data = self._parse_json_array(content)

                    for diff in diffs_data:
                        all_differences.append(
                            PDFDifference(
                                page=diff.get("page", page_num),
                                difference_type=diff.get("difference_type", "text_change"),
                                description=diff.get("description", ""),
                                old_value=diff.get("old_value"),
                                new_value=diff.get("new_value"),
                                bbox=(tuple(diff["bbox"]) if diff.get("bbox") else None),
                            )
                        )

                    logger.debug(
                        "PDF comparison for page %d: %d differences",
                        page_num,
                        len(diffs_data),
                    )

                except Exception as e:
                    logger.error(
                        "PDF comparison failed for page %d: %s",
                        page_num,
                        e,
                    )
                    raise AIVisionError(f"PDF comparison failed: {e}") from e

        return PDFComparisonResult(
            differences=all_differences,
            total_differences=len(all_differences),
            identical=len(all_differences) == 0,
            model=model,
        )

    @staticmethod
    def _parse_json_array(content: str) -> list[dict[str, Any]]:
        """Parse JSON array from AI response, handling code blocks."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [line for line in lines[1:] if not line.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            return [result] if isinstance(result, dict) else []
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse AI response as JSON: %s",
                cleaned[:100],
            )
            return []
