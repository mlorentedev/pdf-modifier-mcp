---
id: pdf-modifier-troubleshooting-pdf-preview
type: troubleshooting
status: active
tags: [troubleshooting, pdf-modifier, frontend]
created: "2026-08-04"
owner: manu
---

# PDF Preview (Frontend)

Troubleshooting the PDF.js-based preview component in the SvelteKit frontend.

## PDF Canvas Shows Black Screen

### Problem

After uploading a PDF, the preview panel shows a black canvas instead of the rendered page. The sidebar shows detected elements (structure analysis works), but the canvas is empty.

### Root Cause

The `<canvas>` element is wrapped inside a Svelte `{#if loading}` block. In `onMount`, `renderPage()` was called **before** `loading` was set to `false` — the canvas wasn't in the DOM yet, so `canvas` was `null` and the render silently no-oped.

### Diagnostic Steps

1. Check if the canvas element is in the DOM (browser DevTools)
2. Check if `renderPage` is being called when `canvas` is null
3. Add a `console.log(canvas)` inside `renderPage` to verify availability

### Solution

```javascript
// In onMount: set loading first, then await tick(), then render
loading = false;
await tick();
renderPage(currentPage);
```

### Prevention

- Canvas elements inside `{#if}` blocks are not available in `onMount`
- Always use `tick()` after changing the boolean that controls the canvas's visibility
- Reactive prop changes (e.g., `highlightText`) need a `$effect` to trigger re-render

## PDF.js getDocument: "expected either data, range, or url parameter"

### Problem

`pdfjsLib.getDocument(url)` throws: `"getDocument - expected either data, range, or url parameter."`

### Root Cause

**pdf.js v6** changed the `getDocument()` API. In v4/v5, passing a plain string URL worked. In v6, it requires an object parameter: `getDocument({ url })`.

### Diagnostic Steps

1. Check the pdfjs-dist version: `cat node_modules/pdfjs-dist/package.json | grep version`
2. Verify the `getDocument` call signature

### Solution

```javascript
// Before (v4/v5 API — fails in v6):
const loadingTask = pdfjsLib.getDocument(url);

// After (v6 API):
const loadingTask = pdfjsLib.getDocument({ url });
```

### Prevention

- Pin pdfjs-dist version in `package.json` to avoid unexpected breaking changes
- After upgrading pdfjs-dist, check the changelog for API changes

## PDF.js structuredClone Error: Failed to execute 'structuredClone'

### Problem

After fixing the `getDocument` API, the preview still fails with: `"Failed to execute 'structuredClone' on 'Window': [object Object] could not be cloned."`

### Root Cause

Passing a URL to `pdfjsLib.getDocument({ url })` triggers a worker fetch that can fail with `structuredClone` errors in certain pdf.js v6 configurations. The worker tries to clone a non-cloneable object when processing the document.

### Solution

Load the PDF data as a `Uint8Array` instead of fetching via URL:

```javascript
const response = await fetch(`/api/pdf/${sessionId}/download`);
const buffer = await response.arrayBuffer();
const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(buffer) });
```

### Prevention

- Use `{ data: Uint8Array }` for pdf.js document loading instead of `{ url }`
- This also avoids CORS issues and range-request requirements

## nginx Serves .mjs Files as application/octet-stream

### Problem

The PDF.js worker file `pdf.worker.min.mjs` fails to load as a module. Browser shows: `"Failed to fetch dynamically imported module"`. The file exists in the nginx container but is served with `Content-Type: application/octet-stream`.

### Root Cause

nginx does not have a default MIME type mapping for `.mjs` files. Adding a `types { application/javascript mjs; }` block in the `server` context **replaces** the entire default MIME table, causing ALL files (including `.html`) to be served as `application/octet-stream`.

### Diagnostic Steps

```bash
curl -I http://localhost:8080/pdf.worker.min.mjs | grep content-type
# Expected: Content-Type: application/javascript
# Bad:      Content-Type: application/octet-stream

curl -I http://localhost:8080/ | grep content-type
# Expected: Content-Type: text/html
# Bad:      Content-Type: application/octet-stream
```

### Solution

```nginx
# Include defaults FIRST, then add custom types
include /etc/nginx/mime.types;
types {
    application/javascript mjs;
}
```

### Prevention

- Always `include /etc/nginx/mime.types;` before adding custom `types {}` blocks
- Test MIME types with `curl -I` after nginx config changes
- Verify both the custom file AND regular files (`.html`, `.css`) have correct Content-Type