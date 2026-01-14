# Roadmap: PDF Modifier MCP

This document outlines the project's direction, including completed features and a comprehensive list of planned improvements.

> **See Also**: [llm.txt](./llm.txt) for LLM/agent context.

---

## Current Release: v0.0.1

Initial release with dual-interface PDF modification capabilities.

### Included Features
- Text replacement with style preservation
- Regex pattern support
- Hyperlink creation/neutralization
- CLI interface (Typer + Rich)
- MCP server interface (FastMCP)
- Pydantic models for validation
- Typed exception hierarchy
- 90% test coverage
- CI/CD with semantic release
- Docker support

---

## Planned Features & Improvements

Use the provided `gh` commands to easily add these tasks to the project's issue tracker.

### 1. Core Modification Engine

#### **[High] Text Reflow & Layout Management**
Implement a basic layout engine to handle text that is longer or shorter than the original.
*   **Goal**: Prevent text overlap and gaps.
*   **Details**: Add support for multi-line wrapping and overflow warnings ("check only" mode).
```bash
gh issue create --title "feat(core): text reflow and layout management" --body "Implement a basic layout engine that respects the original bounding box. Add support for multi-line replacement (wrapping text). Add a 'check only' mode that warns if the new text won't fit in the original bbox." --label "enhancement,high-priority,core"
```

#### **[Medium] Advanced Font Support**
Improve font matching beyond the current "Base 14" approximation.
*   **Goal**: Better visual fidelity for documents with custom fonts.
*   **Details**: Enhance `_get_font_properties` to detect weight/flags. Support providing paths to custom font files.
```bash
gh issue create --title "feat(core): advanced font support and custom font paths" --body "Enhance _get_font_properties to better detect font attributes. Allow users to provide a path to a custom font file for replacements. Investigate extracting embedded fonts." --label "enhancement,core"
```

#### **[Medium] Multi-span Regex Matching**
Enable regex patterns to match text across element boundaries.
*   **Goal**: Replace phrases that are split by formatting changes or line breaks.
*   **Details**: Stitch text spans together for matching, then map replacements back to original positions.
```bash
gh issue create --title "feat(core): multi-span regex matching" --body "Implement a text extraction strategy that stitches spans together for matching, then maps the replacement back to the individual spans." --label "enhancement,core"
```

#### **[Medium] Image Replacement**
Ability to identify and swap images within the PDF.
*   **Goal**: Update logos, diagrams, or placeholder images programmatically.
```bash
gh issue create --title "feat(core): image replacement support" --body "Add functionality to identify images by location/index and replace them with new image files, maintaining aspect ratio or bounds." --label "enhancement,core"
```

#### **[Low] Color Space Handling**
Support for CMYK and Grayscale color spaces.
*   **Goal**: Prevent color shifting when modifying professional print documents.
```bash
gh issue create --title "feat(core): support CMYK and Grayscale color spaces" --body "Detect the color space of the original text span. Support CMYK input/output for text insertion in _convert_color." --label "enhancement,low-priority"
```

### 2. Analysis & Extraction

#### **[Medium] Table Extraction**
Detect and parse table structures into structured data.
*   **Goal**: Convert PDF tables into JSON/CSV for analysis.
```bash
gh issue create --title "feat(analyzer): table extraction to JSON" --body "Integrate a library or logic to detect table boundaries and extract rows/columns into structured JSON." --label "enhancement,analyzer"
```

#### **[Low] Link Inventory**
Extract a list of all existing hyperlinks.
*   **Goal**: Audit and validate links in a document.
```bash
gh issue create --title "feat(analyzer): hyperlink inventory" --body "Add a method/tool to list all hyperlinks in the document with their locations and URIs." --label "enhancement,analyzer"
```

#### **[Low] Metadata Management**
View and edit PDF metadata.
*   **Goal**: Update Title, Author, Keywords, and XMP data.
```bash
gh issue create --title "feat(analyzer): metadata read/write" --body "Add tools to read and modify standard PDF metadata fields (XMP and Info dict)." --label "enhancement,analyzer"
```

### 3. MCP & Agents

#### **[High] Visual Preview Tool**
Allow agents to request a rendered image of a page.
*   **Goal**: Enable agents to visually verify their changes (e.g., checking for text overflow).
*   **Details**: Render a specific page to a base64 image.
```bash
gh issue create --title "feat(mcp): preview_pdf_modification tool" --body "Create an MCP tool that renders a specific page to an image (base64). Essential for agents to verify visual layout after text replacement." --label "mcp,enhancement"
```

#### **[Medium] Batch Processing**
Modify multiple PDFs in a single request.
*   **Goal**: Apply a standard set of redactions or updates to a folder of documents.
```bash
gh issue create --title "feat(mcp): batch processing support" --body "Add an MCP tool to apply the same set of replacements to a list of files or a directory." --label "mcp,enhancement"
```

### 4. Security & Compliance

#### **[High] PDF Sanitization**
Remove potentially malicious or unwanted content.
*   **Goal**: Ensure documents are safe for distribution.
*   **Details**: Strip JavaScript, embedded files, and non-printable objects.
```bash
gh issue create --title "feat(security): pdf sanitization tool" --body "Add a 'sanitize' command/tool to strip JavaScript, embedded files, and non-printable objects to ensure safety." --label "security,enhancement"
```

#### **[Medium] Password & Encryption Support**
Handle encrypted PDF documents.
*   **Goal**: Process protected documents and apply new security settings.
```bash
gh issue create --title "feat(security): password protected pdf support" --body "Add parameters to open encrypted PDFs with a password and options to save with encryption/permissions." --label "security"
```
