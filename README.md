# PDF Modifier MCP

A robust Python tool for modifying text within PDF files while preserving the original layout and font styles. Features dual interfaces: a human-friendly CLI and an MCP server for AI agent integration.

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
- **Structured Output**: JSON responses for programmatic processing

## Installation

### From PyPI

```bash
pip install pdf-modifier-mcp
```

### From Source

```bash
git clone https://github.com/mlorentedev/pdf-modifier-mcp.git
cd pdf-modifier-mcp
poetry install
```

### Docker

```bash
docker pull mlorentedev/pdf-modifier-mcp
# Or build locally
docker build -t pdf-modifier-mcp .
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
# Start MCP server
make run-mcp
```

## Claude Desktop Integration

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pdf-modifier": {
      "command": "pdf-modifier-mcp",
      "args": []
    }
  }
}
```

Or with Docker:

```json
{
  "mcpServers": {
    "pdf-modifier": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "/path/to/pdfs:/data", "mlorentedev/pdf-modifier-mcp"]
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

## Usage Examples

### Price Adjustment

```bash
pdf-mod modify invoice.pdf updated.pdf \
  -r "$27.99=$45.00" \
  -r "$111.70=$128.71"
```

### Document Anonymization

```bash
pdf-mod modify document.pdf redacted.pdf \
  -r "Order # \d{3}-\d{7}-\d{7}=Order # REDACTED" \
  -r "John Doe=REDACTED" \
  --regex
```

### Date Rolling

```bash
pdf-mod modify report.pdf updated.pdf \
  -r "January \d{2}, 2024=February 01, 2025" \
  --regex
```

### Hyperlink Neutralization

```bash
# Disable existing links
pdf-mod modify doc.pdf safe.pdf -r "Click Here=Click Here|void(0)"
```

## Docker Usage

```bash
# Run CLI commands
docker run --rm -v $(pwd)/data:/data pdf-modifier-mcp \
  pdf-mod modify /data/input.pdf /data/output.pdf -r "old=new"

# Run MCP server
docker run -i --rm -v $(pwd)/data:/data pdf-modifier-mcp

# Using docker-compose
docker compose run cli modify /data/input/doc.pdf /data/output/result.pdf -r "old=new"
```

## Architecture Overview

The project follows a layered architecture to ensure separation of concerns and easy extensibility.

```text
┌─────────────────────────────────────────────────────┐
│                    Entry Points                      │
├──────────────────────┬──────────────────────────────┤
│   CLI (Typer+Rich)   │      MCP (FastMCP)           │
│   pdf-mod command    │   pdf-modifier-mcp server    │
│   Human interaction  │   LLM interaction            │
└──────────────────────┴──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   Core Layer                         │
├─────────────────────────────────────────────────────┤
│  modifier.py   │  analyzer.py  │  models.py         │
│  PDFModifier   │  PDFAnalyzer  │  Pydantic schemas  │
│                │               │                     │
│  exceptions.py │               │                     │
│  Error types   │               │                     │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   PyMuPDF (fitz)                     │
│              PDF manipulation engine                 │
└─────────────────────────────────────────────────────┘
```

### Layer Descriptions

#### 1. Interfaces Layer (Entry Points)

This is how users and agents interact with the system. It handles input parsing and output formatting but contains no business logic.

- **CLI (`interfaces/cli.py`)**: Uses `Typer` and `Rich` to provide a user-friendly command-line experience.
- **MCP Server (`interfaces/mcp.py`)**: Uses `FastMCP` to expose tools to AI agents (like Claude).

#### 2. Core Layer (Business Logic)

This layer coordinates the actual work. It uses Pydantic models to ensure data validity between the interfaces and the engine.

- **`modifier.py`**: The "Coordinator." It receives a `ReplacementSpec`, finds the text in the PDF, calculates positions, and applies changes.
- **`analyzer.py`**: The "Reader." It extracts text, analyzes structure (pages, text blocks), and inspects fonts.
- **`models.py`**: The "Contract." Defines strict data structures (Input/Output schemas) that all parts of the system must check against.

#### 3. Engine Layer (Infrastructure)

- **PyMuPDF (`fitz`)**: The low-level library that performs the raw I/O operations on the PDF file bytes. The Core layer wraps this dependency so it can be swapped or upgraded without breaking the Interfaces.

## Documentation

- [Roadmap](docs/ROADMAP.md): Development phases and changelog
- [Contributing](CONTRIBUTING.md): Setup, commands, and workflows
- [LLM Context](docs/llm.txt): AI/LLM agent context file

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on setting up the environment, running tests, and submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.
