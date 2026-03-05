---
title: Getting Started
description: Install pdf-modifier-mcp, use the CLI, and configure the MCP server for AI agents.
---

## Installation

Install from PyPI:

```bash
pip install pdf-modifier-mcp
```

Or run directly without installing (requires [uv](https://docs.astral.sh/uv/)):

```bash
uvx pdf-modifier-mcp
```

Requires **Python 3.10** or later.

To install from source:

```bash
git clone https://github.com/mlorentedev/pdf-modifier-mcp.git
cd pdf-modifier-mcp
make setup
```

## CLI Usage

The `pdf-mod` command exposes four operations.

### Replace text

```bash
pdf-mod modify input.pdf output.pdf -r "old text=new text"
```

Stack multiple replacements in a single pass:

```bash
pdf-mod modify input.pdf output.pdf -r "$99.99=$149.99" -r "Draft=Final"
```

Font style (family, weight, size, color) is preserved automatically. The tool maps embedded fonts to the nearest Base 14 family — Helvetica, Times-Roman, or Courier — with bold variant detection.

### Regex replacement

Enable pattern matching with `--regex`:

```bash
pdf-mod modify input.pdf output.pdf -r "Order #\d+=Order #REDACTED" --regex
pdf-mod modify input.pdf output.pdf -r "January \d{2}, \d{4}=DATE REDACTED" --regex
```

Patterns are validated at input. Invalid regex returns an error before touching the PDF.

### Create and neutralize hyperlinks

Append a URL after `|` to make the replacement text clickable:

```bash
pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"
```

Neutralize an existing link with `void(0)`:

```bash
pdf-mod modify input.pdf output.pdf -r "Click Here=Click Here|void(0)"
```

Supported schemes: `http://`, `https://`, `mailto:`, `javascript:`.

### Analyze PDF structure

Plain text extraction with page separators:

```bash
pdf-mod analyze input.pdf
```

Full structure as JSON — every text span with position, font, size, and color:

```bash
pdf-mod analyze input.pdf --json
```

### Inspect fonts

Search for terms and display their font properties in a Rich table:

```bash
pdf-mod inspect input.pdf "Invoice" "Total" "$"
```

Output columns: Page, Term, Font, Size, Context (first 100 characters of the containing span).

## MCP Server

The MCP server exposes the same functionality over stdio for AI agent integration.

### Start the server

```bash
pdf-modifier-mcp
```

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdf-modifier": {
      "command": "pdf-modifier-mcp"
    }
  }
}
```

Or run from PyPI without a local install:

```json
{
  "mcpServers": {
    "pdf-modifier": {
      "command": "uvx",
      "args": ["pdf-modifier-mcp"]
    }
  }
}
```

### Cursor

Add an MCP server in Cursor settings with `pdf-modifier-mcp` as the command. Any MCP-compatible client that supports stdio transport will work.

### Available tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_pdf_structure` | `input_path` | Returns complete PDF structure — text, bounding boxes, font names, sizes, colors — as JSON. Use this first to understand the document layout before making changes. |
| `inspect_pdf_fonts` | `input_path`, `terms[]` | Searches for text terms (substring match) and returns font name, size, and position for each match. Run this before replacements to verify font handling. |
| `modify_pdf_content` | `input_path`, `output_path`, `replacements{}`, `use_regex?` | Find and replace text with style preservation. Supports regex patterns and hyperlink syntax (`text\|URL`). Returns replacements made, pages modified, and any warnings. |

All tools return structured JSON. Errors include a typed error code (`FILE_NOT_FOUND`, `READ_ERROR`, `WRITE_ERROR`), a human-readable message, and a details object.

### Typical agent workflow

1. Call `read_pdf_structure` to get the full document layout.
2. Call `inspect_pdf_fonts` with the target terms to confirm font properties.
3. Call `modify_pdf_content` with the replacement map.

## How it works

1. The PDF is opened with PyMuPDF and each page is scanned for text spans matching the target.
2. All matches on a page are collected, then redacted in batch (`apply_redactions()` called once per page).
3. Replacement text is inserted at the original coordinates with matched font properties.
4. Embedded font names are mapped to Base 14 equivalents: `"Arial-BoldMT"` becomes Helvetica-Bold (`HeBo`), `"TimesNewRomanPSMT"` becomes Times-Roman (`TiRo`), etc.

**Known limitation:** text matching operates within individual PDF spans. If a target phrase is split across two spans by the PDF producer, it will not match. Use `read_pdf_structure` to inspect span boundaries when this happens.

## Architecture

```
Entry Points               Core Layer                  Engine
+-----------------------+   +-----------------------+   +----------------+
| CLI (Typer + Rich)    |-->| PDFModifier           |-->| PyMuPDF (fitz) |
| MCP Server (FastMCP)  |   | PDFAnalyzer           |   +----------------+
+-----------------------+   | Pydantic v2 models    |
                            +-----------------------+
```

- **PDFModifier** — context manager that opens, modifies, and saves the PDF. Batch-redact strategy for efficiency.
- **PDFAnalyzer** — reads structure via `page.get_text("dict")`, traverses the block/line/span hierarchy.
- **Pydantic models** — `ReplacementSpec` validates input (regex compilation, max 100 replacements). `ModificationResult`, `PDFStructure`, and `FontInspectionResult` are the typed outputs.
