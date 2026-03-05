---
title: Getting Started
description: Install pdf-modifier-mcp, use the CLI, and configure the MCP server for AI agents.
---

## Installation

Install from PyPI:

```bash
pip install pdf-modifier-mcp
```

Or run directly without installing:

```bash
uvx pdf-modifier-mcp
```

Requires Python 3.10 or later.

## CLI Usage

The `pdf-mod` command provides four operations: `modify`, `analyze`, `inspect`, and `--help`.

### Simple text replacement

```bash
pdf-mod modify input.pdf output.pdf -r "old text=new text"
```

Repeat `-r` for multiple replacements in a single pass:

```bash
pdf-mod modify input.pdf output.pdf -r "$99.99=$149.99" -r "Draft=Final"
```

### Regex replacement

Enable pattern matching with `--regex`:

```bash
pdf-mod modify input.pdf output.pdf -r "Order #\d+=Order #REDACTED" --regex
pdf-mod modify input.pdf output.pdf -r "January \d{2}, \d{4}=DATE REDACTED" --regex
```

### Hyperlinks

Append a URL after `|` to create a clickable link on the replacement text:

```bash
pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"
```

Use `void(0)` to neutralize an existing link:

```bash
pdf-mod modify input.pdf output.pdf -r "Click Here=Click Here|void(0)"
```

### Analyze PDF structure

Extract text content with page separators:

```bash
pdf-mod analyze input.pdf
```

Get full structure as JSON (positions, fonts, colors):

```bash
pdf-mod analyze input.pdf --json
```

### Inspect fonts

Search for terms and display their font properties:

```bash
pdf-mod inspect input.pdf "Invoice" "Total" "$"
```

Returns a table with columns: Page, Term, Font, Size, and Context.

## MCP Server

Start the server over stdio:

```bash
pdf-modifier-mcp
```

### Claude Desktop configuration

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

### MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_pdf_structure` | `input_path` | Extract complete PDF structure — text, positions, fonts, colors — as JSON. Use first to understand document layout. |
| `inspect_pdf_fonts` | `input_path`, `terms[]` | Search for text terms and return their font name, size, and position. Useful before making replacements. |
| `modify_pdf_content` | `input_path`, `output_path`, `replacements{}`, `use_regex?` | Find and replace text with style preservation. Supports regex and hyperlink syntax (`text\|URL`). Returns count of replacements and warnings. |

### How modification works

1. The tool opens the PDF with PyMuPDF and scans each page for matching text spans.
2. Matched spans are redacted (white fill) and `apply_redactions()` is called once per page.
3. Replacement text is inserted at the original position with matched font properties (family, weight, size, color).
4. Font names are mapped to the nearest Base 14 family: Helvetica, Times-Roman, or Courier, with bold variant detection.

Text matching operates within individual spans. If a target phrase is split across multiple spans in the PDF, it will not match — this is a known limitation of span-level processing.

## Architecture

```
Entry Points               Core Layer                  Engine
├── CLI (Typer + Rich)  →   ├── PDFModifier          →  PyMuPDF (fitz)
└── MCP Server (FastMCP)    ├── PDFAnalyzer
                            └── Pydantic models
```

- **PDFModifier**: Context manager. Collects replacements per page, batch-applies redactions, inserts styled text.
- **PDFAnalyzer**: Reads PDF structure via `page.get_text("dict")`, traverses block/line/span hierarchy.
- **Models**: `ReplacementSpec` (input, validates regex, max 100 replacements), `ModificationResult`, `PDFStructure`, `FontInspectionResult`.
