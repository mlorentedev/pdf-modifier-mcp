"""
MCP (Model Context Protocol) server for PDF Modifier.

Provides LLM-friendly tools for PDF analysis and modification.
Uses FastMCP with stdio transport for Claude Desktop integration.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastmcp import FastMCP

from ..core.analyzer import PDFAnalyzer
from ..core.exceptions import PDFModifierError
from ..core.models import ReplacementSpec
from ..core.modifier import PDFModifier, batch_process
from ..logger import setup_logging

logger = setup_logging(__name__)

mcp = FastMCP(
    "pdf-modifier-mcp",
)


def handle_mcp_errors(func: Callable[..., str]) -> Callable[..., str]:
    """Decorator to handle exceptions in MCP tools and return JSON error responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return func(*args, **kwargs)
        except PDFModifierError as e:
            return json.dumps(e.to_dict(), indent=2)
        except Exception as e:
            logger.exception("Unexpected error in MCP tool %s", func.__name__)
            return json.dumps(
                {
                    "success": False,
                    "error": "UNEXPECTED_ERROR",
                    "message": str(e),
                },
                indent=2,
            )

    return wrapper


@mcp.tool()
@handle_mcp_errors
def read_pdf_structure(input_path: str, password: str | None = None) -> str:
    """
    Extract the complete structural content of a PDF document.

    Returns detailed information about each page including:
    - Page dimensions (width, height)
    - All text elements with their:
      - Exact text content
      - Bounding box coordinates (x0, y0, x1, y1)
      - Origin point for text insertion
      - Font name and size
      - Color value

    Use this tool FIRST to understand the document layout before
    making any modifications. The output helps identify exact text
    to target for replacements.

    Args:
        input_path: Absolute path to the PDF file to analyze.
                   Must be a valid, accessible PDF file.
        password: Optional password if the PDF is encrypted.

    Returns:
        JSON string containing the complete page structure.
        On error, returns JSON with success=false and error details.

    Example:
        read_pdf_structure("/home/user/documents/invoice.pdf")
    """
    analyzer = PDFAnalyzer(input_path, password=password)
    result = analyzer.get_structure()
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def inspect_pdf_fonts(input_path: str, terms: list[str], password: str | None = None) -> str:
    """
    Search for specific text terms and report their font properties.

    Use this tool to understand the exact font styling of text you
    want to replace. This ensures replacements will match the
    surrounding document style as closely as possible.

    The tool searches through all pages and returns matches with:
    - Page number where the term was found
    - The search term that matched
    - Surrounding context (first 100 characters)
    - Font name (e.g., "Helvetica-Bold", "Times-Roman")
    - Font size in points
    - Origin coordinates for precise positioning

    Args:
        input_path: Absolute path to the PDF file to inspect.
        terms: List of text strings to search for (1-50 terms).
               Each term is searched as a substring.
        password: Optional password if the PDF is encrypted.

    Returns:
        JSON string with all matches and their font properties.
        Returns empty matches array if no terms are found.

    Example:
        inspect_pdf_fonts("/path/to/doc.pdf", ["Invoice", "$99.99", "Total"])
    """
    analyzer = PDFAnalyzer(input_path, password=password)
    result = analyzer.inspect_fonts(terms)
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def modify_pdf_content(
    input_path: str,
    output_path: str,
    replacements: dict[str, str],
    use_regex: bool = False,
    password: str | None = None,
) -> str:
    """
    Find and replace text in a PDF while preserving font styles.

    This tool performs text replacement by:
    1. Locating all occurrences of the search text
    2. Redacting the original text (white fill)
    3. Inserting the replacement text with matched styling

    IMPORTANT BEHAVIORS:
    - Text is matched within individual text spans
    - Font style is approximated using Base 14 fonts (Helvetica, Times, Courier)
    - Replacement text should be similar length to avoid overlap
    - Multiple replacements can be specified in a single call

    HYPERLINK SUPPORT:
    - Append "|URL" to create a clickable link: "Click Here|https://example.com"
    - Use "|void(0)" to neutralize existing links: "Product|void(0)"

    REGEX SUPPORT:
    - Set use_regex=true to treat keys as regex patterns
    - Useful for matching dates, IDs, or variable content
    - Example: {"Order #\\d+": "Order #REDACTED"}

    Args:
        input_path: Absolute path to the source PDF file.
        output_path: Absolute path where the modified PDF will be saved.
                    Parent directory must exist.
        replacements: Dictionary mapping old text to new text.
                     Keys are search strings (or regex if use_regex=true).
                     Values are replacement strings (optionally with |URL).
        use_regex: If true, treat replacement keys as regex patterns.
                  Default is false for literal string matching.
        password: Optional password if the source PDF is encrypted.

    Returns:
        JSON string with modification results including:
        - success: boolean indicating if operation completed
        - replacements_made: count of text spans modified
        - pages_modified: count of pages with changes
        - warnings: any non-fatal issues encountered

    Examples:
        # Simple text replacement
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"$99.99": "$149.99", "Draft": "Final"}
        )

        # Regex replacement for dates
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"\\d{2}/\\d{2}/\\d{4}": "01/01/2025"},
            use_regex=True
        )

        # Create hyperlink
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"Learn More": "Visit Website|https://example.com"}
        )
    """
    spec = ReplacementSpec(replacements=replacements, use_regex=use_regex)
    modifier = PDFModifier(input_path, output_path, password=password)
    result = modifier.process(spec)
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def list_pdf_hyperlinks(input_path: str, password: str | None = None) -> str:
    """
    Extract all existing hyperlinks and clickable URIs from a PDF.

    Use this tool to inventory the links in a document before or after
    making modifications. It reports the target URI, its location (bbox),
    and the text covered by the link if detectable.

    Args:
        input_path: Absolute path to the PDF file to scan.
        password: Optional password if the PDF is encrypted.

    Returns:
        JSON string with the inventory of found hyperlinks.

    Example:
        list_pdf_hyperlinks("/path/to/report.pdf")
    """
    analyzer = PDFAnalyzer(input_path, password=password)
    result = analyzer.get_hyperlinks()
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def batch_modify_pdf_content(
    input_paths: list[str],
    output_dir: str,
    replacements: dict[str, str],
    use_regex: bool = False,
    password: str | None = None,
) -> str:
    """
    Apply the same text replacements to multiple PDF files at once.

    Each file is processed independently -- a failure in one file does
    not stop the rest of the batch. Output files are written to
    ``output_dir`` using the same filename as the input.

    Args:
        input_paths: List of absolute paths to input PDF files.
        output_dir: Directory where modified PDFs will be saved.
        replacements: Dictionary mapping old text to new text.
        use_regex: If true, treat keys as regex patterns.
        password: Optional password if PDFs are encrypted.

    Returns:
        JSON string with batch results including per-file status.

    Example:
        batch_modify_pdf_content(
            ["/path/a.pdf", "/path/b.pdf"],
            "/path/output",
            {"Draft": "Final", "2024": "2025"}
        )
    """
    spec = ReplacementSpec(replacements=replacements, use_regex=use_regex)
    result = batch_process(input_paths, output_dir, spec, password=password)
    return result.model_dump_json(indent=2)


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
