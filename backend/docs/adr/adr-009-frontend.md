# ADR-009: Frontend — SvelteKit with PDF.js

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu

## Context

The frontend needs: drag-and-drop PDF upload, visual structure editor, AI-powered field detection panel, live preview overlay, and responsive design. Must work on desktop browsers.

## Decision

### Stack

- **Framework:** SvelteKit (SPA mode)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **PDF Rendering:** pdfjs-dist (Mozilla's PDF.js)
- **Build:** Vite
- **Testing:** Vitest + Playwright (E2E, deferred)

### Component Architecture

```
apps/web/src/lib/components/
├── PDFDropzone.svelte        # Drag & drop upload area
├── StructureViewer.svelte    # Visual representation of PDF elements
├── ReplacementForm.svelte    # "Old → New" replacement editor
├── AIPanel.svelte            # AI detection/classification results
├── PDFPreview.svelte         # PDF.js rendered preview with overlay
├── DownloadButton.svelte     # Export modified PDF
└── Layout.svelte             # App shell (header, sidebar, main)
```

### State Management

```typescript
// stores/session.ts
interface SessionState {
  sessionId: string | null;
  structure: PDFStructure | null;
  replacements: Map<string, string>;
  aiSuggestions: AISuggestions | null;
  isLoading: boolean;
  error: string | null;
}

// stores/pdf.ts
interface PDFState {
  file: File | null;
  pageCount: number;
  currentPage: number;
  zoom: number;
}
```

### API Client

```typescript
// api/client.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  upload: (file: File) => multipartPost('/api/pdf/upload', file),
  structure: (id: string) => get(`/api/pdf/${id}/structure`),
  replace: (id: string, replacements: Record<string, string>) =>
    post(`/api/pdf/${id}/replace`, { replacements }),
  download: (id: string) => getBlob(`/api/pdf/${id}/download`),
  aiDetect: (id: string) => post(`/api/ai/${id}/detect`),
  aiClassify: (id: string) => post(`/api/ai/${id}/classify`),
  aiRedact: (id: string) => post(`/api/ai/${id}/redact`),
};
```

### User Flow

```
1. Home Page (/)
   └── PDFDropzone (drag & drop or file picker)
       └── POST /api/pdf/upload → redirect to /edit/{sessionId}

2. Editor Page (/edit/{sessionId})
   ├── Left: StructureViewer (text elements with positions)
   ├── Center: PDFPreview (PDF.js rendered, zoomable)
   ├── Right: ReplacementForm + AIPanel
   └── Bottom: DownloadButton

3. AI Panel
   ├── "Detect Fields" button → POST /api/ai/{id}/detect
   ├── Shows detected fields as editable form
   ├── "Classify Document" → POST /api/ai/{id}/classify
   └── "Redact PII" → POST /api/ai/{id}/redact

4. Replace Flow
   ├── User edits ReplacementForm
   ├── Live preview updates (debounced)
   └── Download button → GET /api/pdf/{id}/download
```

### PDF.js Integration

```svelte
<script lang="ts">
  import * as pdfjsLib from 'pdfjs-dist';

  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

  async function renderPage(canvas: HTMLCanvasElement, pdf: any, pageNum: number) {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: zoom });
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    const ctx = canvas.getContext('2d')!;
    await page.render({ canvasContext: ctx, viewport }).promise;
  }
</script>
```

### Responsive Design

- Desktop-first (this is a tool, not a mobile app)
- Minimum viewport: 1024px
- Breakpoints: 1024px (tablet), 1440px (desktop), 1920px (large)

## Consequences

- SvelteKit provides minimal bundle size and fast builds
- PDF.js handles all PDF rendering in the browser (no server-side)
- TypeScript strict mode catches type errors early
- Tailwind CSS for rapid UI development
- Component-based architecture enables testability

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| React + Vite | Larger ecosystem | Heavier bundle, more boilerplate | **Rejected** |
| Vue + Vite | Good DX | Less Svelte's compiler advantages | **Rejected** |
| Vanilla JS | No dependencies | No DX, no tooling | **Rejected** |
| Server-rendered PDF | Simpler | Can't do live overlay, slow | **Rejected** |
