# PDF Modifier MCP

A Python tool for modifying text within PDF files while preserving the original layout and font styles. Features dual interfaces: a human-friendly CLI and an MCP server for AI agent integration.

[![CI](https://github.com/mlorentedev/pdf-modifier-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/mlorentedev/pdf-modifier-mcp/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/pdf-modifier-mcp.svg)](https://badge.fury.io/py/pdf-modifier-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Text Replacement**: Find and replace text while preserving font styles
- **Regex Support**: Pattern-based replacements for dates, IDs, prices
- **Hyperlink Management**: Create or neutralize clickable links
- **Style Preservation**: Matches bold/regular fonts using Base 14 fonts
- **Dual Interface**: CLI for humans, MCP server for AI agents

## Installation

### From PyPI

```bash
pip install pdf-modifier-mcp
```

### From Source

```bash
git clone https://github.com/mlorentedev/pdf-modifier-mcp.git
cd pdf-modifier-mcp
make setup
```

## Quick Start

### CLI Usage

```bash
# Simple text replacement
pdf-mod modify input.pdf output.pdf -r "old text=new text"

# Multiple replacements
pdf-mod modify input.pdf output.pdf -r "$99.99=$149.99" -r "Draft=Final"

# Regex replacement (dates, IDs, etc.)
pdf-mod modify input.pdf output.pdf -r "Order #\d+=Order #REDACTED" --regex

# Create hyperlinks
pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"

# Analyze PDF structure
pdf-mod analyze input.pdf --json

# Inspect fonts for specific terms
pdf-mod inspect input.pdf "Invoice" "Total" "$"
```

### MCP Server (for AI Agents)

```bash
pdf-modifier-mcp
```

## Claude Desktop Integration

Add to your Claude Desktop configuration (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pdf-modifier": {
      "command": "pdf-modifier-mcp"
    }
  }
}
```

Or run directly from PyPI without installing:

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

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `read_pdf_structure` | Extract complete PDF structure with text positions and fonts |
| `inspect_pdf_fonts` | Search for terms and report their font properties |
| `modify_pdf_content` | Find and replace text with style preservation |

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│                    Entry Points                      │
├──────────────────────┬──────────────────────────────┤
│   CLI (Typer+Rich)   │      MCP (FastMCP)           │
│   pdf-mod command    │   pdf-modifier-mcp server    │
└──────────────────────┴──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   Core Layer                         │
├─────────────────────────────────────────────────────┤
│  modifier.py   │  analyzer.py  │  models.py         │
│  PDFModifier   │  PDFAnalyzer  │  Pydantic schemas  │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   PyMuPDF (fitz)                     │
└─────────────────────────────────────────────────────┘
```

## Development

```bash
# Setup
make setup

# Run quality checks
make check

# Format code
make format

# Run tests
make test
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.
