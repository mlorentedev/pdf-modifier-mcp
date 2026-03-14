---
title: Architecture
description: Technical architecture of pdf-modifier-mcp — layers, data flow, and design decisions.
---

## Overview

```
Entry Points               Core Layer                  Engine
+-----------------------+   +-----------------------+   +----------------+
| CLI (Typer + Rich)    |-->| PDFModifier           |-->| PyMuPDF (fitz) |
| MCP Server (FastMCP)  |   | PDFAnalyzer           |   +----------------+
+-----------------------+   | Pydantic v2 models    |
                            +-----------------------+
```

The project follows a clean architecture with two layers:

- **Interface layer** — thin wrappers that handle I/O format (CLI output, JSON-RPC responses)
- **Core layer** — pure business logic with typed inputs and outputs

Both interfaces share the same core. Adding a new interface (e.g., HTTP API) requires only a new file in `interfaces/` with no core changes.

## Core layer

### PDFModifier

The main modification engine. Implements a batch-redact strategy:

1. **Scan** — iterate all spans on a page, collect matches against the replacement spec
2. **Redact** — add redaction annotations for all matches, then call `apply_redactions()` once per page
3. **Insert** — place replacement text at original coordinates with matched font properties

This approach is more efficient than per-match processing because `apply_redactions()` is expensive and benefits from batching.

**Font mapping:** Embedded PDF font names are mapped to Base 14 equivalents using substring matching:

| Font name contains | Code | Base 14 name |
|-------------------|------|--------------|
| `courier` + `bold` | `CoBo` | Courier-Bold |
| `courier` | `Cour` | Courier |
| `times` or `serif` + `bold` | `TiBo` | Times-Bold |
| `times` or `serif` | `TiRo` | Times-Roman |
| (any) + `bold` | `HeBo` | Helvetica-Bold |
| (default) | `helv` | Helvetica |

**Hyperlink support:** Replacement values can include a URL suffix (`text|URL`). The modifier calculates text width using `fitz.Font.text_length()` and creates a link annotation covering the text area.

### PDFAnalyzer

Read-only analysis of PDF structure. Provides:

- `get_structure()` — full page/element hierarchy as Pydantic models
- `extract_text()` — plain text with page separators
- `inspect_fonts()` — search for terms and report font properties
- `get_hyperlinks()` — inventory all URI links in the document

All methods use `_open_doc()` for consistent password handling.

### Pydantic models

Input and output contracts are defined as Pydantic v2 models:

- **`ReplacementSpec`** — validates input, compiles regex patterns via `model_validator`
- **`ModificationResult`** — success status, counts, warnings
- **`PDFStructure` / `PageStructure` / `TextElement`** — document structure hierarchy
- **`FontInspectionResult` / `FontMatch`** — font inspection output
- **`HyperlinkInventory` / `Hyperlink`** — link extraction output

### Exception hierarchy

All exceptions inherit from `PDFModifierError`, which includes:
- Typed `code` field (e.g., `"FILE_NOT_FOUND"`)
- `to_dict()` method for JSON serialization
- `details` dict for structured error context

```
PDFModifierError
├── PDFNotFoundError    (FILE_NOT_FOUND)
├── PDFReadError        (READ_ERROR)
├── PDFWriteError       (WRITE_ERROR)
├── PDFPasswordError    (PASSWORD_ERROR)
└── InvalidPatternError (INVALID_PATTERN)
```

## Interface layer

### MCP server

Uses FastMCP with stdio transport. Each tool is a thin wrapper:

1. Construct core objects from parameters
2. Call core method
3. Serialize result to JSON string

The `@handle_mcp_errors` decorator catches all exceptions and returns structured JSON error responses, so tool calls never raise — they always return parseable JSON.

### CLI

Uses Typer with Rich console output. Commands map 1:1 to core methods:

| Command | Core method |
|---------|-------------|
| `modify` | `PDFModifier.process()` |
| `analyze` | `PDFAnalyzer.get_structure()` / `extract_text()` |
| `inspect` | `PDFAnalyzer.inspect_fonts()` |
| `links` | `PDFAnalyzer.get_hyperlinks()` |

## Logging

Structured JSON logging to `~/.pdf-modifier/logs/pdf-modifier.log` with 5MB rotation (3 backups). Uses UTC timestamps. Logging is file-only — no stdout pollution for MCP server compatibility.

## Design decisions

**Why Base 14 fonts only?** PDF viewers are required to have Base 14 fonts available. Using them guarantees the replacement text will render correctly on any viewer without embedding custom fonts.

**Why batch redactions?** PyMuPDF's `apply_redactions()` rebuilds the page content stream. Calling it once per page (with all redactions queued) is significantly faster than calling it per-match.

**Why no async?** PDF operations are CPU-bound (parsing, rendering). Async would add complexity without performance benefit. The MCP server uses synchronous tool handlers, which FastMCP runs in threads for concurrency.

**Why no file size validation?** The project is zero-config by design. PyMuPDF handles large files efficiently with memory-mapped I/O. Adding size limits would require configuration, breaking the zero-config principle.
